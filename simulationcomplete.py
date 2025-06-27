import streamlit as st
import plotly.graph_objects as go
import matplotlib.pyplot as plt
import math
from datetime import datetime

# CONFIG
st.set_page_config(page_title="Simulation PV & Ombres", layout="centered")
st.title("🔆 Simulation photovoltaïque dynamique avec obstacles")

st.markdown("Configurez votre installation solaire et ajoutez des obstacles pour visualiser les pertes d’ombrage et estimer votre production réelle.")

# === CONFIG UTILISATEUR ===
with st.sidebar:
    st.header("⚙️ Paramètres")
    panneau = st.selectbox("Type de panneau", ["Monocristallin", "Polycristallin", "Amorphe", "Hétérojonction", "Bifacial"])
    ville = st.selectbox("Ville", ["Marseille", "Lille", "Paris", "Nice", "Metz", "Nancy", "Colmar", "Strasbourg", "Toulouse", "Lyon", "Bordeaux"])
    mois = st.slider("Mois", 1, 12, datetime.now().month)
    heure = st.slider("Heure", 6, 18, 12)
    meteo = st.radio("Météo", ["Ensoleillé", "Nuageux", "Pluvieux"])
    nb_panneaux = st.slider("Nombre de panneaux", 1, 25, 20)

# === OBSTACLES ===
with st.sidebar:
    st.header("🪵 Obstacles")
    nb_obstacles = st.slider("Combien ?", 0, 3, 1)
    obstacles = []
    for i in range(nb_obstacles):
        with st.expander(f"Obstacle #{i+1}", expanded=True):
            type_obs = st.selectbox("Type", ["Arbre", "Bâtiment", "Mur"], key=f"type{i}")
            h = st.slider("Hauteur (m)", 1, 20, 5, key=f"h{i}")
            d = st.slider("Distance (m)", 1, 50, 10, key=f"d{i}")
            obstacles.append({"type": type_obs, "hauteur": h, "distance": d})

# === DONNÉES DE BASE ===
villes = {
    "Marseille": {"lat": 43.3, "irr": 1824},
    "Nice": {"lat": 43.7, "irr": 1800},
    "Paris": {"lat": 48.9, "irr": 1400},
    "Lille": {"lat": 50.6, "irr": 1300},
    "Metz": {"lat": 49.1, "irr": 1350},
    "Nancy": {"lat": 48.7, "irr": 1360},
    "Colmar": {"lat": 48.1, "irr": 1400},
    "Strasbourg": {"lat": 48.6, "irr": 1380},
    "Toulouse": {"lat": 43.6, "irr": 1650},
    "Lyon": {"lat": 45.8, "irr": 1600},
    "Bordeaux": {"lat": 44.8, "irr": 1550},
}
latitude = villes[ville]["lat"]
irradiation = villes[ville]["irr"]

declinaison = 23.45 * math.sin(math.radians(360 / 12 * (mois - 2)))
hauteur_midi = 90 - latitude + declinaison
hauteur_soleil = max(0, hauteur_midi * math.sin(math.pi * (heure - 6) / 12))

# === DONNÉES PANNEAU ===
types = {
    "Monocristallin": {"rendement": 20.0, "prix": 1.20, "prod_ref": 11862},
    "Polycristallin": {"rendement": 17.5, "prix": 1.00, "prod_ref": 10500},
    "Amorphe": {"rendement": 10.0, "prix": 0.80, "prod_ref": 6000},
    "Hétérojonction": {"rendement": 21.5, "prix": 1.50, "prod_ref": 12500},
    "Bifacial": {"rendement": 19.5, "prix": 1.40, "prod_ref": 11200},
}
rendement = types[panneau]["rendement"]
prod_ref = types[panneau]["prod_ref"]
prix_watt = types[panneau]["prix"]
power_per_panel = 0.4
surface_panel = 1.7
facteur_meteo = {"Ensoleillé": 1.0, "Nuageux": 0.75, "Pluvieux": 0.55}[meteo]

# === CALCULS ===
kWp = power_per_panel * nb_panneaux
surface_totale = surface_panel * nb_panneaux
prod_base = (kWp / 8) * prod_ref * (irradiation / 1824) * facteur_meteo

def perte_ombrage_dyn(obs, h_sun):
    pertes = 0
    for o in obs:
        try:
            angle = math.degrees(math.atan(o["hauteur"] / o["distance"]))
        except:
            angle = 90
        if angle > h_sun:
            pertes += min(angle / 90 * 25, 25)
    return min(pertes, 60)

perte_pct = perte_ombrage_dyn(obstacles, hauteur_soleil)
prod_corrigee = prod_base * (1 - perte_pct / 100)
efficacite = prod_corrigee / surface_totale
cout = kWp * 1000 * prix_watt

# === CONSOMMATION ===
conso_maison = 8260
autoconso = min(prod_corrigee, conso_maison) * 0.9
injecte = max(0, prod_corrigee - autoconso)
reprise = max(0, conso_maison - autoconso)

# === AFFICHAGE ===
st.subheader("📊 Résultats techniques")
col1, col2 = st.columns(2)
col1.metric("🔆 Production estimée", f"{prod_corrigee:.0f} kWh/an")
col2.metric("❌ Perte ombrage", f"{perte_pct:.1f} %")
col1.metric("📐 Efficacité", f"{efficacite:.1f} kWh/m²/an")
col2.metric("💰 Coût total", f"{cout:,.0f} €")

st.markdown(f"""
**Ville :** `{ville}`  
**Heure :** `{heure}h`  
**Hauteur du soleil :** `{hauteur_soleil:.1f}°`
""")

# === ÉNERGIE ===
st.subheader("⚡ Répartition de l'énergie")
fig1, ax1 = plt.subplots()
labels = ["Autoconsommée", "Injectée", "Reprise"]
values = [autoconso, injecte, reprise]
colors = ["green", "orange", "red"]
ax1.bar(labels, values, color=colors)
ax1.set_ylabel("Énergie (kWh)")
ax1.set_title("Répartition annuelle")
ax1.grid(True)
st.pyplot(fig1)

# === VISUEL PLOTLY ===
st.subheader("🌇 Vue schématique (orientation sud)")

fig = go.Figure()

# Maison
fig.add_trace(go.Scatter(
    x=[0, 0], y=[0, 6],
    mode="lines+text",
    line=dict(width=10, color="gray"),
    text=["Maison"], textposition="top right"
))

# Obstacles
for i, obs in enumerate(obstacles):
    fig.add_trace(go.Scatter(
        x=[obs["distance"], obs["distance"]],
        y=[0, obs["hauteur"]],
        mode="lines+text",
        line=dict(width=6, color="brown"),
        text=[f"{obs['type']} {obs['hauteur']}m"],
        textposition="top center"
    ))

# Soleil
fig.add_trace(go.Scatter(
    x=[-5], y=[20],
    mode="markers+text",
    marker=dict(size=30, color="gold"),
    text=["☀️ Soleil (midi)"],
    textposition="bottom right"
))

fig.update_layout(
    height=400,
    xaxis=dict(title="Distance (m)", range=[-10, 60]),
    yaxis=dict(title="Hauteur (m)", range=[0, 25]),
    margin=dict(l=40, r=40, t=40, b=40),
    plot_bgcolor="#f9fafb",
    paper_bgcolor="#ffffff",
    showlegend=False
)

st.plotly_chart(fig, use_container_width=True)

st.markdown("---")
st.caption("Projet S8 – Attaibe Salma – Simulation PV dynamique – 2025")

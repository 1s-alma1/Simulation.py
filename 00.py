import streamlit as st
import plotly.graph_objects as go
import matplotlib.pyplot as plt
import math
from datetime import datetime

# CONFIG
st.set_page_config(page_title="Simulation PV & Ombres", layout="centered")
st.title("🌞 Simulation photovoltaïque dynamique avec ombrages")

st.markdown("Ce simulateur combine la configuration de votre installation solaire avec les obstacles et la météo pour estimer la production, les pertes et l’ombrage visuel.")

# --- ENTRÉES PHOTOVOLTAÏQUES ---
st.sidebar.header("⚙️ Configuration PV")
panneau = st.sidebar.selectbox("Type de panneau solaire", ["Monocristallin", "Polycristallin", "Amorphe", "Hétérojonction", "Bifacial"])
ville = st.sidebar.selectbox("Ville d'installation", ["Marseille", "Lille", "Paris", "Nice", "Metz", "Nancy", "Colmar", "Strasbourg", "Toulouse", "Lyon", "Bordeaux"])
mois = st.sidebar.slider("Mois de l'année", 1, 12, datetime.now().month)
heure = st.sidebar.slider("Heure de la journée", 6, 18, 12)
meteo = st.sidebar.radio("Conditions météo", ["Ensoleillé", "Nuageux", "Pluvieux"])
nb_panneaux = st.sidebar.slider("Nombre de panneaux", 0, 25, 20)

# --- OBSTACLES ---
st.sidebar.header("🪵 Obstacles")
nb_obstacles = st.sidebar.slider("Nombre d'obstacles", 0, 3, 1)

obstacles = []
for i in range(nb_obstacles):
    with st.sidebar.expander(f"Obstacle #{i+1}", expanded=True):
        type_obs = st.selectbox("Type", ["Arbre", "Bâtiment", "Mur"], key=f"type{i}")
        hauteur = st.slider("Hauteur (m)", 1, 20, 5, key=f"haut{i}")
        distance = st.slider("Distance (m)", -20, 40, 10, key=f"dist{i}")
        obstacles.append({"type": type_obs, "hauteur": hauteur, "distance": distance})

# --- DONNÉES PAR VILLE ---
villes_data = {
    "Marseille": {"lat": 43.3, "irradiation": 1824},
    "Nice": {"lat": 43.7, "irradiation": 1800},
    "Paris": {"lat": 48.9, "irradiation": 1400},
    "Lille": {"lat": 50.6, "irradiation": 1300},
    "Metz": {"lat": 49.1, "irradiation": 1350},
    "Nancy": {"lat": 48.7, "irradiation": 1360},
    "Colmar": {"lat": 48.1, "irradiation": 1400},
    "Strasbourg": {"lat": 48.6, "irradiation": 1380},
    "Toulouse": {"lat": 43.6, "irradiation": 1650},
    "Lyon": {"lat": 45.8, "irradiation": 1600},
    "Bordeaux": {"lat": 44.8, "irradiation": 1550}
}
latitude = villes_data[ville]["lat"]
irradiation = villes_data[ville]["irradiation"]
declinaison = 23.45 * math.sin(math.radians(360 / 12 * (mois - 2)))
hauteur_midi = 90 - latitude + declinaison
hauteur_soleil = max(0, hauteur_midi * math.sin(math.pi * (heure - 6) / 12))

# --- DONNÉES PANNEAU ---
data = {
    "Monocristallin": {"rendement": 20.0, "prix": 1.20, "prod_ref": 11862},
    "Polycristallin": {"rendement": 17.5, "prix": 1.00, "prod_ref": 10500},
    "Amorphe": {"rendement": 10.0, "prix": 0.80, "prod_ref": 6000},
    "Hétérojonction": {"rendement": 21.5, "prix": 1.50, "prod_ref": 12500},
    "Bifacial": {"rendement": 19.5, "prix": 1.40, "prod_ref": 11200}
}
rendement = data[panneau]["rendement"]
prod_ref = data[panneau]["prod_ref"]
prix_watt = data[panneau]["prix"]
puissance_par_panneau = 0.4
surface_par_module = 1.7
puissance_kWp = nb_panneaux * puissance_par_panneau
puissance_kWp_ref = 8
surface_totale = nb_panneaux * surface_par_module
facteur_meteo = {"Ensoleillé": 1.0, "Nuageux": 0.75, "Pluvieux": 0.55}[meteo]

# --- CALCUL OMBRAGE CUMULÉ ---
def perte_ombrage(obs, h_sun):
    total = 0
    for o in obs:
        try:
            angle = math.degrees(math.atan(o["hauteur"] / abs(o["distance"])))
        except ZeroDivisionError:
            angle = 90
        if angle > h_sun:
            total += min(angle / 90 * 25, 25)
    return min(total, 60)

perte_pct = perte_ombrage(obstacles, hauteur_soleil)

# --- PRODUCTION ---
production = (puissance_kWp / puissance_kWp_ref) * prod_ref * (irradiation / 1824) * facteur_meteo
production_corrigee = production * (1 - perte_pct / 100)
efficacite = production_corrigee / surface_totale if surface_totale else 0
cout_total = puissance_kWp * 1000 * prix_watt

# --- CONSOMMATION ---
conso_batiment = 8260
autoconso = min(conso_batiment, production_corrigee) * 0.9
injecte = max(0, production_corrigee - autoconso)
reprise = max(0, conso_batiment - autoconso)

# --- AFFICHAGE DES RÉSULTATS ---
st.subheader("📊 Résultats")
col1, col2 = st.columns(2)
col1.metric("Production nette", f"{production_corrigee:.0f} kWh/an")
col2.metric("Perte d’ombrage", f"{perte_pct:.1f} %")
col1.metric("Efficacité réelle", f"{efficacite:.1f} kWh/m²/an")
col2.metric("Coût total estimé", f"{cout_total:,.0f} €")

# --- GRAPHIQUE ÉNERGIE ---
st.subheader("⚡ Répartition de l'énergie")
fig1, ax1 = plt.subplots()
labels = ["Autoconsommée", "Injectée", "Reprise"]
values = [autoconso, injecte, reprise]
colors = ["green", "orange", "red"]
ax1.bar(labels, values, color=colors)
ax1.set_ylabel("Énergie (kWh)")
ax1.grid(axis='y')
st.pyplot(fig1)

# --- VISUALISATION PLOTLY ---
st.subheader("🖼️ Vue simplifiée (orientation sud)")

fig = go.Figure()

# Maison
fig.add_trace(go.Scatter(
    x=[0, 0], y=[0, 6],
    mode="lines+text",
    line=dict(width=10, color="gray"),
    text=["Maison"], textposition="top right"
))

# Obstacles
colors = ["green", "brown", "black"]
for i, obs in enumerate(obstacles):
    fig.add_trace(go.Scatter(
        x=[obs["distance"], obs["distance"]],
        y=[0, obs["hauteur"]],
        mode="lines+text",
        line=dict(width=6, color=colors[i % len(colors)]),
        text=[f"{obs['type']} ({obs['hauteur']}m)"],
        textposition="top center"
    ))

# Soleil
fig.add_trace(go.Scatter(
    x=[0], y=[20],
    mode="markers+text",
    marker=dict(size=30, color="gold"),
    text=["☀️ Soleil (midi)"],
    textposition="bottom center"
))

fig.update_layout(
    height=400,
    xaxis=dict(title="Distance (m)", range=[-25, 50]),
    yaxis=dict(title="Hauteur (m)", range=[0, 25]),
    plot_bgcolor="#f8f9fa",
    paper_bgcolor="#ffffff",
    margin=dict(l=40, r=40, t=40, b=40),
    showlegend=False
)

st.plotly_chart(fig, use_container_width=True)

st.markdown("---")
st.caption("Projet S8 – Attaibe Salma – Simulation PV + ombrage – 2025")

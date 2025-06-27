import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import math
from datetime import datetime

# CONFIGURATION
st.set_page_config(page_title="Simulation Photovoltaïque Complète", layout="centered")
st.title("☀️ Simulation Photovoltaïque Résidentielle Complète")

st.markdown("Ce simulateur inclut le type de panneau, la météo, l'heure, le mois et les ombrages pour une étude réaliste.")

# ENTRÉES PRINCIPALES
panneau = st.selectbox("🔧 Type de panneau solaire", ["Monocristallin", "Polycristallin", "Amorphe", "Hétérojonction", "Bifacial"])
ville = st.selectbox("📍 Ville d'installation", ["Marseille", "Lille", "Paris", "Nice", "Metz", "Nancy", "Colmar", "Strasbourg", "Toulouse", "Lyon", "Bordeaux"])
mois = st.slider("📅 Mois de l'année", 1, 12, datetime.now().month)
heure = st.slider("🕒 Heure de la journée", 6, 18, 12)
meteo = st.radio("🌦️ Conditions météo", ["Ensoleillé", "Nuageux", "Pluvieux"])
nb_panneaux = st.slider("🔢 Nombre de panneaux", 0, 25, 20)

# DONNÉES PAR VILLE
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

# DONNÉES PAR PANNEAU
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

# GÉNÉRALES
surface_par_module = 1.7
puissance_par_panneau = 0.4
puissance_kWp = nb_panneaux * puissance_par_panneau
puissance_kWp_ref = 8
surface_totale = nb_panneaux * surface_par_module
facteur_meteo = {"Ensoleillé": 1.0, "Nuageux": 0.75, "Pluvieux": 0.55}[meteo]

# OBSTACLE FIXE
hauteur_obstacle = 8
distance_obstacle = 10
angle_obstacle = math.degrees(math.atan(hauteur_obstacle / distance_obstacle))

# CALCUL PERTE D’OMBRAGE
if angle_obstacle > hauteur_soleil:
    perte_ombrage = min((angle_obstacle / 90) * 25, 25)
else:
    perte_ombrage = 0

# PRODUCTION
production = (puissance_kWp / puissance_kWp_ref) * prod_ref * (irradiation / 1824) * facteur_meteo
production_corrigee = production * (1 - perte_ombrage / 100)
efficacite = production_corrigee / surface_totale if surface_totale else 0
cout_total = puissance_kWp * 1000 * prix_watt

# CONSOMMATION
conso_batiment = 8260
autoconso = min(conso_batiment, production_corrigee) * 0.9
injecte = max(0, production_corrigee - autoconsommation)
reprise = max(0, conso_batiment - autoconsommation)

# AFFICHAGE
st.subheader("📊 Résultats de simulation")
col1, col2 = st.columns(2)
col1.metric("Production corrigée", f"{production_corrigee:.0f} kWh/an")
col2.metric("Puissance installée", f"{puissance_kWp:.2f} kWc")

col1, col2 = st.columns(2)
col1.metric("Efficacité réelle", f"{efficacite:.1f} kWh/m²/an")
col2.metric("Coût estimé", f"{cout_total:,.0f} €")

st.markdown(f"""
**Ville :** `{ville}`  
**Mois :** `{mois}`  
**Heure :** `{heure}h`  
**Météo :** `{meteo}`  
**Hauteur du soleil :** `{hauteur_soleil:.1f}°`  
**Perte d’ombrage estimée :** `{perte_ombrage:.1f} %`
""")

# GRAPHIQUE ÉNERGIE
st.subheader("⚡ Répartition de l'énergie")
fig1, ax1 = plt.subplots()
labels = ["Autoconsommée", "Injectée", "Reprise"]
values = [autoconso, injecte, reprise]
colors = ["green", "orange", "red"]
ax1.bar(labels, values, color=colors)
ax1.set_ylabel("Énergie (kWh)")
ax1.set_title("Répartition annuelle")
ax1.grid(axis='y')
st.pyplot(fig1)

# COURBE DES PERTES
st.subheader("🕒 Courbe des pertes d'ombrage journalières")
heures = list(range(6, 19))
hauteurs = [max(0, hauteur_midi * math.sin(math.pi * (h - 6) / 12)) for h in heures]
pertes = [min((angle_obstacle / 90) * 25, 25) if angle_obstacle > hs else 0 for hs in hauteurs]

fig2, ax2 = plt.subplots()
ax2.plot(heures, pertes, color='orange', linewidth=2)
ax2.set_xticks(heures)
ax2.set_xlabel("Heure")
ax2.set_ylabel("Perte d'ombrage (%)")
ax2.set_title("Variation des pertes d'ombrage dans la journée")
ax2.grid(True)
st.pyplot(fig2)

# SIGNATURE
st.markdown("---")
st.markdown("**Attaibe Salma – Université de Lorraine**")
st.caption("Simulation dynamique PV avec ombrage – Projet S8 – Juin 2025")


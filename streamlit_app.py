import streamlit as st
import pandas as pd
from streamlit_folium import st_folium
import folium
import geopandas as gpd
import matplotlib.pyplot as plt
import plotly.express as px

dataset = pd.read_csv("./Samples/traitement_general.csv")

st.set_page_config(layout='wide', initial_sidebar_state='expanded')
st.sidebar.header('DITP Dashboard `version 1`')

with open('style.css') as f:
    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    
st.markdown("<h1 style='text-align: center; color: black;'>DIRECTION INTERMINISTERIELLE DE LA TRANSFORMATION PUBLIQUE</h1>", unsafe_allow_html=True)

st.image("./Images/Logo_Services_Publics_Plus_.png", caption=None, width=None, use_column_width=None, clamp=False, channels="RGB", output_format="auto")

nbr_total_avis = len(dataset)

nbr_avis_neg = 0
nbr_avis_pos = 0
nbr_avis_neu = 0

for elt in dataset["Labels"]:
    if elt == "Négatif":
        nbr_avis_neg += 1
    elif elt == "Positif":
        nbr_avis_pos += 1
    else:
        nbr_avis_neu += 1

st.markdown("<h1 style='text-align: center; color: black;'>ADMINISTRATIONS CONCERNEES</h1>", unsafe_allow_html=True)
st.markdown("<h1 style='text-align: center; color: black;'>POLICE NATIONALE - GENDARMERIE - COMMISSARIAT</h1></br></br>", unsafe_allow_html=True)

# Nomnre total d'avis
st.markdown(f"## Nombre total d\'avis : {nbr_total_avis}")
col1, col2, col3 = st.columns(3)
col1.metric("Nombre d'avis Neutres", f"{nbr_avis_neu}")
col2.metric("Nombre d'avis Positifs", f"{nbr_avis_pos}")
col3.metric("Nombre d'avis Négatifs", f"{nbr_avis_neg}")

#
col_1, col_2 = st.columns(2)
with col_1:
    # Le service qui a le plus d'avis
    services = dataset.groupby('Administration').size().reset_index(name="Nombre d'avis")
    services = services.sort_values("Nombre d'avis", ascending=False)

    nbr_avis_commist = 0
    nbr_avis_police = 0
    nbr_avis_gdmr = 0

    for index in range(len(services)):
        if "Commissariat" in services["Administration"][index]:
            nbr_avis_commist += services["Nombre d'avis"][index]
        elif "Police" in services["Administration"][index] and "Commissariat" not in services["Administration"][index]:
            nbr_avis_police += services["Nombre d'avis"][index]
        elif "Gendarmerie" in services["Administration"][index]:
            nbr_avis_gdmr += services["Nombre d'avis"][index]
            
    services_dict = {
        "Administration": ["Police Nationale", "Commissariat de Police", "Gendarmerie Nationale"],
        "Nombre d'avis": [nbr_avis_police, nbr_avis_commist, nbr_avis_gdmr]
    }

    df_services = pd.DataFrame(services_dict)
            
    figure = px.pie(
        data_frame=df_services,
        names="Administration", values="Nombre d'avis",
        title="Le service ayant le plus d'avis",
        width=500
    )

    st.plotly_chart(figure)

with col_2:
    # Le service qui a le plus d'avis par label
    df = pd.pivot_table(dataset, index='Administration', columns='Labels', aggfunc='size', fill_value=0)
    df_nbr_avis_service_label = pd.DataFrame(df)

    select_labels = st.selectbox("Sélectionner un label pour les administrations", list(set(dataset["Labels"])))
    # Filtrer les données en fonction du sentiment sélectionné
    df_nbr_avis_service_label = df_nbr_avis_service_label[select_labels].reset_index()

    nbr_avis_commist = 0
    nbr_avis_police = 0
    nbr_avis_gdmr = 0

    for index in range(len(services)):
        if "Commissariat" in df_nbr_avis_service_label["Administration"][index]:
            nbr_avis_commist += df_nbr_avis_service_label[f"{select_labels}"][index]
        elif "Police" in df_nbr_avis_service_label["Administration"][index] and "Commissariat" not in df_nbr_avis_service_label["Administration"][index]:
            nbr_avis_police += df_nbr_avis_service_label[f"{select_labels}"][index]
        elif "Gendarmerie" in df_nbr_avis_service_label["Administration"][index]:
            nbr_avis_gdmr += df_nbr_avis_service_label[f"{select_labels}"][index]
            
    services_dict = {
        "Administration": ["Police Nationale", "Commissariat de Police", "Gendarmerie Nationale"],
        "Nombre d'avis": [nbr_avis_police, nbr_avis_commist, nbr_avis_gdmr]
    }

    df_services_labels = pd.DataFrame(services_dict)
            
    figure = px.bar(
        data_frame=df_services_labels,
        x="Administration", y="Nombre d'avis",
        width=500
    )

    st.plotly_chart(figure)

# Nombre d'avis par région
st.markdown("## Nombre d'avis par région")

df_nbr_avis = dataset.groupby('Régions').size().reset_index(name="Nombre d'avis")
geo_region = gpd.read_file("./regions.geojson")

map_region_by_avis = folium.Map(
    location = [46.22,2.21],
    tiles = 'CartoDB positron',
    name = "Light Map",
    zoom_start = 6,
    attr = "Régions France",
    scrollWheelZoom = False
)

choropleth = folium.Choropleth(
    geo_data=geo_region,
    data=df_nbr_avis,
    columns=("Régions", "Nombre d'avis"),
    key_on="feature.properties.nom",
    fill_color="YlOrRd",
    fill_opacity=0.7,
    line_opacity=1,
    highlight=True,
    line_weight=3
)

choropleth.geojson.add_to(map_region_by_avis)

df_nbr_avis["Régions"] = df_nbr_avis["Régions"].apply(lambda x: x.lstrip())
df_nbr_avis["Régions"] = df_nbr_avis["Régions"].apply(lambda x: "\u00cele-de-France" if x == "Ile-de-France" else x)
df_nbr_avis = df_nbr_avis.set_index('Régions')

for feature in choropleth.geojson.data["features"]:
    region_name = feature["properties"]["nom"]
    if region_name in df_nbr_avis.index:
        feature["properties"]["Nbr_Avis"] = f"Nombre d'avis : {str(df_nbr_avis.loc[region_name][0])}"

choropleth.geojson.add_child(
    folium.features.GeoJsonTooltip(['nom', 'Nbr_Avis'], labels=False)
)

st_map = st_folium(map_region_by_avis, width=900, height=700)

# Nombre d'avis par région et par label
st.markdown("## Nombre d'avis par région et par label")

df = pd.pivot_table(dataset, index='Régions', columns='Labels', aggfunc='size', fill_value=0)
df_nbr_avis_label = pd.DataFrame(df)

select_labels = st.selectbox("Sélectionner un label", list(set(dataset["Labels"])))
# Filtrer les données en fonction du sentiment sélectionné
df_nbr_avis_label = df_nbr_avis_label[select_labels].reset_index()

df_nbr_avis_label["Régions"] = df_nbr_avis_label["Régions"].apply(lambda x: x.lstrip())
df_nbr_avis_label["Régions"] = df_nbr_avis_label["Régions"].apply(lambda x: "\u00cele-de-France" if x == "Ile-de-France" else x)
df_nbr_avis_label = df_nbr_avis_label.set_index('Régions')

map_region_by_label = folium.Map(
    location = [46.22,2.21],
    tiles = 'CartoDB positron',
    name = "Light Map",
    zoom_start = 6,
    attr = "Régions France",
    scrollWheelZoom = False
)

choropleth = folium.Choropleth(
    geo_data=geo_region,
    data=df_nbr_avis_label,
    columns=(df_nbr_avis_label.index, select_labels),
    key_on="feature.properties.nom",
    fill_color="YlOrRd",
    fill_opacity=0.7,
    line_opacity=1,
    highlight=True,
    line_weight=3
)

choropleth.geojson.add_to(map_region_by_label)

for feature in choropleth.geojson.data["features"]:
    region_name = feature["properties"]["nom"]
    if region_name in df_nbr_avis_label.index:
        feature["properties"]["label"] = f"{select_labels} : {str(df_nbr_avis_label.loc[region_name][0])}"

choropleth.geojson.add_child(
    folium.features.GeoJsonTooltip(['nom', 'label'], labels=False)
)

st_map = st_folium(map_region_by_label, width=900, height=700)

# Obtention des topics
st.markdown("## Les techniques d'obtention de topics")
c1, c2 = st.columns(2)

with c1:
    st.subheader("LDA")
    st.image("./Images/newplot.png")
with c2:
    st.subheader("WordCloud")
    st.image("./Images/output.png")

st.sidebar.markdown('''---''')
st.sidebar.header("Réalisé par :")
st.sidebar.subheader("Kevin DOUKPENI")
st.sidebar.subheader("Elisabeth-Lucie BATONGA")
st.sidebar.subheader("Jérémi VESPUCE")
st.sidebar.subheader("Henri GOHI")

st.sidebar.markdown('''
---
❤️ HETIC x Master Data & IA 2022-2024 ❤️
''')
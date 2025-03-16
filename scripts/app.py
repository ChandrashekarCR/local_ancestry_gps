import streamlit as st
import pandas as pd
import folium
from streamlit_folium import folium_static
from chromosome_plot import plot_chromosome_segments, plot_chromosome_country, plot_chromosome_continent
from world_map import plot_world_map, plot_world_map_country, plot_world_map_continent

# Streamlit App
st.title("Local Ancestry Data Visualization")

# Upload CSV File
uploaded_file = st.file_uploader("Upload CSV file", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file)

    # Sidebar filters
    st.sidebar.header("Select Population and Individual")

    # Select Population
    selected_population = st.sidebar.selectbox("Select Population", ["None"] + list(df['Population'].dropna().unique()))

    if selected_population != "None":
        filtered_df = df[df['Population'] == selected_population]
        individuals = filtered_df['individual'].unique()
    else:
        filtered_df = df
        individuals = filtered_df['individual'].unique()

    # Select Individual
    selected_individual = st.sidebar.selectbox("Select Individual", ["None"] + list(individuals))

    if selected_individual != "None":
        filtered_df = filtered_df[filtered_df['individual'] == selected_individual]
        filtered_df['segment'] = filtered_df.groupby('chromosome').cumcount() + 1

        # Chromosome Visualization
        st.subheader("Chromosome Visualization by Prediction")
        st.plotly_chart(plot_chromosome_segments(filtered_df, selected_individual), use_container_width=True)

        st.subheader("Chromosome Visualization by Country")
        st.plotly_chart(plot_chromosome_country(filtered_df, selected_individual), use_container_width=True)

        st.subheader("Chromosome Visualization by Continent")
        st.plotly_chart(plot_chromosome_continent(filtered_df, selected_individual), use_container_width=True)

        # World Map
        st.subheader("World Map of Samples")
        folium_static(plot_world_map(filtered_df, selected_individual))

        # Now ask user for chromosome to plot the world map by chromosome
        chromosomes = filtered_df['chromosome'].unique()
        selected_chromosome = st.sidebar.selectbox("Select Chromosome", chromosomes)

        if selected_chromosome:
            st.subheader(f"World Map of Chromosome {selected_chromosome} Distribution by Country")
            st.plotly_chart(plot_world_map_country(filtered_df, selected_chromosome, '/home/inf-21-2024/binp29/population_genetic_project/data/04_geopandas/ne_110m_admin_0_countries.shp'), use_container_width=True)

            st.subheader(f"World Map of Chromosome {selected_chromosome} Distribution by Continent")
            st.plotly_chart(plot_world_map_continent(filtered_df, selected_chromosome, '/home/inf-21-2024/binp29/population_genetic_project/data/04_geopandas/ne_110m_admin_0_countries.shp'), use_container_width=True)

        # Rename Admixture Columns
        admix_mapping = {
            'Admixture1': 'NORTHEASTASIAN', 'Admixture2': 'MEDITERRANIAN',
            'Admixture3': 'SOUTHAFRICA', 'Admixture4': 'SOUTHWESTASIAN',
            'Admixture5': 'NATIVEAMERICAN', 'Admixture6': 'OCEANIAN',
            'Admixture7': 'SOUTHEASTASIA', 'Admixture8': 'NORTHERNEUROPEAN',
            'Admixture9': 'SUBSAHARANAFRICA'
        }
        filtered_df.rename(columns=admix_mapping, inplace=True)

        st.subheader(f"Full Data for {selected_individual}")
        st.dataframe(filtered_df, width=1000, height=500)

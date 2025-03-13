import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import folium
from streamlit_folium import folium_static
from chromosome_plot import plot_chromosome
from world_map import plot_world_map

# Streamlit App
st.title("Genetic Data Visualization")

# Upload CSV File
uploaded_file = st.file_uploader("Upload CSV file", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file)

    # Select Individual
    individuals = df['individual'].unique()
    selected_individual = st.selectbox("Select Individual", individuals)
    
    # Filter Data for Selected Individual
    filtered_df = df[df['individual'] == selected_individual].copy()

    # Add 'segment' column based on chromosome
    filtered_df['segment'] = filtered_df.groupby('chromosome').cumcount() + 1
    
    # Reorder columns: 'segment' after 'chromosome' and before 'start_pos'
    cols_order = ['individual', 'chromosome', 'segment', 'start_pos'] + [col for col in filtered_df.columns if col not in ['individual', 'chromosome', 'segment', 'start_pos']]
    filtered_df = filtered_df[cols_order]
    
    st.subheader(f"Full Data for {selected_individual}")
    st.dataframe(filtered_df)  # Display the updated dataframe
    
    # Chromosome Visualization
    st.subheader("Chromosome Visualization")
    fig = plot_chromosome(filtered_df, selected_individual)
    st.plotly_chart(fig, use_container_width=True)

    # World Map of Samples
    st.subheader("World Map of Samples")
    world_map = plot_world_map(filtered_df, selected_individual)
    folium_static(world_map)

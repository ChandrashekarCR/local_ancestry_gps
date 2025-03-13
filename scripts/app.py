import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import folium
from streamlit_folium import folium_static
from chromosome_plot import plot_chromosome
from world_map import plot_world_map



# Streamlit App
st.title("Genetic Data Visualization")

uploaded_file = st.file_uploader("Upload CSV file", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    individuals = df['individual'].unique()
    selected_individual = st.selectbox("Select Individual", individuals)
    
    st.subheader("Chromosome Visualization")
    fig = plot_chromosome(df, selected_individual)
    # Use container width for better fit
    st.plotly_chart(fig, use_container_width=True)


    st.subheader("World Map of Samples")
    world_map = plot_world_map(df, selected_individual)
    folium_static(world_map)
    
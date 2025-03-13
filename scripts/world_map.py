import pandas as pd
import numpy as np
import folium


# Function to plot world map
def plot_world_map(df, individual):
    test_df = df[df['individual'] == individual]
    
    m = folium.Map(location=[test_df['Lat'].mean(), test_df['Lon'].mean()], zoom_start=3)
    
    for _, row in test_df.iterrows():
        folium.Marker(
            location=[row['Lat'], row['Lon']],
            popup=f"Sample: {row['SAMPLE_ID']}<br>Prediction: {row['Prediction']}<br>Population: {row['Population']}",
            icon=folium.Icon(color='blue')
        ).add_to(m)
    
    return m

'''
import streamlit as st
import pandas as pd
import folium
import plotly.express as px
import plotly.graph_objects as go
from streamlit_folium import folium_static
from folium.plugins import MarkerCluster
import base64
import tempfile

def generate_pie_chart(row):
    admixture_cols = [col for col in row.index if col.startswith("Admixture")]
    values = row[admixture_cols].values
    labels = admixture_cols

    fig = go.Figure(data=[go.Pie(labels=labels, values=values, textinfo='percent+label')])
    fig.update_layout(title=f"Admixture Proportions for {row['SAMPLE_ID']}")
    
    return fig

def plot_world_map(df, individual):
    test_df = df[df['individual'] == individual]
    
    m = folium.Map(location=[test_df['Lat'].mean(), test_df['Lon'].mean()], zoom_start=3)
    marker_cluster = MarkerCluster().add_to(m)

    for _, row in test_df.iterrows():
        # Generate Pie Chart
        pie_chart = generate_pie_chart(row)
        
        # Save Plotly Figure as an HTML file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".html") as tmpfile:
            pie_chart.write_html(tmpfile.name)
            tmpfile.close()
            with open(tmpfile.name, "r") as f:
                html_string = f.read()

        # Convert HTML to base64
        encoded_html = base64.b64encode(html_string.encode()).decode()
        iframe = f'<iframe src="data:text/html;base64,{encoded_html}" width="350" height="350"></iframe>'

        popup_html = f"""
        <b>Sample:</b> {row['SAMPLE_ID']}<br>
        <b>Prediction:</b> {row['Prediction']}<br>
        <b>Population:</b> {row['Population']}<br>
        {iframe}
        """
        
        folium.Marker(
            location=[row['Lat'], row['Lon']],
            popup=folium.Popup(popup_html, max_width=400),
            icon=folium.Icon(color='blue')
        ).add_to(marker_cluster)
    
    return m
'''
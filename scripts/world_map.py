import pandas as pd
import numpy as np
import folium


import geopandas as gpd
import pandas as pd
from shapely.geometry import Point
from scipy.spatial import cKDTree
from geopy.distance import geodesic

import geopandas as gpd
import pandas as pd
import numpy as np
from shapely.geometry import Point
from scipy.spatial import cKDTree
from geopy.distance import geodesic

def pull_land(df, lat_col='Lat', lon_col='Lon', coastline_path="/home/inf-21-2024/binp29/population_genetic_project/data/04_geopandas/ne_110m_coastline.shp"):
    """
    Adjusts points that fall in water by moving them to the nearest coastline.
    """
    
    # Load coastline shapefile
    coastline = gpd.read_file(coastline_path)

    # Convert DataFrame to GeoDataFrame
    df['geometry'] = df.apply(lambda row: Point(row[lon_col], row[lat_col]) if np.isfinite(row[lon_col]) and np.isfinite(row[lat_col]) else None, axis=1)
    df.dropna(subset=['geometry'], inplace=True)
    
    gdf = gpd.GeoDataFrame(df, geometry='geometry', crs="EPSG:4326")
    
    # Identify points in water
    world = gpd.read_file("/home/inf-21-2024/binp29/population_genetic_project/data/04_geopandas/ne_110m_admin_0_countries.shp")
    in_water = ~gdf.geometry.within(world.geometry.union_all())
    water_points = gdf[in_water].copy()

    # Extract coastline points
    coast_points = []
    for geom in coastline.geometry:
        if geom.geom_type == 'LineString':
            coast_points.extend(list(geom.coords))
        elif geom.geom_type == 'MultiLineString':
            for line in geom:
                coast_points.extend(list(line.coords))
    
    # Filter out NaN or infinite values
    coast_points = [point for point in coast_points if np.isfinite(point[0]) and np.isfinite(point[1])]

    if not coast_points:
        raise ValueError("No valid coastline points found!")

    coast_tree = cKDTree(coast_points)  # KDTree for nearest neighbor search

    # Find nearest coastline point for water points
    new_coords = []
    for idx, row in water_points.iterrows():
        if not np.isfinite(row.geometry.x) or not np.isfinite(row.geometry.y):
            continue  # Skip invalid points

        _, nearest_idx = coast_tree.query([row.geometry.x, row.geometry.y])
        nearest_point = coast_points[nearest_idx]
        new_coords.append((nearest_point[0], nearest_point[1]))
    
    # Update water points with new coordinates
    if new_coords:
        water_points[lon_col], water_points[lat_col] = zip(*new_coords)

    # Compute distance moved
    water_points["Distance_from_origin_km"] = water_points.apply(
        lambda row: geodesic((row[lat_col], row[lon_col]), (row.geometry.y, row.geometry.x)).kilometers
        if np.isfinite(row.geometry.x) and np.isfinite(row.geometry.y) else np.nan, axis=1
    )
    
    # Merge updated water points back into the original DataFrame
    gdf.update(water_points)
    
    return gdf.drop(columns=['geometry'])

data = pd.read_csv("/home/inf-21-2024/binp29/population_genetic_project/data/03_plotting_data/final_plotting.csv")
data = pull_land(data)
data.to_csv("/home/inf-21-2024/binp29/population_genetic_project/data/03_plotting_data/final_plotting_pulled_to_land.csv",index=False)


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
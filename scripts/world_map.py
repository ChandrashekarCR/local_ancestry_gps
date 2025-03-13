import pandas as pd
import numpy as np
import folium
import matplotlib.pyplot as plt
import io
import base64
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas

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

# Dictionary mapping original 'Admixture' column names to new names
admixture_mapping = {
    'Admixture1': 'NorthEastAsian',
    'Admixture2': 'Mediterranean',
    'Admixture3': 'SouthAfrican',
    'Admixture4': 'SouthWestAsian',
    'Admixture5': 'NativeAmerican',
    'Admixture6': 'Oceanian',
    'Admixture7': 'SouthEastAsian',
    'Admixture8': 'NorthernEuropean',
    'Admixture9': 'SubsaharanAfrican'
}




data = pd.read_csv("/home/inf-21-2024/binp29/population_genetic_project/data/03_plotting_data/final_plotting.csv")
#data = pull_land(data)
#data.to_csv("/home/inf-21-2024/binp29/population_genetic_project/data/03_plotting_data/final_plotting_pulled_to_land.csv",index=False)


# Function to plot world map
def plot_world_map(df, individual):
    test_df = df[df['individual'] == individual]
    test_df = test_df.rename(columns=admixture_mapping)
    
    m = folium.Map(location=[test_df['Lat'].mean(), test_df['Lon'].mean()], zoom_start=3)
    
    for _, row in test_df.iterrows():
        # Rename columns using the mapping dictionary
        
        
        # Generate pie chart as an image string
        pie_chart_img = generate_pie_chart(row)
        
        # Prepare the popup HTML with the pie chart and additional information
        popup_html = f'''
        <html>
            <img src="data:image/png;base64,{pie_chart_img}" width="300" height="300">
            <br><br>
            Sample: {row['SAMPLE_ID']}<br>
            Prediction: {row['Prediction']}<br>
            Population: {row['Population']}<br>
            Chromosome: {row['chromosome']}<br>
            Segment: {row['segment']}
        </html>
        '''
        
        # Add marker to the map with the popup
        folium.Marker(
            location=[row['Lat'], row['Lon']],
            popup=folium.Popup(popup_html, max_width=400),
            icon=folium.Icon(color='blue')
        ).add_to(m)
    
    return m

def generate_pie_chart(row):
    admixture_cols = list(admixture_mapping.values())
    
    # Ensure the necessary columns exist in the row
    if not all(col in row for col in admixture_cols):
        raise KeyError(f"Missing columns for admixture: {admixture_cols}")
    
    values = row[admixture_cols].values
    labels = admixture_cols

    # Check if the values sum to 100% (for percentage) or 1 (for proportion)
    total = sum(values)
    
    if total != 1:
        # Normalize values to sum to 1 (for proportion) or 100% (for percentage)
        values = [v / total for v in values]

    threshold = 1e-04

    # Filter out labels with zero values to avoid empty segments in the pie chart and legend
    filtered_labels = [label for value, label in zip(values, labels) if value > threshold]
    filtered_values = [value for value in values if value > threshold]

    # Create the pie chart using matplotlib
    fig, ax = plt.subplots()
    wedges, _ = ax.pie(filtered_values, startangle=90, labels=None)  # No labels on the pie chart

    # Add a legend only for the segments that are plotted
    ax.legend(wedges, filtered_labels, title="Admixture Groups", loc="best", fontsize=8)

    ax.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.

    # If proportions were adjusted, show a warning in the title
    title = f"Admixture Proportions for {row['SAMPLE_ID']}"
    
    ax.set_title(title)

    buf = io.BytesIO()
    canvas = FigureCanvas(fig)
    canvas.print_png(buf)
    buf.seek(0)

    # Correct way to encode binary image data in base64
    img_str = base64.b64encode(buf.getvalue()).decode("utf-8")
    
    return img_str

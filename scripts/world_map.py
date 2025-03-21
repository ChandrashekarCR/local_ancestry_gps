import pandas as pd
import numpy as np
import folium
import matplotlib.pyplot as plt
import io
import base64
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from folium import MacroElement
from jinja2 import Template
import plotly.express as px
import geopandas as gpd
import pycountry




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


# Define a consistent color palette for admixture components
admixture_colors = {
    "NorthEastAsian": "#1f77b4",  # Blue
    "Mediterranean": "#ff7f0e",  # Orange
    "SouthAfrican": "#2ca02c",  # Green
    "SouthWestAsian": "#d62728",  # Red
    "NativeAmerican": "#9467bd",  # Purple
    "Oceanian": "#8c564b",  # Brown
    "SouthEastAsian": "#e377c2",  # Pink
    "NorthernEuropean": "#7f7f7f",  # Gray
    "SubsaharanAfrican": "#bcbd22"   # Yellow-green
}



color_map = {
    1: 'blue',
    2: 'red',
    3: 'green',
    4: 'purple',
    5: 'orange',
    6: 'darkblue',
    7: 'lightblue',
    8: 'pink',
    9: 'black',
    10: 'gray',
    11: 'white',
    12: 'beige',
    13: 'cadetblue',
    14: 'darkgreen',
    15: 'darkpurple',
    16: 'darkred',
    17: 'lightred',
    18: 'lightgray',
    19: 'lightgreen',
    20: 'orange',
    21: 'darkorange',
    22: 'pink'
}



def add_legend(m):
    """
    Adds a draggable legend to the provided folium map.

    The legend includes:
    - Symbols representing different types of areas and routes.
    - A color gradient representing scaled genetic distances.

    Parameters:
    m (folium.Map, optional): An existing Folium map object to plot on.

    Returns:
    m : The map object with the legend added.
    """
    template = """
            {% macro html(this, kwargs) %}
    <div id='maplegend' class='maplegend'
    style='position: absolute; z-index: 9999; background-color: rgba(255, 255, 255, 0.8);
    border-radius: 6px; padding: 10px; font-size: 12px; width: 200px; right: 20px; top: 20px; cursor: move;
    border: 1px solid black; box-shadow: 2px 2px 5px rgba(0,0,0,0.4);'>
    
        <div class='legend-title' style="font-weight: bold; text-align: center;">Chromosome Legend</div>
        <div class='legend-scale'>
            <div class='legend-columns' style="display: flex; flex-wrap: wrap; justify-content: space-between;">
                <ul class='legend-labels' style="list-style: none; padding: 0; margin: 0; width: 45%; ">
                    <li><span style="background: rgb(0,0,255);"></span> 1</li> 
                    <li><span style="background: rgb(255,0,0);"></span> 2</li>
                    <li><span style="background: rgb(0,128,0);"></span> 3</li>
                    <li><span style="background: rgb(128,0,128);"></span> 4</li>
                </ul>
                <ul class='legend-labels' style="list-style: none; padding: 0; margin: 0; width: 45%;">
                    <li><span style="background: rgb(255,165,0);"></span> 5</li>
                    <li><span style="background: rgb(0,0,139);"></span> 6</li>
                    <li><span style="background: rgb(173,216,230);"></span> 7</li>
                    <li><span style="background: rgb(255,192,203);"></span> 8</li>
                </ul>
                <ul class='legend-labels' style="list-style: none; padding: 0; margin: 0; width: 45%;">
                    <li><span style="background: rgb(0,0,0); color: white;"></span> 9</li>
                </ul>
                <ul class='legend-labels' style="list-style: none; padding: 0; margin: 0; width: 45%;">
                    <li><span style="background: rgb(169,169,169);"></span> 10</li>
                </ul>
            </div>
        </div>
    </div>
    
    <style>
    .maplegend .legend-scale ul li {
        display: flex;
        align-items: center;
        margin-bottom: 5px;
    }
    .maplegend .legend-scale ul li span {
        display: inline-block;
        width: 15px;
        height: 15px;
        margin-right: 10px;
        border-radius: 3px;
        border: 1px solid black;
    }
    </style>
    
    <script type='text/javascript'>
    function dragElement(element) {
        var pos1 = 0, pos2 = 0, pos3 = 0, pos4 = 0;
        element.onmousedown = dragMouseDown;
        function dragMouseDown(e) {
            e.preventDefault();
            pos3 = e.clientX;
            pos4 = e.clientY;
            document.onmouseup = closeDragElement;
            document.onmousemove = elementDrag;
        }
        function elementDrag(e) {
            e.preventDefault();
            pos1 = pos3 - e.clientX;
            pos2 = pos4 - e.clientY;
            pos3 = e.clientX;
            pos4 = e.clientY;
            element.style.top = (element.offsetTop - pos2) + "px";
            element.style.left = (element.offsetLeft - pos1) + "px";
        }
        function closeDragElement() {
            document.onmouseup = null;
            document.onmousemove = null;
        }
    }
    dragElement(document.getElementById('maplegend'));
    </script>
    {% endmacro %}

        """
    macro = MacroElement()
    macro._template = Template(template)

    macro.add_to(m)
    return m



# Function to plot the world map
def plot_world_map(df, individual):
    test_df = df
    test_df = test_df.rename(columns=admixture_mapping)
    unique_chromosomes = test_df['chromosome'].unique()

    # Create the map centered around the mean latitude and longitude
    m = folium.Map(location=[test_df['Lat'].mean(), test_df['Lon'].mean()], zoom_start=3)
    
    for _, row in test_df.iterrows():
        # Generate pie chart as an image string
        pie_chart_img = generate_pie_chart(row)
        
        # Prepare the popup HTML with the pie chart and additional information
        popup_html = f'''
        <html>
            <style>
                body {{
                    font-size: 16px;  /* Increase text size */
                    font-family: Arial, sans-serif;
                }}
                .info {{
                    font-size: 14px;  /* Increase text size of the info */
                }}
            </style>
            <img src="data:image/png;base64,{pie_chart_img}" width="300" height="300">
            <br><br>
            <div class="info">
                Sample: {row['SAMPLE_ID']}<br>
                Prediction: {row['Prediction']}<br>
                Population: {row['Population']}<br>
                Chromosome: {row['chromosome']}<br>
                Segment: {row['segment']}
            </div>
        </html>
        '''
        
        chrom_color = color_map.get(row['chromosome'])

        # Add marker to the map with the popup
        folium.Marker(
            location=[row['Lat'], row['Lon']],
            popup=folium.Popup(popup_html, max_width=500),
            icon=folium.Icon(color=chrom_color)
        ).add_to(m)
    
    m = add_legend(m)

    return m


def generate_pie_chart(row):
    admixture_cols = list(admixture_mapping.values())

    if not all(col in row for col in admixture_cols):
        raise KeyError(f"Missing columns for admixture: {admixture_cols}")
    
    values = row[admixture_cols].values
    labels = admixture_cols

    total = sum(values)
    if total != 1:
        values = [v / total for v in values]

    threshold = 1e-04
    percent_threshold = 10  

    filtered_labels = [label for value, label in zip(values, labels) if value > threshold]
    filtered_values = [value for value in values if value > threshold]

    # Use predefined colors, ensuring the same color is used for each admixture type
    filtered_colors = [admixture_colors[label] for label in filtered_labels]

    def autopct_format(pct):
        return f"{pct:.1f}%" if pct > percent_threshold else ""

    fig, ax = plt.subplots(figsize=(10, 10), dpi=200)
    wedges, texts, autotexts = ax.pie(
        filtered_values, startangle=90, labels=None, 
        autopct=autopct_format, textprops={'fontsize': 18, 'color': 'black'}, colors=filtered_colors
    )

    ax.legend(wedges, filtered_labels, loc="upper center", fontsize=20, title=None, framealpha=0.4, bbox_to_anchor=(0.5, -0.1))
    
    ax.axis('equal')
    ax.set_title(f"Admixture Proportions for {row['SAMPLE_ID']}", fontsize=32)

    buf = io.BytesIO()
    fig.tight_layout(pad=1.0)
    fig.savefig(buf, format="png", bbox_inches="tight", pad_inches=0.1)
    buf.seek(0)

    img_str = base64.b64encode(buf.getvalue()).decode("utf-8")

    return img_str


def plot_world_map_country(country_plot_df, chromosome, shapefile_path):
    """
    Plots the distribution of a given chromosome on a world map using Plotly and GeoPandas.
    
    Parameters:
        country_plot_df (pd.DataFrame): DataFrame containing 'Country' and 'chromosome' columns.
        chromosome (int): Chromosome number to filter data.
        shapefile_path (str): Path to the world shapefile.
    
    Returns:
        plotly.graph_objects.Figure: Interactive choropleth map.
    """
    # Filter data for the given chromosome
    chromosome_data = country_plot_df[country_plot_df['chromosome'] == chromosome]
    
    # Load world map shapefile
    world = gpd.read_file(shapefile_path)
    # Merge world shapefile with chromosome data
    world = world.merge(chromosome_data, left_on='NAME', right_on='Country', how='left')
    # Create a mask for countries that are in chromosome_data
    world['color'] = world['Country'].apply(lambda x: 'Chromosome Data' if pd.notnull(x) else 'Other')

    
    # Create hover text for additional details
    world['hover_text'] = world.apply(
        lambda row: (
            f"Country: {row['NAME']}<br>"
            f"Sample: {row['SAMPLE_ID']}<br>"
            f"Chromosome: {row['chromosome']}<br>"
            f"Population: {row['Population']}"
        ) if pd.notnull(row['Country']) else "No Data Available", 
        axis=1
    )
    
    # Create a Plotly choropleth map
    fig = px.choropleth(world,
                        geojson=world.geometry.__geo_interface__,
                        locations=world.index,
                        color='color',
                        color_discrete_map={'Other': 'lightgray', 'Chromosome Data': 'blue'},
                        hover_name=None,
                        hover_data={'hover_text': True, 'color':False},
                        title=f'Chromosome {chromosome} Segments on World Map')
    
    # Add annotations for countries with data
    for _, row in world.iterrows():
        if pd.notnull(row['Country']):
            centroid = row['geometry'].centroid
            fig.add_annotation(
                x=centroid.x,
                y=centroid.y,
                text=row['Country'],
                showarrow=False,
                font=dict(size=8, color='black'),
                align='center'
            )
    
    # Update layout
    fig.update_geos(showcoastlines=True, coastlinecolor="Black", projection_type="natural earth")
    fig.update_layout(
        geo=dict(showland=True, landcolor="lightgray"),
        title_text=f"Chromosome {chromosome} Segments on World Map",
        geo_showlakes=True,
        geo_lakecolor="white",
        margin={"r": 0, "t": 30, "l": 0, "b": 0},
        showlegend=True
    )
    
    return fig


def plot_world_map_continent(country_plot_df, chromosome, shapefile_path):
    """
    Plots the distribution of a given chromosome on a world map by continent.

    Parameters:
        country_plot_df (pd.DataFrame): DataFrame containing 'Continent' and 'chromosome' columns.
        chromosome (int): Chromosome number to filter data.
        shapefile_path (str): Path to the world shapefile.

    Returns:
        plotly.graph_objects.Figure: Interactive choropleth map.
    """
    # Filter data for the given chromosome
    chromosome_data = country_plot_df[country_plot_df['chromosome'] == chromosome]

    # Load world map shapefile
    world = gpd.read_file(shapefile_path)

    # Merge world shapefile with chromosome data based on Continent
    world = world.merge(chromosome_data, left_on='CONTINENT', right_on='Continent', how='left')

    # Assign color based on chromosome presence
    world['color'] = world['chromosome'].apply(lambda x: 'Chromosome Data' if pd.notnull(x) else 'Other')

    # Create hover text for more details
    world['hover_text'] = world.apply(
        lambda row: (
            f"Continent: {row['CONTINENT']}<br>"
            f"Chromosome: {row['chromosome']}<br>"
            f"Population: {row['Population']}"
        ) if pd.notnull(row['chromosome']) else "No Data Available", 
        axis=1
    )

    # Create a Plotly choropleth map
    fig = px.choropleth(
        world,
        geojson=world.geometry.__geo_interface__,
        locations=world.index,
        color='color',
        color_discrete_map={'Other': 'lightgray', 'Chromosome Data': 'blue'},
        hover_name='CONTINENT',
        hover_data={'color': False, 'hover_text': True},
        title=f'Chromosome {chromosome} Segments by Continent'
    )

    # Update layout
    fig.update_geos(showcoastlines=True, coastlinecolor="Black", projection_type="natural earth")
    fig.update_layout(
        geo=dict(showland=True, landcolor="lightgray"),
        title_text=f"Chromosome {chromosome} Segments by Continent",
        geo_showlakes=True,
        geo_lakecolor="white",
        margin={"r": 0, "t": 30, "l": 0, "b": 0},
        showlegend=True
    )

    return fig


import pandas as pd
import numpy as np
import os
import argparse
import ast
import geopandas as gpd
from shapely.geometry import Point
from scipy.spatial import cKDTree
from geopy.distance import geodesic
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
import reverse_geocoder as rg
import pycountry
import pycountry_convert as pc

# Initialize geolocator
geolocator = Nominatim(user_agent='popgen_project_version1')  # Change user_agent if you get a 403 error

def process_gps_files(gps_results):
    """
    Reads and combines GPS result files from a specified directory.
    """
    gps_list = []
    gps_files = []
    
    # Extract numeric suffix from filenames and sort numerically
    for file in os.listdir(gps_results):
        if file.startswith("output_data_") and file.endswith(".txt"):
            try:
                num = int(file.split('_')[-1].split('.')[0])
                gps_files.append((num, file))
            except ValueError:
                print(f"Skipping {file}: Unexpected filename format")
                continue
    
    # Sort files numerically and read them
    gps_files.sort()
    for _, file in gps_files:
        file_path = os.path.join(gps_results, file)
        df = pd.read_csv(file_path, sep="\t")
        gps_list.append(df)
    
    return pd.concat(gps_list, ignore_index=True) if gps_list else pd.DataFrame()

def convert_to_list_if_needed(value):
    """Convert a string representation of a list back to a Python list if it has brackets."""
    if isinstance(value, str) and value.startswith("[") and value.endswith("]"):
        try:
            return ast.literal_eval(value)  # Safely evaluate the string into a Python object
        except (SyntaxError, ValueError):
            return value  # Return as is if there's an error
    return value  # Return as is if it's not a string with brackets

def pull_land(df, coastline_path, countries, lat_col='Lat', lon_col='Lon'):
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
    world = gpd.read_file(countries)
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


def get_country_region(lat, lon):
    """
    Get country and region using reverse_geocoder.
    """
    result = rg.search((lat, lon))  # Returns a list of results
    if result:
        country = result[0].get("cc", "Unknown")  # Country code
        region = result[0].get("admin1", "Unknown")  # Region/State
        return country, region
    return "Unknown", "Unknown"

def convert_country_code_to_name(country_code):
    """
    Convert a two-letter country code to a full country name.
    
    Args:
        country_code (str): Two-letter country code.
    
    Returns:
        str: Full country name or "Unknown" if conversion fails.
    """
    try:
        country = pycountry.countries.get(alpha_2=country_code)
        if country:
            return country.name
    except Exception:
        pass
    return "Unknown"


def get_continent_from_country(country_name):
    """
    Get the continent name from a country name.
    
    Args:
        country_name (str): Full country name.
    
    Returns:
        str: Continent name or "Unknown" if conversion fails.
    """
    try:
        # Convert country name to alpha-2 code
        country = pycountry.countries.get(name=country_name)
        if country:
            alpha_2_code = country.alpha_2
            # Convert alpha-2 code to continent code
            continent_code = pc.country_alpha2_to_continent_code(alpha_2_code)
            # Map continent code to continent name
            continent = {
                "AF": "Africa",
                "NA": "North America",
                "OC": "Oceania",
                "AN": "Antarctica",
                "AS": "Asia",
                "EU": "Europe",
                "SA": "South America"
            }.get(continent_code, "Unknown")
            return continent
    except Exception:
        pass
    return "Unknown"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Merge all the re-run GPS file into a final dataframe.")
    
    parser.add_argument('-d', "--data_directory", required=True, help="Directory of the re-run GPS")
    parser.add_argument('-m', "--merged_file", required=True, help="Enter the file that has the merged information")
    parser.add_argument('-o', '--output_directory', required=True, help='Enter a directory to save the final data')
    parser.add_argument('-c', '--coastline', required=True, help='Enter the ne_110m_coastline.shp file')
    parser.add_argument('-w', '--water_points', required=True, help='Enter the ne_110m_admin_0_countries.shp')
    parser.add_argument('-l', '--countries', required=True, help='Enter the hgdp file to get the countries for each sample ID.')

    args = parser.parse_args()
    data_directory = args.data_directory
    merged_file = args.merged_file
    output_directory = args.output_directory
    countries_file = args.countries

    # Process GPS files
    gps_df = process_gps_files(data_directory)

    # Load merged file
    merged_df = pd.read_csv(merged_file)
    
    # Set indices for merging
    gps_df.set_index("Sample_id", inplace=True)
    merged_df.set_index("SAMPLE_ID", inplace=True)

    # Update merged_df with GPS data
    mask = merged_df.index.str.contains("_mark_")
    merged_df.loc[mask, "Prediction"] = gps_df.loc[merged_df.index[mask], 'Prediction']
    merged_df.loc[mask, 'Lat'] = gps_df.loc[merged_df.index[mask], 'Lat']
    merged_df.loc[mask, 'Lon'] = gps_df.loc[merged_df.index[mask], 'Lon']      

    # Reset indices
    gps_df.reset_index(inplace=True)
    merged_df.reset_index(inplace=True)

    # Clean up Prediction and Population columns
    merged_df['Prediction'] = merged_df['Prediction'].apply(convert_to_list_if_needed)
    merged_df['Population'] = merged_df['Population'].apply(convert_to_list_if_needed)
    merged_df['Prediction'] = merged_df['Prediction'].astype(str).str.replace(r"[\[\]']", "", regex=True)
    merged_df['Population'] = merged_df['Population'].astype(str).str.replace(r"[\[\]']", "", regex=True)
    merged_df['SAMPLE_ID'] = merged_df['SAMPLE_ID'].apply(lambda x: x.split("_")[0])

    # Adjust points in water to nearest coastline
    print('Pulling points that are on water bodies or oceans to the nearest coastlines')
    merged_df = pull_land(merged_df, coastline_path=args.coastline, countries=args.water_points)  

    # Get countries from hgdp.xlsx 
    print('Getting countries for each SAMPLE ID')
    countries_df = pd.read_excel(countries_file)
    countries_df.rename(columns={'ID': 'SAMPLE_ID'}, inplace=True)
    countries_df['Country'] = countries_df['Country'].apply(lambda x: x.strip())
    countries_df['Region'] = countries_df['Region'].apply(lambda x: x.strip())

    # Merge with the main DataFrame
    merged_df = pd.merge(merged_df, countries_df[['SAMPLE_ID', 'Country', 'Region']], on='SAMPLE_ID', how='left')

    # Fill missing values in 'Country' and 'Region' using Lat, Lon
    missing_country_mask = merged_df['Country'].isna()
    missing_region_mask = merged_df['Region'].isna()

    # Extract unique coordinates for geocoding
    unique_coords = merged_df.loc[missing_country_mask, ['Lat', 'Lon']].drop_duplicates().values.tolist()
    unique_coords = [(lat, lon) for lat, lon in unique_coords]
    results = rg.search(unique_coords)

    # Create a mapping from coordinates to country/region
    coord_to_country_region = {
        (coord[0], coord[1]): (result["cc"], result["admin1"])
        for coord, result in zip(unique_coords, results)
    }

    # Map results back to the original DataFrame
    merged_df.loc[missing_country_mask, 'Country'] = merged_df.loc[missing_country_mask, ['Lat', 'Lon']].apply(
        lambda row: coord_to_country_region.get((row["Lat"], row["Lon"]), ("Unknown", "Unknown"))[0], axis=1
    )
    merged_df.loc[missing_region_mask, 'Region'] = merged_df.loc[missing_region_mask, ['Lat', 'Lon']].apply(
        lambda row: coord_to_country_region.get((row["Lat"], row["Lon"]), ("Unknown", "Unknown"))[1], axis=1
    )

    # Convert country codes to full country names (only for rows where Country was filled using rg)
    merged_df.loc[missing_country_mask, 'Country'] = merged_df.loc[missing_country_mask, 'Country'].apply(
        lambda x: convert_country_code_to_name(x)
    )
    
    merged_df['Continent'] = merged_df['Country'].apply(lambda x: get_continent_from_country(x))

    ## Reorder columns
    cols = ["SAMPLE_ID", "individual", "chromosome", "start_pos", "end_pos", "Prediction", "Population", 
            "Lat", "Lon", "Country", "Continent",  # Moving Country & Region after Lat & Lon
            "Admixture1", "Admixture2", "Admixture3", "Admixture4", "Admixture5", 
            "Admixture6", "Admixture7", "Admixture8", "Admixture9"]
    merged_df = merged_df[cols]  # Reordering the DataFrame

    # Save the final DataFrame
    processed_file = os.path.join(args.output_directory, "final_plotting.csv")
    merged_df.to_csv(processed_file, index=False)
    print(f"Final data saved to: {processed_file}")
import os
import pandas as pd
import argparse
import math
import numpy as np

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

def haversine(lat1, lon1, lat2, lon2):
    """
    Calculate the great-circle distance between two points using the Haversine formula.
    """
    R = 6371.0  # Earth's radius in km
    phi1, phi2 = map(math.radians, [lat1, lat2])
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    
    a = (math.sin(delta_phi / 2) ** 2 +
         math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    return R * c

def geographic_center(coord_tuple):
    """
    Compute the geographic centroid from latitude and longitude lists.
    """
    lat_list, lon_list = coord_tuple
    if not lat_list or not lon_list or len(lat_list) != len(lon_list):
        raise ValueError("Latitude and Longitude lists must be non-empty and of equal length.")
    
    lat_radians, lon_radians = np.radians(lat_list), np.radians(lon_list)
    x, y, z = (np.cos(lat_radians) * np.cos(lon_radians),
               np.cos(lat_radians) * np.sin(lon_radians),
               np.sin(lat_radians))
    
    x_avg, y_avg, z_avg = np.mean(x), np.mean(y), np.mean(z)
    lat_center, lon_center = np.arctan2(z_avg, np.sqrt(x_avg**2 + y_avg**2)), np.arctan2(y_avg, x_avg)
    
    return np.degrees(lat_center), np.degrees(lon_center)

def calculate_haversine_distances_by_sample(df):
    """
    Calculate the Haversine distance for consecutive rows within each SAMPLE_ID.
    """
    distances = []
    for _, group in df.groupby('SAMPLE_ID'):
        group_distances = [None]
        for i in range(len(group) - 1):
            distance = haversine(group.iloc[i]['Lat'], group.iloc[i]['Lon'],
                                 group.iloc[i + 1]['Lat'], group.iloc[i + 1]['Lon'])
            group_distances.append(distance)
        distances.extend(group_distances)
    df['distance_to_next'] = distances
    return df

def merge_segments(group):
    """
    Merge consecutive segments within a sample based on geographic distances.
    """
    if len(group) == 1:
        return group
    
    merged = {
        'SAMPLE_ID': group['SAMPLE_ID'].iloc[0],
        'chromosome': group['chromosome'].iloc[0],
        'start_pos': group['start_pos'].min(),
        'end_pos': group['end_pos'].max(),
        'Population': list(group['Population'].unique()),
        'Prediction': list(group['Prediction'].unique()),
        'window': list(group['window'].unique()),
        'individual': group['individual'].min(),
    }
    
    admixture_cols = [col for col in group.columns if col.startswith("Admixture")]
    for col in admixture_cols:
        merged[col] = group[col].mean()
    
    lat_list, lon_list = list(group['Lat']), list(group['Lon'])
    merged['Lat'], merged['Lon'] = geographic_center((lat_list, lon_list))
    merged['distance_to_next'] = group['distance_to_next'].mean()
    
    return pd.DataFrame([merged])


if __name__ == "__main__":
    """
    Main function to process GPS data and merge genomic segments.
    """
    parser = argparse.ArgumentParser(description="Process GPS and combined data, and output merged results.")
    parser.add_argument("-g", "--gps_results", type=str, help="Directory containing GPS result files")
    parser.add_argument("-c", "--combined_df_path", type=str, help="Path to the combined dataframe file (CSV)")
    parser.add_argument("-o", "--output_path", type=str, help="Path to save the merged output dataframe")
    parser.add_argument('-t','--threshold', type=float, help='Enter a value in km for mergeing chromosome segements',default=200)
    args = parser.parse_args()
    
    print("Loading the combined dataframe...")
    combined_df = pd.read_csv(args.combined_df_path)
    
    print("Processing the GPS files...")
    gps_df = process_gps_files(args.gps_results)

    full_df = pd.concat([combined_df,gps_df],axis=1)
    full_df = full_df.loc[:, ~full_df.columns.duplicated()]

    temp_df = full_df.copy()
    temp_df['row'] = temp_df.groupby('Sample_id').cumcount()  # Assign row index (0-55)
    temp_df.drop(columns=['GROUP_ID'],axis=1,inplace=True)

    # Set MultiIndex
    temp_df = temp_df.set_index(['Sample_id', 'row']).sort_index()
    temp_df = temp_df[~temp_df['chromosome'].astype(str).str.contains(',')]

    print("Calculating Haversine distances...")
    combined_df = calculate_haversine_distances_by_sample(temp_df)
    
    threshold = args.threshold  # Set merging threshold in km
    combined_df['merge_group'] = (combined_df['distance_to_next'] >= threshold).cumsum()
    
    print("Merging segments...")
    merged_df = combined_df.groupby(['SAMPLE_ID', 'chromosome', 'merge_group'], group_keys=False).apply(merge_segments)
    merged_df = merged_df.reset_index(drop=True).drop(columns=['merge_group'])
    
    column_order = [
        "SAMPLE_ID", "individual", "chromosome", "start_pos", "end_pos", 
        "Prediction", "Population", "Lat", "Lon"
    ] + list(merged_df.filter(like="Admixture").columns)
    
    merged_df = merged_df[column_order]
    merged_df.to_csv(args.output_path, index=False)
    print(f"Processed data saved to {args.output_path}")
    print("Done!")

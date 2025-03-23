# Ancstry Map - A tool to visualize local acestry

## Introduction
This project focuses on biogeographical analysis by determining an individual's geographical origins based on their DNA at a local ancestry level. Unlike global ancestry, which provides overall genetic composition, local ancestry breaks the genome into smaller chromosomal segments to infer their geographical origins. The Geographical Population Structure (GPS) algorithm, developed by Elhaik et al. (2014), plays a crucial role in this analysis, allowing for a more detailed understanding of genetic heritage.

This pipeline processes Q_files, BIM, and FAM files, runs the GPS algorithm in parallel, merges segment predictions, and generates a dataset for visualization through a web application.

## Author
- [@ChandrashekarCR](https://github.com/ChandrashekarCR)

## Installation & Setup

### Prerequisites:
- Miniconda
- Python 3
- Required packages (`numpy`, `pandas`, `Ray`, `geopandas`, `matplotlib`, `seaborn`, `scikit-learn`)
- R with GPS dependencies installed

### Steps:
1. Clone the repository:
```bash
git clone https://github.com/your-repo/local_ancestry_gps.git
cd local-ancestry-gps
```
2. Create a Conda environment:
```bash
conda env create -f popgen_environment.yml -n popgen_env  
conda activate popgen_env
cd script/
```
3. Run the Bash script to execute the full pipeline:
```bash
bash popgen_pipeline.sh
```
4. Run the web application
```bash
streamlit run app.py
```
5. Upload the in data/03_plotting_data/final_plotting.csv on the website and visualize the results.

## Project Workflow

1. **Input Data Preparation**
   - Process Q_files, BIM, and FAM files.
   - Q_files contain admixture proportions for 1069 individuals across 9 gene pools.
   - Output: Prepared dataset for GPS.

2. **Run GPS Algorithm (Parallel Processing)**
   - Process multiple individuals in parallel using the Ray framework.
   - Reduces runtime significantly from hours to ~12 minutes.

3. **Merge Chromosome Predictions**
   - Calculate Haversine distance between adjacent segments.
   - Merge segments based on a user-defined threshold.

4. **Prepare Files for Re-running GPS**
   - Split merged predictions into smaller files (1000 entries each) for efficiency.

5. **Re-run GPS Algorithm on Split Files**
   - Obtain refined geographical coordinates for merged segments.

6. **Final Merge for Plotting Dataset**
   - Adjust segments falling in water bodies.
   - Map each segment to a country and continent.
   - Prepare dataset for visualization.

## Scripts and Usage

### 1. `process_data_for_gps.py`
Prepares input files for the GPS algorithm.
```bash
import pandas as pd
import numpy as np
import os
import re
import argparse

# Global chunk size for splitting data into manageable parts
chunk_size = 1069  # Default value, will be updated dynamically during processing

def update_sample_id(row):
    """
    Updates the SAMPLE_ID in a row based on GROUP_ID.
    If the base of SAMPLE_ID (without trailing digits) matches the base of GROUP_ID,
    the GROUP_ID is returned. Otherwise, the original SAMPLE_ID is returned.

    Args:
        row (pd.Series): A row from the DataFrame containing 'SAMPLE_ID' and 'GROUP_ID'.

    Returns:
        str: Updated SAMPLE_ID or GROUP_ID.
    """
    sample_base = re.sub(r'\d+$', '', row['SAMPLE_ID'])  # Remove trailing digits from SAMPLE_ID
    group_base = re.sub(r'\d+$', '', row['GROUP_ID'])    # Remove trailing digits from GROUP_ID
    return row['GROUP_ID'] if sample_base == group_base else row['SAMPLE_ID']


def process_fam_file(fam_file):
    """
    Processes a .fam file to extract SAMPLE_ID and GROUP_ID, and updates SAMPLE_ID using `update_sample_id`.

    Args:
        fam_file (str): Path to the .fam file.

    Returns:
        pd.DataFrame: DataFrame with 'SAMPLE_ID' and 'GROUP_ID' columns.
    """
    try:
        # Read the .fam file, extracting the first two columns (SAMPLE_ID and GROUP_ID)
        fam_df = pd.read_csv(fam_file, sep=" ", header=None, usecols=[0, 1])
        fam_df.columns = ["SAMPLE_ID", "GROUP_ID"]
        # Update SAMPLE_ID based on GROUP_ID
        fam_df['SAMPLE_ID'] = fam_df.apply(update_sample_id, axis=1)
        return fam_df
    except Exception as e:
        print(f"Error processing FAM file: {e}")
        exit(1)


def process_q_files(q_files_dir, fam_df):
    """
    Processes all .Q files in a directory, combining them into a single DataFrame.
    Each .Q file is associated with a window number, and the data is aligned with the FAM file.

    Args:
        q_files_dir (str): Directory containing .Q files.
        fam_df (pd.DataFrame): DataFrame from the .fam file.

    Returns:
        pd.DataFrame: Combined DataFrame with admixture data, window numbers, and sample information.
    """
    global chunk_size
    data_list = []  # List to store DataFrames from each .Q file
    q_files = []    # List to store tuples of (window number, file name)

    # Iterate through all files in the directory
    for file in os.listdir(q_files_dir):
        if file.endswith(".Q"):
            try:
                # Extract window number from the file name (e.g., "window_1.Q")
                window = int(file.split('_')[1].split('.')[0])
                q_files.append((window, file))
            except (IndexError, ValueError):
                print(f"Skipping {file}: Unexpected filename format")
                continue

    if not q_files:
        print("Error: No valid .Q files found in the directory.")
        exit(1)

    q_files.sort()  # Sort files by window number

    for window, file in q_files:
        file_path = os.path.join(q_files_dir, file)
        df = pd.read_csv(file_path, sep=" ", header=None)  # Read the .Q file

        # Check if the number of individuals matches the FAM file
        if len(df) != len(fam_df):
            print(f"Warning: {file} has {len(df)} individuals, but FAM file has {len(fam_df)}. Skipping.")
            continue

        # Add window number, individual ID, and sample information to the DataFrame
        df['window'] = window + 1
        df['individual'] = range(1, len(df) + 1)
        df['SAMPLE_ID'] = fam_df['SAMPLE_ID'].to_list()
        df['GROUP_ID'] = fam_df['GROUP_ID'].to_list()

        data_list.append(df)

    if not data_list:
        print("Error: No valid data found in .Q files. Exiting.")
        exit(1)

    chunk_size = len(df)  # Update global chunk size based on the last processed file
    print(f"Chunk size set to {chunk_size}")

    # Combine all DataFrames into one and rename admixture columns
    combined_df = pd.concat(data_list, ignore_index=True)
    combined_df = combined_df.rename(columns={i: f'Admixture{i+1}' for i in range(9)})
    # Hard-coding this here because the user has give the files in the wrong order. Trying to find the correct order would result in 9! permuatations. Very illogical.
    #new_order = ['SAMPLE_ID','Admixture3','Admixture1','Admixture6','Admixture8','Admixture2','Admixture5','Admixture7','Admixture4','Admixture9','GROUP_ID']
    #combined_df = combined_df[new_order]
    return combined_df


def save_chunks(combined_df, output_dir):
    """
    Saves the combined DataFrame into smaller CSV chunks based on the global chunk size.

    Args:
        combined_df (pd.DataFrame): Combined DataFrame to be split into chunks.
        output_dir (str): Directory to save the chunked CSV files.
    """
    os.makedirs(output_dir, exist_ok=True)

    # Split the DataFrame into chunks and save each as a CSV file
    for i in range(0, len(combined_df), chunk_size):
        chunk_df = combined_df.iloc[i:i + chunk_size]
        chunk_df = chunk_df[['SAMPLE_ID'] + [f'Admixture{j}' for j in range(1, 10)] + ['GROUP_ID']]
        # Hard-coded new order because the order of the test files were in a different order. To run GPS the admixture must always be in a certain order.
        new_order = ['SAMPLE_ID','Admixture3','Admixture1','Admixture6','Admixture8','Admixture2','Admixture5','Admixture7','Admixture4','Admixture9','GROUP_ID']
        chunk_df = chunk_df[new_order]
        chunk_df.to_csv(os.path.join(output_dir, f'data_{i // chunk_size}.csv'), index=False)

    print(f"Saved data in {len(combined_df) // chunk_size} chunks.")


def extract_chromosome_info(bim_file, window_size):
    """
    Extracts chromosome information from a .bim file for each window.

    Args:
        bim_file (str): Path to the .bim file.
        window_size (int): Size of the window used to split the data.

    Returns:
        dict: A dictionary mapping window numbers to chromosome information.
    """
    try:
        # Read the .bim file into a DataFrame
        bim_df = pd.read_csv(bim_file, sep="\t", header=None, names=["chr", "snp", "cm", "pos", "a1", "a2"])
    except Exception as e:
        print(f"Error reading BIM file: {e}")
        exit(1)

    unique_chromosomes_per_chunk = {}

    # Iterate through the .bim file in chunks of size `window_size`
    for i in range(0, len(bim_df), window_size):
        chunk = bim_df.iloc[i:i + window_size]
        unique_chromosomes_per_chunk[f"{i//window_size+1}"] = {
            "chromosomes": ",".join(map(str, chunk["chr"].unique())),  # Unique chromosomes in the chunk
            "start_pos": chunk["pos"].iloc[0],  # Start position of the chunk
            "end_pos": chunk["pos"].iloc[-1]   # End position of the chunk
        }

    # Create a mapping dictionary for chromosome, start, and end positions
    mapped_info = {
        k: {
            "chromosome": ",".join(map(str, v["chromosomes"])),
            "start_pos": v["start_pos"],
            "end_pos": v["end_pos"]
        } 
        for k, v in unique_chromosomes_per_chunk.items()
    }

    return mapped_info


def map_chromosome_info_to_combined_df(combined_df, mapped_info):
    """
    Maps chromosome information to the combined DataFrame based on window numbers.

    Args:
        combined_df (pd.DataFrame): Combined DataFrame with admixture data.
        mapped_info (dict): Dictionary containing chromosome information for each window.

    Returns:
        pd.DataFrame: Combined DataFrame with added chromosome information.
    """
    combined_df['window'] = combined_df['window'].astype(str)
    # Add chromosome, start position, and end position columns
    combined_df['chromosome'] = combined_df['window'].map(lambda x: mapped_info.get(x, {}).get("chromosome", "NA"))
    combined_df['start_pos'] = combined_df['window'].map(lambda x: mapped_info.get(x, {}).get("start_pos", "NA"))
    combined_df['end_pos'] = combined_df['window'].map(lambda x: mapped_info.get(x, {}).get("end_pos", "NA"))
    return combined_df


if __name__ == '__main__':
    # Set up command-line argument parsing
    parser = argparse.ArgumentParser(description="Process population genetic data files.")
    
    parser.add_argument('-f', '--fam_file', type=str, required=True, help='Path to the .fam file')
    parser.add_argument('-q', '--q_files_dir', type=str, required=True, help='Directory containing .Q files')
    parser.add_argument('-o', '--output_dir', type=str, required=True, help='Directory to save the output CSV chunks')
    parser.add_argument('-b', '--bim_file', type=str, required=True, help='Path to the .bim file')
    parser.add_argument('-w','--window_size',type=int,required=True,default=500,help='Enter the value of the window size used to create the Q files. The default is set to 500.')
    parser.add_argument('-o2', '--output_dir_2', type=str, required=True, help='Directory to save final data with chromosome info')

    args = parser.parse_args()

    print("Starting processing...")

    # Process the .fam file
    fam_df = process_fam_file(args.fam_file)
    print("Processed FAM file")

    # Process the .Q files
    combined_df = process_q_files(args.q_files_dir, fam_df)
    print("Processed Q files")

    # Save the combined data into chunks
    save_chunks(combined_df, args.output_dir)
    print("Saved chunked data")

    # Extract chromosome information from the .bim file
    mapped_info = extract_chromosome_info(args.bim_file, args.window_size)
    print("Extracted chromosome info")

    # Map chromosome information to the combined DataFrame
    final_df = map_chromosome_info_to_combined_df(combined_df, mapped_info)
    print("Mapped chromosome data")

    # Save the final DataFrame with chromosome information
    os.makedirs(args.output_dir_2, exist_ok=True)
    final_df.to_csv(os.path.join(args.output_dir_2, 'combined_data.csv'), index=False)
    print("Final data saved with chromosome info\n")

    print("Done!")
```
### 2. `run_gps_parallely.py`
Runs the GPS algorithm in parallel.
```python
import os
import ray
import subprocess
import argparse
from pathlib import Path

# Function to run the R script for each CSV file
@ray.remote
def run_gps_for_file(data_file, geo_file, gen_file, output_file, rscript_file):
    """Run the GPS R script for a specific file."""
    command = [
        "Rscript", rscript_file,
        geo_file, gen_file, data_file, output_file
    ]
    
    # Execute the R script using subprocess
    try:
        subprocess.run(command, check=True)
        print(f"Successfully processed {data_file}")
    except subprocess.CalledProcessError as e:
        print(f"Error processing {data_file}: {e}")

def process_files_in_parallel(data_directory, geo_file, gen_file, output_directory, rscript_file):
    """Process all CSV files in parallel using Ray."""
    
    # Get all CSV files in the data directory
    data_files = Path(data_directory).glob("*.csv")
    
    # Create output directory if it doesn't exist
    Path(output_directory).mkdir(parents=True, exist_ok=True)
    
    # Prepare the tasks for parallel processing
    tasks = []
    
    for data_file in data_files:
        # Define the output file path
        output_file = os.path.join(output_directory, f"output_{data_file.stem}.txt")
        
        # Add the task to the list
        tasks.append(run_gps_for_file.remote(str(data_file), geo_file, gen_file, output_file, rscript_file))
    
    # Wait for all tasks to complete
    ray.get(tasks)

if __name__ == "__main__":
    # Create argument parser
    parser = argparse.ArgumentParser(description="Run GPS analysis on multiple CSV files in parallel.")
    
    # Define command-line arguments
    parser.add_argument('-d',"--data_directory", help="Directory containing the data CSV files")
    parser.add_argument('-go',"--geo_file", help="Path to the geo.csv file")
    parser.add_argument('-ge',"--gen_file", help="Path to the gen.csv file")
    parser.add_argument('-o',"--output_directory", help="Directory to store the output results")
    parser.add_argument('-r',"--rscript_file", help="Path to the R script to run")
    
    # Parse the arguments
    args = parser.parse_args()
    
    # Initialize Ray
    ray.init(ignore_reinit_error=True)
    
    # Process the files in parallel
    process_files_in_parallel(args.data_directory, args.geo_file, args.gen_file, args.output_directory, args.rscript_file)


```
### 3. `assign_merge_chr.py`
Merges chromosome segment predictions.
```python
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
    """Merge genomic segments within a given group."""
    if len(group) == 0:
        return pd.DataFrame()  # Return an empty DataFrame for empty groups
    if len(group) == 1:
        return group  # No merging needed
    
    merged = {
        'SAMPLE_ID': group['SAMPLE_ID'].iloc[0],
        'chromosome': group['chromosome'].iloc[0],
        'start_pos': group['start_pos'].min(),
        'end_pos': group['end_pos'].max(),
        'Population': list(group['Population'].unique()),
        'Prediction': list(group['Prediction'].unique()),
        'window': list(group['window'].unique()),
        'individual': group['individual'].min(),
        'Lat': np.nan,
        'Lon': np.nan,
        'distance_to_next': group['distance_to_next'].mean()
    }

    # Compute geographic centroid
    if 'Lat' in group and 'Lon' in group:
        merged['Lat'], merged['Lon'] = geographic_center((group['Lat'].tolist(), group['Lon'].tolist()))

    # Average admixture values
    admixture_cols = [col for col in group.columns if col.startswith("Admixture")]
    for col in admixture_cols:
        merged[col] = group[col].mean()

    return pd.DataFrame([merged])

if __name__ == "__main__":
    """
    Main function to process GPS data and merge genomic segments.
    """
    parser = argparse.ArgumentParser(description="Process GPS and combined data, and output merged results.")
    parser.add_argument("-g", "--gps_results", type=str, help="Directory containing GPS result files")
    parser.add_argument("-c", "--combined_df_path", type=str, help="Path to the combined dataframe file (CSV)")
    parser.add_argument("-o", "--output_path", type=str, help="Path to save the merged output dataframe")
    parser.add_argument('-t','--threshold', type=float, help='Enter a value in km for merging chromosome segments', default=200)
    args = parser.parse_args()
    
    print("Loading the combined dataframe...")
    combined_df = pd.read_csv(args.combined_df_path)
    
    print("Processing the GPS files...")
    gps_df = process_gps_files(args.gps_results)

    full_df = pd.concat([combined_df, gps_df], axis=1)
    full_df = full_df.loc[:, ~full_df.columns.duplicated()]

    temp_df = full_df.copy()
    temp_df['row'] = temp_df.groupby('Sample_id').cumcount()  # Assign row index (0-55)
    temp_df.drop(columns=['GROUP_ID'], axis=1, inplace=True)

    # Set MultiIndex
    temp_df = temp_df.set_index(['Sample_id', 'row']).sort_index()
    temp_df = temp_df[~temp_df['chromosome'].astype(str).str.contains(',')]

    print("Calculating Haversine distances...")
    temp_df = calculate_haversine_distances_by_sample(temp_df)
    
    threshold = args.threshold  # Set merging threshold in km
    temp_df['merge_group'] = (temp_df['distance_to_next'] >= threshold).cumsum()

    
    print("Merging segments...")

    merged_segments = []
    for _, group in temp_df.groupby(['SAMPLE_ID', 'chromosome', 'merge_group']):
        merged_segments.append(merge_segments(group))
    merged_df = pd.concat(merged_segments, ignore_index=True)
    merged_df = merged_df.drop(columns=['merge_group', 'Sample_no'], errors='ignore')
    
    column_order = [
        "SAMPLE_ID", "individual", "chromosome", "start_pos", "end_pos", 
        "Prediction", "Population", "Lat", "Lon"
    ] + list(merged_df.filter(like="Admixture").columns)
    
    merged_df = merged_df[column_order]
    
    if not merged_df.empty:
        merged_df.to_csv(args.output_path, index=False)
        print(f"Processed data saved to {args.output_path}")
    else:
        print("No data to save. The merged DataFrame is empty.")
    
    print("Done!")
```

### 4. `file_parse_gps.py`
Prepares files for re-running GPS on ambiguous predictions.
```python
import pandas as pd
import os
import numpy as np
import argparse
import ast

def convert_to_list_if_needed(value):
    """
    Converts a string representation of a list (e.g., "[1, 2, 3]") back to a Python list.
    If the input is not a string or does not represent a list, it is returned as is.

    Args:
        value (str or any): The value to be converted.

    Returns:
        list or any: The converted list or the original value.
    """
    if isinstance(value, str) and value.startswith("[") and value.endswith("]"):
        try:
            # Safely evaluate the string into a Python object (e.g., "[1, 2, 3]" -> [1, 2, 3])
            return ast.literal_eval(value)
        except (SyntaxError, ValueError):
            # Return the original value if evaluation fails
            return value
    return value  # Return the original value if it's not a string representation of a list


def rename_merged_df(merged_data_path):
    """
    Reads a CSV file, filters rows where the 'Prediction' column has more than one unique value,
    and modifies the 'SAMPLE_ID' column for filtered and non-filtered rows.

    Args:
        merged_data_path (str): Path to the CSV file containing merged data.

    Returns:
        pd.DataFrame: The modified DataFrame with updated 'SAMPLE_ID' values.
    """
    # Read the CSV file into a DataFrame
    merged_df = pd.read_csv(merged_data_path)
    
    # Convert the 'Prediction' column to a list if it is a string representation of a list
    merged_df['Prediction'] = merged_df['Prediction'].apply(convert_to_list_if_needed)
    
    # Filter rows where the 'Prediction' column has more than one unique value
    filtered_df = merged_df[merged_df['Prediction'].apply(lambda x: len(np.unique(x)) > 1)]
    
    # Iterate over the rows in the DataFrame and update 'SAMPLE_ID'
    for i, index in enumerate(merged_df.index):
        if index in filtered_df.index:
            # For filtered rows, append "_mark_{i+1}" to 'SAMPLE_ID'
            merged_df.at[index, 'SAMPLE_ID'] = f"{merged_df.at[index, 'SAMPLE_ID']}_mark_{i+1}"
        else:
            # For non-filtered rows, append "_{i+1}" to 'SAMPLE_ID'
            merged_df.at[index, 'SAMPLE_ID'] = f"{merged_df.at[index, 'SAMPLE_ID']}_{i+1}"

    return merged_df


def split_and_save_csv(input_file, output_dir, chunk_size):
    """
    Splits a CSV file into smaller chunks of a specified row size and saves them as separate CSV files.

    Args:
        input_file (str): Path to the input CSV file.
        output_dir (str): Directory to save the split CSV files.
        chunk_size (int): Number of rows per split file.
    """
    # Create the output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # Read the input CSV file into a DataFrame
    df = pd.read_csv(input_file)
    
    # Split the DataFrame into chunks and save each chunk as a separate CSV file
    for i in range(0, len(df), chunk_size):
        chunk_df = df.iloc[i:i+chunk_size]  # Extract a chunk of rows
        chunk_df.to_csv(os.path.join(output_dir, f"data_chunk_{i//chunk_size}.csv"), index=False)

    print("Splitting completed successfully!")


if __name__ == "__main__":
    # Set up command-line argument parsing
    parser = argparse.ArgumentParser(description="Process and split merged data into smaller CSV files.")
    
    # Define command-line arguments
    parser.add_argument('-d', "--data_file", required=True, help="Full merged data file")
    parser.add_argument('-o', "--output_directory", required=True, help="Directory to store the output results")
    parser.add_argument('-s', "--chunk_size", type=int, default=1000, help="Number of rows per split file (default: 1000)")
    parser.add_argument('-o2', '--split_files', required=True, help='Directory to save the split files')

    # Parse the command-line arguments
    args = parser.parse_args()

    print("Processing merged data...")
    
    # Process the merged data file to rename 'SAMPLE_ID'
    merged_df = rename_merged_df(args.data_file)
    
    # Save the renamed data to a new CSV file
    processed_file = os.path.join(args.output_directory, "renamed_merged_data.csv")
    merged_df.to_csv(processed_file, index=False)
    print(f"Renamed data saved to: {processed_file}")
    
    # Select and rename specific columns for further processing
    merged_df = merged_df[['SAMPLE_ID'] + [f'Admixture{j}' for j in range(1, 10)] + ['Population']]
    merged_df['Population'] = merged_df['Population'].astype(str).str.replace(r"[\[\]']", "", regex=True)  # Clean up 'Population' values
    merged_df.rename(columns={'Population': 'GROUP_ID'}, inplace=True)  # Rename 'Population' to 'GROUP_ID'
    merged_df['GROUP_ID'] = merged_df['GROUP_ID'].astype(str)  # Ensure 'GROUP_ID' is a string
    
    # Save the modified DataFrame to another CSV file
    processed_file = os.path.join(args.output_directory, "renamed_merged_data_for_gps_file.csv")
    merged_df.to_csv(processed_file, index=False)
    print(f"Renamed data saved to: {processed_file}")

    print("Splitting the processed data into smaller files...")
    
    # Split the processed data into smaller CSV files
    split_and_save_csv(processed_file, args.split_files, args.chunk_size)

    print("All tasks completed successfully!")
```
### 5. `final_data_merge.py`
Merges GPS results and prepares dataset for visualization.
```python
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
    print('Getting countries for each SAMPLE ID')

    # Merge with the main DataFrame
    #merged_df = pd.merge(merged_df, countries_df[['SAMPLE_ID', 'Country', 'Region']], on='SAMPLE_ID', how='left')

    merged_df['Country'] = np.nan
    merged_df['Region'] = np.nan
    # Fill missing values in 'Country' and 'Region' using Lat, Lon
    missing_country_mask = merged_df['Country'].isna()
    missing_region_mask = merged_df['Region'].isna()


    # Extract unique coordinates for geocoding
    unique_coords = merged_df[['Lat', 'Lon']].drop_duplicates().values.tolist()
    unique_coords = [(lat, lon) for lat, lon in unique_coords]
    results = rg.search(unique_coords)

    # Create a mapping from coordinates to country/region
    coord_to_country_region = {
        (coord[0], coord[1]): (result["cc"], result["admin1"])
        for coord, result in zip(unique_coords, results)
    }

    # Apply mapping to the DataFrame
    merged_df['Country Code'] = merged_df.apply(
        lambda row: coord_to_country_region.get((row["Lat"], row["Lon"]), ("Unknown", "Unknown"))[0], axis=1
    )
    merged_df['Region'] = merged_df.apply(
        lambda row: coord_to_country_region.get((row["Lat"], row["Lon"]), ("Unknown", "Unknown"))[1], axis=1
    )

    # Convert country codes to full country names
    merged_df['Country'] = merged_df['Country Code'].apply(
        lambda x: pycountry.countries.get(alpha_2=x).name if pycountry.countries.get(alpha_2=x) else "Unknown"
    )

    merged_df['Continent'] = merged_df['Country'].apply(lambda x: get_continent_from_country(x))

    ## Reorder columns
    cols = ["SAMPLE_ID", "individual", "chromosome", "start_pos", "end_pos", "Prediction", "Population", 
            "Lat", "Lon", "Country", "Continent",  # Moving Country & Region after Lat & Lon
            "Admixture3", "Admixture1", "Admixture6", "Admixture8", "Admixture2", 
            "Admixture5", "Admixture7", "Admixture4", "Admixture9"]
    merged_df = merged_df[cols]  # Reordering the DataFrame
    # Save the final DataFrame
    processed_file = os.path.join(args.output_directory, "final_plotting.csv")
    merged_df.to_csv(processed_file, index=False)
    print(f"Final data saved to: {processed_file}")
```
### Centralized Pipeline
```bash
#!/bin/bash

# Script to perfrom the complete local ancestry for individuals given Q_files, bim and fam files.
# Note that the Q files must have the admixture prorpotions in this paricular order for te GPS algorithm to work. The algorithm will 
# work regardless, but the results won't make any sense.
data="/home/inf-21-2024/binp29/population_genetic_project/data" #"/home/inf-21-2024/binp29/GPS/GPS-original-code/data" #
scripts="/home/inf-21-2024/binp29/population_genetic_project/scripts"

## Source the conda.sh script to enable `conda activate` command
source ~/miniconda3/etc/profile.d/conda.sh  
## Activate your environment
echo "Activating environment"
conda activate popgen_env  # Replace `popgen_env` with your environment name
## Now you can run commands in the activated environment
echo "Environment activated"

# Step1: Prepare the data from the Q_file, bim and fam files to run the GPS algorithm
echo "Preparing Q, bim and fam files for running GPS algorithm..."
python3 $scripts/process_data_for_gps.py -f $data/01_raw_data/local_ancestry/merged.fam -q $data/01_raw_data/local_ancestry_1000/q_files/ -w 1000  -o $data/02_GPS/gps_file/ -b $data/01_raw_data/local_ancestry/merged.bim -o2 $data/01_raw_data/combined_data/

# Step2: Run GPS algorithm using parallel processing
echo "Running GPS on multiple cores..."
python3 $scripts/run_gps_parallely.py -d $data/02_GPS/gps_file/ -go $data/02_GPS/gps_helper/geo.csv -ge $data/02_GPS/gps_helper/gen.csv -o $data/02_GPS/gps_results/ -r $scripts/GPS_command_line.R 

# Step3: Merge the chromosome predictions for adjacent windows based on geographic threshold
echo "Merging the chromosome segment predictions for adjacent windows based on geographic threshold..."
python3 $scripts/assign_merge_chr.py -g $data/02_GPS/gps_results/ -c $data/01_raw_data/combined_data/combined_data.csv -o $data/02_GPS/merged_files/merged_data.csv -t 200

# Step 4: Preparing files to re-run GPS on entires that have more than one unique prediction from the GPS algorithm after merging
echo "Preparing files for re-running GPS..."
python3 $scripts/file_parse_gps.py -d $data/02_GPS/merged_files/merged_data.csv -o $data/03_plotting_data/renamed_merged_files/ -s 400 -o2 $data/03_plotting_data/split_files/

# Step 5: Run GPS algorithm on the newly created split files
echo "Running GPS on multiple cores for the split files....."
python3 $scripts/run_gps_parallely.py -d $data/03_plotting_data/split_files -go $data/02_GPS/gps_helper/geo.csv -ge $data/02_GPS/gps_helper/gen.csv -o $data/03_plotting_data/gps_results_split_files/ -r $scripts/GPS_command_line.R 

# Step 6: Final merge of the data to create a dataset for making plots
echo "Merging all the unique predictions into a single prediction after GPS..."
python3 $scripts/final_data_merge.py -d $data/03_plotting_data/gps_results_split_files/ -m $data/03_plotting_data/renamed_merged_files/renamed_merged_data.csv -c $data/04_geopandas/ne_110m_coastline.shp -w $data/04_geopandas/ne_110m_admin_0_countries.shp -o $data/03_plotting_data/plot_files/ -l $data/01_raw_data/local_ancestry/hgdp.xlsx


## Deactivate environment
conda deactivate
echo "Environment Deactivated"
````

## Web Application
The final dataset is used as input for a web application that allows users to visualize local ancestry interactively.

### Features:
- **Chromosome Visualization**: View segment origins at chromosome level.
- **World Map**: Displays origins of chromosomal segments on a global scale.
- **Downloadable Data**: Export processed data for further analysis.


## Future Improvements
- Automating the pipeline from raw data to web visualization.
- Enhancing the web app’s front-end for a smoother user experience.
- Transitioning from Streamlit to a more efficient framework to reduce reload times.

## Contributors
- Chandrashekar CR
- Eran Elhaik

---
This README provides an overview of the project, setup instructions, workflow details, and script usage to help users execute local ancestry analysis efficiently.


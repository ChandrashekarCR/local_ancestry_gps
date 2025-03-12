import pandas as pd
import numpy as np
import os
import re
import argparse

def update_sample_id(row):
    # Remove any number suffix in Sample_ID
    sample_base = re.sub(r'\d+$', '', row['SAMPLE_ID'])
    group_base = re.sub(r'\d+$', '', row['GROUP_ID'])
    
    # If the base of Sample_ID matches the base of GROUP_ID, update Sample_ID
    if sample_base == group_base:
        return row['GROUP_ID']
    return row['SAMPLE_ID']

def process_fam_file(fam_file):
    fam_df = pd.read_csv(fam_file, sep=" ", header=None)
    fam_df = fam_df.rename({0: "SAMPLE_ID", 1: 'GROUP_ID'}, axis=1)[['SAMPLE_ID', 'GROUP_ID']]
    fam_df['SAMPLE_ID'] = fam_df.apply(update_sample_id, axis=1)
    return fam_df

def process_q_files(q_files_dir, fam_df):
    data_list = []
    
    # Extract and sort files numerically based on the window number
    q_files = []
    for file in os.listdir(q_files_dir):
        if file.endswith(".Q"):
            try:
                window = int(file.split('_')[1].split('.')[0])  # Extract window number
                q_files.append((window, file))  # Store as tuple (window_number, filename)
            except (IndexError, ValueError):
                print(f"Skipping {file}: Unexpected filename format")
                continue

    # Sort files based on the window number
    q_files.sort()  # Sorts by the first element in the tuple (window number)

    # Process each Q file
    for window, file in q_files:
        file_path = os.path.join(q_files_dir, file)
        df = pd.read_csv(file_path, sep=" ", header=None)
        df['window'] = window + 1  # Increment the window size for the dataset

        # Reset individual IDs per file (from 1 to 1069)
        df['individual'] = range(1, len(df) + 1)
        df['SAMPLE_ID'] = fam_df['SAMPLE_ID'].to_list()
        df['GROUP_ID'] = fam_df['GROUP_ID'].to_list()

        data_list.append(df)

    if not data_list:
        print("No valid .Q files found in directory.")
        return None

    # Combine all data
    combined_df = pd.concat(data_list, ignore_index=True)
    
    # Rename columns to Admixture1 to Admixture9
    combined_df = combined_df.rename({i: f'Admixture{i+1}' for i in range(9)}, axis=1)
    return combined_df

def save_chunks(combined_df, output_dir, chunk_size=1069):
    dfs = []
    
    # Loop through the DataFrame in chunks of 1069 rows
    for i in range(0, len(combined_df), chunk_size):
        chunk_df = combined_df.iloc[i:i + chunk_size]
        
        # Select the relevant columns (Sample_ID, Admixture1 to Admixture9, GROUP_ID)
        chunk_df = chunk_df[['SAMPLE_ID'] + [f'Admixture{j}' for j in range(1, 10)] + ['GROUP_ID']]
        
        # Append the chunk DataFrame to the list
        dfs.append(chunk_df)
        
        # Save each chunk as a CSV
        chunk_df.to_csv(f'{output_dir}data_{i // chunk_size}.csv', index=False)
    

def extract_chromosome_info(bim_file):
    bim_df = pd.read_csv(bim_file, sep="\t", header=None, names=["chr", "snp", "cm", "pos", "a1", "a2"])
    
    unique_chromosomes_per_chunk = {}

    for i in range(0, len(bim_df), 500):
        chunk = bim_df.iloc[i:i + 500]  # Extract 500-row chunk
        unique_chromosomes = chunk["chr"].unique()  
        start_pos = chunk["pos"].iloc[0]   # First position in chunk
        end_pos = chunk["pos"].iloc[-1]    # Last position in chunk

        unique_chromosomes_per_chunk[f"{i//500+1}"] = {
            "chromosomes": unique_chromosomes.tolist(),
            "start_pos": start_pos,
            "end_pos": end_pos
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
    combined_df['window'] = combined_df['window'].astype(str)

    # Map each window to its corresponding chromosome info
    combined_df['chromosome'] = combined_df['window'].map(lambda x: mapped_info.get(x, {}).get("chromosome", "NA"))
    combined_df['start_pos'] = combined_df['window'].map(lambda x: mapped_info.get(x, {}).get("start_pos", "NA"))
    combined_df['end_pos'] = combined_df['window'].map(lambda x: mapped_info.get(x, {}).get("end_pos", "NA"))
    
    return combined_df

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Process population genetic data files.")
    
    # Arguments for input and output directories
    parser.add_argument('-f', '--fam_file', type=str, required=True, help='Path to the merged .fam file')
    parser.add_argument('-q', '--q_files_dir', type=str, required=True, help='Directory containing the .Q files')
    parser.add_argument('-o', '--output_dir', type=str, required=True, help='Directory to save the output CSV chunks')
    parser.add_argument('-b', '--bim_file', type=str, required=True, help='Path to the merged .bim file')
    parser.add_argument('-o2', '--output_dir_2', type=str, required=True, help='Second directory to save final data with chromosome info')

    args = parser.parse_args()
    fam_file = args.fam_file
    q_files_dir = args.q_files_dir
    output_dir = args.output_dir
    bim_file = args.bim_file
    output_dir_2 = args.output_dir_2
    
    # Process the FAM file
    fam_df = process_fam_file(fam_file)
    print('Processing fam files...')
    
    # Process the Q files and combine the data
    combined_df = process_q_files(q_files_dir, fam_df)
    print('Processing Q files...')
    
    if combined_df is not None:
        # Save the combined data in chunks
        save_chunks(combined_df, output_dir)

        # Extract chromosome info from the BIM file
        mapped_info = extract_chromosome_info(bim_file)
        print('Extracting bim information...')

        # Map chromosome info to the combined data
        final_df = map_chromosome_info_to_combined_df(combined_df, mapped_info)
        print('Concatenating a combined data file....')

        # Save the final data with chromosome information to the second output location
        final_df.to_csv(os.path.join(output_dir_2, 'combined_data.csv'), index=False)
        print("Final data saved with chromosome info.")

print('Done!')
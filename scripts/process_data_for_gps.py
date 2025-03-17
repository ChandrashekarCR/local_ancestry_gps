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
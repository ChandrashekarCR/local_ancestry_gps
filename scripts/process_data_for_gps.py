import pandas as pd
import numpy as np
import os
import re
import argparse

# Global chunk size
chunk_size = 1069  # Default value, will be updated dynamically


def update_sample_id(row):
    sample_base = re.sub(r'\d+$', '', row['SAMPLE_ID'])
    group_base = re.sub(r'\d+$', '', row['GROUP_ID'])
    return row['GROUP_ID'] if sample_base == group_base else row['SAMPLE_ID']


def process_fam_file(fam_file):
    try:
        fam_df = pd.read_csv(fam_file, sep=" ", header=None, usecols=[0, 1])
        fam_df.columns = ["SAMPLE_ID", "GROUP_ID"]
        fam_df['SAMPLE_ID'] = fam_df.apply(update_sample_id, axis=1)
        return fam_df
    except Exception as e:
        print(f"Error processing FAM file: {e}")
        exit(1)


def process_q_files(q_files_dir, fam_df):
    global chunk_size
    data_list = []
    q_files = []

    for file in os.listdir(q_files_dir):
        if file.endswith(".Q"):
            try:
                window = int(file.split('_')[1].split('.')[0])  # Extract window number
                q_files.append((window, file))
            except (IndexError, ValueError):
                print(f"Skipping {file}: Unexpected filename format")
                continue

    if not q_files:
        print("Error: No valid .Q files found in the directory.")
        exit(1)

    q_files.sort()  # Sort by window number

    for window, file in q_files:
        file_path = os.path.join(q_files_dir, file)
        df = pd.read_csv(file_path, sep=" ", header=None)

        # Remember to uncomment this!!!
        if len(df) != len(fam_df):
            print(f"Warning: {file} has {len(df)} individuals, but FAM file has {len(fam_df)}. Skipping.")
            continue

        df['window'] = window + 1
        df['individual'] = range(1, len(df) + 1)
        df['SAMPLE_ID'] = fam_df['SAMPLE_ID'].to_list()
        df['GROUP_ID'] = fam_df['GROUP_ID'].to_list()

        data_list.append(df)

    if not data_list:
        print("Error: No valid data found in .Q files. Exiting.")
        exit(1)

    chunk_size = len(df)  # Set the global chunk size dynamically
    print(f"Chunk size set to {chunk_size}")

    combined_df = pd.concat(data_list, ignore_index=True)
    combined_df = combined_df.rename(columns={i: f'Admixture{i+1}' for i in range(9)})
    return combined_df


def save_chunks(combined_df, output_dir):
    os.makedirs(output_dir, exist_ok=True)

    for i in range(0, len(combined_df), chunk_size):
        chunk_df = combined_df.iloc[i:i + chunk_size]
        chunk_df = chunk_df[['SAMPLE_ID'] + [f'Admixture{j}' for j in range(1, 10)] + ['GROUP_ID']]
        chunk_df.to_csv(os.path.join(output_dir, f'data_{i // chunk_size}.csv'), index=False)

    print(f"Saved data in {len(combined_df) // chunk_size} chunks.")


def extract_chromosome_info(bim_file,window_size):
    try:
        bim_df = pd.read_csv(bim_file, sep="\t", header=None, names=["chr", "snp", "cm", "pos", "a1", "a2"])
    except Exception as e:
        print(f"Error reading BIM file: {e}")
        exit(1)

    unique_chromosomes_per_chunk = {}

    for i in range(0, len(bim_df), window_size):
        chunk = bim_df.iloc[i:i + window_size]
        unique_chromosomes_per_chunk[f"{i//window_size+1}"] = {
            "chromosomes": ",".join(map(str, chunk["chr"].unique())),
            "start_pos": chunk["pos"].iloc[0],
            "end_pos": chunk["pos"].iloc[-1]
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
    combined_df['chromosome'] = combined_df['window'].map(lambda x: mapped_info.get(x, {}).get("chromosome", "NA"))
    combined_df['start_pos'] = combined_df['window'].map(lambda x: mapped_info.get(x, {}).get("start_pos", "NA"))
    combined_df['end_pos'] = combined_df['window'].map(lambda x: mapped_info.get(x, {}).get("end_pos", "NA"))
    return combined_df


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Process population genetic data files.")
    
    parser.add_argument('-f', '--fam_file', type=str, required=True, help='Path to the .fam file')
    parser.add_argument('-q', '--q_files_dir', type=str, required=True, help='Directory containing .Q files')
    parser.add_argument('-o', '--output_dir', type=str, required=True, help='Directory to save the output CSV chunks')
    parser.add_argument('-b', '--bim_file', type=str, required=True, help='Path to the .bim file')
    parser.add_argument('-w','--window_size',type=int,required=True,default=500,help='Enter the value of the window size used to create the Q files. The default is set to 500.')
    parser.add_argument('-o2', '--output_dir_2', type=str, required=True, help='Directory to save final data with chromosome info')

    args = parser.parse_args()

    print("Starting processing...")

    fam_df = process_fam_file(args.fam_file)
    print("Processed FAM file")

    combined_df = process_q_files(args.q_files_dir, fam_df)
    print("Processed Q files")

    save_chunks(combined_df, args.output_dir)
    print("Saved chunked data")

    mapped_info = extract_chromosome_info(args.bim_file,args.window_size)
    print("Extracted chromosome info")

    final_df = map_chromosome_info_to_combined_df(combined_df, mapped_info)
    print("Mapped chromosome data")

    os.makedirs(args.output_dir_2, exist_ok=True)
    final_df.to_csv(os.path.join(args.output_dir_2, 'combined_data.csv'), index=False)
    print("Final data saved with chromosome info\n")

    print("Done!")

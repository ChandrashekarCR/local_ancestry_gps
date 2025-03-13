import pandas as pd
import numpy as np
import os
import argparse
import ast

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



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Merge all the re-run GPS file into a final dataframe.")
    
    parser.add_argument('-d', "--data_directory", required=True, help="Directory of the re-run GPS")
    parser.add_argument('-m', "--merged_file", required=True, help="Enter the file that has the merged information")
    parser.add_argument('-o','--output_directory',required=True,help='Enter a directory to save the final data')

    args = parser.parse_args()
    data_directory = args.data_directory
    merged_file = args.merged_file
    #output_directory = args.output_directory

    gps_df = process_gps_files(data_directory)

    merged_df = pd.read_csv(merged_file)
    
    gps_df.set_index("Sample_id",inplace=True)
    merged_df.set_index("SAMPLE_ID",inplace=True)

    mask = merged_df.index.str.contains("_mark_")

    merged_df.loc[mask, "Prediction"] = gps_df.loc[merged_df.index[mask],'Prediction']

    gps_df.reset_index(inplace=True)
    merged_df.reset_index(inplace=True)
    merged_df['Prediction'] = merged_df['Prediction'].apply(convert_to_list_if_needed)
    merged_df['Population'] = merged_df['Population'].apply(convert_to_list_if_needed)

    merged_df['Prediction'] = merged_df['Prediction'].astype(str).str.replace(r"[\[\]']", "", regex=True)
    merged_df['Population'] = merged_df['Population'].astype(str).str.replace(r"[\[\]']", "", regex=True)
    merged_df['SAMPLE_ID'] = merged_df['SAMPLE_ID'].apply(lambda x: x.split("_")[0])

    processed_file = os.path.join(args.output_directory, "final_plotting.csv")
    merged_df.to_csv(processed_file, index=False)
    print(f"Final data saved to: {processed_file}")
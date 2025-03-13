import pandas as pd
import os
import numpy as np
import argparse
import ast

def convert_to_list_if_needed(value):
    """Convert a string representation of a list back to a Python list if it has brackets."""
    if isinstance(value, str) and value.startswith("[") and value.endswith("]"):
        try:
            return ast.literal_eval(value)  # Safely evaluate the string into a Python object
        except (SyntaxError, ValueError):
            return value  # Return as is if there's an error
    return value  # Return as is if it's not a string with brackets



def rename_merged_df(merged_data_path):
    """Read the CSV, filter rows with more than one unique prediction, and modify SAMPLE_ID."""
    merged_df = pd.read_csv(merged_data_path)
    merged_df['Prediction'] = merged_df['Prediction'].apply(convert_to_list_if_needed)
    
    # Filter rows where Prediction has more than one unique value
    filtered_df = merged_df[merged_df['Prediction'].apply(lambda x: len(np.unique(x)) > 1)]
    

    # Iterate over the rows in merged_df and update SAMPLE_ID
    for i, index in enumerate(merged_df.index):
        if index in filtered_df.index:
            # For the filtered rows (Prediction has more than one unique value)
            merged_df.at[index, 'SAMPLE_ID'] = f"{merged_df.at[index, 'SAMPLE_ID']}_mark_{i+1}"
        else:
            # For the other rows
            merged_df.at[index, 'SAMPLE_ID'] = f"{merged_df.at[index, 'SAMPLE_ID']}_{i+1}"

# Display the updated merged_df
    return merged_df

def split_and_save_csv(input_file, output_dir, chunk_size):
    """Split processed_data.csv into smaller DataFrames of specified row size and save them."""
    os.makedirs(output_dir, exist_ok=True)

    df = pd.read_csv(input_file)
    
    for i in range(0, len(df), chunk_size):
        chunk_df = df.iloc[i:i+chunk_size]
        chunk_df.to_csv(os.path.join(output_dir, f"data_chunk_{i//chunk_size}.csv"), index=False)

    print("Splitting completed successfully!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process and split merged data into smaller CSV files.")
    
    parser.add_argument('-d', "--data_file", required=True, help="Full merged data file")
    parser.add_argument('-o', "--output_directory", required=True, help="Directory to store the output results")
    parser.add_argument('-s', "--chunk_size", type=int, default=1000, help="Number of rows per split file (default: 1000)")
    parser.add_argument('-o2','--split_files',required=True,help='Enter another directory to svae the split files')

    args = parser.parse_args()

    print("Processing merged data...")
    merged_df = rename_merged_df(args.data_file)
    processed_file = os.path.join(args.output_directory, "renamed_merged_data.csv")
    merged_df.to_csv(processed_file, index=False)
    print(f"Renamed data saved to: {processed_file}")
    merged_df = merged_df[['SAMPLE_ID'] + [f'Admixture{j}' for j in range(1, 10)] + ['Population']]
    merged_df['Population'] = merged_df['Population'].astype(str).str.replace(r"[\[\]']", "", regex=True)
    merged_df.rename(columns={'Population': 'GROUP_ID'}, inplace=True)
    merged_df['GROUP_ID'] = merged_df['GROUP_ID'].astype(str)

    processed_file = os.path.join(args.output_directory, "renamed_merged_data_gps_file.csv")
    merged_df.to_csv(processed_file, index=False)
    print(f"Renamed data saved to: {processed_file}")

    print("Splitting the processed data into smaller files...")
    split_and_save_csv(processed_file, args.split_files, args.chunk_size)

    print("All tasks completed successfully!")

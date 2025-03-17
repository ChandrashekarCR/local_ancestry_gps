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
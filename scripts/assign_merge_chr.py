import os
import pandas as pd
import argparse

def process_gps_files(gps_results):
    gps_list = []

    # Extract numeric suffix from filenames and sort numerically
    gps_files = []
    for file in os.listdir(gps_results):
        if file.startswith("output_data_") and file.endswith(".txt"):  # Ensure correct file format
            try:
                num = int(file.split('_')[-1].split('.')[0])  # Extract numeric part
                gps_files.append((num, file))  # Store as tuple (number, filename)
            except ValueError:
                print(f"Skipping {file}: Unexpected filename format")
                continue

    # Sort files numerically by extracted number
    gps_files.sort()

    # Read and concatenate files in sorted order
    for num, file in gps_files:
        file_path = os.path.join(gps_results, file)
        df = pd.read_csv(file_path, sep="\t")
        gps_list.append(df)

    # Combine all data
    if gps_list:
        gps_df = pd.concat(gps_list, ignore_index=True)
    else:
        print("No valid files found.")
        gps_df = pd.DataFrame()

    return gps_df

def merge_and_process_data(combined_df, gps_df):
    # Merge combined_df with gps_df
    full_df = pd.concat([combined_df, gps_df], axis=1)
    full_df = full_df.loc[:, ~full_df.columns.duplicated()]

    # Process temp_df with new calculations
    temp_df = full_df.copy()
    temp_df['row'] = temp_df.groupby('Sample_id').cumcount()  # Assign row index (0-55)
    temp_df.drop(columns=['GROUP_ID'], axis=1, inplace=True)

    # Set MultiIndex
    temp_df = temp_df.set_index(['Sample_id', 'row']).sort_index()
    temp_df = temp_df[~temp_df['chromosome'].astype(str).str.contains(',')]

    # Add Group column for aggregation
    temp_df["Group"] = (temp_df["Prediction"] != temp_df["Prediction"].shift()).cumsum()

    # Define aggregation functions
    agg_funcs = {
        "start_pos": "first",
        "end_pos": "last",
        "Lat": "mean",
        "Lon": "mean",
    }

    # Dynamically find all Admixture columns and set aggregation to mean
    admixture_cols = temp_df.filter(like="Admixture").columns
    for col in admixture_cols:
        agg_funcs[col] = "mean"

    # Include other columns that should remain unchanged
    other_cols = ["SAMPLE_ID", "window", "individual", "Population", "Sample_no", "Prediction"]
    for col in other_cols:
        agg_funcs[col] = "first"

    # Group and aggregate
    df_merged = temp_df.groupby(["chromosome", "Group"], as_index=False).agg(agg_funcs)

    # Drop temporary Group column
    df_merged.drop(columns=["Group"], inplace=True)

    # Define the desired column order
    column_order = [
        "SAMPLE_ID", "individual", "chromosome", "start_pos", "end_pos", 
        "Prediction", "Population", "Lat", "Lon"
    ] + list(temp_df.filter(like="Admixture").columns)

    # Reorder the dataframe
    df_merged = df_merged[column_order]
    df_merged = df_merged.sort_values(by=["individual", "chromosome", "start_pos"], ascending=[True, True, True])

    return df_merged
    

if __name__ == "__main__":
    # Set up command-line argument parsing
    parser = argparse.ArgumentParser(description="Process GPS and combined data, and output merged results.")
    parser.add_argument("-g","--gps_results", type=str, help="Directory containing GPS result files")
    parser.add_argument('-c',"--combined_df_path", type=str, help="Path to the combined dataframe file (CSV)")
    parser.add_argument('-o',"--output_path", type=str, help="Path to save the merged output dataframe")

    args = parser.parse_args()
    combined_df_path = args.combined_df_path
    gps_results = args.gps_results
    output_path = args.output_path

    # Load the combined dataframe
    combined_df = pd.read_csv(combined_df_path)
    print('Loading the combined data frame...')

    # Process GPS files
    gps_df = process_gps_files(gps_results)
    print('Processing the GPS files')

    # Merge and process data
    df_merged = merge_and_process_data(combined_df, gps_df)
    print('Merging the files')

    # Save the final merged dataframe to the output path
    df_merged.to_csv(output_path, index=False)
    print(f"Processed data saved to {output_path}")
    print('Done!')

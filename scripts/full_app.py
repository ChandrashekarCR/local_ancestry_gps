import streamlit as st
import os
import subprocess
import tempfile
from process_data_for_gps import process_fam_file, process_q_files, save_chunks, extract_chromosome_info, map_chromosome_info_to_combined_df
from run_gps_parallely import process_files_in_parallel

# Persistent temp directory
if "temp_dir" not in st.session_state:
    st.session_state.temp_dir = tempfile.TemporaryDirectory().name  # Store temp dir globally

def main():
    st.title("GPS Data Processing Streamlit App")
    
    st.header("Step 1: Upload Required Files")
    fam_file = st.file_uploader("Upload .fam file", type=["fam"])
    q_files = st.file_uploader("Upload .Q files", accept_multiple_files=True)
    bim_file = st.file_uploader("Upload .bim file", type=["bim"])
    
    if st.button("Process Data for GPS"):
        if fam_file and q_files and bim_file:
            temp_dir = st.session_state.temp_dir  # Use persistent temp directory
            os.makedirs(temp_dir, exist_ok=True)

            # Create raw data folder (01_raw_data)
            raw_data_dir = os.path.join(temp_dir, "01_raw_data")
            os.makedirs(raw_data_dir, exist_ok=True)

            # Create combined_data and q_files folders
            combined_data_dir = os.path.join(raw_data_dir, "combined_data")
            os.makedirs(combined_data_dir, exist_ok=True)
            
            q_files_dir = os.path.join(raw_data_dir, "q_files")
            os.makedirs(q_files_dir, exist_ok=True)

            # Save uploaded Q files into q_files folder
            for uploaded_file in q_files:
                file_path = os.path.join(q_files_dir, uploaded_file.name)
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.read())

            # Process FAM and Q files
            fam_df = process_fam_file(fam_file)
            combined_df = process_q_files(q_files_dir, fam_df)
            save_chunks(combined_df, temp_dir)
            
            # Extract chromosome info and map
            mapped_info = extract_chromosome_info(bim_file)
            final_df = map_chromosome_info_to_combined_df(combined_df, mapped_info)
            
            # Ensure the combined_data folder exists and save combined_data.csv
            final_df.to_csv(os.path.join(combined_data_dir, 'combined_data.csv'), index=False)

            st.success(f"Processing complete! Data stored in {temp_dir}")

    st.header("Step 2: Run GPS Analysis")
    geo_file = st.file_uploader("Upload geo.csv file", type=["csv"])
    gen_file = st.file_uploader("Upload gen.csv file", type=["csv"])
    rscript_file = st.file_uploader("Upload GPS_command_line.R")
    
    if st.button("Run GPS Analysis"):
        temp_dir = st.session_state.temp_dir  # Use persistent temp directory
        os.makedirs(temp_dir, exist_ok=True)

        if geo_file and gen_file and rscript_file:
            # Create second raw data folder (02_raw_data)
            raw_data_dir_2 = os.path.join(temp_dir, "02_gps_data")
            os.makedirs(raw_data_dir_2, exist_ok=True)

            # Create gps_helper_folder, gps_files, gps_results folders
            gps_helper_folder = os.path.join(raw_data_dir_2, "gps_helper_folder")
            os.makedirs(gps_helper_folder, exist_ok=True)

            gps_files_dir = os.path.join(raw_data_dir_2, "gps_files")
            os.makedirs(gps_files_dir, exist_ok=True)

            gps_results_dir = os.path.join(raw_data_dir_2, "gps_results")
            os.makedirs(gps_results_dir, exist_ok=True)

            # Save geo_file, gen_file, and rscript_file to gps_helper_folder
            geo_path = os.path.join(gps_helper_folder, "geo.csv")
            gen_path = os.path.join(gps_helper_folder, "gen.csv")
            rscript_path = os.path.join(gps_helper_folder, "GPS_command_line.R")

            with open(geo_path, "wb") as f:
                f.write(geo_file.read())
            with open(gen_path, "wb") as f:
                f.write(gen_file.read())
            with open(rscript_path, "wb") as f:
                f.write(rscript_file.read())

            # Save the geo_file and gen_file to gps_files folder
            with open(os.path.join(gps_files_dir, geo_file.name), "wb") as f:
                f.write(geo_file.read())
            with open(os.path.join(gps_files_dir, gen_file.name), "wb") as f:
                f.write(gen_file.read())

            # Run GPS analysis and save the results to gps_results folder
            with tempfile.TemporaryDirectory() as temp_output_dir:
                process_files_in_parallel(temp_dir, geo_path, gen_path, temp_output_dir, rscript_path)
                
                # Save the results to gps_results folder
                for result_file in os.listdir(temp_output_dir):
                    result_path = os.path.join(gps_results_dir, result_file)
                    os.rename(os.path.join(temp_output_dir, result_file), result_path)

                st.success(f"GPS Analysis Completed! Results stored in {gps_results_dir}")

if __name__ == "__main__":
    main()

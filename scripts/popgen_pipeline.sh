#!/bin/bash

# Script to perfrom the complete local ancestry for individuals given Q_files, bim and fam files.

data="/home/inf-21-2024/binp29/population_genetic_project/data" #"/home/inf-21-2024/binp29/GPS/GPS-original-code/data" #
scripts="/home/inf-21-2024/binp29/population_genetic_project/scripts"

## Source the conda.sh script to enable `conda activate` command
source ~/miniconda3/etc/profile.d/conda.sh  
## Activate your environment
echo "Activating environment"
conda activate popgen_env  # Replace `vcf_env` with your environment name
## Now you can run commands in the activated environment
echo "Environment activated"

# Step1: Prepare the data from the Q_file, bim and fam files to run the GPS algorithm
echo "Preparing Q, bim and fam files for running GPS algorithm..."
python3 $scripts/process_data_for_gps.py -f $data/01_raw_data/local_ancestry/merged.fam -q $data/01_raw_data/local_ancestry/q_files/ -w 500  -o $data/02_GPS/gps_file/ -b $data/01_raw_data/local_ancestry/merged.bim -o2 $data/01_raw_data/combined_data/

# Step2: Run GPS algorithm using parallel processing
echo "Running GPS on multiple cores..."
python3 $scripts/run_gps_parallely.py -d $data/02_GPS/gps_file/ -go $data/02_GPS/gps_helper/geo.csv -ge $data/02_GPS/gps_helper/gen.csv -o $data/02_GPS/gps_results/ -r $scripts/GPS_command_line.R 

# Step3: Merge the chromosome predictions for adjacent windows based on geographic threshold
echo "Merging the chromosome segment predictions for adjacent windows based on geographic threshold..."
python3 $scripts/assign_merge_chr.py -g $data/02_GPS/gps_results/ -c $data/01_raw_data/combined_data/combined_data.csv -o $data/02_GPS/merged_files/merged_data.csv -t 200

# Step 4: Preparing files to re-run GPS on entires that have more than one unique prediction from the GPS algorithm after merging
echo "Preparing files for re-running GPS..."
python3 $scripts/file_parse_gps.py -d $data/02_GPS/merged_files/merged_data.csv -o $data/03_plotting_data/renamed_merged_files/ -s 1000 -o2 $data/03_plotting_data/split_files/

# Step 5: Run GPS algorithm on the newly created split files
echo "Running GPS on multiple cores for the split files....."
python3 $scripts/run_gps_parallely.py -d $data/03_plotting_data/split_files -go $data/02_GPS/gps_helper/geo.csv -ge $data/02_GPS/gps_helper/gen.csv -o $data/03_plotting_data/gps_results_split_files/ -r $scripts/GPS_command_line.R 

# Step 6: Final merge of the data to create a dataset for making plots
echo "Merging all the unique predictions into a single prediction after GPS..."
python3 $scripts/final_data_merge.py -d $data/03_plotting_data/gps_results_split_files/ -m $data/03_plotting_data/renamed_merged_files/renamed_merged_data.csv -c $data/04_geopandas/ne_110m_coastline.shp -w $data/04_geopandas/ne_110m_admin_0_countries.shp -o $data/03_plotting_data/plot_files/ -l $data/01_raw_data/local_ancestry/hgdp.xlsx


## Deactivate environment
conda deactivate
echo "Environment Deactivated"
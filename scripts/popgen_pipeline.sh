#!/bin/bash

# Script to perfrom the complete local ancestry for individuals given Q_files, bim and fam files.

data="/home/inf-21-2024/binp29/population_genetic_project/data"
scripts="/home/inf-21-2024/binp29/population_genetic_project/scripts"

## Source the conda.sh script to enable `conda activate` command
source ~/miniconda3/etc/profile.d/conda.sh  
## Activate your environment
echo "Activating environment"
conda activate popgen_env  # Replace `vcf_env` with your environment name
## Now you can run commands in the activated environment
echo "Environment activated"

# Step1: Prepare the data from the Q_file, bim and fam files to run the GPS algorithm
#echo "Preparing Q, bim and fam files for running GPS algorithm..."
#python3 $scripts/process_data_for_gps.py -f $data/01_raw_data/local_ancestry/merged.fam -q $data/01_raw_data/local_ancestry/q_files/  -o $data/02_GPS/gps_file/ -b $data/01_raw_data/local_ancestry/merged.bim -o2 $data/01_raw_data/combined_data/

# Step2: Run GPS algorithm using parallel processing
#echo "Running GPS on multiple cores..."
#python3 $scripts/run_gps_parallely.py -d $data/02_GPS/gps_file/ -go $data/02_GPS/gps_helper/geo.csv -ge $data/02_GPS/gps_helper/gen.csv -o $data/02_GPS/gps_results/ -r $scripts/GPS_command_line.R 

# Step3: Merge the chromosome predictions for adjacent windows based on geographic threshold
echo "Merging the chromosome segment predictions for adjacent windows based on geographic threshold..."
python3 $scripts/assign_merge_chr.py -g $data/02_GPS/gps_results/ -c $data/01_raw_data/combined_data/combined_data.csv -o $data/02_GPS/merged_files/merged_data.csv -t 1000



## Deactivate environment
conda deactivate
echo "Environment Deactivated"
import os
import ray
import subprocess
import argparse
from pathlib import Path

# Function to run the R script for each CSV file
@ray.remote
def run_gps_for_file(data_file, geo_file, gen_file, output_file, rscript_file):
    """Run the GPS R script for a specific file."""
    command = [
        "Rscript", rscript_file,
        geo_file, gen_file, data_file, output_file
    ]
    
    # Execute the R script using subprocess
    try:
        subprocess.run(command, check=True)
        print(f"Successfully processed {data_file}")
    except subprocess.CalledProcessError as e:
        print(f"Error processing {data_file}: {e}")

def process_files_in_parallel(data_directory, geo_file, gen_file, output_directory, rscript_file):
    """Process all CSV files in parallel using Ray."""
    
    # Get all CSV files in the data directory
    data_files = Path(data_directory).glob("*.csv")
    
    # Create output directory if it doesn't exist
    Path(output_directory).mkdir(parents=True, exist_ok=True)
    
    # Prepare the tasks for parallel processing
    tasks = []
    
    for data_file in data_files:
        # Define the output file path
        output_file = os.path.join(output_directory, f"output_{data_file.stem}.txt")
        
        # Add the task to the list
        tasks.append(run_gps_for_file.remote(str(data_file), geo_file, gen_file, output_file, rscript_file))
    
    # Wait for all tasks to complete
    ray.get(tasks)

if __name__ == "__main__":
    # Create argument parser
    parser = argparse.ArgumentParser(description="Run GPS analysis on multiple CSV files in parallel.")
    
    # Define command-line arguments
    parser.add_argument('-d',"--data_directory", help="Directory containing the data CSV files")
    parser.add_argument('-go',"--geo_file", help="Path to the geo.csv file")
    parser.add_argument('-ge',"--gen_file", help="Path to the gen.csv file")
    parser.add_argument('-o',"--output_directory", help="Directory to store the output results")
    parser.add_argument('-r',"--rscript_file", help="Path to the R script to run")
    
    # Parse the arguments
    args = parser.parse_args()
    
    # Initialize Ray
    ray.init(ignore_reinit_error=True)
    
    # Process the files in parallel
    process_files_in_parallel(args.data_directory, args.geo_file, args.gen_file, args.output_directory, args.rscript_file)

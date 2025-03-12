import os
import pandas as pd
import scipy as sp
import numpy as np
import argparse

# Define the main GPS function
def GPS(outfile_name='my_GPS_results.txt', N_best=10, filename="data.csv", geo_file="geo.csv", gen_file="gen.csv"):
    # Load the data
    GEO = pd.read_csv(geo_file, header=0, index_col=0)
    GEN = pd.read_csv(gen_file, header=None, index_col=0)
    TRAINING_DATA = pd.read_csv(filename, header=0, index_col=0)
    
    # Create distance matrices x and y from geo and gen
    y = sp.spatial.distance.pdist(GEO)
    x = sp.spatial.distance.pdist(GEN)
    
    # Loop through matrices, if geographical distance is >=70 or genetic distance is >=0.8, both are 0
    LL = len(y)
    for l in range(LL):
        if y[l] >= 70 or x[l] >= 0.8:
            y[l] = 0
            x[l] = 0
            
    # Make the linear regression
    slope, intercept, r, p, std_err = sp.stats.linregress(x, y)      
    
    # Make the groups variable: array with all unique populations
    groups = TRAINING_DATA["GROUP_ID"].unique()
    
    # Write header to output
    with open(outfile_name, "w") as f:
        f.write("Population\tSample_no\tSample_id\tPrediction\tlat\tlon\n")
        
    # Adjust N_best based on the number of available data points
    N_best = min(N_best, len(GEO))
    
    for group in groups:
        training_data_subset = TRAINING_DATA[TRAINING_DATA["GROUP_ID"] == group]  # Subset of the group
        num_rows = len(training_data_subset)  # Number of rows in the subset
        
        # Loop through rows in your subset group data
        for row in range(num_rows):  # Loop over the rows
            current_row_df = training_data_subset.iloc[row, :9].values  # Extract current row data
            E_vector = np.zeros(len(GEO))  # Create zero vector for genetic distances
            
            minE = 10000
            minG = -1
            minG_2 = -1
            
            # Loop through rows in GEO to compute genetic distances
            for geo_population in range(len(GEO)):  # Loop over populations
                ethnic = GEO.index[geo_population]  # Current ethnic group
                gene = GEN.loc[ethnic, :9].values  # Current genetic markers
                E_vector[geo_population] = np.sqrt(np.sum((gene - current_row_df) ** 2))
            
            minE = np.sort(E_vector)[0:N_best]  # Get the N_best smallest distances
            minG = np.zeros(N_best, dtype=int)
            
            for geo_populations_2 in range(len(GEO)):  # Loop over geo populations again
                for n in range(N_best):  # For each of the N_best
                    if np.allclose(minE[n], E_vector[geo_populations_2], rtol=1.5e-8):
                        minG[n] = geo_populations_2  # Store index of closest populations
                        
            radius = E_vector[minG]  # Get the genetic distance values
            best_ethnic = GEO.index[minG]  # These are the closest ethnic groups
            
            radius_geo = slope * radius[0]
            
            try:
                W = (minE[0] / minE) ** 4
                W = W / sum(W)  # Normalize the weights
            except:
                print(minE)
            
            delta_lat = GEO.iloc[minG, 0].values - GEO.iloc[minG[0], 0]
            delta_lon = GEO.iloc[minG, 1].values - GEO.iloc[minG[0], 1]
            
            new_lat = sum(W * delta_lat)
            new_lon = sum(W * delta_lon)
            
            lo1 = new_lon * min(1, radius_geo / np.sqrt(new_lon ** 2 + new_lat ** 2))
            la1 = new_lat * min(1, radius_geo / np.sqrt(new_lon ** 2 + new_lat ** 2))
            
            # Write the result to output file
            with open(outfile_name, "a") as f:
                f.write(f"{group}\t{row+1}\t{training_data_subset.index[row]}\t{best_ethnic[0]}\t{GEO.iloc[minG[0], 0] + la1}\t{GEO.iloc[minG[0], 1] + lo1}\n")

# Set up argument parser to take command-line arguments
def parse_arguments():
    parser = argparse.ArgumentParser(description="Run GPS script")
    
    # Define arguments
    parser.add_argument('--outfile', type=str, default='my_GPS_results.txt', help='Output file name')
    parser.add_argument('--N_best', type=int, default=10, help='Number of best results to consider')
    parser.add_argument('--data', type=str, default='data.csv', help='Data file')
    parser.add_argument('--geo', type=str, default='geo.csv', help='Geo file')
    parser.add_argument('--gen', type=str, default='gen.csv', help='Genetic data file')
    
    # Parse the arguments
    args = parser.parse_args()
    
    return args

if __name__ == '__main__':
    # Parse arguments from command line
    args = parse_arguments()
    
    # Call the GPS function with parsed arguments
    GPS(outfile_name=args.outfile, N_best=args.N_best, filename=args.data, geo_file=args.geo, gen_file=args.gen)

#!/usr/bin/env Rscript

# Load required libraries
args <- commandArgs(trailingOnly=TRUE)

# Check if correct number of arguments is provided
#if(length(args) < 4) {
#  stop("Usage: Rscript GPS.R <geo.csv> <gen.csv> <data.csv> <output_file>")
#}

# Assign command-line arguments
geo_file <- args[1]
gen_file <- args[2]
data_file <- args[3]
output_file <- args[4]

#geo_file <- "/home/inf-21-2024/binp29/population_genetic_project/data/02_GPS/geo.csv"
#gen_file <- "/home/inf-21-2024/binp29/population_genetic_project/data/02_GPS/gen.csv"
#data_file <- "/home/inf-21-2024/binp29/population_genetic_project/data/02_GPS/gps_file/data_1.csv"
#output_file <- "/home/inf-21-2024/binp29/population_genetic_project/data/02_GPS/gps_results/output_data1.txt"



GPS <- function(geo_file, gen_file, data_file, output_file, N_best=10) {
  
  # Read various data files
  GEO <- read.csv(geo_file, header=TRUE, row.names=1)
  GEO <- GEO[,1:2]
  GEN <- read.csv(gen_file, header=FALSE, row.names=1)
  TRAINING_DATA <- read.csv(data_file, header=TRUE, row.names=1)
  # Compute Euclidean distance matrices
  y <- dist(GEO)
  x <- dist(GEN)
  
  # If distance is too large or too small, set it to 0
  LL <- length(y)
  for(l in 1:LL) {
    if(y[l] >= 70 || x[l] >= 0.8) {
      y[l] <- 0
      x[l] <- 0
    }
  }
  
  # Compute linear regression between y and x
  eq1 <- lm(y ~ x)
  
  # Loop over various groups in training data
  GROUPS <- unique(TRAINING_DATA$GROUP)
  
  # Write header to output file
  write("Population\tSample_no\tSample_id\tPrediction\tLat\tLon", output_file, append=FALSE)
  
  N_best <- min(N_best, length(GEO[,1]))
  
  for(GROUP in GROUPS) {
    Y <- subset(TRAINING_DATA, TRAINING_DATA$GROUP_ID == GROUP)
    K <- length(Y[,1])
    for(a in 1:K) {
      X <- Y[a,1:9]
      E <- rep(0, length(GEO[,1]))
      minE <- numeric(0)
      minG <- numeric(0)
      
      for(g in 1:length(GEO[,1])) {
        ethnic <- attributes(GEO[g,])$row.names
        gene <- as.numeric(GEN[ethnic,1:9])
        E[g] <- sqrt(sum((gene - X)^2))
      }
      
      minE <- c(minE, sort(E, FALSE)[1:N_best])
      
      for(g in 1:length(GEO[,1])) {
        for(j in 1:N_best) {
          if(isTRUE(all.equal(minE[j], E[g]))) {
            minG[j] <- g
          }
        }
      }
      
      radius <- E[minG]
      best_ethnic <- attributes(GEO[minG,])$row.names
      radius_geo <- (eq1[[1]][2] * radius[1])
      W <- (minE[1] / minE)^4
      W <- W / sum(W)
      delta_lat <- (GEO[minG,][[1]] - GEO[minG[1],][[1]])
      delta_lon <- (GEO[minG,][[2]] - GEO[minG[1],][[2]])
      new_lon <- sum(W * delta_lon)
      new_lat <- sum(W * delta_lat)
      lo1 <- new_lon * min(1, radius_geo / sqrt(new_lon^2 + new_lat^2))
      la1 <- new_lat * min(1, radius_geo / sqrt(new_lon^2 + new_lat^2))
      
      write(paste(GROUP, a, row.names(Y[a,]), best_ethnic[1], GEO[minG[1],1] + la1, GEO[minG[1],2] + lo1, sep="\t"), output_file, append=TRUE)
    }
  }
  return("Done!")
}

# Run the function with command-line arguments
GPS(geo_file, gen_file, data_file, output_file)

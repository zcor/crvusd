import glob
import os

import pandas as pd
import pylab

# Specify the target directory and the file pattern
target_directory = (
    "scripts/data/"  # Update this to match the directory you want to search
)
file_pattern = "user_losses_*.csv"

# Find all matching files
files = glob.glob(os.path.join(target_directory, file_pattern))

# Get the most recent file
latest_file = max(files, key=os.path.getctime)

# Read the CSV file
data = pd.read_csv(latest_file)

# Get the unique users
users = data["User"].unique()

# Create a new figure with a specific size
pylab.figure(figsize=(12, 6))

# Plot the data for each user
for user in users:
    user_data = data[data["User"] == user]
    times = user_data["Time"]
    losses = user_data["Loss"]
    pylab.plot(times, losses, label=str(user))

# Add labels, legend, and show the plot
pylab.xlabel("t (blocks)")
pylab.ylabel("Loss (%)")
# pylab.legend(loc="best")
pylab.show()

print(f"Data loaded from {latest_file}")

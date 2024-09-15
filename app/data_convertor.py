import os
import glob
import pandas as pd
import numpy as np
from .utils import calculate_hand_angles

# Set directories for raw data and angles output
datasets_dir = "datasets"
raw_data_dir = os.path.join(datasets_dir, "raw_data")
angles_data_dir = os.path.join(datasets_dir, "angles")

# Create output directory if it does not exist
os.makedirs(angles_data_dir, exist_ok=True)

# Get all CSV files from the raw_data directory
csv_files = glob.glob(os.path.join(raw_data_dir, "*.csv"))

for csv_file in csv_files:
    # Read data from CSV file
    df = pd.read_csv(csv_file)

    all_angles = []
    # Calculate angles for each row of landmarks
    for _, row in df.iterrows():
        landmarks = np.array(
            [[row[f"landmark_{i}_{axis}"] for axis in "xyz"] for i in range(21)]
        )
        angles = calculate_hand_angles(landmarks)
        all_angles.append(angles)

    # Define column names for angles
    angle_columns = [f"angle_{i}" for i in range(len(all_angles[0]))]

    # Convert the list of angles to a DataFrame
    angles_df = pd.DataFrame(all_angles, columns=angle_columns)
    angles_df["gesture"] = df["gesture"]  # Add gesture column without timestamp

    # Set the output filename for angles data
    base_filename = os.path.basename(csv_file)
    angles_filename = os.path.join(angles_data_dir, f"angles_{base_filename}")

    # Save the angles data to CSV
    angles_df.to_csv(angles_filename, index=False)
    print(f"Angles data saved to {angles_filename}")

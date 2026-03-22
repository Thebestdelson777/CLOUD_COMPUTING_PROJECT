import pandas as pd
import numpy as np
from glob import glob

# Load all CSV files
files = sorted(glob("../data/raw/*.csv"))

print(f"Loading {len(files)} files...")

df_list = []

for f in files:
    print(f"Processing: {f}")
    df = pd.read_csv(f)
    
    # Fix column names (remove spaces)
    df.columns = df.columns.str.strip()
    
    df_list.append(df)

# Merge all files
df = pd.concat(df_list, ignore_index=True)

print("Merged shape:", df.shape)

# Replace infinite values
df.replace([np.inf, -np.inf], np.nan, inplace=True)

# Drop missing values
df.dropna(inplace=True)

# Convert label to binary
df['Label'] = df['Label'].apply(lambda x: 0 if x == 'BENIGN' else 1)

print("Cleaned shape:", df.shape)

# Save processed dataset
df.to_csv("../data/processed/cleaned_data.csv", index=False)

print("ETL completed successfully!")
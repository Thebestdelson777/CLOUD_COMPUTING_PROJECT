import pandas as pd
import numpy as np
from glob import glob

# Discover all raw CSV files in the raw data directory.
# Sorting ensures a deterministic file order so the merged dataset
# is reproducible regardless of the filesystem's default ordering.
files = sorted(glob("../data/raw/*.csv"))

print(f"Loading {len(files)} files...")

df_list = []

for f in files:
    print(f"Processing: {f}")
    df = pd.read_csv(f)

    # Strip leading/trailing whitespace from column names.
    # The CIC-IDS-2017 dataset includes a leading space in ' Label'
    # and similar columns; normalising names here prevents key errors
    # in all downstream steps.
    df.columns = df.columns.str.strip()

    df_list.append(df)

# Vertically concatenate all files into a single DataFrame.
# ignore_index=True resets the row index so it is unique after the merge.
df = pd.concat(df_list, ignore_index=True)

print("Merged shape:", df.shape)

# Replace infinite values with NaN before dropping nulls.
# Network flow calculations (e.g. packets/second) can produce inf
# when the flow duration is zero; these are not valid measurements.
df.replace([np.inf, -np.inf], np.nan, inplace=True)

# Remove rows that contain any NaN value.
# This is safe here because inf values have just been converted to NaN,
# so dropna() handles both categories in one pass.
df.dropna(inplace=True)

# Convert the multi-class label to binary: 0 = benign, 1 = attack.
# Collapsing attack categories into a single class aligns with the
# project goal of detecting any anomalous traffic, not classifying
# the specific attack type.
df['Label'] = df['Label'].apply(lambda x: 0 if x == 'BENIGN' else 1)

print("Cleaned shape:", df.shape)

# Persist the cleaned dataset to the processed zone.
# index=False keeps the file clean by omitting the row index column.
df.to_csv("../data/processed/cleaned_data.csv", index=False)

print("ETL completed successfully!")

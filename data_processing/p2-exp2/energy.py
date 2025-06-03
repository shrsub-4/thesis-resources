import pandas as pd
from glob import glob

# Load and combine all trials
files = sorted(glob("*_energy_log.csv"))
dfs = []

for file in files:
    df = pd.read_csv(file)
    df.columns = [col.strip().lower() for col in df.columns]
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="raise")
    dfs.append(df)

all_data = pd.concat(dfs, ignore_index=True)

# Filter for worker nodes
worker_data = all_data[all_data["name"].str.contains("worker")].copy()
worker_data.sort_values(by=["name", "timestamp"], inplace=True)

# Compute delta time and energy
worker_data["time_diff"] = (
    worker_data.groupby("name")["timestamp"].diff().dt.total_seconds()
)
worker_data["time_diff"].fillna(0, inplace=True)
worker_data["energy_joules"] = worker_data["power"] * worker_data["time_diff"]

# Aggregate per worker
summary = (
    worker_data.groupby("name")
    .agg({"power": "mean", "energy_joules": "sum"})
    .reset_index()
)

# Final formatting
summary.columns = ["Worker Node", "Avg Power (W)", "Total Energy (J)"]
summary["Energy (Wh)"] = summary["Total Energy (J)"] / 3600
summary[["Avg Power (W)", "Total Energy (J)", "Energy (Wh)"]] = summary[
    ["Avg Power (W)", "Total Energy (J)", "Energy (Wh)"]
].round(4)

# Grand total
grand_total_j = summary["Total Energy (J)"].sum().round(2)
grand_total_wh = summary["Energy (Wh)"].sum().round(4)

# Display
print("\n=== Worker Energy Summary Across All Trials ===")
print(summary)
print(f"\nTotal Energy: {grand_total_j} J ({grand_total_wh} Wh)")

# Optional: Save to file
summary.to_csv("worker_energy_full_summary.csv", index=False)

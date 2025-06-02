import pandas as pd
from glob import glob

# Map internal pod names to clean service labels
service_map = {
    "s1-inference": "S1 Inference",
    "s2-modeldepot": "S2 Storage",
    "s3-sensorcruncher": "S3 Sensor Process",
    "s4-sensorflood": "S4 Flood",
    "s5-audioprocessor": "S5 Audio",
}

# Gather all pod logs
files = glob("t*_pod_log.csv")

dfs = []
for file in files:
    df = pd.read_csv(file)
    df["service_key"] = df["name"].apply(lambda x: "-".join(x.split("-")[0:2]))
    df["Service"] = df["service_key"].map(service_map)
    dfs.append(df[df["Service"].notna()])

# Combine and compute stats
all_data = pd.concat(dfs, ignore_index=True)
summary = (
    all_data.groupby("Service")
    .agg({"cpu_util": "mean", "power": ["mean", "max"]})
    .reset_index()
)

# Rename columns
summary.columns = ["Service", "Avg_CPU_Util", "Avg_Power_W", "Max_Power_W"]
summary = summary.round(4)

# Output
print(summary)
summary.to_csv("cpu_power_with_max.csv", index=False)

import pandas as pd
from glob import glob

# Load and combine all CSVs
file_paths = sorted(glob("t*_pod_log.csv"))
dfs = [pd.read_csv(path) for path in file_paths]
all_data = pd.concat(dfs, ignore_index=True)

# Map pod names to service roles
name_mapping = {
    "s1-inference": "Inference",
    "s2-modeldepot": "Storage",
    "s3-sensorcruncher": "Sensor Process",
    "s4-sensorflood": "Sensor Flood",
    "s5-audioprocessor": "Audio Process",
}
all_data["Service"] = all_data["name"].apply(
    lambda x: name_mapping.get(x.split("-")[0] + "-" + x.split("-")[1], x)
)

# Compute average metrics
avg_metrics = (
    all_data.groupby("Service")[["cpu_util", "power", "memory_mib"]]
    .mean()
    .reset_index()
)
avg_metrics.columns = ["Service", "CPU Utilization (s)", "Power (mW)", "Memory MiB"]
avg_metrics = avg_metrics.round(4)

# Add total row
total_row = pd.DataFrame(
    {
        "Service": ["Total"],
        "Avg_CPU_Util": [avg_metrics["Avg_CPU_Util"].sum()],
        "Avg_Power_W": [avg_metrics["Avg_Power_W"].sum()],
        "Avg_Memory_MiB": [avg_metrics["Avg_Memory_MiB"].sum()],
    }
)
avg_metrics = pd.concat([avg_metrics, total_row], ignore_index=True)

# Save to CSV
avg_metrics.to_csv("always_on_metrics_summary.csv", index=False)

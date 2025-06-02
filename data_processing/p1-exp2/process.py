import pandas as pd

# Service name mapping
pod_service_map = {
    "s1-inference": "S1 Inference",
    "s2-modeldepot": "S2 Storage",
    "s3-sensorcruncher": "S3 Sensor Process",
    "s4-sensorflood": "S4 Flood",
    "s5-audioprocessor": "S5 Audio",
}
locust_services = ["S1 Inference", "S4 Flood", "S5 Audio"]
trials = ["t1", "t2", "t3"]

cpu_power_dfs = []
locust_dfs = []

for trial in trials:
    # Load files
    pod = pd.read_csv(f"{trial}_pod_log.csv")
    locust = pd.read_csv(f"{trial}_report.csv")

    # Extract pod-level service names
    pod["service_key"] = pod["name"].apply(lambda x: "-".join(x.split("-")[0:2]))
    pod["Service"] = pod["service_key"].map(pod_service_map)
    pod = pod[pod["Service"].notna()]

    # Average CPU/Power for all services
    cpu_power = pod.groupby("Service")[["cpu_util", "power"]].mean().reset_index()
    cpu_power.columns = ["Service", "Avg_CPU_Util", "Avg_Power_W"]
    cpu_power_dfs.append(cpu_power)

    # Locust metrics for S1, S4, S5 only
    locust_filtered = locust[locust["Name"].isin(locust_services)][
        [
            "Name",
            "Request Count",
            "Failure Count",
            "Average Response Time",
            "Max Response Time",
        ]
    ].copy()
    locust_filtered.columns = [
        "Service",
        "Request_Count",
        "Failure_Count",
        "Avg_Response_Time_ms",
        "Max_Response_Time_ms",
    ]
    locust_dfs.append(locust_filtered)

# Combine all trials
cpu_power_summary = (
    pd.concat(cpu_power_dfs)
    .groupby("Service")
    .mean(numeric_only=True)
    .reset_index()
    .round(4)
)
locust_summary = (
    pd.concat(locust_dfs)
    .groupby("Service")
    .mean(numeric_only=True)
    .reset_index()
    .round(2)
)

# Save output
cpu_power_summary.to_csv("summary_cpu_power.csv", index=False)
locust_summary.to_csv("summary_response_metrics.csv", index=False)

# Preview
print("\n=== CPU & Power Summary (All Services) ===")
print(cpu_power_summary)
print("\n=== Response Metrics Summary (S1, S4, S5) ===")
print(locust_summary)

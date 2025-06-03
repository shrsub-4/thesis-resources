import glob
import pandas as pd
import os


def aggregate_energy_logs(pattern="*_energy_log.csv"):
    all_files = glob.glob(pattern)
    if not all_files:
        print("No energy log files found.")
        return None

    dfs = [pd.read_csv(f) for f in all_files]
    df_concat = pd.concat(dfs, ignore_index=True)

    # Aggregate by node and round to 2 decimals
    energy_summary = (
        df_concat[df_concat["scope"] == "node"]
        .groupby("name")[["cpu_util", "power", "memory_util"]]
        .mean()
        .round(2)
        .reset_index()
    )
    energy_summary.to_csv("aggregated_energy.csv", index=False)
    print("✅ Saved aggregated_energy.csv")
    return energy_summary


def aggregate_report_logs(pattern="*_report.csv"):
    all_files = glob.glob(pattern)
    if not all_files:
        print("No report files found.")
        return None

    dfs = []
    for f in all_files:
        df = pd.read_csv(f)
        df = df[df["Type"].notna()]  # Remove Aggregated/NaN summary row
        dfs.append(df)

    df_concat = pd.concat(dfs, ignore_index=True)

    metrics = [
        "Request Count",
        "Failure Count",
        "Median Response Time",
        "Average Response Time",
        "Min Response Time",
        "Max Response Time",
        "Average Content Size",
        "Requests/s",
        "Failures/s",
    ]
    summary = df_concat.groupby("Name")[metrics].mean().round(2).reset_index()
    summary.to_csv("aggregated_report.csv", index=False)
    print("✅ Saved aggregated_report.csv")
    return summary


if __name__ == "__main__":
    print("🔄 Aggregating Energy Logs...")
    aggregate_energy_logs()

    print("🔄 Aggregating Report Logs...")
    aggregate_report_logs()

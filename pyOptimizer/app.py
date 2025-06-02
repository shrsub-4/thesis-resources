from math import e
import os
import datetime

from flask import Flask, jsonify, render_template
from dotenv import load_dotenv

from config import config as application_config
from metrics import k8s
from metrics.core import MetricsCore
from optimizer.core import PlacementOptimizer
from metrics.logger import ExperimentLogger

load_dotenv()
# Initialize Flask app
app = Flask(__name__)

KUBE_CONFIG = os.getenv("KUBE_CONFIG", "~/.kube/config")
SERVICE_NAME = os.getenv("SERVICE_NAME", "autocar")

config = application_config.get(SERVICE_NAME)
metrics_core = MetricsCore(config=config)
optimizer = PlacementOptimizer(config=config)
k8s_manager = k8s.KubernetesManager(config_file=KUBE_CONFIG)
logger = ExperimentLogger()


@app.route("/get_node")
def get_node():
    placement_map = k8s_manager.get_pod_mapping(services=config["workloads"])
    network_metrics = metrics_core.collect_network_metrics(placement_map)
    energy_metrics = metrics_core.collect_energy_metrics(
        placement_map, k8s_manager.get_internal_ip_mapping()
    )
    print("Network Metrics:", network_metrics)
    print("Energy Metrics:", energy_metrics)
    best_node = optimizer.loop(network_metrics, placement_map)

    return jsonify(
        {
            "node": best_node,
            "score": 1.0,
            "timestamp": datetime.datetime.now().isoformat(),
        }
    )


@app.route("/get_dashboard_data")
def dashboard():
    """
    Returns current placement and energy metrics, and logs them to CSV.
    """
    placement_map = k8s_manager.get_pod_mapping(services=config["workloads"])
    ip_mapping = k8s_manager.get_internal_ip_mapping()

    energy = metrics_core.collect_energy_metrics(placement_map, ip_mapping)
    timestamp = datetime.datetime.now().isoformat()

    node_rows = []
    pod_rows = []

    for row in energy["node_metrics"]:
        node_rows.append(
            {
                "timestamp": timestamp,
                "scope": "node",
                "name": row["node"],
                "cpu_util": row["cpu_util"],
                "power": row["power"],
                "memory_util": row.get("memory_util", 0.0),  # fraction (0.0–1.0)
            }
        )

    for row in energy["pod_metrics"]:
        pod_rows.append(
            {
                "timestamp": timestamp,
                "scope": "pod",
                "name": row["pod"],
                "node": row["node"],
                "cpu_util": row["cpu_util"],
                "power": row["power"],
                "memory_mib": row.get("memory_mib", 0.0),
            }
        )

    # logger.log(node_rows, filename="t1_node_log.csv")
    # logger.log(pod_rows, filename="t5_pod_log.csv")

    return jsonify({"metrics": energy, "mapping": placement_map})


@app.route("/ui")
def dashboard_ui():
    return render_template("dashboard.html")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8001)

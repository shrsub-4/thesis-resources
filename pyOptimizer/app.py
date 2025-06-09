import os
import re
import datetime

from flask import Flask, jsonify, render_template, request
from dotenv import load_dotenv

from config import config as application_config
from metrics import k8s
from metrics.core import MetricsCore
from metrics.logger import ExperimentLogger
from optimizer.core import HeuristicScheduler

load_dotenv()
# Initialize Flask app
app = Flask(__name__)

KUBE_CONFIG = os.getenv("KUBE_CONFIG", "~/.kube/config")
SERVICE_NAME = os.getenv("SERVICE_NAME", "autocar")

config = application_config.get(SERVICE_NAME)
metrics_core = MetricsCore(config=config)
k8s_manager = k8s.KubernetesManager(config_file=KUBE_CONFIG)
logger = ExperimentLogger()


def extract_service_name(pod_name: str) -> str:
    """
    Extracts full Knative service name from a pod name.
    Example: 's1-inference-00016-deployment-xyz' → 's1-inference'
    """
    match = re.match(r"^(.*)-\d{5}-deployment.*", pod_name)
    if match:
        return match.group(1)
    return pod_name.split("-")[0]


@app.route("/get_node")
def get_node():

    pod_name = request.args.get("pod")
    nodes = request.args.get("nodes", "").split(",")

    service_name = extract_service_name(pod_name) if pod_name else None
    if service_name not in config["workloads"]:
        return jsonify({"error": "No pod name provided"}), 400

    placement_map = k8s_manager.get_pod_mapping(services=config["workloads"])

    latency_metrics = metrics_core.collect_latency_metrics(service_name)

    source_workload = service_name
    destination_workload = config["associations"].get(service_name)

    traffic_metrics = None
    if destination_workload is not None:
        traffic_metrics = metrics_core.collect_traffic_metrics(
            source_workload=source_workload,
            destination_workload=destination_workload,
        )

    smart_cfg = config

    scheduler = HeuristicScheduler(
        placement_map=placement_map,
        nodes=nodes,
        config={
            "node_latency": latency_metrics,
            "node_traffic": traffic_metrics,
            "traffic_weight": smart_cfg["gamma"],
            "latency_weight": smart_cfg["alpha"],
            "energy_weight": smart_cfg["beta"],
            "association_graph": smart_cfg["association_graph"],
        },
    )

    node, score = scheduler.place(service_name)
    print(f"Placing {service_name} on {node} with score {score}")
    return jsonify(
        {
            "node": node,
            "score": score,
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

    energy = metrics_core.collect_dashboard_energy_metrics(placement_map, ip_mapping)
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

    return jsonify({"metrics": energy, "mapping": placement_map})


@app.route("/ui")
def dashboard_ui():
    return render_template("dashboard.html")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8001)

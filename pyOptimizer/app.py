import os

from flask import Flask
from dotenv import load_dotenv

from config import config as application_config
from metrics import k8s
from metrics.core import MetricsCore
from optimizer.core import PlacementOptimizer

load_dotenv()
# Initialize Flask app
app = Flask(__name__)

KUBE_CONFIG = os.getenv("KUBE_CONFIG", "~/.kube/config")
SERVICE_NAME = os.getenv("SERVICE_NAME", "autocar")


def get_node(pod: str):
    config = application_config.get(SERVICE_NAME)
    collector = MetricsCore(config=config)
    optimizer = PlacementOptimizer(
        nodes=config["nodes"],
        alpha=config["alpha"],
        beta=config["beta"],
        gamma=config.get("gamma", 0.0),
    )
    k8s_manager = k8s.KubernetesManager(config_file=KUBE_CONFIG)
    placement_map = k8s_manager.get_pod_mapping(services=config["workloads"])

    source_workload = placement_map.get(config["workloads"][0], {})
    destination_workload = placement_map.get(config["workloads"][1], {})

    raw_metrics = {}

    if len(source_workload) == 1 and len(destination_workload) == 1:
        print("One source and one destination workload are on a single node.")
        preferred_node = list(destination_workload.keys())[0]
        return preferred_node

    elif len(source_workload) == 1 and len(destination_workload) > 1:
        print(
            "Source workload is on one node, destination workload is spread across multiple nodes."
        )
        metrics = collector.collect_metrics(
            source_workload=config["workloads"][0],
            destination_workload=config["workloads"][1],
        )
        node_metrics = collector.aggregate_metrics_by_node(metrics, placement_map)
        return optimizer.loop(node_metrics)

    elif len(source_workload) > 1 and len(destination_workload) > 1:
        print(
            "Collecting node-level metrics for multiple source and destination workloads."
        )
        metrics = collector.collect_metrics(
            source_workload=config["workloads"][0],
            destination_workload=config["workloads"][1],
        )
        node_metrics = collector.aggregate_metrics_by_node(metrics, placement_map)
        return optimizer.loop(node_metrics)


best_node = get_node("autocar")
print(f"Best node for pod 'autocar' is: {best_node}")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8001)

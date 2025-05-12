import os
import time
from collections import defaultdict
from collections import deque
from xml.dom.expatbuilder import parseString

from metrics.metrics import MetricsCollector
from metrics.metrics import MetricsCollector
from metrics.request import RequestGenerator
from metrics.prometheus import PrometheusClient
from metrics.db import DBManager

PROM_URL = os.getenv("PROM_URL", "http://localhost:9090")

timeout = 10  # Timeout for app readiness check


class MetricsCore:
    def __init__(self, config):
        self.config = config
        self.prom = PrometheusClient(PROM_URL)
        self.collector = MetricsCollector(prom=self.prom)
        self.db = DBManager()

    def _flatten_pod_node_map(self, grouped_map):
        flat_map = {}
        for service, nodes in grouped_map.items():
            for node, pods in nodes.items():
                for pod in pods:
                    flat_map[pod] = node
        return flat_map

    def aggregate_metrics_by_node(self, metrics_by_pod, pod_node_map):
        node_metrics = defaultdict(
            lambda: {"latency": [], "bandwidth": [], "energy": 0}
        )
        pod_node_map = self._flatten_pod_node_map(pod_node_map)

        for pod, node in pod_node_map.items():
            if pod in metrics_by_pod.get("latency", {}):
                node_metrics[node]["latency"].append(metrics_by_pod["latency"][pod])
            if pod in metrics_by_pod.get("bandwidth", {}):
                node_metrics[node]["bandwidth"].append(metrics_by_pod["bandwidth"][pod])
            if pod in metrics_by_pod.get("energy", {}):
                node_metrics[node]["energy"] += metrics_by_pod["energy"][pod]

        final = {}
        for node, values in node_metrics.items():
            final[node] = {
                "latency": (
                    sum(values["latency"]) / len(values["latency"])
                    if values["latency"]
                    else 0
                ),
                "bandwidth": (
                    sum(values["bandwidth"]) / len(values["bandwidth"])
                    if values["bandwidth"]
                    else 0
                ),
                "energy": values["energy"],
            }
        return final

    def collect_metrics(self, source_workload, destination_workload):
        resp = self.collector.get_metrics(
            source_workload=source_workload,
            destination_workload=destination_workload,
        )
        return resp

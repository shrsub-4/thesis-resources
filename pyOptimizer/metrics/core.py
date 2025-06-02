import os
import networkx as nx
from collections import defaultdict

from metrics.metrics import MetricsCollector
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

    def _aggregate_metrics_by_node(self, metrics_by_pod, pod_node_map):
        node_metrics = defaultdict(lambda: {"latency": [], "bandwidth": []})
        pod_node_map = self._flatten_pod_node_map(pod_node_map)

        for pod, node in pod_node_map.items():
            if pod in metrics_by_pod.get("latency", {}):
                node_metrics[node]["latency"].append(metrics_by_pod["latency"][pod])
            if pod in metrics_by_pod.get("bandwidth", {}):
                node_metrics[node]["bandwidth"].append(metrics_by_pod["bandwidth"][pod])

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
            }
        return final

    def collect_network_metrics(self, placement_map):
        entrypoints = self.config["entrypoints"]

        if not entrypoints:
            raise ValueError("No entrypoints defined in the configuration.")

        for entrypoint in entrypoints:
            latency_metrics = self.collector._get_workload_request_duration(
                destination_workload=entrypoint,
            )

        return latency_metrics

    # ========== Energy Metrics

    def collect_energy_metrics(self, placement_map, ip_mapping=None):
        """
        Collect energy metrics for the given placement map.
        """
        raw_metrics = self.collector.get_energy_metrics(placement_map, ip_mapping)
        return raw_metrics

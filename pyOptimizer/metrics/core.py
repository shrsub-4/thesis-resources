import os
import time
from collections import deque

from metrics.metrics import MetricsCollector
from metrics.placement import PlacementManager
from metrics.metrics import MetricsCollector
from metrics.request import RequestGenerator
from metrics.prometheus import PrometheusClient
from metrics.db import DBManager

PROM_URL = os.getenv("PROM_URL", "http://localhost:9090")
KUBE_CONFIG = os.getenv("KUBE_CONFIG", "~/.kube/config")

timeout = 10  # Timeout for app readiness check


class MetricsCore:
    def __init__(self, config):
        self.config = config
        self.prom = PrometheusClient(PROM_URL)
        self.collector = MetricsCollector(prom=self.prom)
        self.requester = RequestGenerator(url=self.config["application_url"])
        self.placement_manager = PlacementManager(config_file=KUBE_CONFIG)
        self.db = DBManager()
        self.source_workload = self.config["workloads"][0]
        self.destination_workload = self.config["workloads"][1]

    def _open_file(self, file_path):
        if os.path.exists(file_path):
            return self._open_file(file_path)
        else:
            return None

    def _request_pod(self):
        headers = self.config["request"]["headers"]
        data = self.config["request"]["data"]
        files = self.config["request"]["files"]

        for _ in range(2):
            if files:
                file = {
                    "image": (files["name"], open(files["path"], "rb"), files["type"])
                }
            resp_code, duration = self.requester.send_request(
                headers=headers, data=data, files=file
            )
            print(f"Response code: {resp_code}, Duration: {duration}")

    def _collect_metrics(self):
        metrics = []

        resp = self.collector.get_metrics(
            source_workload=self.config["workloads"][0],
            destination_workload=self.config["workloads"][1],
        )
        return resp

    def loop(self):
        node_queue = deque(self.config["nodes"])
        while node_queue:
            print(node_queue)
            node = node_queue.popleft()

            # ==== Placement Logic
            actual_node = self.placement_manager.get_running_node(
                app_name=self.source_workload
            )
            if actual_node != node:
                print(
                    f"App {self.source_workload} expect on {node} but found in {actual_node}. Rotating.."
                )
                print(f"Placing {self.source_workload} on {node}")
                self.placement_manager.place_app_on(
                    node_name=node, deployment_name=self.source_workload
                )
                time.sleep(5)

            print(f"App {self.source_workload} is running on {node}")

            if not self.placement_manager.is_app_ready(app_name=self.source_workload):
                print(f"App {self.source_workload} is not ready on {node}. Skipping...")
                node_queue.append(node)
                continue

            # ==== Metrics Logic
            print("Sending request to pod...")
            self._request_pod()

            metrics = self._collect_metrics()
            if not metrics or metrics.get("request_duration") is None:
                print("No metrics collected for node {node}. Skipping...")
                continue
            self.db.write_metrics(metrics=metrics, node=node)

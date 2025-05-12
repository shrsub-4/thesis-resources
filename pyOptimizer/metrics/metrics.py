import math
from metrics.queries import (
    REQUEST_PER_SEC_QUERY,
    BYTES_PER_SEC_QUERY,
    LATENCY_QUERY,
    POD_ENERGY,
)
from metrics.prometheus import PrometheusClient
from dotenv import load_dotenv

load_dotenv()


class MetricsCollector:
    def __init__(self, prom: PrometheusClient):
        self.prom = prom

    def _get_request_duration(self, destination_workload):
        result = self.prom.query(LATENCY_QUERY.format(app=destination_workload))
        pod_latencies = {}

        for entry in result:
            pod = entry["metric"].get("pod")
            try:
                value = float(entry["value"][1])
                if not math.isnan(value):
                    pod_latencies[pod] = value
            except (ValueError, TypeError):
                continue

        return pod_latencies

    def _get_request_bandwidth(self, source_workload, destination_workload):
        result = self.prom.query(
            BYTES_PER_SEC_QUERY.format(
                source=source_workload, destination=destination_workload
            )
        )
        bandwidths = {}
        for entry in result:
            pod = entry["metric"].get("source_pod") or entry["metric"].get("pod")
            try:
                value = float(entry["value"][1])
                if not math.isnan(value):
                    bandwidths[pod] = value
            except (ValueError, TypeError):
                continue
        return bandwidths

    def _get_request_per_sec(self, source_workload, destination_workload):
        result = self.prom.query(
            REQUEST_PER_SEC_QUERY.format(
                source=source_workload, destination=destination_workload
            )
        )
        rps = {}
        for entry in result:
            pod = entry["metric"].get("source_pod") or entry["metric"].get("pod")
            try:
                value = float(entry["value"][1])
                if not math.isnan(value):
                    rps[pod] = value
            except (ValueError, TypeError):
                continue
        return rps

    def _get_per_request_bandwidth(self, source_workload, destination_workload):
        bandwidths = self._get_request_bandwidth(source_workload, destination_workload)
        rps = self._get_request_per_sec(source_workload, destination_workload)

        bpr = {}
        for pod, bps in bandwidths.items():
            requests = rps.get(pod)
            if requests and requests > 0:
                bpr[pod] = (bps / 1024) / requests  # in KB/request
            else:
                bpr[pod] = 0
        return bpr

    def _estimate_power(self, cpu_util: float):
        return 3.4842 * cpu_util + 2.2434

    def _get_energy_watts(self, app):
        result = self.prom.query(POD_ENERGY.format(app=app))
        energy = {}
        for entry in result:
            pod = entry["metric"].get("pod")
            try:
                cpu_util = float(entry["value"][1])
                if not math.isnan(cpu_util):
                    energy[pod] = self._estimate_power(cpu_util)
            except (ValueError, TypeError):
                continue
        return energy

    def get_metrics(self, source_workload, destination_workload):
        request_duration = self._get_request_duration(destination_workload)
        per_request_bandwidth = self._get_per_request_bandwidth(
            source_workload, destination_workload
        )
        energy_watts = self._get_energy_watts(source_workload) | self._get_energy_watts(
            destination_workload
        )

        return {
            "latency": request_duration,
            "bandwidth": per_request_bandwidth,
            "energy": energy_watts,
        }

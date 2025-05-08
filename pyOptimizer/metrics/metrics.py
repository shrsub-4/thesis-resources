import math
from metrics.queries import REQUEST_PER_SEC_QUERY, BYTES_PER_SEC_QUERY, LATENCY_QUERY
from metrics.prometheus import PrometheusClient
from dotenv import load_dotenv

load_dotenv()

class MetricsCollector:
    def __init__(self, prom: PrometheusClient):
        self.prom = prom

    def _get_request_duration(self, destination_workload):
        result = self.prom.query(LATENCY_QUERY.format(app=destination_workload))
        if result:
            value = float(result[0]["value"][1])
            if math.isnan(value):
                return None
            return value
        return None

    def _get_request_bandwidth(self, source_workload, destination_workload):
        result = self.prom.query(BYTES_PER_SEC_QUERY.format(source=source_workload, destination=destination_workload))
        if result:
            value = float(result[0]["value"][1])
            if math.isnan(value):
                return None
            return value
        return None
    
    def _get_request_per_sec(self, source_workload, destination_workload):
        result = self.prom.query(REQUEST_PER_SEC_QUERY.format(source=source_workload, destination=destination_workload))
        if result:
            value = float(result[0]["value"][1])
            if math.isnan(value):
                return None
            return value
        return None
    
    def _get_per_request_bandwidth(self, source_workload, destination_workload):
        bandwidth = self._get_request_bandwidth(source_workload, destination_workload)
        request_per_sec = self._get_request_per_sec(source_workload, destination_workload)
        if bandwidth is not None:
            if request_per_sec is not None and request_per_sec > 0:
                return (bandwidth / 1024) / request_per_sec
            else:
                # If request_per_sec is 0 or None, we can't calculate per_request_bandwidth
                # We can return None or raise an exception based on your requirement
                # For now, we'll just return None
                print("Request per second is zero or None, cannot calculate per request bandwidth.")
        return None

    def get_metrics(self, source_workload, destination_workload):
        request_duration = self._get_request_duration(destination_workload)
        per_request_bandwidth = self._get_per_request_bandwidth(source_workload, destination_workload)

        return {
            "request_duration": request_duration,
            "per_request_bandwidth": per_request_bandwidth
        }
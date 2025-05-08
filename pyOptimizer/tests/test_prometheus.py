import os
from metrics.prometheus import PrometheusClient

PROM_URL = os.getenv("PROM_URL", "http://192.168.112.23:30529")

def test_prometheus_client():
    prom = PrometheusClient(url=PROM_URL)
    query = """
    (histogram_quantile(0.95, sum(irate(istio_request_duration_milliseconds_bucket{{reporter="destination", connection_security_policy="mutual_tls", destination_service=~"{app}.default.svc.cluster.local", destination_workload=~"{app}", destination_workload_namespace=~"shadow"}}[1m])) by (destination_workload, destination_workload_namespace, le)) / 1000)
    """
    result = prom.query(query.format(app="appservice"))
    assert result is not None, "Expected non-empty result"

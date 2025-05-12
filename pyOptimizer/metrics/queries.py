LATENCY_QUERY = """
histogram_quantile(0.95, sum(
  irate(istio_request_duration_milliseconds_bucket{{
    reporter="destination",
    connection_security_policy="mutual_tls",
    destination_workload="{app}",
    destination_workload_namespace="default"
  }}[1m])
) by (pod, le))
"""

BYTES_PER_SEC_QUERY = """
sum(
  irate(istio_request_bytes_sum{{
    source_workload="{source}",
    source_workload_namespace="default",
    destination_workload="{destination}"
  }}[1m])
) by (pod)
"""

REQUEST_PER_SEC_QUERY = """
sum(irate(istio_requests_total{{
  source_workload="{source}",
  destination_workload="{destination}",
  source_workload_namespace="default"
}}[1m])) by (source_pod)
"""

POD_ENERGY = """
sum(rate(container_cpu_usage_seconds_total{{
  namespace="default",
  pod=~"{app}.*"
}}[1m])) by (pod)
"""

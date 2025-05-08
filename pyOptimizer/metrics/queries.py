LATENCY_QUERY = """
(histogram_quantile(0.50, sum(irate(istio_request_duration_milliseconds_bucket{{reporter="destination", 
connection_security_policy="mutual_tls", destination_service=~"{app}.shadow.svc.cluster.local", 
destination_workload=~"{app}", 
destination_workload_namespace=~"shadow"}}[1m])) by (destination_workload, destination_workload_namespace, le)))
"""

BYTES_PER_SEC_QUERY = """
sum(irate(istio_request_bytes_bucket{{
  source_workload_namespace="shadow",
  source_workload=~"{source}",
  destination_service=~"{destination}.*"
}}[1m])) by (source_workload, destination_service)
"""

REQUEST_PER_SEC_QUERY = """
sum(irate(istio_requests_total{{source_workload_namespace="shadow",source_workload=~"{source}", destination_service=~"{destination}.*"}}[1m])) by (source_workload)
"""

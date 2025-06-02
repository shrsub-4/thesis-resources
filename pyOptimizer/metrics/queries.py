LATENCY_QUERY = """
histogram_quantile(0.95, sum(
  irate(istio_request_duration_milliseconds_bucket{{
    reporter="destination",
    destination_workload=~"^{destination}.*",
    destination_workload_namespace="default"
  }}[1m])
) by (node, le))
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
}}[1m])) by (pod)
"""

REQUEST_TOTAL = """
sum(irate(istio_requests_total{
  namespace="default"
}[1m])) by (source_workload, destination_workload)"""

POD_ENERGY = """
sum(rate(container_cpu_usage_seconds_total{{
  namespace="default",
  pod=~"{app}.*"
}}[1m])) by (pod)
"""

NODE_ENERGY = """
1 - avg(rate(node_cpu_seconds_total{{mode="idle", instance="{instance_ip}:9100"}}[1m]))
"""

POD_MEMORY = """
container_memory_working_set_bytes{{
  namespace="default",
  pod="{app}"
}}
"""

NODE_MEMORY = """
1 - (
  (node_memory_MemAvailable_bytes{{instance="{instance_ip}:9100"}}) /
  (node_memory_MemTotal_bytes{{instance="{instance_ip}:9100"}})
)
"""

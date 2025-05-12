import time
from kubernetes import client, config


class KubernetesManager:
    def __init__(self, namespace="default", config_file=None):
        config.load_kube_config(config_file=config_file)
        self.namespace = namespace
        self.apps = client.AppsV1Api()
        self.core = client.CoreV1Api()

    def get_running_node(self, app_name):
        pods = self.core.list_namespaced_pod(
            namespace=self.namespace, label_selector=f"app={app_name}"
        ).items
        if not pods:
            return None
        return pods[0].spec.node_name

    def get_pod_mapping(self, services: list[str]):
        service_pods = {}

        for service in services:
            pods = self.core.list_namespaced_pod(
                namespace=self.namespace, label_selector=f"app={service}"
            ).items

            if not pods:
                continue  # Skip this service if no pods

            if service not in service_pods:
                service_pods[service] = {}

            for pod in pods:
                node_name = pod.spec.node_name
                pod_name = pod.metadata.name

                if node_name not in service_pods[service]:
                    service_pods[service][node_name] = []

                service_pods[service][node_name].append(pod_name)

        return service_pods

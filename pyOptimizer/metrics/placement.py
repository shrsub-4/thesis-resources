import time
from kubernetes import client, config


class PlacementManager:
    def __init__(self, namespace="shadow", config_file=None):
        config.load_kube_config(config_file=config_file)
        self.namespace = namespace
        self.apps = client.AppsV1Api()
        self.core = client.CoreV1Api()

    def place_app_on(self, node_name, deployment_name):
        print(f"Patching {deployment_name} to run on {node_name}...")

        patch = {
            "spec": {
                "template": {
                    "spec": {
                        "affinity": {
                            "nodeAffinity": {
                                "requiredDuringSchedulingIgnoredDuringExecution": {
                                    "nodeSelectorTerms": [
                                        {
                                            "matchExpressions": [
                                                {
                                                    "key": "kubernetes.io/hostname",
                                                    "operator": "In",
                                                    "values": [node_name],
                                                }
                                            ]
                                        }
                                    ]
                                }
                            }
                        }
                    }
                }
            }
        }

        self.apps.patch_namespaced_deployment(
            name=deployment_name, namespace=self.namespace, body=patch
        )

        self._restart_pods(app_name=deployment_name)

    def _restart_pods(self, app_name):
        print(f"Restarting pods for {app_name}...")
        pods = self.core.list_namespaced_pod(
            namespace=self.namespace, label_selector=f"app={app_name}"
        )
        for pod in pods.items:
            self.core.delete_namespaced_pod(
                name=pod.metadata.name, namespace=self.namespace
            )
            print(f"Deleted pod {pod.metadata.name}")

    def get_running_node(self, app_name):
        pods = self.core.list_namespaced_pod(
            namespace=self.namespace, label_selector=f"app={app_name}"
        ).items
        if not pods:
            return None
        return pods[0].spec.node_name

    def is_app_ready(self, app_name, timeout=60):
        print(f"Waiting for pod '{app_name}' to become Ready...")

        start = time.time()
        while time.time() - start < timeout:
            pods = self.core.list_namespaced_pod(
                namespace=self.namespace, label_selector=f"app={app_name}"
            ).items

            # Delays if terminating pods are found
            # if len(pods) != 1:
            #     time.sleep(2)
            #     continue

            pod = pods[0]
            if pod.status.phase != "Running":
                time.sleep(2)
                continue

            conditions = pod.status.conditions or []
            ready = any(
                cond.type == "Ready" and cond.status == "True" for cond in conditions
            )
            if ready:
                print(f"Pod {pod.metadata.name} is Ready.")
                return True

            time.sleep(2)

        print(f"Timeout: Pod '{app_name}' did not become ready within {timeout}s.")
        return False

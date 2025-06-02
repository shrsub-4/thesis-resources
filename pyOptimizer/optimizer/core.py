class HeuristicScheduler:
    def __init__(self, placement_map, metrics, traffic_graph, config):
        self.placement_map = placement_map
        self.metrics = metrics
        self.traffic_graph = traffic_graph  # e.g. {'s1': ['s2'], 's4': ['s3']}
        self.config = config

        self.node_metrics = {m["node"]: m for m in metrics["node_metrics"]}
        self.pod_metrics = {m["pod"]: m for m in metrics["pod_metrics"]}

    def node_has_pods(self, node):
        return any(node in pods for pods in self.placement_map.values())

    def compute_node_score(self, candidate_node, app_name):
        deps = self.traffic_graph.get(app_name, [])
        score = 0.0

        # ⚡ Add energy cost if node is currently off
        if not self.node_has_pods(candidate_node):
            score += self.config["idle_node_penalty"]  # e.g. 2.38W

        for dep in deps:
            dep_nodes = self.placement_map.get(dep, {})
            colocated = candidate_node in dep_nodes

            # 📦 Inter-node traffic cost
            if not colocated:
                traffic = self.config["traffic_costs"].get((app_name, dep), 0)
                score += self.config["traffic_weight"] * traffic

            # 📶 Latency cost
            latency = (
                self.config["latency_costs"]
                .get((app_name, dep), {})
                .get(candidate_node)
            )
            if latency:
                score += self.config["latency_weight"] * latency

        return score  # Lower is better

    def place(self, app_name):
        best_node = None
        best_score = float("inf")

        for node in self.node_metrics.keys():
            score = self.compute_node_score(node, app_name)
            if score < best_score:
                best_score = score
                best_node = node

        return best_node

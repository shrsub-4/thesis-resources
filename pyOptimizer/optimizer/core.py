class HeuristicScheduler:
    def __init__(self, placement_map, nodes, config):
        """
        Args:
            placement_map: dict of {service: {node: [pods]}}
            traffic_graph: dict of {service: [dependent_service]}
            config: weights and cost mappings
        """
        self.placement_map = placement_map
        self.nodes = nodes
        self.config = config

    def node_has_pods(self, node):
        return any(node in node_pods for node_pods in self.placement_map.values())

    def compute_energy_activation_penalty(self, node, service):
        if self.node_has_pods(node):
            return 0.0
        return self.config.get("idle_node_penalty", 2.2857)

    def get_colocation_ratio(self, dep_service, candidate_node):
        dep_nodes = self.placement_map.get(dep_service, {})
        total_pods = sum(len(pods) for pods in dep_nodes.values())
        colocated_pods = len(dep_nodes.get(candidate_node, []))
        if total_pods == 0:
            return 0.0
        return colocated_pods / total_pods

    def get_effective_latency(self, node: str, colocated: bool, meta: dict) -> float:
        """
        Returns the effective latency for a given node, considering colocation and overrides.
        """
        node_latency = self.config.get("node_latency", {})

        if node in node_latency:
            return node_latency[node] / 1000

        return (
            meta.get("colocated_latency", 1.5)
            if colocated
            else meta.get("remote_latency", 10.0)
        )

    def get_cost_components(self, app_name):
        traffic_vals, latency_vals, node_scores = [], [], {}

        for node in self.nodes:
            traffic_total = 0.0
            latency_total = 0.0

            for (src, dst), meta in self.config["association_graph"].items():
                if src != app_name:
                    continue

                coloc_ratio = self.get_colocation_ratio(dst, node)
                is_colocated = coloc_ratio >= 1.0

                # --- Traffic ---
                traffic = self.config.get("traffic", None)
                traffic_total += (1 - coloc_ratio) * (
                    traffic if traffic is not None else meta.get("traffic_cost", 0.0)
                )

                # --- Latency ---
                latency_val = self.get_effective_latency(node, is_colocated, meta)
                latency_total += latency_val

            activation_cost = self.compute_energy_activation_penalty(node, app_name)

            node_scores[node] = {
                "traffic": traffic_total,
                "latency": latency_total,
                "activation": activation_cost,
            }

            traffic_vals.append(traffic_total)
            latency_vals.append(latency_total)

        return node_scores, traffic_vals, latency_vals

    def normalize(self, val, min_val, max_val):
        if max_val == min_val:
            return 0.0
        return (val - min_val) / (max_val - min_val)

    def place(self, app_name):
        best_node = None
        best_score = float("inf")

        node_scores, traffic_vals, latency_vals = self.get_cost_components(app_name)
        t_min, t_max = min(traffic_vals), max(traffic_vals)
        l_min, l_max = min(latency_vals), max(latency_vals)
        p_min, p_max = 0, self.config.get("idle_node_penalty", 2.2857)
        for node, raw in node_scores.items():
            t_hat = self.normalize(raw["traffic"], t_min, t_max)
            l_hat = self.normalize(raw["latency"], l_min, l_max)
            p_hat = self.normalize(raw["activation"], p_min, p_max)

            score = (
                self.config.get("traffic_weight", 0.2) * t_hat
                + self.config.get("latency_weight", 0.4) * l_hat
                + self.config.get("energy_weight", 0.4) * p_hat
            )

            if score < best_score:
                best_score = score
                best_node = node

        return best_node, best_score

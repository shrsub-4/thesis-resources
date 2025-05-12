import sqlite3


class PlacementOptimizer:
    def __init__(self, nodes=None, limit=5, alpha=0.3, beta=0.2, gamma=0.5):
        self.nodes = nodes
        self.alpha = alpha
        self.beta = beta
        self.gamma = gamma
        self.best_node = None

    def _normalize(self, raw_metrics):
        max_latency = max(m["latency"] for m in raw_metrics.values())
        max_bandwidth = max(m["bandwidth"] for m in raw_metrics.values())
        max_energy = max(m["energy"] for m in raw_metrics.values())
        normalized = {}
        for node, m in raw_metrics.items():
            normalized[node] = {
                "latency": m["latency"] / max_latency if max_latency else 1,
                "bandwidth": m["bandwidth"] / max_bandwidth if max_bandwidth else 1,
                "energy": m["energy"] / max_energy if max_energy else 1,
            }
        return normalized

    def _score_nodes(self, normalized):
        scores = {}
        for node, m in normalized.items():
            score = (
                self.alpha * m["latency"]
                + self.beta * m["bandwidth"]
                + self.gamma * m["energy"]
            )
            scores[node] = score
        return scores

    def _get_best_node(self, scores):
        best_node = min(scores, key=scores.get)
        return best_node

    def loop(self, metrics):
        normalized = self._normalize(metrics)
        scores = self._score_nodes(normalized)
        print(f"Scores written to DB: {scores}")
        return self._get_best_node(scores)

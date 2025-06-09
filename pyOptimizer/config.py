config = {
    "smart-house": {
        "version": "1.0",
        "nodes": ["worker-1", "worker-2", "worker-3"],
        "workloads": [
            "s1-inference",
            "s2-modeldepot",
            "s3-sensorcruncher",
            "s4-sensorflood",
            "s5-audioprocessor",
        ],
        "associations": {
            "s1-inference": "s2-modeldepot",
            "s4-sensorflood": "s3-sensorcruncher",
            "s5-audioprocessor": None,
        },
        "association_graph": {
            ("s1-inference", "s2-modeldepot"): {
                "traffic_cost": 24255131,
                "colocated_latency": 1.7,
                "remote_latency": 10.47,
            },
            ("s4-sensorflood", "s3-sensorcruncher"): {
                "traffic_cost": 1281787,
                "colocated_latency": 1.22,
                "remote_latency": 2.31,
            },
            ("s3-sensorcruncher", "s3-sensorcruncher"): {
                "traffic_cost": 0,
                "colocated_latency": 0.877,
                "remote_latency": 0.877,
            },
            ("s5-audioprocessor", "s5-audioprocessor"): {
                "traffic_cost": 0,
                "colocated_latency": 0.877,
                "remote_latency": 0.877,
            },
        },
        "entrypoints": ["s1-inference", "s4-sensorflood", "s5-audioprocessor"],
        "alpha": 0.5,
        "beta": 0.3,
        "gamma": 0.2,
    }
}

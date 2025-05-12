import random

config = {
    "autocar": {
        "version": "1.0",
        "application_url": "http://192.168.112.23:32423/upload",
        "nodes": ["worker-1", "worker-2", "worker-3"],
        "workloads": ["appservice", "db-service"],
        "alpha": 0.3,
        "beta": 0.2,
        "gamma": 0.5,
        "request": {
            "headers": {"Host": "appservice.default.example.com"},
            "data": {
                "lidar_distance": str(round(random.uniform(1.0, 3.5), 1)),
                "radar_speed": str(round(random.uniform(4.0, 8.0), 1)),
                "ultrasonic": str(round(random.uniform(2.0, 5.0), 1)),
            },
            "files": {"name": "img.webp", "path": "img.webp", "type": "image/webp"},
        },
        "deployment": [
            {
                "name": "appservice",
                "type": "web",
                "replicas": 3,
                "resources": {"cpu": 2, "memory": 4},
            },
            {
                "name": "db-service",
                "type": "database",
                "replicas": 2,
                "resources": {"cpu": 4, "memory": 8},
            },
        ],
    }
}

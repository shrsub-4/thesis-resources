config = {
    "smart-house": {
        "version": "1.0",
        "workloads": [
            "s1-inference",
            "s2-modeldepot",
            "s3-sensorcruncher",
            "s4-sensorflood",
            "s5-audioprocessor",
        ],
        "associations": [
            ("s1-inference", "s2-modeldepot"),
            ("s4-sensorflood", "s3-sensorcruncher"),
        ],
        "entrypoints": ["s1-inference", "s4-sensorflood", "s5-audioprocessor"],
        "alpha": 0.3,
        "beta": 0.2,
        "gamma": 0.5,
    },
}

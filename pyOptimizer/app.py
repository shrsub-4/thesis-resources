import os
import threading
import time
from tracemalloc import start
from flask import Flask, jsonify
from dotenv import load_dotenv

from config import config
from metrics.core import MetricsCore

load_dotenv()

COLLECT_INTERVAL = int(os.getenv("COLLECT_INTERVAL", 10))
SERVICE_NAME = os.getenv("SERVICE_NAME", "appservice")
# Initialize Flask app
app = Flask(__name__)

print("Starting Optimizer...")
collector = MetricsCore(config=config[SERVICE_NAME])


def start_collector():
    while True:
        collector.loop()
        time.sleep(COLLECT_INTERVAL)


threading.Thread(target=start_collector, daemon=True).start()


@app.route("/placement")
def index():
    return jsonify({"status": "ok", "message": "Optimizer is alive."})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=4000)

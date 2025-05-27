import requests
import time
import os

GATEWAY_URL = os.getenv("GATEWAY_URL", "http://192.168.163.23:32710")
HOST_HEADER = "s4-sensorflood.default.example.com"
CSV_PATH = "assets/sensors.csv"


def run_flood_loop():
    try:
        while True:
            try:
                if not os.path.exists(CSV_PATH):
                    print(f"File not found: {CSV_PATH}")
                    time.sleep(5)
                    continue

                with open(CSV_PATH, "rb") as f:
                    start = time.time()
                    r = requests.post(
                        GATEWAY_URL + "/upload?batch_size=10000",
                        files={"file": ("sensors.csv", f, "text/csv")},
                        headers={"Host": HOST_HEADER},
                        timeout=10,
                    )
                    duration = time.time() - start
                    print(f"S4 Flood: {r.status_code} in {duration:.2f}s")
                    print(f"Response: {r.text[:100]}")
            except Exception as e:
                print(f"S4 Inner Error: {e}")
            time.sleep(5)
    except Exception as e:
        print(f"S4 Flood thread crashed: {e}")

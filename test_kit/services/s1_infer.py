import requests
import time
import os

GATEWAY_URL = os.getenv("GATEWAY_URL", "http://192.168.163.23:32710")
HOST_HEADER = "s1-inference.default.example.com"
IMAGE_PATH = "assets/img.webp"


def run_inference_loop():
    while True:
        try:
            with open(IMAGE_PATH, "rb") as f:
                start = time.time()
                r = requests.post(
                    GATEWAY_URL + "/infer",
                    files={"file": f},
                    headers={"Host": HOST_HEADER},
                )
                duration = time.time() - start
                print(r.json())
                print(f"S1 Inference: {r.status_code} in {duration:.2f}s")
        except Exception as e:
            print(f"S1 Error: {e}")
        time.sleep(5)

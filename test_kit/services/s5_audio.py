import requests
import time
import os

GATEWAY_URL = os.getenv("GATEWAY_URL", "http://192.168.163.23:30119")
HOST_HEADER = "s5-audioprocessor.default.example.com"
AUDIO_PATH = "assets/sound.wav"


def run_audio_loop():
    while True:
        try:
            with open(AUDIO_PATH, "rb") as f:
                start = time.time()
                r = requests.post(
                    GATEWAY_URL + "/audio",
                    files={"file": f},
                    headers={"Host": HOST_HEADER},
                )
                duration = time.time() - start
                print(f"S5 RoomAudio: {r.status_code} in {duration:.2f}s")
        except Exception as e:
            print(f"S5 Error: {e}")
        time.sleep(5)

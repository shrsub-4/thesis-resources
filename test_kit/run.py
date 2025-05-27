import threading
import time
from services.s1_infer import run_inference_loop
from services.s5_audio import run_audio_loop
from services.s4_flood import run_flood_loop

if __name__ == "__main__":
    print("Starting TestKit...")

    threads = [
        threading.Thread(target=run_inference_loop, daemon=True),
        threading.Thread(target=run_audio_loop, daemon=True),
        threading.Thread(target=run_flood_loop, daemon=True),
    ]

    for t in threads:
        t.start()

    print("Load running. Press Ctrl+C to stop.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopped by user.")

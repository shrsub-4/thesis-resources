from locust import HttpUser, task, between
import time


class AutonomousCarUser(HttpUser):
    wait_time = between(5, 8)  # 1 second delay between requests

    @task
    def send_inference_request(self):
        headers = {"Host": "knappservice.default.example.com"}
        data = {"lidar_distance": "2.0", "radar_speed": "5.4", "ultrasonic": "3.2"}
        with open("img.webp", "rb") as image_file:
            files = {"image": ("img.webp", image_file, "image/webp")}
            start_time = time.time()
            response = self.client.post(
                "/upload", headers=headers, data=data, files=files, name="/upload"
            )
            duration = time.time() - start_time
            print(f"Response_time ======== {duration}")
            print(f"Status Code: {response.status_code}")


# locust -f locustfile.py --host=http://192.168.163.23:30772

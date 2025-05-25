import requests
import time


def sendRequest():
    # Define the server URL
    url = "http://192.168.163.23:30772/upload"

    # Set the headers (including the required Host header)
    headers = {"Host": "knappservice.default.example.com"}

    # Define the form data
    data = {"lidar_distance": "2.0", "radar_speed": "5.4", "ultrasonic": "3.2"}

    # Define the file to upload
    files = {"image": ("img.webp", open("img.webp", "rb"), "image/webp")}
    start_time = time.time()
    response = requests.post(url, headers=headers, data=data, files=files)
    duration = time.time() - start_time
    print(f"Response_time ======== {duration}")
    print("Response Code:", response.status_code)
    print("Response Body:", response.text)


if __name__ == "__main__":
    for i in range(1000):
        sendRequest()
        time.sleep(1)

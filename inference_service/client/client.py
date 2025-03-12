import requests

# Define the server URL
url = "http://10.104.0.94:31245/upload"

# Set the headers (including the required Host header)
headers = {
    "Host": "gateway.default.example.com"
}

# Define the form data
data = {
    "lidar_distance": "2.0",
    "radar_speed": "5.4",
    "ultrasonic": "3.2"
}

# Define the file to upload
files = {
    "image": ("img.webp", open("img.webp", "rb"), "image/webp")
}

# Send the POST request
response = requests.post(url, headers=headers, data=data, files=files)

    # Print the server's response
print("Response Code:", response.status_code)
print("Response Body:", response.text)
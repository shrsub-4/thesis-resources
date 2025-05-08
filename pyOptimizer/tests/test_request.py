from metrics.request import RequestGenerator

def test_request_generator():
    url = "http://192.168.112.23:30912/upload"
    generator = RequestGenerator(url)
    
    headers = {
        "Host": "appservice.shadow.example.com"
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
    
    status_code, duration = generator.send_request(headers=headers, data=data, files=files)
    
    assert status_code == 200, f"Expected status code 200, got {status_code}"
    assert duration > 0, f"Expected positive duration, got {duration}"
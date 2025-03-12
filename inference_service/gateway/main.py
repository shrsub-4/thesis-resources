from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

INFERENCE_URL = os.getenv("INFERENCE_URL", "http://inference.default.svc.cluster.local/detect")

@app.route("/upload", methods=["POST"])
def upload_data():
    # Extract sensor data
    lidar_distance = request.form.get("lidar_distance")
    radar_speed = request.form.get("radar_speed")
    ultrasonic = request.form.get("ultrasonic")

    if not (lidar_distance and radar_speed and ultrasonic):
        return jsonify({"error": "Missing required sensor data"}), 400

    try:
        lidar_distance = float(lidar_distance)
        radar_speed = float(radar_speed)
        ultrasonic = float(ultrasonic)
    except ValueError:
        return jsonify({"error": "Invalid sensor data format"}), 400

    # Extract image file
    image_file = request.files.get("image")
    if not image_file:
        return jsonify({"error": "Image file is required"}), 400

    # Send request to Inference Service
    files = {"image": (image_file.filename, image_file.stream, image_file.mimetype)}
    data = {
        "lidar_distance": str(lidar_distance),
        "radar_speed": str(radar_speed),
        "ultrasonic": str(ultrasonic)
    }

    try:
        inference_response = requests.post(INFERENCE_URL, files=files, data=data)
        inference_response.raise_for_status()
        response_data = inference_response.json()
    except requests.RequestException as e:
        return jsonify({"error": f"Failed to communicate with inference service: {str(e)}"}), 500

    return jsonify(response_data), 200

@app.route("/status", methods=["GET"])
def status_check():
    return jsonify({"status": "Gateway Service is running"}), 200

if __name__ == "__main__":
    app.run(port=5000, debug=True)
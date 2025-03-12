from flask import Flask, request, jsonify
import requests
import cv2
import numpy as np
import os

app = Flask(__name__)

DECISION_URL = os.getenv("DECISION_URL", "http://decision.default.svc.cluster.local/make-decision")

# Load YOLOv4 Tiny Model for Object Detection
net = cv2.dnn.readNet("yolov4-tiny.weights", "yolov4-tiny.cfg")
layer_names = net.getLayerNames()
out_layers = [layer_names[i - 1] for i in net.getUnconnectedOutLayers()]

# Constants for visualization
MARGIN = 10  # pixels
ROW_SIZE = 10  # pixels
FONT_SIZE = 1
FONT_THICKNESS = 1
TEXT_COLOR = (255, 0, 0)  # red

# Load COCO class labels
with open("coco.names", "r") as f:
    CLASSES = f.read().strip().split("\n")

def visualize(image, detections, confidences, class_ids, boxes):
    """Draw bounding boxes on the input image and return it."""
    for i in range(len(boxes)):
        x, y, w, h = boxes[i]
        cv2.rectangle(image, (x, y), (x + w, y + h), TEXT_COLOR, 2)
        label = f"{CLASSES[class_ids[i]]} ({confidences[i]:.2f})"
        cv2.putText(image, label, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, FONT_SIZE, TEXT_COLOR, FONT_THICKNESS)
    return image

@app.route("/detect", methods=["POST"])
def detect():
    # Extract sensor data
    lidar_distance = request.form.get("lidar_distance")
    radar_speed = request.form.get("radar_speed")
    ultrasonic = request.form.get("ultrasonic")
    image_file = request.files.get("image")

    if not (lidar_distance and radar_speed and ultrasonic and image_file):
        return jsonify({"error": "Missing required data"}), 400

    try:
        lidar_distance = float(lidar_distance)
        radar_speed = float(radar_speed)
        ultrasonic = float(ultrasonic)
    except ValueError:
        return jsonify({"error": "Invalid sensor data format"}), 400

    # Convert image to OpenCV format
    image_np = np.frombuffer(image_file.read(), np.uint8)
    image = cv2.imdecode(image_np, cv2.IMREAD_COLOR)
    height, width = image.shape[:2]

    # Prepare YOLO input
    blob = cv2.dnn.blobFromImage(image, 0.00392, (416, 416), swapRB=True, crop=False)
    net.setInput(blob)
    detections = net.forward(out_layers)

    # Process YOLO detections
    boxes, confidences, class_ids = [], [], []
    for output in detections:
        for detection in output:
            scores = detection[5:]
            class_id = np.argmax(scores)
            confidence = scores[class_id]
            if confidence > 0.5:
                center_x, center_y, w, h = (detection[0:4] * np.array([width, height, width, height])).astype("int")
                x = int(center_x - w / 2)
                y = int(center_y - h / 2)
                boxes.append([x, y, int(w), int(h)])
                confidences.append(float(confidence))
                class_ids.append(class_id)

    detected_classes = [CLASSES[i] for i in class_ids] if class_ids else ["Unknown"]

    # Visualize detection results (optional)
    annotated_image = visualize(image, detections, confidences, class_ids, boxes)
    cv2.imwrite("annotated_image.jpg", annotated_image)  # Save for debugging

    # Forward processed data to Decision Service
    decision_data = {
        "lidar_distance": lidar_distance,
        "radar_speed": radar_speed,
        "ultrasonic": ultrasonic,
        "detected_classes": detected_classes
    }

    try:
        decision_response = requests.post(DECISION_URL, json=decision_data)
        decision_response.raise_for_status()
        decision_result = decision_response.json()
    except requests.RequestException as e:
        return jsonify({"error": f"Failed to communicate with decision service: {str(e)}"}), 500

    # Return final response to Gateway
    return jsonify({
        "detected_classes": detected_classes,
        "decision": decision_result.get("decision", "Unknown")
    }), 200

@app.route("/status", methods=["GET"])
def status_check():
    return jsonify({"status": "Inference Service is running"}), 200

if __name__ == "__main__":
    app.run(port=5001, debug=True)

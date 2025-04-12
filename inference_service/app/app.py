from flask import Flask, request, jsonify
import cv2
import numpy as np
import requests
import os
import datetime

app = Flask(__name__)

# DB
DB_BASE = os.getenv("DB_BASE", "http://localhost:5000")
TABLE_NAME = "inference_logs"
DB_API = f"{DB_BASE}/record/{TABLE_NAME}"
TABLES_API = f"{DB_BASE}/tables"

# === DECISION CONFIG ===
STOP_OBJECTS = {"person", "cat", "dog", "bicycle", "motorcycle", "bus", "truck"}
SLOW_DOWN_OBJECTS = {"car", "scooter", "cart"}

# === YOLO CONFIG ===
net = cv2.dnn.readNet("yolov4-tiny.weights", "yolov4-tiny.cfg")
layer_names = net.getLayerNames()
out_layers = [layer_names[i - 1] for i in net.getUnconnectedOutLayers()]

with open("coco.names", "r") as f:
    CLASSES = f.read().strip().split("\n")

TEXT_COLOR = (255, 0, 0)
FONT_SIZE = 1
FONT_THICKNESS = 1

# DB Services
_table_cache = set()

def table_exists():
    if TABLE_NAME in _table_cache:
        return True
    try:
        response = requests.get(TABLES_API, timeout=2)
        response.raise_for_status()
        tables = response.json()
        if TABLE_NAME in tables:
            _table_cache.add(TABLE_NAME)
            return True
    except requests.RequestException as e:
        print(f"Couldn't fetch table list: {e}")
    return False

def log_to_db(lidar_distance, radar_speed, ultrasonic, detected_classes, decision):
    payload = {
        "record": {
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "lidar_distance": lidar_distance,
            "radar_speed": radar_speed,
            "ultrasonic": ultrasonic,
            "detected_classes": ",".join(detected_classes),
            "decision": decision
        }
    }

    # Add schema only if table is missing
    if not table_exists():
        payload["schema"] = {
            "timestamp": "TEXT",
            "lidar_distance": "REAL",
            "radar_speed": "REAL",
            "ultrasonic": "REAL",
            "detected_classes": "TEXT",
            "decision": "TEXT"
        }

    try:
        response = requests.post(DB_API, json=payload, timeout=3)
        response.raise_for_status()
        print("Log saved to DB")
    except requests.RequestException as e:
        print(f"Failed to log to DB: {e}")

def visualize(image, boxes, confidences, class_ids):
    for i in range(len(boxes)):
        x, y, w, h = boxes[i]
        cv2.rectangle(image, (x, y), (x + w, y + h), TEXT_COLOR, 2)
        label = f"{CLASSES[class_ids[i]]} ({confidences[i]:.2f})"
        cv2.putText(image, label, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, FONT_SIZE, TEXT_COLOR, FONT_THICKNESS)
    return image

def run_object_detection(image):
    height, width = image.shape[:2]
    blob = cv2.dnn.blobFromImage(image, 0.00392, (416, 416), swapRB=True, crop=False)
    net.setInput(blob)
    detections = net.forward(out_layers)

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
    return detected_classes, boxes, confidences, class_ids

def make_decision(detected_classes):
    detected_set = set(detected_classes)
    if detected_set & STOP_OBJECTS:
        return "STOP"
    elif detected_set & SLOW_DOWN_OBJECTS:
        return "SLOW DOWN"
    else:
        return "GO"

@app.route("/upload", methods=["POST"])
def handle_upload():
    # Sensor data
    lidar_distance = request.form.get("lidar_distance")
    radar_speed = request.form.get("radar_speed")
    ultrasonic = request.form.get("ultrasonic")
    image_file = request.files.get("image")

    if not (lidar_distance and radar_speed and ultrasonic and image_file):
        return jsonify({"error": "Missing sensor or image data"}), 400

    try:
        lidar_distance = float(lidar_distance)
        radar_speed = float(radar_speed)
        ultrasonic = float(ultrasonic)
    except ValueError:
        return jsonify({"error": "Invalid sensor data format"}), 400

    # Image processing
    image_np = np.frombuffer(image_file.read(), np.uint8)
    image = cv2.imdecode(image_np, cv2.IMREAD_COLOR)
    detected_classes, boxes, confidences, class_ids = run_object_detection(image)

    # Annotated image (optional for debugging)
    annotated_image = visualize(image, boxes, confidences, class_ids)
    cv2.imwrite("annotated_image.jpg", annotated_image)

    # Decision logic
    decision = make_decision(detected_classes)

    log_to_db(
        lidar_distance,
        radar_speed,
        ultrasonic,
        detected_classes,
        decision
    )

    return jsonify({
        "detected_classes": detected_classes,
        "decision": decision
    }), 200

@app.route("/status", methods=["GET"])
def status():
    return jsonify({"status": "Unified Service is running"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
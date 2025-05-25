from flask import Flask, request, jsonify
import cv2
import numpy as np
import requests
import os
import datetime
import threading

app = Flask(__name__)

# === CONFIG ===
DB_BASE = os.getenv("DB_BASE", "http://localhost:5000")
TABLE_NAME = "inference_logs"
DB_API = f"{DB_BASE}/record/{TABLE_NAME}"
TABLES_API = f"{DB_BASE}/tables"

STOP_OBJECTS = {"person", "cat", "dog", "bicycle", "motorcycle", "bus", "truck"}
SLOW_DOWN_OBJECTS = {"car", "scooter", "cart"}

with open("coco.names", "r") as f:
    CLASSES = f.read().strip().split("\n")

TEXT_COLOR = (255, 0, 0)
FONT_SIZE = 1
FONT_THICKNESS = 1

thread_local = threading.local()


def get_net():
    """Thread-local DNN model"""
    if not hasattr(thread_local, "net"):
        net = cv2.dnn.readNet("yolov4-tiny.weights", "yolov4-tiny.cfg")
        layer_names = net.getLayerNames()
        out_layers = [layer_names[i - 1] for i in net.getUnconnectedOutLayers()]
        thread_local.net = (net, out_layers)
    return thread_local.net


def run_object_detection(image):
    height, width = image.shape[:2]
    blob = cv2.dnn.blobFromImage(image, 0.00392, (416, 416), swapRB=True, crop=False)
    net, out_layers = get_net()
    net.setInput(blob)
    detections = net.forward(out_layers)

    boxes, confidences, class_ids = [], [], []
    for output in detections:
        for detection in output:
            scores = detection[5:]
            class_id = np.argmax(scores)
            confidence = scores[class_id]
            if confidence > 0.5:
                center_x, center_y, w, h = (
                    detection[0:4] * np.array([width, height, width, height])
                ).astype("int")
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
    return "GO"


def log_to_db(lidar_distance, radar_speed, ultrasonic, detected_classes, decision):
    payload = {
        "record": {
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "lidar_distance": lidar_distance,
            "radar_speed": radar_speed,
            "ultrasonic": ultrasonic,
            "detected_classes": ",".join(detected_classes),
            "decision": decision,
        }
    }

    try:
        response = requests.get(TABLES_API, timeout=2)
        if TABLE_NAME not in response.json():
            payload["schema"] = {
                "timestamp": "TEXT",
                "lidar_distance": "REAL",
                "radar_speed": "REAL",
                "ultrasonic": "REAL",
                "detected_classes": "TEXT",
                "decision": "TEXT",
            }
    except:
        pass

    try:
        requests.post(DB_API, json=payload, timeout=3)
    except Exception as e:
        print("DB log failed:", e)


@app.route("/upload", methods=["POST"])
def handle_upload():
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

    image_np = np.frombuffer(image_file.read(), np.uint8)
    image = cv2.imdecode(image_np, cv2.IMREAD_COLOR)
    detected_classes, boxes, confidences, class_ids = run_object_detection(image)
    decision = make_decision(detected_classes)

    log_to_db(lidar_distance, radar_speed, ultrasonic, detected_classes, decision)

    return jsonify({"detected_classes": detected_classes, "decision": decision}), 200


@app.route("/status", methods=["GET"])
def status():
    return jsonify({"status": "Service is running"}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

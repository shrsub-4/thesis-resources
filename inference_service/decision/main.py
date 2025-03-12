from flask import Flask, request, jsonify

app = Flask(__name__)

# Define objects that should trigger actions
STOP_OBJECTS = {"person", "cat", "dog", "bicycle", "motorcycle", "bus", "truck"}  # Stop for humans & animals
SLOW_DOWN_OBJECTS = {"car", "scooter", "cart"}  # Slow down for vehicles

@app.route("/make-decision", methods=["POST"])
def make_decision():
    data = request.json

    if not data or "detected_classes" not in data:
        return jsonify({"error": "Missing detected classes"}), 400

    detected_classes = set(data["detected_classes"])  # Convert list to set for fast lookup

    # Decision logic
    if detected_classes & STOP_OBJECTS:  # If any STOP object is detected
        decision = "STOP"
    elif detected_classes & SLOW_DOWN_OBJECTS:  # If any SLOW DOWN object is detected
        decision = "SLOW DOWN"
    else:
        decision = "GO"

    return jsonify({"decision": decision}), 200

@app.route("/status", methods=["GET"])
def status_check():
    return jsonify({"status": "Decision Service is running"}), 200

if __name__ == "__main__":
    app.run(port=5002, debug=True)
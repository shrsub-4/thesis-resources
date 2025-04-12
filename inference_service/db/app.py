from flask import Flask, request, jsonify
import sqlite3
import os
from datetime import datetime

app = Flask(__name__)
DB_PATH = os.getenv("DB_PATH", "decisions.db")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.close()

init_db()

@app.route("/record/<table>", methods=["POST"])
def record_to_table(table):
    data = request.json
    if not data:
        return jsonify({"error": "Empty request"}), 400

    schema = data.get("schema")  # Optional: used to define the table
    record = data.get("record")

    if not record or not isinstance(record, dict):
        return jsonify({"error": "Missing or invalid 'record' object"}), 400

    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()

        # Create table if schema is provided
        if schema:
            fields = ", ".join([f"{k} {v}" for k, v in schema.items()])
            c.execute(f"CREATE TABLE IF NOT EXISTS {table} ({fields})")

        # Insert record
        columns = ", ".join(record.keys())
        placeholders = ", ".join(["?"] * len(record))
        values = tuple(record.values())
        c.execute(f"INSERT INTO {table} ({columns}) VALUES ({placeholders})", values)

        conn.commit()
        conn.close()
        return jsonify({"message": "Record inserted"}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/tables", methods=["GET"])
def list_tables():
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in c.fetchall()]
        conn.close()
        return jsonify(tables), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/status", methods=["GET"])
def status():
    return jsonify({"status": "DB Service running"}), 200

if __name__ == "__main__":
    print("Starting DB Service...")
    app.run(host="0.0.0.0", port=5001, debug=True)
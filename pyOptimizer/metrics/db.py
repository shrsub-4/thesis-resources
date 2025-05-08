import sqlite3
import os
from datetime import datetime


class DBManager:
    def __init__(self, db_path="metrics.db"):
        self.db_path = db_path
        self._initialize_db()

    def _initialize_db(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS metrics_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    node TEXT,
                    latency REAL,
                    bandwidth REAL,
                    timestamp TEXT
                )
            """
            )
            conn.commit()

    def write_metrics(self, metrics: dict, node: str = None):
        if not metrics:
            print("[DB] Empty metrics, nothing to write.")
            return

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO metrics_log (node, latency, bandwidth, timestamp)
                VALUES (?, ?, ?, ?)
            """,
                (
                    node,
                    metrics.get("request_duration"),
                    metrics.get("per_request_bandwidth"),
                    datetime.utcnow().isoformat(),
                ),
            )
            conn.commit()
            print(f"[DB] Metrics written for node {node}.")

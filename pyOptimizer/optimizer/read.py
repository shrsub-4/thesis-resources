import sqlite3


class DBReader:
    def __init__(self, db_path="metrics.db"):
        self.db_path = db_path

    def read_metrics(self, node: str = None, limit: int = 10):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            if node:
                cursor.execute(
                    """
                    SELECT node, latency, bandwidth, timestamp
                    FROM metrics_log WHERE node = ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                    """,
                    (node, limit),
                )
            else:
                cursor.execute(
                    """
                    SELECT * FROM metrics_log
                    """
                )
            rows = cursor.fetchall()
            return rows

from read import DBReader

db = DBReader()
metrics = db.read_metrics("worker-2", limit=5)
print(metrics)

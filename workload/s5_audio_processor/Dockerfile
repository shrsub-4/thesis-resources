FROM python:3.12-slim

WORKDIR /app
COPY . .

RUN apt-get update && apt-get install -y libsndfile1 && \
    pip install --no-cache-dir -r requirements.txt

EXPOSE 8080
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080"]
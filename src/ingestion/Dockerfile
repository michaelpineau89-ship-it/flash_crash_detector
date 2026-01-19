FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .

# Cloud Functions Gen 2 uses port 8080 by default
CMD ["python", "main.py"]
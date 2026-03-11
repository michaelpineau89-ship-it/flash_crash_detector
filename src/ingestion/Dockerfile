# 1. Use an official, lightweight Python base image
FROM python:3.11-slim

# 2. Set the working directory inside the container
WORKDIR /app

# 3. Copy the requirements file first (this caches dependencies to speed up future builds)
COPY requirements.txt .

# 4. Install the Python packages
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copy your ingestion script into the container
COPY main.py .

# 6. Set default environment variables (these can be overridden in Cloud Run)
ENV PROJECT_ID="mike-personal-portfolio"
ENV TOPIC_ID="crypto-ticks"

# 7. Start the WebSocket listener when the container launches
CMD ["python", "main.py"]
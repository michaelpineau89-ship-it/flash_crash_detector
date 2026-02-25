import os
import json
import logging
from flask import Flask, request
from google.cloud import pubsub_v1

# Configure logging so you can see it in Cloud Run Logs
logging.basicConfig(level=logging.INFO)

# Initialize the Flask web server
app = Flask(__name__)

# Initialize the Pub/Sub client globally (best practice for performance)
publisher = pubsub_v1.PublisherClient()

# Grab the project and topic from environment variables (with fallbacks)
PROJECT_ID = os.environ.get("PROJECT_ID", "mike-personal-portfolio")
TOPIC_ID = os.environ.get("TOPIC_ID", "stock-ticks")
topic_path = publisher.topic_path(PROJECT_ID, TOPIC_ID)

@app.route("/", methods=["POST"])
def entry_point():
    try:
        # 1. Parse the incoming JSON payload from the HTTP request
        stock_data = request.get_json()
        
        if not stock_data:
            return "No JSON data provided", 400

        # 2. Convert to bytes for Pub/Sub
        message_bytes = json.dumps(stock_data).encode("utf-8")
        
        # 3. Publish the message
        publish_future = publisher.publish(topic_path, data=message_bytes)
        publish_future.result() # Wait for confirmation
        
        # 4. Log and return success
        logging.info(f"Published: {stock_data.get('symbol', 'UNKNOWN')} @ ${stock_data.get('price', 'UNKNOWN')}")
        return "Data published.", 200

    except Exception as e:
        logging.error(f"Publish Error: {e}")
        return f"Publish Error: {e}", 500

# The magic loop that keeps the Cloud Run container alive
if __name__ == "__main__":
    # Cloud Run injects the PORT environment variable
    port = int(os.environ.get("PORT", 8080))
    # Run the server on all network interfaces (0.0.0.0)
    app.run(host="0.0.0.0", port=port)
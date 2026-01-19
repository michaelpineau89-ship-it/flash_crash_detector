import os
import json
import time
import logging
import requests
from google.cloud import pubsub_v1

# Configure Logging
logging.basicConfig(level=logging.INFO)

# Initialize Pub/Sub Client (Global to reuse across invocations)
publisher = pubsub_v1.PublisherClient()

def get_stock_data(api_key, symbol="IBM"):
    """Fetch raw data from Alpha Vantage."""
    url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={api_key}"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if "Global Quote" not in data:
            logging.warning(f"API Rate Limit or Error: {data}")
            return None
            
        quote = data["Global Quote"]
        return {
            "symbol": quote.get("01. symbol"),
            "price": float(quote.get("05. price", 0)),
            "volume": int(quote.get("06. volume", 0)),
            "change_percent": quote.get("10. change percent"),
            "timestamp": time.time()  # Ingestion time
        }
    except Exception as e:
        logging.error(f"Error fetching data: {e}")
        return None

def entry_point(request):
    """
    Cloud Function Entry Point.
    Triggered by HTTP request (from Cloud Scheduler).
    """
    project_id = os.environ.get('PROJECT_ID')
    topic_id = os.environ.get('TOPIC_ID', 'stock-ticks-topic')
    api_key = os.environ.get('API_KEY')
    
    if not api_key:
        logging.error("API_KEY environment variable not set.")
        return "Config Error", 500

    # 1. Fetch Data
    stock_data = get_stock_data(api_key)
    
    if not stock_data:
        return "API Error or Rate Limit", 429

    # 2. Publish to Pub/Sub
    try:
        topic_path = publisher.topic_path(project_id, topic_id)
        message_json = json.dumps(stock_data)
        message_bytes = message_json.encode('utf-8')
        
        # Publish returns a future
        publish_future = publisher.publish(topic_path, data=message_bytes)
        publish_future.result()  # Wait for confirmation
        
        logging.info(f"Published: {stock_data['symbol']} @ ${stock_data['price']}")
        return "Data published.", 200
        
    except Exception as e:
        logging.error(f"Publish Error: {e}")
        return f"Publish Error: {e}", 500
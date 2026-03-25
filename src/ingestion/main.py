import os
import logging
import websocket
from google.cloud import pubsub_v1

# 1. Configuration
PROJECT_ID = os.environ.get("PROJECT_ID", "mike-personal-portfolio")
TOPIC_ID = os.environ.get("TOPIC_ID", "crypto-ticks")
WS_URL = "wss://stream.binance.com:9443/ws/btcusdt@trade"

# 2. Initialize Pub/Sub Publisher
publisher = pubsub_v1.PublisherClient()
topic_path = publisher.topic_path(PROJECT_ID, TOPIC_ID)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# 3. WebSocket Callbacks
def on_message(ws, message):
    try:
        # Binance sends a JSON string. We encode it to bytes and fire it directly to Pub/Sub.
        publisher.publish(topic_path, message.encode('utf-8'))
    except Exception as e:
        logging.error(f"❌ Failed to publish message: {e}")

def on_error(ws, error):
    logging.error(f"⚠️ WebSocket Error: {error}")

def on_close(ws, close_status_code, close_msg):
    logging.warning("🔴 WebSocket connection closed.")

def on_open(ws):
    logging.info("🟢 Connected to Binance WebSocket. Listening for trades...")

# 4. Main Execution
def run():
    ws = websocket.WebSocketApp(
        WS_URL,
        on_open=on_open,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close
    )
    
    # run_forever blocks the main thread and keeps the script alive.
    # reconnect=5 tells it to automatically try reconnecting after 5 seconds if the connection drops.
    ws.run_forever(reconnect=5)

if __name__ == "__main__":
    run()
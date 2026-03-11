import os
import websocket
from google.cloud import pubsub_v1

import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
import logging

# Configures standard Python logging to output timestamps and severity levels
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# 1. Initialize Pub/Sub Client
PROJECT_ID = os.environ.get("PROJECT_ID", "mike-personal-portfolio")
TOPIC_ID = os.environ.get("TOPIC_ID", "crypto-ticks")
publisher = pubsub_v1.PublisherClient()
topic_path = publisher.topic_path(PROJECT_ID, TOPIC_ID)

# 2. Binance WebSocket URL for raw BTC/USDT trades
WS_URL = "wss://stream.binance.com:9443/ws/btcusdt@trade"

def on_open(ws):
    logging.info("🟢 Connected to Binance WebSocket: Streaming BTC/USDT trades...")

def on_message(ws, message):
    try:
        data_bytes = message.encode("utf-8")
        publisher.publish(topic_path, data=data_bytes)
    except Exception as e:
        logging.error(f"❌ Error publishing to Pub/Sub: {e}")

def on_error(ws, error):
    logging.error(f"⚠️ WebSocket Error: {error}")

def on_close(ws, close_status_code, close_msg):
    logging.info("🔴 WebSocket connection closed")

# A dummy server that just replies "200 OK" to Cloud Run's health checks
class DummyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Alive")

def run_dummy_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), DummyHandler)
    server.serve_forever()

if __name__ == "__main__":
    logging.info("🚀 Starting real-time crypto ingestion service...")
    threading.Thread(target=run_dummy_server, daemon=True).start()
    
    ws = websocket.WebSocketApp(
        WS_URL,
        on_open=on_open,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close
    )
    
    ws.run_forever(reconnect=5)
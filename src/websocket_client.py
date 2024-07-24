from loguru import logger
from tqdm import tqdm
from pathlib import Path
import Utils.config as config
import time
from websocket import WebSocketApp, WebSocketException, enableTrace
import _thread
import json

script_path = Path(__file__).resolve()
script_dir = script_path.parent

ws = None  # Global variable to hold the WebSocket connection

def on_message(ws, message):
    logger.info(f"Received message: {message}")

def on_error(ws, error):
    logger.error(f"WebSocket Error: {error}")

def on_close(ws, status_code, message):
    logger.warning(f"WebSocket connection closed with status code {status_code} and message {message}")

def on_open(ws): 
    logger.info("WebSocket connection opened")
    ws.send(json.dumps({"message": "Hello Server!"}))

def start_websocket():
    global ws
    ws_address = "ws://python-app:6000/"

    enableTrace(True)
    retries = 5
    for attempt in range(retries):
        try:
            ws = WebSocketApp(ws_address, 
                              on_message=on_message, 
                              on_error=on_error, 
                              on_close=on_close)
            ws.on_open = on_open
            ws.run_forever()
            break  # exit the loop if connection is successful
        except WebSocketException as e:
            if attempt < retries - 1:
                logger.error(f"WebSocket Error: {e}. Retrying in 5 seconds...")
                time.sleep(5)
            else:
                logger.error("WebSocket Error: Max retries reached. Giving up.")

def websocket_sink(message):
    if ws is not None:
        ws.send(json.dumps({"message": str(message)}))

if __name__ == "__main__":
    start_websocket()
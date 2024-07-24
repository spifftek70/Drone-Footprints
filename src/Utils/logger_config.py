from quart import Quart
import asyncio
import json
from loguru import logger
import websockets
from pathlib import Path
from datetime import datetime
import sys
from tqdm import tqdm
from collections import deque
import hashlib

app = Quart(__name__)
handlers_added = False
log_cache = deque(maxlen=150)  # Adjust maxlen to your needs


class WebSocketHandler:
    def __init__(self, port):
        self.active_websockets = set()
        self.port = port

    async def handler(self, websocket, path):
        self.active_websockets.add(websocket)
        try:
            while True:
                await asyncio.sleep(10)
        finally:
            self.active_websockets.remove(websocket)

    async def send(self, message):
        tasks = [ws.send(message) for ws in self.active_websockets if ws.open]
        await asyncio.gather(*tasks)

log_websocket_handler = WebSocketHandler(6060)

async def start_websocket_server(handler, port):
    await websockets.serve(handler.handler, '0.0.0.0', port)

@app.before_serving
async def startup():
    global handlers_added
    if not handlers_added:
        logger.add(sys.stdout, format="{time} | {level} | {message}", level="INFO")
        logger.add(websocket_log_formatter, format="{time} | {level} | {message}", level="INFO", filter=lambda record: "tqdm" not in record["message"])
        handlers_added = True
    await start_websocket_server(log_websocket_handler, 6060)

def websocket_log_formatter(message):
    if "tqdm" not in message.record["message"]:
        record = message.record
        log_dict = {
            "time": record["time"].strftime("%Y-%m-%d %H:%M:%S"),
            "level": record["level"].name,
            "message": record["message"]
        }
        formatted_message = json.dumps(log_dict)
        asyncio.run_coroutine_threadsafe(log_websocket_handler.send(formatted_message), asyncio.get_event_loop())

def hash_message(message):
    return hashlib.md5(message.encode()).hexdigest()

def unique_log_filter(record):
    message_hash = hash_message(record["message"])
    if message_hash in log_cache:
        return False
    log_cache.append(message_hash)
    return True

def websocket_log_formatter(message):
    if "tqdm" not in message.record["message"] and unique_log_filter(message.record):
        record = message.record
        log_dict = {
            "time": record["time"].strftime("%Y-%m-%d %H:%M:%S"),
            "level": record["level"].name,
            "message": record["message"]
        }
        formatted_message = json.dumps(log_dict)
        asyncio.run_coroutine_threadsafe(log_websocket_handler.send(formatted_message), asyncio.get_event_loop())


def init_logger(outer_path):
    log_path = Path(outer_path) / "logfiles" / f"log_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    file_handler_id = logger.add(log_path, format="{time} | {level} | {message}\n", level="INFO")  # File output  # File output
    return file_handler_id

def get_logger():
    logger.remove()  # Remove all previous handlers to prevent duplication
    logger.add(sys.stdout, format="{time} | {level} | {message}", level="INFO", filter=unique_log_filter)  # Console output
    logger.add(websocket_log_formatter, format="{time} | {level} | {message}", level="INFO", filter=lambda record: "tqdm" not in record["message"])
    return logger

class TqdmWebSocket(tqdm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.websocket_handler = log_websocket_handler

    def update(self, n=1):
        super().update(n)
        message = {
            "type": "progress",
            "current": self.n,
            "total": self.total,
            "description": self.desc
        }
        try:
            asyncio.run_coroutine_threadsafe(self.websocket_handler.send(json.dumps(message)), asyncio.get_event_loop())
            logger.info(f"Sent WebSocket progress update: {message}")
        except Exception as e:
            logger.error(f"Failed to send WebSocket progress update: {e}")

    def close(self):
        super().close()
        message = {
            "type": "progress",
            "status": "completed"
        }
        try:
            asyncio.run_coroutine_threadsafe(self.websocket_handler.send(json.dumps(message)), asyncio.get_event_loop())
            logger.info(f"Sent WebSocket progress completion message.")
        except Exception as e:
            logger.error(f"Failed to send WebSocket progress completion message: {e}")

def end_logger(file_handler_id):
    logger.remove(file_handler_id)
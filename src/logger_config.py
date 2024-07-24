from quart import Quart
import asyncio
import json
from loguru import logger
import websockets
from pathlib import Path
from datetime import datetime  # Correct this import to access datetime.now()
import sys
from tqdm import tqdm

app = Quart(__name__)

class WebSocketHandler:
    def __init__(self, port):
        self.active_websockets = set()
        self.port = port

    async def handler(self, websocket, path):
        self.active_websockets.add(websocket)
        try:
            while True:
                await asyncio.sleep(10)  # Keep the connection alive
        finally:
            self.active_websockets.remove(websocket)

    async def send(self, message):
        tasks = [ws.send(message) for ws in self.active_websockets if ws.open]
        await asyncio.gather(*tasks)

log_websocket_handler = WebSocketHandler(6060)
progress_websocket_handler = WebSocketHandler(6061)

async def start_websocket_server(handler, port):
    await websockets.serve(handler.handler, '0.0.0.0', port)

@app.before_serving
async def startup():
    await asyncio.gather(
        start_websocket_server(log_websocket_handler, 6060),
        start_websocket_server(progress_websocket_handler, 6061)
    )

async def send_log(message):
    await log_websocket_handler.send(message)

def websocket_log_formatter(message):
    if "tqdm" not in message.record["message"]:
        record = message.record
        log_dict = {
            "time": record["time"].strftime("%Y-%m-%d %H:%M:%S"),
            "level": record["level"].name,
            "message": record["message"]
        }
        formatted_message = json.dumps(log_dict)
        asyncio.run_coroutine_threadsafe(send_log(formatted_message), asyncio.get_event_loop())

def init_logger(outer_path):
    log_path = Path(outer_path) / "logfiles" / f"log_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.log"  # Correct usage here
    log_path.parent.mkdir(parents=True, exist_ok=True)
    logger.remove()
    bob = get_logger()
    logger.add(log_path, format="{time} | {level} | {message}", level="INFO")  # File output
    return bob


def get_logger():
    logger.remove() 
    logger.add(sys.stdout, format="{time} | {level} | {message}", level="INFO")  # Console output
    logger.add(websocket_log_formatter, format="{time} | {level} | {message}", level="INFO", filter=lambda record: "tqdm" not in record["message"])
    return logger


class TqdmWebSocket(tqdm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.websocket_handler = progress_websocket_handler

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

def end_logger():
    logger.remove()

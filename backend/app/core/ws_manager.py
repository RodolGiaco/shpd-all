# app/core/ws_manager.py
from typing import Dict
from starlette.websockets import WebSocket

class WSManager:
    def __init__(self):
        self.inputs: Dict[str, WebSocket] = {}

ws_manager = WSManager()

import websockets
import json
import asyncio
from typing import Optional, Dict, Any

class NetworkClient:
    def __init__(self, page):
        self.page = page
        self.ws: Optional[websockets.client.WebSocketClientProtocol] = None
        self.name = ""
        self.role: Optional[str] = None
        self.players: Dict[str, Any] = {}
        self.game_ui = None
        self.night_data: Dict[str, Any] = {}
        self.is_alive = True

    async def connect(self, name: str) -> bool:
        try:
            self.name = name
            self.ws = await websockets.connect("ws://localhost:8000/ws")
            await self.ws.send(json.dumps({"type": "join", "name": name}))
            asyncio.create_task(self.listen())
            return True
        except Exception as e:
            print(f"Connection error: {e}")
            return False

    async def listen(self):
        try:
            async for message in self.ws:
                data = json.loads(message)
                await self.handle_message(data)
        except websockets.exceptions.ConnectionClosed:
            await self.handle_disconnect()

    async def send(self, data: dict):
        await self.ws.send(json.dumps(data))
        print("Действие отправлено")

    async def handle_message(self, data: dict):
        message_type = data["type"]
        print(f"Получено сообщение типа: {message_type}")
        if message_type == "show_roles":
            if self.game_ui:
                self.game_ui.show_role_view(self.role, data.get("players", []), data["duration"])
        elif message_type == "role":
            await self.handle_role_assignment(data)
        elif message_type=="night_result":
            self.night_data=data
            if data.get("killed") == self.name and data.get("killed") != data.get("protected"):
                self.is_alive = False
        elif message_type == "day_result":
            if data.get("executed") == self.name:
                self.is_alive = False
            self.game_ui.show_day_result(data)
        elif message_type == "phase":
            print(data["phase"])
            await self.handle_phase_change(data)
        elif message_type == "players_update":
            await self.handle_players_update(data)
        elif message_type == "game_over":
            await self.handle_game_over(data)
        elif message_type == "error":
            await self.handle_error(data)
        elif message_type == "game_starting":
            if self.game_ui:
                print(f"Игра начнется через {data['seconds']} секунд")
                self.game_ui.show_countdown(data["seconds"], data["players"])
        elif message_type == "game_cancelled":
            if self.game_ui:
                print("Игра отменена: недостаточно игроков")
        elif message_type == "chat_message":
            if self.game_ui:
                self.game_ui.add_chat_message(data["sender"], data["message"])

    async def handle_role_assignment(self, data: dict):
        self.role = data["role"]

    async def handle_phase_change(self, data: dict):
        phase = data["phase"]
        players=data.get("players", [])
        for player in players:
            print(player)
        if self.game_ui:
            if phase == "night":
                if self.is_alive:
                    self.game_ui.show_night_phase(
                        self.role,
                        data.get("players", [])
                    )
                else: self.game_ui.not_alive_night_phase(self.role)
            elif phase == "day":
                if self.is_alive:
                    self.game_ui.show_day_phase(
                        data.get("players", []),
                        self.night_data
                    )
                else: self.game_ui.not_alive_day_phase(data.get("players", []), self.night_data)

    async def handle_players_update(self, data: dict):
        self.players = data["players"]
        players = data.get("players", [])
        for player in players:
            print(player)
        if self.game_ui:
            self.game_ui.update_players_list(self.players)

    async def handle_game_over(self, data: dict):
        self.is_alive = True
        self.role = None
        self.players = {}
        if self.game_ui:
            self.game_ui.show_game_over(data["winner"], data["roles"])
        await self.close_ws()

    async def handle_error(self, data: dict):
        error_msg = data["message"]
        if self.game_ui:
            self.game_ui.show_error(error_msg)

    async def handle_disconnect(self):
        if self.game_ui:
            self.game_ui.show_connection_error()
        await self.close_ws()

    async def close_ws(self):
        if self.ws and not self.ws.closed:
            await self.ws.close()
        self.ws = None
        self.name = ""

    def set_game_ui(self, game_ui):
        self.game_ui = game_ui



from typing import Dict, List, Optional
from player import Player, Role
from fastapi import WebSocket
import random
import json
import asyncio

class Game:
    def __init__(self):
        self.players: Dict[str, Player] = {}
        self.connections: Dict[str, WebSocket] = {}
        self.game_started = False
        self.phase = "lobby"
        self.day_number = 1
        self.night_actions: Dict[Role, str] = {}
        self.votes: Dict[str, str] = {}
        self.min_players = 5
        self.start_task = None
        self.lock = asyncio.Lock()

    async def handle_connection(self, websocket: WebSocket, player_name: str):
        if player_name in self.players:
            await websocket.close(code=4001, reason="Name already exists")
            return
        self.connections[player_name] = websocket
        self.players[player_name] = Player(name=player_name)
        await self.broadcast({
            "type": "players_update",
            "players": [p.name for p in self.players.values()]
        })
        print(f"Новый игрок: {player_name}, Всего игроков: {len(self.players)}")
        async with self.lock:
            if (
                len(self.players) >= self.min_players
                and not self.game_started
                and (not self.start_task or self.start_task.done())
            ):
                self.start_task = asyncio.create_task(self.start_game())
                print("Игра скоро начнется")
        try:
            while True:
                data = await websocket.receive_json()
                await self.handle_message(player_name, data)
        except Exception as e:
            print(f"Error with {player_name}: {e}")
        finally:
            await self.handle_disconnect(player_name)

    async def handle_message(self, player_name: str, data: dict):
        if data["type"] == "night_action":
            print(f"Получено сообщение {data["type"]}")
            print(data["role"])
            print(data["target"])
            await self.handle_night_action(player_name, data)
        elif data["type"] == "vote":
            print(f"Получено сообщение {data["type"]}")
            await self.handle_vote(player_name, data)
        elif data["type"] == "chat":
            await self.broadcast({
                "type": "chat_message",
                "sender": player_name,
                "message": data["message"],
                "timestamp": asyncio.get_event_loop().time()
            })

    async def handle_disconnect(self, player_name: str):
        print(f"Игрок {player_name} отключился")
        was_alive = False
        if player_name in self.players:
            was_alive = self.players[player_name].is_alive
            del self.players[player_name]
        if player_name in self.connections:
            try:
                await self.connections[player_name].close()
            except Exception as e:
                print(f"Ошибка при закрытии соединения: {e}")
            finally:
                del self.connections[player_name]

        if self.game_started:
            if was_alive:
                alive_players = [p.name for p in self.players.values() if p.is_alive]
                await self.broadcast({
                    "type": "players_update",
                    "players": alive_players
                })
                current_alive = len([p for p in self.players.values() if p.is_alive])
                if current_alive < self.min_players:
                    await self.end_game("game_cancelled")
        else:

            await self.broadcast({
                "type": "players_update",
                "players": [p.name for p in self.players.values()]
            })

    async def start_game(self):
        try:
            async with self.lock:
                if self.game_started:
                    return
                self.game_started = True
                initial_players = list(self.players.keys())

                for i in range(5, 0, -1):
                    await self.broadcast({
                        "type": "game_starting",
                        "seconds": i,
                        "players": initial_players
                    })
                    await asyncio.sleep(1)

                    current_players = list(self.players.keys())
                    if (len(current_players) < self.min_players
                            or set(current_players) != set(initial_players)):
                        await self.broadcast({"type": "game_cancelled"})
                        print("[Сервер] Игра отменена")
                        return

                # Назначение ролей
                roles = [Role.MAFIA, Role.DOCTOR] + [Role.VILLAGER] * (len(initial_players) - 2)
                random.shuffle(roles)

                for player in self.players.values():
                    player.role = roles.pop()
                    await self.send_to_player(player.name, {
                        "type": "role",
                        "role": player.role.value,
                        "players": initial_players
                    })

                # Новая задержка для показа ролей
                for i in range(5, 0, -1):
                    await self.broadcast({"type": "show_roles", "duration": i})
                    await asyncio.sleep(1)
                #await asyncio.sleep(5)

                # Проверка подключения после показа ролей
                current_players = list(self.players.keys())
                if (len(current_players) < self.min_players
                        or set(current_players) != set(initial_players)):
                    await self.broadcast({"type": "game_cancelled"})
                    print("[Сервер] Игра отменена после показа ролей")
                    return

                # Запуск основного цикла
                await self.game_loop()

        except Exception as e:
            print(f"[Сервер] Ошибка: {str(e)}")
            await self.broadcast({"type": "game_cancelled"})
        finally:
            self.start_task = None

    async def game_loop(self):
        while self.game_started:
            self.phase = "night"
            await self.night_phase()
            await asyncio.sleep(1)
            await self.check_win_conditions()
            if not self.game_started:
                break

            self.phase = "day"
            await self.day_phase()
            await self.check_win_conditions()
            self.day_number += 1
            await asyncio.sleep(2)

    async def night_phase(self):
        await self.broadcast({
            "type": "phase",
            "phase": "night",
            "players": [p.name for p in self.players.values() if p.is_alive]
        })
        await asyncio.sleep(2)
        self.night_actions.clear()
        mafia_players = [p for p in self.players.values() if p.role == Role.MAFIA]
        doctor_players = [p for p in self.players.values() if p.role == Role.DOCTOR]
        tasks = []
        for player in mafia_players + doctor_players:
            tasks.append(
                self.wait_for_night_action(player.name, player.role)
            )
        await asyncio.gather(*tasks)
        await self.process_night_actions()

    async def wait_for_night_action(self, player_name: str, role: Role):
        try:
            await self.send_to_player(player_name, {
                "type": "request_night_action",
                "role": role.value,
                "players": [p.name for p in self.players.values() if p.is_alive]
            })
            await asyncio.wait_for(
                self.night_action_received(role),
                timeout=60
            )
        except asyncio.TimeoutError:
            print(f"Таймаут ночного действия для {role}")

    async def night_action_received(self, role: Role):
        while role not in self.night_actions:
            await asyncio.sleep(1)

    async def handle_night_action(self, player_name: str, data: dict):
        role = self.players[player_name].role
        self.night_actions[role] = data["target"]
        #await self.check_night_actions_complete()

    async def check_night_actions_complete(self):
        pass

    async def process_night_actions(self):
        print("Обработка ночных действий")
        kill_target = self.night_actions.get(Role.MAFIA)
        protection_target = self.night_actions.get(Role.DOCTOR)
        if kill_target and kill_target in self.players:
            victim = self.players[kill_target]
            if kill_target != protection_target:
                victim.is_alive = False
            role_info = victim.role.value
        else:
            role_info = None
            kill_target = None

        result_message = {
            "type": "night_result",
            "killed": kill_target,
            "protected": protection_target,
            "role": role_info
        }
        await self.broadcast(result_message)
        print(f"Отправлены результаты ночи: {result_message}")
        await asyncio.sleep(3)

    async def day_phase(self):
        await self.broadcast({
            "type": "phase",
            "phase": "day",
            "players": [p.name for p in self.players.values() if p.is_alive]
        })

        for i in range(3, 0, -1):
            await self.broadcast({"type": "day_countdown", "message": f"Рассвет через {i}..."})
            await asyncio.sleep(1)

        self.votes.clear()
        alive_players = [p.name for p in self.players.values() if p.is_alive]
        await self.broadcast({"type": "start_voting", "candidates": alive_players})
        try:
            await asyncio.wait_for(
                self.wait_for_votes_completion(alive_players),
                timeout=60
            )
        except asyncio.TimeoutError:
            print("Таймаут голосования")

        await self.process_votes()

    async def wait_for_votes_completion(self, alive_players):
        while True:
            current_alive = [p.name for p in self.players.values() if p.is_alive]
            valid_voters = [v for v in self.votes if v in current_alive]
            if len(valid_voters) >= len(current_alive):
                break
            await asyncio.sleep(1)

    async def collect_votes(self):
        alive_players = [p.name for p in self.players.values() if p.is_alive]
        await self.broadcast({
            "type": "start_voting",
            "candidates": alive_players
        })
        while len(self.votes) < len(alive_players):
            await asyncio.sleep(1)

    async def handle_vote(self, player_name: str, data: dict):
        if not self.game_started or self.phase != "day":
            return
        voter = player_name
        target = data.get("target")
        if (voter not in self.players or
                not self.players[voter].is_alive or
                target not in self.players or
                not self.players[target].is_alive):
            return

        self.votes[voter] = target
        await self.send_to_player(voter, {
            "type": "vote_accepted",
            "target": target
        })
        print(f"Голос получен от {voter} за {target}")

    async def process_votes(self):
        valid_votes = {
            voter: target
            for voter, target in self.votes.items()
            if voter in self.players and self.players[voter].is_alive
        }

        if not valid_votes:
            await self.broadcast({
                "type": "day_result",
                "executed": None,
                "message": "Никто не проголосовал"
            })
            return

        vote_counts = {}
        for target in valid_votes.values():
            if target in vote_counts:
                vote_counts[target] += 1
            else:
                vote_counts[target] = 1

        max_votes = max(vote_counts.values(), default=0)
        candidates = [k for k, v in vote_counts.items() if v == max_votes]

        if len(candidates) == 1:
            executed = candidates[0]
            self.players[executed].is_alive = False
            await self.broadcast({
                "type": "day_result",
                "executed": executed,
                "message": f"{executed} ({self.players[executed].role}) был казнен"
            })
        else:
            await self.broadcast({
                "type": "day_result",
                "executed": None,
                "message": "Ничья, никто не казнен"
            })
        await asyncio.sleep(3)

    async def check_win_conditions(self):
        alive_players = [p for p in self.players.values() if p.is_alive]
        mafia_count = sum(1 for p in alive_players if p.role == Role.MAFIA)
        villagers_count = sum(1 for p in alive_players if p.role != Role.MAFIA)

        if mafia_count == 0:
            await self.end_game("villagers")
        elif mafia_count >= villagers_count:
            await self.end_game("mafia")

    async def end_game(self, winner: str):
        self.game_started = False
        roles = {p.name: p.role.value for p in self.players.values()}
        await self.broadcast({
            "type": "game_over",
            "winner": winner,
            "roles": roles
        })
        self.players.clear()
        self.connections.clear()

    async def send_to_player(self, player_name: str, message: dict):
        ws = self.connections.get(player_name)
        if ws:
            await ws.send_json(message)

    async def broadcast(self, message: dict):
        for ws in self.connections.values():
            try:
                print(f"Отправка {message['type']}")
                await ws.send_json(message)
            except:
                pass

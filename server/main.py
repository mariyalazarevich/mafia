# server/main.py
from fastapi import FastAPI
from fastapi.websockets import WebSocket
from fastapi.middleware.cors import CORSMiddleware
from game import Game
import uvicorn

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

game = Game()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        data = await websocket.receive_json()
        player_name = data.get("name")
        if not player_name:
            await websocket.close(code=1008, reason="Name required")
            return
        await game.handle_connection(websocket, player_name)
    except Exception as e:
        print(f"Connection error: {e}")
        await websocket.close()


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
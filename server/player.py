from enum import Enum
from typing import Optional

class Role(Enum):
    MAFIA = "mafia"
    DOCTOR = "doctor"
    VILLAGER = "villager"

class Player:
    def __init__(self, name: str):
        self.name = name
        self.role: Optional[Role] = None
        self.is_alive = True
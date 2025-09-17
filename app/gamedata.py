import copy
import json
import os
import random
from dataclasses import dataclass
from typing import ClassVar

class GameInformation:
    pass

class GameStatistics:
    pass

@dataclass
class GameData:

    id: ClassVar[str] = None
    name: ClassVar[str] = None
    number: ClassVar[str] = None
    turn: ClassVar[int] = None
    status: ClassVar[int] = None
    
    current_event: ClassVar[dict] = None
    active_events: ClassVar[dict] = None
    inactive_events: ClassVar[list] = None
    
    info: ClassVar[GameInformation] = None
    stats: ClassVar[GameStatistics] = None
    
    @classmethod
    def load(cls, game_id: str) -> None:

        cls.id = game_id

        with open("active_games.json", 'r') as json_file:
            active_games_dict = json.load(json_file)

        cls._data = active_games_dict.get(cls.id)
        if cls._data is None:
            raise RuntimeError(f"Error: Game data not found for {cls.id} when attempting to initiate GameData class.")
        
        cls.name = cls._data["name"]
        cls.number = cls._data["number"]
        cls.turn = cls._data["turn"]
        cls.status = cls._data["status"]
        cls.current_event = cls._data["currentEvent"]
        cls.active_events = cls._data["activeEvents"]
        cls.inactive_events = cls._data["inactiveEvents"]
        cls.info = GameInformation(cls._data["information"])
        cls.stats = GameStatistics(cls._data["statistics"])

    @classmethod
    def save(cls) -> None:

        if cls._data is None:
            raise RuntimeError("Error: GameData has not been loaded.")
        
        with open("active_games.json", 'r') as json_file:
            active_games_dict = json.load(json_file)
        
        active_games_dict[cls.id] = cls._data
        with open('active_games.json', 'w') as json_file:
            json.dump(active_games_dict, json_file, indent=4)
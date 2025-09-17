import copy
import json
import os
import random
from dataclasses import dataclass
from typing import ClassVar

@dataclass
class Games:

    _data: ClassVar[dict[str, dict]] = None
    
    @classmethod
    def load(cls) -> None:

        with open("active_games.json", 'r') as json_file:
            cls._data = json.load(json_file)

    @classmethod
    def save(cls) -> None:

        if cls._data is None:
            raise RuntimeError("Error: Games dataclass has not been loaded.")
        
        with open("active_games.json", 'w') as json_file:
            json.dump(cls._data, json_file, indent=4)

class GameData:
    
    def __init__(self, game_id: str):

        self._data = Games._data[game_id]
        
        self.id = game_id
        self.name = self._data["name"]
        self.number = self._data["number"]
        self.turn = self._data["turn"]
        self.status = self._data["status"]

        self.current_event = self._data["currentEvent"]
        self.active_events = self._data["activeEvents"]
        self.inactive_events = self._data["inactiveEvents"]

        self.info = GameInformation(self._data["information"])
        self.stats = GameStatistics(self._data["statistics"])

    # need to add getters and setters

class GameInformation:
    pass

class GameStatistics:
    pass
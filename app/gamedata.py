import copy
import json
import os
import random
from datetime import datetime
from enum import Enum, IntEnum
from dataclasses import dataclass
from typing import ClassVar

class GamesMeta(type):

    def __len__(cls):
        return len(cls._data)

@dataclass
class Games(metaclass=GamesMeta):

    _data: ClassVar[dict[str, dict]]
    with open("active_games.json", "r") as json_file:
        _data = json.load(json_file)

    @classmethod
    def save(cls) -> None:
        with open("active_games.json", 'w') as json_file:
            json.dump(cls._data, json_file, indent=4)

    @classmethod
    def create(cls, game_id: str, form_data_dict: dict) -> "GameData":

        GAME_VERSION = "Development"
        current_date = datetime.today().date()

        with open("game_records.json", 'r') as json_file:
            game_records_dict = json.load(json_file)
        
        game_data = {
            "name": form_data_dict["Game Name"],
            "number": len(game_records_dict) + len(cls) + 1,
            "turn": 0,
            "status": 100,
            "information": {
                "version": GAME_VERSION,
                "scenario": form_data_dict["Scenario"],
                "map": form_data_dict["Map"],
                "playerCount": form_data_dict["Player Count"],
                "victoryConditions": form_data_dict["Victory Conditions"],
                "fogOfWar": form_data_dict["Fog of War"],
                "turnLength": form_data_dict["Turn Length"],
                "acceleratedSchedule": form_data_dict["Accelerated Schedule"],
                "weekendDeadlines": form_data_dict["Deadlines on Weekends"]
            },
            "statistics": {
                "regionDisputes": 0,
                "daysEllapsed": 0,
                "gameStarted": current_date.strftime("%m/%d/%Y")
            },
            "inactiveEvents": [],
            "activeEvents": {},
            "currentEvent": {}
        }

        cls._data[game_id] = game_data

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

class GameStatus(IntEnum):
    REGION_SELECTION = 100
    NATION_SETUP = 101
    ACTIVE = 200
    ACTIVE_PENDING_EVENT = 201
    FINISHED = 300

    def is_setup(self) -> bool:
        return 100 <= self.value < 200

    def is_active(self) -> bool:
        return 200 <= self.value < 300

    def is_finished(self) -> bool:
        return self is GameStatus.FINISHED
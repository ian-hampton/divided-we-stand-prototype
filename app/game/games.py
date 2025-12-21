import json
from datetime import datetime
from dataclasses import dataclass
from typing import ClassVar, Iterator

from .game import Game

class GamesMeta(type):

    def __iter__(cls) -> Iterator[Game]:
        for game_id in cls._data:
            yield Game(game_id, cls._data[game_id])

    def __len__(cls):
        return len(cls._data)

@dataclass
class Games(metaclass=GamesMeta):

    _data: ClassVar[dict[str, dict]]
    _instances: ClassVar[dict[str, Game]] = {}
    with open("active_games.json", "r") as json_file:
        _data = json.load(json_file)

    @classmethod
    def save(cls) -> None:
        with open("active_games.json", 'w') as json_file:
            json.dump(cls._data, json_file, indent=4)

    @classmethod
    def create(cls, game_id: str, form_data_dict: dict) -> None:

        GAME_VERSION = "Development"
        current_date = datetime.today().date()

        with open("game_records.json", 'r') as json_file:
            game_records_dict = json.load(json_file)
        
        game_data = {
            "name": form_data_dict["Game Name"],
            "number": len(game_records_dict) + len(cls) + 1,
            "turn": 0,
            "status": 101,
            "information": {
                "version": GAME_VERSION,
                "scenario": form_data_dict["Scenario"],
                "map": form_data_dict["Map"],
                "playerCount": form_data_dict["Player Count"],
                "victoryConditions": form_data_dict["Victory Conditions"],
                "turnLength": form_data_dict["Turn Length"],
                "fogOfWar": form_data_dict["Fog of War"],
                "acceleratedSchedule":form_data_dict["Accelerated Schedule"],
                "weekendDeadlines": form_data_dict["Deadlines on Weekends"]
            },
            "statistics": {
                "regionDisputes": 0,
                "daysElapsed": 0,
                "gameStarted": current_date.strftime("%m/%d/%Y")
            },
            "inactiveEvents": [],
            "activeEvents": {},
            "currentEvent": {}
        }

        cls._data[game_id] = game_data

    @classmethod
    def delete(cls, game_id: str) -> None:
        if game_id in cls._data:
            del cls._data[game_id]

    @classmethod
    def load(cls, game_id: str) -> Game:
        
        # trying to load a game that does not exist is a critical error
        if game_id not in cls._data:
            raise Exception(f"Error loading Game. {game_id} not recognized as a valid Game ID.")
        
        # reuse cached Game object if it exists
        if game_id not in cls._instances:
            cls._instances[game_id] = Game(game_id, cls._data[game_id])
        return cls._instances[game_id]
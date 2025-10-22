import json
import os
from dataclasses import dataclass
from typing import ClassVar, Iterator

class NotificationsMeta(type):

    def __iter__(cls) -> Iterator[tuple[int, str]]:
        for notification in cls._data:
            yield notification

@dataclass
class Notifications(metaclass=NotificationsMeta):

    game_id: ClassVar[str] = None
    _data: ClassVar[list[tuple]] = None

    @classmethod
    def initialize(cls, game_id: str) -> None:
        cls.game_id = game_id
        cls._data = []

    @classmethod
    def load(cls, game_id: str) -> None:
        
        cls.game_id = game_id
        gamedata_filepath = f"gamedata/{cls.game_id}/gamedata.json"
        if not os.path.exists(gamedata_filepath):
            raise FileNotFoundError(f"Error: Unable to locate required game files for Notifications class.")
        
        with open(gamedata_filepath, 'r') as f:
            gamedata_dict = json.load(f)

        cls._data = gamedata_dict["notifications"]
    
    @classmethod
    def save(cls) -> None:
        
        if cls._data is None:
            raise RuntimeError("Error: Notifications has not been loaded.")
        
        gamedata_filepath = f'gamedata/{cls.game_id}/gamedata.json'
        with open(gamedata_filepath, 'r') as json_file:
            gamedata_dict = json.load(json_file)

        gamedata_dict["notifications"] = cls._data
        with open(gamedata_filepath, 'w') as json_file:
            json.dump(gamedata_dict, json_file, indent=4)
    
    @classmethod
    def add(cls, string: str, priority: int) -> None:
        cls._data.append((priority, string))
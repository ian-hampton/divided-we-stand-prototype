import json
import os
from dataclasses import dataclass
from typing import ClassVar, Iterator, Tuple

from app.gamedata import Games

class TrucesMeta(type):

    def __iter__(cls) -> Iterator["Truce"]:
        for truce_id in cls._data:
            yield Truce(truce_id)

    def __len__(cls):
        return len(cls._data)

@dataclass
class Truces(metaclass=TrucesMeta):

    game_id: ClassVar[str] = None
    _data: ClassVar[dict[str, dict]] = None

    @classmethod
    def load(cls, game_id: str) -> None:
        
        cls.game_id = game_id
        gamedata_filepath = f"gamedata/{cls.game_id}/gamedata.json"
        if not os.path.exists(gamedata_filepath):
            raise FileNotFoundError(f"Error: Unable to locate required game files for Truces class.")
        
        with open(gamedata_filepath, 'r') as f:
            gamedata_dict = json.load(f)

        cls._data = gamedata_dict["truces"]

    @classmethod
    def save(cls) -> None:
        
        if cls._data is None:
            raise RuntimeError("Error: Truces has not been loaded.")
        
        gamedata_filepath = f"gamedata/{cls.game_id}/gamedata.json"
        with open(gamedata_filepath, 'r') as json_file:
            gamedata_dict = json.load(json_file)

        gamedata_dict["truces"] = cls._data
        with open(gamedata_filepath, 'w') as json_file:
            json.dump(gamedata_dict, json_file, indent=4)

    @classmethod
    def create(cls, signatories: list[str], truce_length: int) -> None:

        game = Games.load(cls.game_id)
        truce_id = len(Truces) + 1

        new_truce_data = {
            "startTurn": game.turn,
            "endTurn": game.turn + truce_length + 1,
            "signatories": {nation_id: True for nation_id in signatories}
        }

        cls._data[truce_id] = new_truce_data

    @classmethod
    def are_truced(cls, nation1_id: str, nation2_id: str) -> bool:
        for truce in cls:
            if (truce.is_active
                and nation1_id in truce.signatories
                and nation2_id in truce.signatories):
                return True
        return False

class Truce:

    def __init__(self, truce_id: str):
        self._data = Truces._data[truce_id]
        self.id = truce_id
        self.start_turn: int = self._data["startTurn"]

    @property
    def end_turn(self) -> int:
        return self._data["endTurn"]
    
    @end_turn.setter
    def end_turn(self, turn: int) -> None:
        self._data["endTurn"] = turn

    @property
    def signatories(self) -> dict[str, bool]:
        return self._data["signatories"]
    
    @signatories.setter
    def signatories(self, value: dict) -> None:
        self._data["signatories"] = value

    @property
    def is_active(self) -> bool:
        game = Games.load(Truces.game_id)
        return True if self.end_turn > game.turn else False

    def __str__(self):
        signatories_list = list(self.signatories.keys())
        return " - ".join(signatories_list)
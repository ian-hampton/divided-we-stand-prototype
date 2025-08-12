import json
import os
from dataclasses import dataclass
from typing import ClassVar, Iterator, Tuple

from app import core

class AlliancesMeta(type):

    def __iter__(cls) -> Iterator["Alliance"]:
        for alliance_name in cls._data:
            yield Alliance(alliance_name)

    def __len__(cls):
        return len(cls._data) if cls._data else 0

@dataclass
class Alliances(metaclass=AlliancesMeta):
    
    game_id: ClassVar[str] = None
    _data: ClassVar[dict[str, dict]] = None

    @classmethod
    def load(cls, game_id: str) -> None:
        
        cls.game_id = game_id
        gamedata_filepath = f"gamedata/{cls.game_id}/gamedata.json"
        
        if not os.path.exists(gamedata_filepath):
            raise FileNotFoundError(f"Error: Unable to locate required game files for Alliances class.")
        
        with open(gamedata_filepath, 'r') as f:
            cls._data = json.load(f)

    @classmethod
    def save(cls) -> None:
        
        if cls._data is None:
            raise RuntimeError("Error: Alliances has not been loaded.")
        
        gamedata_filepath = f"gamedata/{cls.game_id}/gamedata.json"
        with open(gamedata_filepath, 'r') as json_file:
            gamedata_dict = json.load(json_file)

        gamedata_dict["alliances"] = cls._data
        with open(gamedata_filepath, 'w') as json_file:
            json.dump(gamedata_dict, json_file, indent=4)

    @classmethod
    def create(cls, alliance_name: str, alliance_type: str, founding_members: list[str]) -> None:

        current_turn_num = core.get_current_turn_num(cls.game_id)

        new_alliance_data = {
            "allianceType": alliance_type,
            "turnCreated": current_turn_num,
            "turnEnded": 0,
            "currentMembers": {},
            "foundingMembers": {},
            "formerMembers": {}
        }

        for nation_name in founding_members:
            new_alliance_data["currentMembers"][nation_name] = current_turn_num
            new_alliance_data["foundingMembers"][nation_name] = current_turn_num

        cls._data[alliance_name] = new_alliance_data
    
    @classmethod
    def get(cls, alliance_name: str) -> "Alliance":
        if alliance_name in cls._data:
            return Alliance(alliance_name)
        return None
    
    @classmethod
    def are_allied(cls, nation_name_1: str, nation_name_2: str) -> bool:
        pass

    @classmethod
    def former_ally_truce(cls, nation_name_1: str, nation_name_2: str) -> bool:
        pass

    @classmethod
    def allies(cls, nation_name: str, type_to_search = "ALL") -> list:
        pass

    @classmethod
    def longest_alliance(cls) -> Tuple[str, int]:
        pass

class Alliance:
    
    def __init__(self, alliance_name: str):

        self._data = Alliances._data[alliance_name]

        self.name = alliance_name
        self._type: str = self._data["allianceType"]
        self._turn_created: int = self._data["turnCreated"]
        self._turn_ended: int = self._data["turnEnded"]
        self._current_members: dict = self._data["currentMembers"]
        self._founding_members: dict = self._data["foundingMembers"]
        self._former_members: dict = self._data["formerMembers"]

        if self._turn_ended == 0:
            self.is_active: bool = True
            self.age: int = core.get_current_turn_num(Alliances.game_id) - self._turn_created
        else:
            self.is_active: bool = False
            self.age: int = self._turn_ended - self._turn_created
    
    @property
    def type(self):
        return self._type

    @property
    def turn_created(self):
        return self._turn_created

    @property
    def turn_ended(self):
        return self._turn_ended

    @property
    def current_members(self):
        return self._current_members

    @property
    def founding_members(self):
        return self._founding_members

    @property
    def former_members(self):
        return self._former_members
    
    @type.setter
    def type(self, alliance_type: str):
        self._type = alliance_type
        self._data["allianceType"] = alliance_type
    
    @turn_created.setter
    def turn_created(self, turn: int):
        self._turn_created = turn
        self._data["turnCreated"] = turn

    @turn_ended.setter
    def turn_ended(self, turn: int):
        self._turn_ended = turn
        self._data["turnEnded"] = turn

    def add_member(self, nation_name: str) -> None:
        
        if nation_name in self.former_members:
            del self._former_members[nation_name]
            self._data["formerMembers"] = self._former_members
        
        self._current_members[nation_name] = core.get_current_turn_num(Alliances.game_id)
        self._data["currentMembers"] = self._current_members

    def remove_member(self, nation_name: str) -> None:
        
        del self._current_members[nation_name]
        self._data["currentMembers"] = self._current_members

        self._former_members[nation_name] = core.get_current_turn_num(Alliances.game_id)
        self._data["formerMembers"] = self._former_members

    def calculate_yield(self) -> Tuple[float, str | None]:
        pass

    def end(self) -> None:
        pass
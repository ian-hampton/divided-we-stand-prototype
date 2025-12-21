import json
import os
from dataclasses import dataclass
from typing import ClassVar, Iterator, Tuple

from app.gamedata import Games
from .alliance import Alliance

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
            gamedata_dict = json.load(f)

        cls._data = gamedata_dict["alliances"]

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
        
        game = Games.load(cls.game_id)

        new_alliance_data = {
            "allianceType": alliance_type,
            "turnCreated": game.turn,
            "turnEnded": 0,
            "currentMembers": {},
            "foundingMembers": {},
            "formerMembers": {}
        }

        for nation_name in founding_members:
            new_alliance_data["currentMembers"][nation_name] = game.turn
            new_alliance_data["foundingMembers"][nation_name] = game.turn

        cls._data[alliance_name] = new_alliance_data
    
    @classmethod
    def get(cls, alliance_name: str) -> "Alliance":
        if alliance_name in cls._data:
            return Alliance(alliance_name, cls._data[alliance_name], cls.game_id)
        return None
    
    @classmethod
    def are_allied(cls, nation_name_1: str, nation_name_2: str) -> bool:
        for alliance in cls:
            if (alliance.is_active
                and nation_name_1 in alliance.current_members
                and nation_name_2 in alliance.current_members):
                return True
        return False

    @classmethod
    def allies(cls, nation_name: str, type_to_search = "ALL") -> list:
        
        from app.nation import Nations

        allies_set = set()
        for alliance in cls:
            if alliance.is_active and nation_name in alliance.current_members:
                if type_to_search != "ALL" and type_to_search != alliance.type:
                    continue
                for alliance_member_name in alliance.current_members:
                    if alliance_member_name != nation_name:
                        allies_set.add(alliance_member_name)

        allies_list = []
        for nation_name in allies_set:
            nation = Nations.get(nation_name)
            allies_list.append(nation.id)

        return allies_list

    @classmethod
    def longest_alliance(cls) -> Tuple[str, int]:
        
        longest_alliance_name = None
        longest_alliance_duration = -1

        for alliance in cls:
            if alliance.age > longest_alliance_duration:
                longest_alliance_name = alliance.name
                longest_alliance_duration = alliance.age

        return longest_alliance_name, longest_alliance_duration
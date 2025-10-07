import json
import os
from dataclasses import dataclass
from typing import ClassVar, Iterator, Tuple

from app.gamedata import Games

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
            return Alliance(alliance_name)
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
    def former_ally_truce(cls, nation_name_1: str, nation_name_2: str) -> bool:
        
        game = Games.load(cls.game_id)

        for alliance in cls:
            
            if nation_name_1 in alliance.former_members and nation_name_2 in alliance.current_members:
                if game.turn - alliance.former_members[nation_name_1] <= 2:
                    return True
                
            elif nation_name_2 in alliance.former_members and nation_name_1 in alliance.current_members:
                if game.turn - alliance.former_members[nation_name_2] <= 2:
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

class Alliance:
    
    def __init__(self, alliance_name: str):
        self._data = Alliances._data[alliance_name]
        self.name = alliance_name

    @property
    def type(self) -> str:
        return self._data["allianceType"]

    @type.setter
    def type(self, value: str) -> None:
        self._data["allianceType"] = value
    
    @property
    def turn_created(self) -> int:
        return self._data["turnCreated"]

    @turn_created.setter
    def turn_created(self, value: int) -> None:
        self._data["turnCreated"] = value

    @property
    def turn_ended(self) -> int:
        return self._data["turnEnded"]
    
    @turn_ended.setter
    def turn_ended(self, value: int) -> None:
        self._data["turnEnded"] = value
    
    @property
    def is_active(self) -> bool:
       return True if self.turn_ended == 0 else False

    @property
    def age(self) -> int:
        game = Games.load(Alliances.game_id)
        if self.turn_ended == 0:
           return game.turn - self.turn_created
        else:
           return self.turn_ended - self.turn_created

    @property
    def current_members(self) -> dict[str, int]:
        return self._data["currentMembers"]

    @current_members.setter
    def current_members(self, value: dict) -> None:
        self._data["currentMembers"] = value

    @property
    def founding_members(self) -> dict[str, int]:
        return self._data["foundingMembers"]
    
    @founding_members.setter
    def founding_members(self, value: dict) -> None:
        self._data["foundingMembers"] = value

    @property
    def former_members(self) -> dict[str, int]:
        return self._data["formerMembers"]

    @former_members.setter
    def former_members(self, value: dict) -> None:
        self._data["formerMembers"] = value

    def add_member(self, nation_name: str) -> None:
        game = Games.load(Alliances.game_id)
        if nation_name in self.former_members:
            del self.former_members[nation_name]
        self.current_members[nation_name] = game.turn

    def remove_member(self, nation_name: str) -> None:
        game = Games.load(Alliances.game_id)
        del self.current_members[nation_name]
        self.former_members[nation_name] = game.turn

    def calculate_yield(self) -> Tuple[float, str | None]:
        
        from app.scenario import ScenarioData as SD
        from app.nation import Nations

        if not self.is_active:
            return 0.0, None

        match self.type:
            
            case "Trade Agreement":
                
                total = 0.0
                for ally_name in self.current_members:
                    nation = Nations.get(ally_name)
                    total += nation.improvement_counts["Settlement"]
                    total += nation.improvement_counts["City"]
                    total += nation.improvement_counts["Central Bank"]
                    total += nation.improvement_counts["Capital"]
                
                return total * 0.5, "Dollars"

            case "Research Agreement":
                
                tech_set = set()
                for ally_name in self.current_members:
                    nation = Nations.get(ally_name)
                    ally_research_list = list(nation.completed_research.keys())
                    tech_set.update(ally_research_list)

                tech_set_filtered = set()
                for research_name in tech_set:
                    if research_name not in SD.agendas:
                        tech_set_filtered.add(research_name)

                return len(tech_set_filtered) * 0.2, "Research"

            case "Defense Pact":
                
                return len(self.current_members), "Military Capacity"

        return 0.0, None

    def end(self) -> None:
        
        from app.nation import Nations
        from app.truce import Truces
        game = Games.load(Alliances.game_id)

        # add truce periods
        for nation1_name in self.current_members:
            for nation2_name in self.current_members:
                
                if nation1_name == nation2_name:
                    continue

                nation1 = Nations.get(nation1_name)
                nation2 = Nations.get(nation2_name)
                
                signatories = [nation1.id, nation2.id]
                Truces.create(signatories, 2)

        # dissolve alliance
        names = list(self.current_members.keys())
        for nation_name in names:
            self.remove_member(nation_name)
        self.current_members = {}
        self.turn_ended = game.turn
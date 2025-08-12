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
        
        from app.nationdata import NationTable
        nation_table = NationTable(Alliances.game_id)
        agenda_data_dict = core.get_scenario_dict(Alliances.game_id, "Agendas")

        if not self.is_active:
            return 0.0, None

        match self.type:
            
            case "Trade Agreement":
                
                total = 0.0
                for ally_name in self.current_members:
                    nation = nation_table.get(ally_name)
                    total += nation.improvement_counts["Settlement"]
                    total += nation.improvement_counts["City"]
                    total += nation.improvement_counts["Central Bank"]
                    total += nation.improvement_counts["Capital"]
                
                return total * 0.5, "Dollars"

            case "Research Agreement":
                
                tech_set = set()
                for ally_name in self.current_members:
                    nation = nation_table.get(ally_name)
                    ally_research_list = list(nation.completed_research.keys())
                    tech_set.update(ally_research_list)

                tech_set_filtered = set()
                for research_name in tech_set:
                    if research_name not in agenda_data_dict:
                        tech_set_filtered.add(research_name)

                return len(tech_set_filtered) * 0.2, "Research"

            case "Defense Pact":
                
                return len(self.current_members), "Military Capacity"

        return 0.0, None

    def end(self) -> None:
        
        from app.nationdata import NationTable
        nation_table = NationTable(Alliances.game_id)
        current_turn_num = core.get_current_turn_num(Alliances.game_id)

        # add truce periods
        for nation1_name in self.current_members:
            for nation2_name in self.current_members:
                
                if nation1_name == nation2_name:
                    continue

                nation1 = nation_table.get(nation1_name)
                nation2 = nation_table.get(nation2_name)
                
                signatories_list = [False] * len(nation_table)
                signatories_list[int(nation1.id) - 1] = True
                signatories_list[int(nation2.id) - 1] = True
                core.add_truce_period(Alliances.game_id, signatories_list, 2)

        # dissolve alliance
        names = list(self.current_members.keys())
        for nation_name in names:
            self.remove_member(nation_name)
        self.current_members = {}
        self.turn_ended = current_turn_num
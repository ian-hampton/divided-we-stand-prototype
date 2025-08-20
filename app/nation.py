import json
import os
import random
from dataclasses import dataclass
from typing import ClassVar, Iterator, Tuple

from app import core

class NationsMeta(type):

    def __iter__(cls) -> Iterator["Nation"]:
        for nation_id in cls._data:
            if nation_id != "99":
                yield Nation(nation_id)

    def __len__(cls):
        length = len(cls._data)
        if "99" in cls._data:
            length -= 1
        return length

@dataclass
class Nations(metaclass=NationsMeta):

    game_id: ClassVar[str] = None
    _data: ClassVar[dict[str, dict]] = None

    @classmethod
    def load(cls, game_id: str) -> None:

        cls.game_id = game_id
        gamedata_filepath = f"gamedata/{cls.game_id}/gamedata.json"
        if not os.path.exists(gamedata_filepath):
            raise FileNotFoundError(f"Error: Unable to locate required game files for Nations class.")

        with open(gamedata_filepath, 'r') as f:
            gamedata_dict = json.load(f)

        cls._data = gamedata_dict["nations"]

    @classmethod
    def save(cls) -> None:

        if cls._data is None:
            raise RuntimeError("Error: Nations has not been loaded.")

        gamedata_filepath = f"gamedata/{cls.game_id}/gamedata.json"
        with open(gamedata_filepath, 'r') as json_file:
            gamedata_dict = json.load(json_file)

        gamedata_dict["nations"] = cls._data
        with open(gamedata_filepath, 'w') as json_file:
            json.dump(gamedata_dict, json_file, indent=4)

    @classmethod
    def names(cls) -> list:
        names = []
        for nation in cls:
            names.append(nation.name)
        return names

    @classmethod
    def create(cls, nation_id: str, player_id: int) -> None:

        improvement_dict = core.get_scenario_dict(cls.game_id, "Improvements")
        unit_dict = core.get_scenario_dict(cls.game_id, "Units")

        nation_data = {
            "nationName": "N/A",
            "playerID": player_id,
            "color": "#ffffff",
            "government": "N/A",
            "foreignPolicy": "N/A",
            "status": "Independent Nation",
            "tradeFee": "1:2",
            "standardMissileStockpile": 0,
            "nuclearMissileStockpile": 0,
            "score": 0,
            "chosenVictorySet": {},
            "victorySets": cls._generate_vc_sets(2),
            "satisfiedVictorySet": {},
            "resources": {
                "Dollars": {
                    "stored": "5.00",
                    "income": "0.00",
                    "grossIncome": "0.00",
                    "max": 100,
                    "rate": 100
                },
                "Political Power": {
                    "stored": "1.00",
                    "income": "0.00",
                    "grossIncome": "0.00",
                    "max": 50,
                    "rate": 100
                },
                "Research": {
                    "stored": "0.00",
                    "income": "0.00",
                    "grossIncome": "0.00",
                    "max": 50,
                    "rate": 100
                },
                "Food": {
                    "stored": "0.00",
                    "income": "0.00",
                    "grossIncome": "0.00",
                    "max": 50,
                    "rate": 100
                },
                "Coal": {
                    "stored": "0.00",
                    "income": "0.00",
                    "grossIncome": "0.00",
                    "max": 50,
                    "rate": 100
                },
                "Oil": {
                    "stored": "0.00",
                    "income": "0.00",
                    "grossIncome": "0.00",
                    "max": 50,
                    "rate": 100
                },
                "Basic Materials": {
                    "stored": "0.00",
                    "income": "0.00",
                    "grossIncome": "0.00",
                    "max": 50,
                    "rate": 100
                },
                "Common Metals": {
                    "stored": "0.00",
                    "income": "0.00",
                    "grossIncome": "0.00",
                    "max": 50,
                    "rate": 100
                },
                "Advanced Metals": {
                    "stored": "0.00",
                    "income": "0.00",
                    "grossIncome": "0.00",
                    "max": 50,
                    "rate": 100
                },
                "Uranium": {
                    "stored": "0.00",
                    "income": "0.00",
                    "grossIncome": "0.00",
                    "max": 50,
                    "rate": 100
                },
                "Rare Earth Elements": {
                    "stored": "0.00",
                    "income": "0.00",
                    "grossIncome": "0.00",
                    "max": 50,
                    "rate": 100
                },
                "Energy": {
                    "income": "0.00",
                    "grossIncome": "0.00",
                    "rate": 100
                },
                "Military Capacity": {
                    "used": "0.00",
                    "max": "0.00",
                    "rate": 100
                },
            },
            "statistics": {
                "regionsOwned": 0,
                "regionsOccupied": 0,
                "resourcesGiven": 0,
                "resourcesReceived": 0
            },
            "records": {
                "militaryStrength": [],
                "nationSize": [],
                "netIncome": [],
                "researchCount": [],
                "transactionCount": []
            },
            "improvementCounts": {key: 0 for key in improvement_dict},
            "unitCounts": {key: 0 for key in unit_dict},
            "unlockedResearch": {},
            "incomeDetails": [],
            "tags": {},
            "actionLog": []
        }
        
        cls._data[nation_id] = nation_data

    @classmethod
    def get(cls, string: str) -> "Nation":
        
        # check if nation id was provided
        if string in cls._data:
            return Nation(string)
        
        # check if nation name was provided
        for nation in cls:
            if nation.name.lower() == string.lower():
                return Nation(nation.id)

        raise Exception(f"Failed to retrieve nation with identifier {string}.")
    
    @classmethod
    def update_records(cls) -> None:
        pass

    @classmethod
    def get_top_three(cls, record_name: str) -> list[Tuple[str, float|int]]:
        pass

    @classmethod
    def get_lowest_in_record(cls, record_name: str) -> Tuple[str, float|int]:
        pass

    @classmethod
    def add_leaderboard_bonuses(cls):
        pass

    @classmethod
    def check_tags(cls) -> None:
        pass

    @classmethod
    def _generate_vc_sets(cls, count: int) -> dict:

        victory_conditions = core.get_scenario_dict(cls.game_id, "victory")
        easy_list = victory_conditions["easy"]
        medium_list = victory_conditions["medium"]
        hard_List = victory_conditions["hard"]

        vc_sets = {}
        random_easys = random.sample(easy_list, len(easy_list))
        random_mediums = random.sample(medium_list, len(medium_list))
        random_hards = random.sample(hard_List, len(hard_List))

        for i in range(count):
            name = f"set{i+1}"
            vc_sets[name] = {}
            vc_sets[name][random_easys.pop()] = False
            vc_sets[name][random_mediums.pop()] = False
            vc_sets[name][random_hards.pop()] = False

        return vc_sets

class Nation:
    
    def __init__(self, nation_id: str):

        self._data = Nations._data[nation_id]

        self.id: str = nation_id
        self._name: str = self._data["nationName"]
        self._player_id: int = self._data["playerID"]
        self._color: str = self._data["color"]
        self._gov: str = self._data["government"]
        self._fp: str = self._data["foreignPolicy"]
        self._status: str = self._data["status"]
        self._trade_fee: str = self._data["tradeFee"]
        self._missile_count: int = self._data["standardMissileStockpile"]
        self._nuke_count: int = self._data["nuclearMissileStockpile"]
        
        self._score: int = self._data["score"]
        self.victory_conditions: dict = self._data["chosenVictorySet"]
        self._sets: dict = self._data["victorySets"]
        self._satisfied: dict = self._data["satisfiedVictorySet"]
        
        self.completed_research: dict = self._data["unlockedResearch"]
        self.improvement_counts: dict = self._data["improvementCounts"]
        self.unit_counts: dict = self._data["unitCounts"]
        self.tags: dict = self._data["tags"]
        self.action_log: list = self._data["actionLog"]

        self.income_details: list = self._data["incomeDetails"]
        self.stats = NationStatistics(self._data["statistics"])
        self._records: dict = self._data["records"]
        self._resources: dict = self._data["resources"]

class NationStatistics:

    def __init__(self, d: dict):

        self._data = d
        self._regions_owned: int = d["regionsOwned"]
        self._regions_occupied: int = d["regionsOccupied"]
        self._resources_given: float = d["resourcesGiven"]
        self._resources_received: float = d["resourcesReceived"]

    @property
    def regions_owned(self):
        return self._regions_owned
    
    @property
    def regions_occupied(self):
        return self._regions_occupied
    
    @property
    def resources_given(self):
        return self._resources_given
    
    @property
    def resources_received(self):
        return self._resources_received
    
    @regions_owned.setter
    def regions_owned(self, value: int):
        self._regions_owned = value
        self._data["regionsOwned"] = value

    @regions_occupied.setter
    def regions_occupied(self, value: int):
        self._regions_occupied = value
        self._data["regionsOccupied"] = value

    @resources_given.setter
    def resources_given(self, value: float):
        self._resources_given = value
        self._data["resourcesGiven"] = value

    @resources_received.setter
    def resources_received(self, value: float):
        self._resources_received = value
        self._data["resourcesReceived"] = value
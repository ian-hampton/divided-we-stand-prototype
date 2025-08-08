import json
import os
from dataclasses import dataclass
from typing import ClassVar

import core

@dataclass
class Regions:

    game_id: ClassVar[str]
    _data: ClassVar[dict[str, dict]] = None
    _graph: ClassVar[dict[str, dict]] = None

    @classmethod
    def load(cls, game_id: str):
        cls.game_id = game_id
        regdata_filepath = f"gamedata/{Regions.game_id}/regdata.json"
        graph_filepath = f"maps/{core.get_map_str(Regions.game_id)}/graph.json"
        
        if not (os.path.exists(regdata_filepath) and os.path.exists(graph_filepath)):
            raise FileNotFoundError(f"Error: Unable to locate required game files for Regions class.")
        
        with open(regdata_filepath, 'r') as f:
            cls._data = json.load(f)
        with open(graph_filepath, 'r') as f:
            cls._graph = json.load(f)
    
    @classmethod
    def save(cls):
        if cls._data is None:
            raise RuntimeError("Error: Regions data not loaded.")
        
        regdata_filepath = f"gamedata/{cls.game_id}/regdata.json"
        
        with open(regdata_filepath, 'w') as json_file:
            json.dump(cls._data, json_file, indent=4)
    
    @classmethod
    def __iter__(cls):
        for region_id in cls._graph:
            yield Region(region_id)

class Region:

    def __init__(self, region_id: str):

        if Regions.game_id is None:
            raise RuntimeError("Error: Error: Regions data not loaded.")

        self.game_id = Regions.game_id

        self.region_id = region_id
        self.data = RegionData(Regions._data[self.region_id]["regionData"])
        self.graph = GraphData(Regions._graph[self.region_id])
        self.improvement = ImprovementData(
            Regions._data[self.region_id]["improvementData"],
            Regions._graph[self.region_id]
        )
        self.unit = ImprovementData(
            Regions._data[self.region_id]["unitData"],
            Regions._graph[self.region_id]
        )

class RegionData:

    def __init__(self, d: dict):
    
        self.owner_id: int = d["ownerID"]
        self.occupier_id: int = d["occupierID"]
        self.purchase_cost: int = d["purchaseCost"]
        self.resource: str = d["regionResource"]
        self.fallout: int = d["nukeTurns"]

class GraphData:
        
    def __init__(self, d: dict):

        self.is_edge: bool = d["isEdgeOfMap"]
        self.is_significant: bool = d["hasRegionalCapital"]
        self.is_magnified: bool = d["isMagnified"]
        self.is_start: bool = d["randomStartAllowed"]
        self.additional_region_coordinates: list = d["additionalRegionCords"]
        self.adjacent_regions: dict = d["adjacencyMap"]

class ImprovementData:
    
    def __init__(self, regiondata: dict, graphdata: dict):

        self.name: str = regiondata["name"]
        self.health: int = regiondata["health"]
        self.countdown: int = regiondata["turnTimer"]
        self.coords: list = graphdata["improvementCords"]

        improvement_data_dict = core.get_scenario_dict(Regions.game_id, "Improvements")
        if self.name is not None:
            self.hit_value = improvement_data_dict[self.name]["Combat Value"]
            self.missile_defense = improvement_data_dict[self.name]["Standard Missile Defense"]
            self.nuke_defense = improvement_data_dict[self.name]["Nuclear Missile Defense"]
        else:
            self.hit_value = None
            self.missile_defense = None
            self.nuke_defense = None

class UnitData:
    
    def __init__(self, regiondata: dict, graphdata: dict):

        self.name: str = regiondata["name"]
        self.health: int = regiondata["health"]
        self.owner_id: int = regiondata["ownerID"]
        self.coords: list = graphdata["unitCords"]

        unit_data_dict = core.get_scenario_dict(Regions.game_id, "Units")
        if self.name is not None:
            self.type = unit_data_dict[self.name]["Unit Type"]
            self.hit_value = unit_data_dict[self.name]["Combat Value"]
            self.value = unit_data_dict[self.name]["Point Value"]
        else:
            self.type = None
            self.hit_value = None
            self.value = None
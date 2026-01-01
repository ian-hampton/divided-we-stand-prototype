import json
import os
from dataclasses import dataclass
from typing import ClassVar, Iterator

from app.game.games import Games
from .region import Region

class RegionsMeta(type):
    
    def __contains__(cls, region_id: str):
        return cls._graph is not None and region_id in cls._graph

    def __iter__(cls) -> Iterator[Region]:
        for region_id in cls._graph:
            yield Region(region_id, cls._data[region_id], cls._graph[region_id], cls.game_id)

    def __len__(cls):
        return len(cls._graph) if cls._graph else 0

@dataclass
class Regions(metaclass=RegionsMeta):

    game_id: ClassVar[str] = None
    _data: ClassVar[dict[str, dict]] = None
    _graph: ClassVar[dict[str, dict]] = None
    _instances: ClassVar[dict[str, Region]] = {}

    @classmethod
    def _regdata_path(cls) -> str:
        return f"gamedata/{cls.game_id}/regdata.json"

    @classmethod
    def initialize(cls, game_id: str) -> None:

        game = Games.load(game_id)
        
        cls.game_id = game_id
        regdata_path = cls._regdata_path()
        graph_filepath = f"maps/{game.get_map_string()}/graph.json"
        
        if not (os.path.exists(regdata_path) and os.path.exists(graph_filepath)):
            raise FileNotFoundError(f"Error: Unable to locate required game files for Regions class.")
        
        with open(regdata_path, 'r') as f:
            cls._data = json.load(f)
        with open(graph_filepath, 'r') as f:
            cls._graph = json.load(f)
        
        cls._instances.clear()
    
    @classmethod
    def save(cls) -> None:
        if cls._data is None:
            raise RuntimeError("Error: Regions data not loaded.")
        
        regdata_filepath = f"gamedata/{cls.game_id}/regdata.json"
        
        with open(regdata_filepath, 'w') as json_file:
            json.dump(cls._data, json_file, indent=4)

    @classmethod
    def load(cls, region_id: str) -> Region:
        """
        Loads a Region based on the region id. Creates new Region object if one does not already exist.
        """
        if region_id not in cls._data:
            raise Exception(f"Failed to load Region with id {region_id}. Region ID not valid for this game.")
        
        if region_id not in cls._instances:
            cls._instances[region_id] = Region(region_id, cls._data[region_id], cls._graph[region_id], cls.game_id)
        return cls._instances[region_id]
    
    @classmethod
    def ids(cls) -> list:
        return list(cls._graph.keys())
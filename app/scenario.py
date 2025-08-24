import json
import os
import random
from dataclasses import dataclass
from typing import ClassVar, Iterator, Tuple

class ScenarioDataFile:
    
    def __init__(self, filename: str):

        self.file: dict = {}
        self.filename = filename

        filepath = f"scenarios/{ScenarioData.scenario}/{filename}.json"
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Error: {ScenarioData} scenario is missing {filename} file.")

        with open(filepath, 'r') as file:
            self.file = json.load(file)

    def get(self, name: str) -> any:
        
        data: dict = self.file.get(name)

        if data is None:
            return None
        
        files = {
            "agendas": SD_Agenda,
            "alliances": SD_Alliance,
            "events": SD_Event,
            "improvements": SD_Improvement,
            "justifications": SD_WarJustification,
            "missiles": SD_Missile,
            "technologies": SD_Technology,
            "units": SD_Units,
            "victory": SD_VictoryCondition
        }

        return files[self.filename](data)
    
    def names(self) -> list:
        return self.file.keys()

@dataclass
class ScenarioData:
    """
    Simple read-only class for fetching scenario data on demand.
    """

    game_id: ClassVar[str] = None
    scenario: ClassVar[str] = None
    agendas: ClassVar[ScenarioDataFile] = None
    alliances: ClassVar[ScenarioDataFile] = None
    events: ClassVar[ScenarioDataFile] = None
    improvements: ClassVar[ScenarioDataFile] = None
    missiles: ClassVar[ScenarioDataFile] = None
    technologies: ClassVar[ScenarioDataFile] = None
    units: ClassVar[ScenarioDataFile] = None
    victory_conditions: ClassVar[ScenarioDataFile] = None
    war_justificiations: ClassVar[ScenarioDataFile] = None
    
    @classmethod
    def load(cls, game_id: str) -> None:

        cls.game_id = game_id
        cls.scenario = cls._get_scenario_name()

        cls.agendas = ScenarioDataFile("agendas")
        cls.alliances = ScenarioDataFile("alliances")
        cls.events = ScenarioDataFile("events")
        cls.improvements = ScenarioDataFile("improvements")
        cls.missiles = ScenarioDataFile("justifications")
        cls.technologies = ScenarioDataFile("missiles")
        cls.units = ScenarioDataFile("technologies")
        cls.victory_conditions = ScenarioDataFile("units")
        cls.war_justificiations = ScenarioDataFile("victory")

    @classmethod
    def _get_scenario_name(cls) -> str:
        if cls.game_id != "TBD":
            with open('active_games.json', 'r') as json_file:
                active_games_dict = json.load(json_file)
            scenario_name: str = active_games_dict[cls.game_id]["Information"]["Scenario"]
            return scenario_name.lower()
        return "standard"

class SD_Agenda:
    
    def __init__(self, d: dict):
        pass

class SD_Alliance:
    
    def __init__(self, d: dict):
        
        self.color_theme: str = d["colorTheme"]
        self.description: list = d["descriptionList"]

class SD_Event:
    
    def __init__(self, d: dict):
        pass

class SD_Improvement:
    
    def __init__(self, d: dict):
        pass

class SD_Missile:
    
    def __init__(self, d: dict):
        pass

class SD_Technology:
    
    def __init__(self, d: dict):
        pass

class SD_Units:
    
    def __init__(self, d: dict):
        pass

class SD_VictoryCondition:
    
    def __init__(self, d: dict):
        pass

class SD_WarJustification:
    
    def __init__(self, d: dict):
        pass
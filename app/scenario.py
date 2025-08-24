import copy
import json
import os
import random
from dataclasses import dataclass
from typing import ClassVar, TypeVar, Generic, Iterator, Tuple

class SD_Agenda:
    
    def __init__(self, d: dict):
        self.type: str = d["Agenda Type"]
        self.prerequisite: str | None = d["Prerequisite"]
        self.cost: int = d["Cost"]
        self.description: str = d["Description"]
        self.location: str = d["Location"]
        self.modifiers: dict = d["Modifiers"]

class SD_Alliance:
    
    def __init__(self, d: dict):
        self.color_theme: str = d["colorTheme"]
        self.description: list = d["descriptionList"]

class SD_Event:
    
    def __init__(self, d: dict):
        self.type: str = d["Type"]
        self.duration: int = d["Duration"]

class SD_Improvement:
    
    def __init__(self, d: dict):
        pass

class SD_Missile:
    
    def __init__(self, d: dict):
        pass

class SD_Technology:
    
    def __init__(self, d: dict):
        self.type: str = d["Agenda Type"]
        self.prerequisite: str | None = d["Prerequisite"]
        self.cost: int = d["Cost"]
        self.description: str = d["Description"]
        self.location: str = d["Location"]
        self.modifiers: dict = d["Modifiers"]

class SD_Units:
    
    def __init__(self, d: dict):
        pass

class SD_VictoryCondition:
    
    def __init__(self):

        filename = "victory"
        filepath = f"scenarios/{ScenarioData.scenario}/{filename}.json"
        
        self.d = {}
        with open(filepath, 'r') as file:
            self.d = json.load(file)
        
    @property
    def easy(self):
        return copy.deepcopy(self.d["easy"])
    
    @property
    def medium(self):
        return copy.deepcopy(self.d["medium"])
    
    @property
    def hard(self):
        return copy.deepcopy(self.d["hard"])

class SD_WarJustification:
    
    def __init__(self, d: dict):
        pass

ClassNameToFileName = {
    "SD_Agenda": "agendas",
    "SD_Alliance": "alliances",
    "SD_Event": "events",
    "SD_Improvement": "improvements",
    "SD_Missile": "missiles",
    "SD_Technology": "technologies",
    "SD_Units": "units",
    "SD_WarJustification": "justifications",
}

T = TypeVar("T")
class ScenarioDataFile(Generic[T]):
    
    def __init__(self, cls: type[T]):

        self._cls: type[T] = cls
        self.filename = ""
        self.file = {}

        try:
            class_name = cls.__name__
            self.filename = ClassNameToFileName[class_name]
            filepath = f"scenarios/{ScenarioData.scenario}/{self.filename}.json"
            with open(filepath, 'r') as file:
                self.file = json.load(file)
        except:
            raise FileNotFoundError(f"Error: {ScenarioData.scenario} scenario is missing {self.filename} file.")

    def __iter__(self):
        for name in self.file:
            yield name, self[name]

    def __contains__(self, name_str: str):
        return self.file is not None and name_str in self.file
    
    def __getitem__(self, name_str: str) -> T:
        """
        Warning: This method will raise an exception if name/key is not found.
        This should only occur if the key does not exist in corresponding the scenario file, or if the action validation code allowed an action with an invalid parameter through.
        """
        data = self.file.get(name_str)
        if data is None:
            raise KeyError(f"Error: \"name\" not found in \"{self.filename}.json\" scenario file.")
        return self._cls(data)
    
    def names(self) -> set:
        return set(self.file.keys())

@dataclass
class ScenarioData:
    """
    Simple read-only class for fetching scenario data on demand.
    """

    agendas: ClassVar[ScenarioDataFile[SD_Agenda]] = None
    alliances: ClassVar[ScenarioDataFile[SD_Alliance]] = None
    events: ClassVar[ScenarioDataFile[SD_Event]] = None
    improvements: ClassVar[ScenarioDataFile[SD_Improvement]] = None
    missiles: ClassVar[ScenarioDataFile[SD_Missile]] = None
    technologies: ClassVar[ScenarioDataFile[SD_Technology]] = None
    units: ClassVar[ScenarioDataFile[SD_Units]] = None
    victory_conditions: ClassVar[SD_VictoryCondition] = None
    war_justificiations: ClassVar[ScenarioDataFile[SD_WarJustification]] = None
    
    @classmethod
    def load(cls, game_id: str) -> None:

        cls.game_id = game_id
        cls.scenario = cls._get_scenario_name()

        cls.agendas = ScenarioDataFile(SD_Agenda)
        cls.alliances = ScenarioDataFile(SD_Alliance)
        cls.events = ScenarioDataFile(SD_Event)
        cls.improvements = ScenarioDataFile(SD_Improvement)
        cls.missiles = ScenarioDataFile(SD_Missile)
        cls.technologies = ScenarioDataFile(SD_Technology)
        cls.units = ScenarioDataFile(SD_Units)
        cls.victory_conditions = SD_VictoryCondition()
        cls.war_justificiations = ScenarioDataFile(SD_WarJustification)

    @classmethod
    def _get_scenario_name(cls) -> str:
        if cls.game_id != "TBD":
            with open('active_games.json', 'r') as json_file:
                active_games_dict = json.load(json_file)
            scenario_name: str = active_games_dict[cls.game_id]["Information"]["Scenario"]
            return scenario_name.lower()
        return "standard"
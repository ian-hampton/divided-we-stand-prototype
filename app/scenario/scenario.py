import json
from dataclasses import dataclass
from typing import ClassVar, TypeVar, Generic

from app.game.games import Games
from .sd_agenda import *
from .sd_alliance import *
from .sd_event import *
from .sd_improvement import *
from .sd_market import *
from .sd_missile import *
from .sd_technology import *
from .sd_unit import *
from .sd_victory import *
from .sd_war import *

ClassNameToFileName = {
    "SD_Agenda": "agendas",
    "SD_Alliance": "alliances",
    "SD_Event": "events",
    "SD_Improvement": "improvements",
    "SD_Market": "market",
    "SD_Missile": "missiles",
    "SD_Technology": "technologies",
    "SD_Unit": "units",
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
            filepath = f"scenarios/{ScenarioInterface.scenario}/{self.filename}.json"
            with open(filepath, 'r') as file:
                self.file = json.load(file)
        except:
            raise FileNotFoundError(f"Error: {ScenarioInterface.scenario} scenario is missing {self.filename} file.")

    def __iter__(self):
        for name in self.file:
            yield str(name), self[name]

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
class ScenarioInterface:
    """
    Simple read-only class for fetching scenario data on demand.
    """

    agendas: ClassVar[ScenarioDataFile[SD_Agenda]] = None
    alliances: ClassVar[ScenarioDataFile[SD_Alliance]] = None
    events: ClassVar[ScenarioDataFile[SD_Event]] = None
    improvements: ClassVar[ScenarioDataFile[SD_Improvement]] = None
    market: ClassVar[ScenarioDataFile[SD_Market]] = None
    missiles: ClassVar[ScenarioDataFile[SD_Missile]] = None
    technologies: ClassVar[ScenarioDataFile[SD_Technology]] = None
    units: ClassVar[ScenarioDataFile[SD_Unit]] = None
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
        cls.market = ScenarioDataFile(SD_Market)
        cls.missiles = ScenarioDataFile(SD_Missile)
        cls.technologies = ScenarioDataFile(SD_Technology)
        cls.units = ScenarioDataFile(SD_Unit)
        cls.victory_conditions = SD_VictoryCondition()
        cls.war_justificiations = ScenarioDataFile(SD_WarJustification)

    @classmethod
    def _get_scenario_name(cls) -> str:
        if cls.game_id != "TBD":
            game = Games.load(cls.game_id)
            return game.info.scenario.lower()
        return "standard"
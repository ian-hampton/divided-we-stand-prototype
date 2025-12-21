import copy
import json
from dataclasses import dataclass
from typing import ClassVar, TypeVar, Generic

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
        self.required_agenda: str = d["Required Agenda"]
        self.capacity: bool = d.get("Capacity") is not None
        self.color_theme: str = d["Color Theme"]
        self.description: list = d["Description"]

class SD_Event:
    
    def __init__(self, d: dict):
        self.type: str = d["Type"]
        self.duration: int = d["Duration"]

class SD_Improvement:
    
    def __init__(self, d: dict):
        
        self.d = d
        self.required_research: str = d["Required Research"]
        self.required_resource: str = d["Required Resource"]
        self.is_fog_of_war: bool = d.get("Fog of War") is not None
        self.color: str = d.get("Reference Color", "stat-grey")

        self.health: int = d.get("Health", 99)
        self.victory_damage: int = d.get("Victory Damage", 99)
        self.draw_damage: int = d.get("Draw Damage", 99)
        self.hit_value: int = d.get("Combat Value", 99)
        self.missile_defense: int = d.get("Standard Missile Defense", 99)
        self.nuclear_defense: int = d.get("Nuclear Missile Defense", 99)
        self.defense_range: int = d.get("Missile Defense Range", 99)

        self.income: dict = d.get("Income", {})
        self.abilities: list = d.get("Abilities", [])

    @property
    def upkeep(self) -> dict:
        return copy.deepcopy(self.d.get("Upkeep", {}))
    
    @property
    def cost(self) -> dict:
        return copy.deepcopy(self.d.get("Build Costs", {}))

class SD_Market:
    
    def __init__(self, d: dict):
        self.base_price = d["Base Price"]

class SD_Missile:
    
    def __init__(self, d: dict):
        
        self.d = d
        self.required_research: str = d["Required Research"]
        self.type: str = d["Type"]
        self.launch_cost: int = d["Launch Capacity"]

    @property
    def cost(self) -> dict:
        return copy.deepcopy(self.d.get("Build Costs", {}))

class SD_Technology:
    
    def __init__(self, d: dict):
        self.type: str = d["Research Type"]
        self.prerequisite: str | None = d["Prerequisite"]
        self.cost: int = d["Cost"]
        self.description: str = d["Description"]
        self.location: str = d["Location"]
        self.modifiers: dict = d["Modifiers"]

class SD_Unit:
    
    def __init__(self, d: dict):
        
        self.d = d
        self.required_research: str = d["Required Research"]
        self.type: str = d["Unit Type"]
        self.abbreviation: str = d["Abbreviation"]
        self.value: int = d["Point Value"]
        self.color: str = d["Reference Color"]
        
        self.health: int = d.get("Health", 99)
        self.victory_damage: int = d.get("Victory Damage", 99)
        self.draw_damage: int = d.get("Draw Damage", 99)
        self.hit_value: int = d.get("Combat Value", 99)
        self.missile_defense: int = d.get("Standard Missile Defense", 99)
        self.nuclear_defense: int = d.get("Nuclear Missile Defense", 99)
        self.defense_range: int = d.get("Missile Defense Range", 99)
        
        self.movement: int = d.get("Movement", 0)
        self.abilities: list = d.get("Abilities", [])

    @property
    def upkeep(self) -> dict:
        return copy.deepcopy(self.d.get("Upkeep", {}))
    
    @property
    def cost(self) -> dict:
        return copy.deepcopy(self.d.get("Build Costs", {}))

class SD_VictoryCondition:
    
    def __init__(self):

        filename = "victory"
        filepath = f"scenarios/{ScenarioInterface.scenario}/{filename}.json"
        
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
        
        self.d = d
        self.required_agenda: str = d["Required Agenda"]
        self.truce_duration: int = d["Truce Duraton"]
        
        self.has_war_claims: bool = d.get("War Claims") is not None
        self.free_claims: int = None if not self.has_war_claims else d["War Claims"]["Free"]
        self.max_claims: int = None if not self.has_war_claims else d["War Claims"]["Max"]
        self.claim_cost: int = None if not self.has_war_claims else d["War Claims"]["Cost"]
        
        self.winner_stockpile_gains: dict = d.get("Winner Stockpile Gains", {})
        self.winner_becomes_independent: bool = d.get("Winner Becomes Independent") is not None

        self.looser_stockpile_gains: dict = d.get("Looser Stockpile Gains", {})
        self.looser_penalty_duration: int = d.get("Looser Penalty Duration", None)
        self.looser_releases_all_puppet_states: bool = d.get("Looser Releases All Puppet States") is not None
        self.looser_becomes_puppet_state: bool = d.get("Looser Becomes Puppet State") is not None
        
        self.for_puppet_states: bool = d.get("For Puppet States") is not None
        self.target_requirements: dict = d.get("Target Requirements", {})

    @property
    def looser_penalties(self) -> dict | None:
        return copy.deepcopy(self.d.get("Looser Penalties", None))

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
        from app.game.games import Games
        if cls.game_id != "TBD":
            game = Games.load(cls.game_id)
            return game.info.scenario.lower()
        return "standard"
from app.scenario.scenario import ScenarioInterface as SD

class ImprovementData:
    
    def __init__(self, d: dict):
        self._data = d
        self._load_attributes_from_game_files()
        self.has_been_attacked = False

    @property
    def name(self) -> str:
        return self._data["name"]
    
    @name.setter
    def name(self, value: str) -> None:
        self._data["name"] = value

    @property
    def health(self) -> int:
        return self._data["health"]
    
    @health.setter
    def health(self, value: int) -> None:
        self._data["health"] = value

    @property
    def countdown(self) -> int:
        return self._data["turnTimer"]
    
    @countdown.setter
    def countdown(self, value: int) -> None:
        self._data["turnTimer"] = value

    @property
    def has_health(self):
        return True if self.health not in [0, 99] else False

    def _load_attributes_from_game_files(self) -> None:
        
        if self.name is not None:
            improvement = SD.improvements[self.name]
            self.damage = improvement.damage
            self.armor = improvement.armor
            self.max_health = improvement.health
            self.missile_defense = improvement.missile_defense
            self.nuclear_defense = improvement.nuclear_defense
        else:
            self.damage = None
            self.armor = None
            self.max_health = None
            self.missile_defense = None
            self.nuke_defense = None

    def set(self, improvement_name: str, starting_health=0) -> None:
        self.clear()
        self.name = improvement_name
        self._load_attributes_from_game_files()
        self.health = self.max_health if starting_health == 0 else starting_health

    def heal(self, amount: int) -> None:
        self.health += amount
        if self.health > self.max_health:
            self.health = self.max_health

    def decrease_countdown(self) -> None:
        if self.countdown != 99:
            self.countdown -= 1

    def clear(self) -> None:
        self.name = None
        self.health = 99
        self.countdown = 99
        self._load_attributes_from_game_files()
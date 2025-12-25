from app.scenario.scenario import ScenarioInterface as SD
from app.war.wars import Wars

class UnitData:
    
    def __init__(self, d: dict):
        self._data = d
        self._load_attributes_from_game_files()

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
    def owner_id(self) -> str:
        return self._data["ownerID"]
    
    @owner_id.setter
    def owner_id(self, new_id: str) -> None:
        self._data["ownerID"] = new_id

    def _load_attributes_from_game_files(self) -> None:

        if self.name is not None:
            self.type = SD.units[self.name].type
            self.value = SD.units[self.name].value
            self.victory_damage = SD.units[self.name].victory_damage
            self.draw_damage = SD.units[self.name].draw_damage
            self.max_health = SD.units[self.name].health
            self.hit_value = SD.units[self.name].hit_value
            self.missile_defense = SD.units[self.name].missile_defense
            self.nuclear_defense = SD.units[self.name].nuclear_defense
        else:
            self.type = None
            self.value = None
            self.victory_damage = None
            self.draw_damage = None
            self.max_health = None
            self.hit_value = None
            self.missile_defense = None
            self.nuclear_defense = None

    def set(self, unit_name: str, owner_id: str, starting_health=0) -> None:
        self.clear()
        self.name = unit_name
        self.owner_id = owner_id
        self._load_attributes_from_game_files()
        self.health = self.max_health if starting_health == 0 else starting_health

    def heal(self, amount: int) -> None:
        self.health += amount
        if self.health > self.max_health:
            self.health = self.max_health

    def clear(self) -> None:
        self.name = None
        self.health = 99
        self.owner_id = "0"
        self._load_attributes_from_game_files()

    def is_hostile(self, other_player_id: str) -> bool:

        # if no unit return False
        if self.owner_id == "0" or other_player_id == "0":
            return False

        # if player_ids are the same than return False
        if self.owner_id == other_player_id:
            return False
        
        # if other_player_id = 99 return True (defending unit is controlled by event)
        if other_player_id == "99":
            return True
        
        # check if at war
        if Wars.get_war_name(self.owner_id, other_player_id) is not None:
            return True
        
        return False
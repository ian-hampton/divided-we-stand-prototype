from app.scenario.scenario import ScenarioInterface as SD

class UnitData:
    
    def __init__(self, d: dict):
        self._data = d
        self._load_attributes_from_game_files()
        self.level = self.xp // 10
        self.has_been_attacked = False
        self.has_movement_queued = False

    @property
    def name(self) -> str:
        return self._data["name"]
    
    @name.setter
    def name(self, value: str) -> None:
        self._data["name"] = value

    @property
    def full_name(self) -> str:
        return self._data["fullName"]
    
    @full_name.setter
    def full_name(self, value: str) -> None:
        self._data["fullName"] = value

    @property
    def health(self) -> int:
        return self._data["health"]
    
    @health.setter
    def health(self, value: int) -> None:
        self._data["health"] = value

    @property
    def xp(self) -> int:
        return self._data["experience"]
    
    @xp.setter
    def xp(self, value: int) -> None:
        self._data["experience"] = min(value, 30)

    @property
    def owner_id(self) -> str:
        return self._data["ownerID"]
    
    @owner_id.setter
    def owner_id(self, new_id: str) -> None:
        self._data["ownerID"] = new_id
    
    @property
    def true_max_health(self) -> int:
        return self.max_health + self.level * 2
    
    @property
    def true_damage(self) -> int:
        return self.damage + self.level

    def _load_attributes_from_game_files(self) -> None:
        if self.name is not None:
            unit = SD.units[self.name]
            self.type = unit.type
            self.value = unit.value
            self.damage = unit.damage
            self.armor = unit.armor
            self.max_health = unit.health
            self.movement = unit.movement
            self.missile_defense = unit.missile_defense
            self.nuclear_defense = unit.nuclear_defense
            self.defense_range = unit.defense_range
        else:
            self.type = None
            self.value = None
            self.damage = None
            self.armor = None
            self.max_health = None
            self.movement = None
            self.missile_defense = None
            self.nuclear_defense = None
            self.defense_range = None

    def calculate_level(self) -> bool:
        """
        Recalculate this unit's level based on its experience.

        Returns:
            bool: True if the unit has increased their level, False otherwise.
        """
        new_level = self.xp // 10
        
        # do nothing if this unit does not exist or level has not changed
        if self.name is None or self.level == new_level:
            return False
        
        if new_level > self.level:
            # unit is at a higher level now than before
            self.level = new_level
            self.heal(2)
            return True
        
        # unit is at a lower level than before - this code should never run but here it is anyway
        self.level = new_level
        self.heal(0)
        return False

    def set(self, unit_name: str, full_unit_name: str, xp: int, owner_id: str, starting_health=0) -> None:
        self.clear()
        self.name = unit_name
        self.full_name = full_unit_name
        self.xp = xp
        self.owner_id = owner_id
        self._load_attributes_from_game_files()
        self.level = self.xp // 10
        self.health = self.true_max_health if starting_health == 0 else starting_health

    def heal(self, amount: int) -> None:
        self.health += amount
        if self.health > self.true_max_health:
            self.health = self.true_max_health

    def clear(self) -> None:
        self.name = None
        self.full_name = None
        self.health = 99
        self.owner_id = "0"
        self._load_attributes_from_game_files()

    def is_hostile(self, other_player_id: str) -> bool:
        from app.war.wars import Wars

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
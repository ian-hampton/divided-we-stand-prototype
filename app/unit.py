import copy
import json

from app import core

class Unit:

    def __init__(self, region_id: str, game_id: str):
        
        # check if game id is valid
        regdata_filepath = f'gamedata/{game_id}/regdata.json'
        try:
            with open(regdata_filepath, 'r') as json_file:
                regdata_dict = json.load(json_file)
        except FileNotFoundError:
            print(f"Error: Unable to locate {regdata_filepath} during Unit class initialization.")

        # check if region id is valid
        try:
            unit_data = regdata_dict[region_id]["unitData"]
        except KeyError:
            print(f"Error: {region_id} not recognized during Unit class initialization.")

        # set attributes now that all checks have passed
        self.region_id = region_id
        self.data = unit_data
        self.game_id = game_id
        self.regdata_filepath = regdata_filepath

    def _save_changes(self) -> None:
        '''
        Saves changes made to Unit object to game files.
        '''
        with open(self.regdata_filepath, 'r') as json_file:
            regdata_dict = json.load(json_file)
        regdata_dict[self.region_id]["unitData"] = self.data
        with open(self.regdata_filepath, 'w') as json_file:
            json.dump(regdata_dict, json_file, indent=4)

    def name(self) -> str:
        '''
        Returns the unit name.
        Returns None if no unit is present.
        '''
        return self.data["name"]
    
    def health(self) -> int:
        '''
        Returns the unit health.
        Returns 99 if the unit has no health bar.
        '''
        return self.data["health"]
    
    def owner_id(self) -> int:
        '''
        Returns the player_id of the unit owner.
        '''
        return self.data["ownerID"]
    
    def set_owner_id(self, new_owner_id: int) -> None:
        '''
        Changes the owner of a unit.
        '''
        self.data["ownerID"] = new_owner_id
        self._save_changes()
    
    def abbrev(self) -> str:
        '''
        Returns the unit name abbreviation.
        Returns None if no unit is present.
        '''
        unit_data_dict = core.get_scenario_dict(self.game_id, "Units")
        unit_name = self.data["name"]
        if unit_name is not None:
            return unit_data_dict[unit_name]["Abbreviation"]
        else:
            return None
        
    def set_unit(self, unit_name: str, owner_id: int) -> None:
        '''
        Sets unit in region.
        '''
        unit_data_dict = core.get_scenario_dict(self.game_id, "Units")
        self.data["name"] = unit_name
        self.data["health"] = unit_data_dict[unit_name]["Health"]
        self.data["ownerID"] = owner_id
        self._save_changes()
        
    def heal(self, health_count: int) -> None:
        '''
        Heals unit by x health.
        Will not heal beyond max health value.
        '''
        unit_data_dict = core.get_scenario_dict(self.game_id, "Units")
        current_health = self.health()
        max_health = unit_data_dict[self.name()]["Health"]
        current_health += health_count
        if current_health > max_health:
            current_health = max_health
        self.data["health"] = current_health
        self._save_changes()

    def clear(self) -> None:
        '''
        Removes the unit in a region.
        '''
        self.data["name"] = None
        self.data["health"] = 99
        self.data["ownerID"] = 99
        self._save_changes()

    def move(self, target_region_id: str, withdraw=False) -> None:
        '''
        Moves a unit to a new region.
        Returns True if move succeeded, otherwise False.
        '''
        target_region_unit = Unit(target_region_id, self.game_id)
        if withdraw:
            # TBA: add checks from withdraw action function to here when player log class is made
            target_region_unit = copy.deepcopy(self)
            target_region_unit._save_changes()
            self.clear()
        else:
            #if target unit friendly cancel move
            #if target unit hostile conduct combat
            pass

import copy
import json

from app import core
from app.wardata import WarData

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
        self.name: str = self.data["name"]
        self.owner_id: int = self.data["ownerID"]

    def _save_changes(self) -> None:
        '''
        Saves changes made to Unit object to game files.
        '''
        with open(self.regdata_filepath, 'r') as json_file:
            regdata_dict = json.load(json_file)
        regdata_dict[self.region_id]["unitData"] = self.data
        with open(self.regdata_filepath, 'w') as json_file:
            json.dump(regdata_dict, json_file, indent=4)
    
    def health(self) -> int:
        '''
        Returns the unit health.
        Returns 99 if the unit has no health bar.
        '''
        return self.data["health"]
    
    def set_owner_id(self, new_owner_id: int) -> None:
        '''
        Changes the owner of a unit.
        '''
        self.owner_id = new_owner_id
        self.data["ownerID"] = new_owner_id
        self._save_changes()
    
    def abbrev(self) -> str:
        '''
        Returns the unit name abbreviation.
        Returns None if no unit is present.
        '''
        unit_data_dict = core.get_scenario_dict(self.game_id, "Units")
        if self.name is not None:
            return unit_data_dict[self.name]["Abbreviation"]
        else:
            return None

    def clear(self) -> None:
        '''
        Removes the unit in a region.
        '''
        self.name = None
        self.owner_id = 99
        self.data["name"] = None
        self.data["health"] = 99
        self.data["ownerID"] = 99
        self._save_changes()

    # basic methods
    ################################################################################
    
    def set_unit(self, unit_name: str, owner_id: int) -> None:
        '''
        Sets unit in region.
        '''
        unit_data_dict = core.get_scenario_dict(self.game_id, "Units")
        self.name = unit_name
        self.data["name"] = unit_name
        self.data["health"] = unit_data_dict[unit_name]["Health"]
        self.owner_id = owner_id
        self.data["ownerID"] = owner_id
        self._save_changes()

    def heal(self, health_count: int) -> None:
        '''
        Heals unit by x health.
        Will not heal beyond max health value.
        '''
        unit_data_dict = core.get_scenario_dict(self.game_id, "Units")
        current_health = self.health()
        max_health = unit_data_dict[self.name]["Health"]
        current_health += health_count
        if current_health > max_health:
            current_health = max_health
        self.data["health"] = current_health
        self._save_changes()

    def move(self, target_region, *, withdraw=False) -> bool:
        '''
        Attempts to move a unit to a new region.
        Returns True if move succeeded, otherwise False.

        :param target_region: Region class
        :param target_region_improvement: Improvement class unless withdraw=True
        :param withdraw: True if withdraw action. False otherwise.
        '''
        from app.region import Region
        from app.improvement import Improvement
        target_region_id = target_region.region_id
        target_region_improvement = Improvement(target_region_id, self.game_id)
        target_region_unit = Unit(target_region_id, self.game_id)

        if withdraw:
            # to-do: add checks from withdraw action function to here when player log class is made
            target_region_unit = copy.deepcopy(self)
            target_region_unit._save_changes()
            self.clear()
            return True
        else:
            # to-do add checks from movement action to here when player log class is made
            # if target unit hostile conduct combat
            if target_region_unit.is_hostile(self.owner_id):
                target_region_unit = self.attack_unit(target_region_unit)
            # if target improvement hostile conduct combat
            if target_region_improvement.is_hostile(self.owner_id):
                target_region_improvement = self.attack_improvement(target_region_improvement)
            # if no resistance and still alive complete move
            if not target_region_unit.is_hostile(self.owner_id) and not target_region_improvement.is_hostile(self.owner_id) and self.name is not None:
                # move unit via deep copy
                # destroy improvement or capture improvement if needed
                # clear old unit
                # region occupation step
                # improvement occupation step
                # return true
                pass

        return False

    # combat methods
    ################################################################################

    def is_hostile(self, other_player_id: int) -> bool:
        '''
        Determines if this unit is hostile to the given player_id.

        :param other_player_id: player_id to compare to
        :return: rue if this unit is hostile to provided player_id. False otherwise.
        '''
        wardata = WarData(self.game_id)

        # if no unit return False
        if self.owner_id == 99:
            return False

        # if player_ids are the same than return False
        if self.owner_id == other_player_id:
            return False
        
        # check if at war
        if wardata.are_at_war(self.owner_id, other_player_id):
            return True
        else:
            return False
    
    def attack_unit(self, hostile_unit: 'Unit'):
        '''
        Resolves unit vs unit combat.
        '''
        playerdata_filepath = f'gamedata/{self.game_id}/playerdata.csv'
        playerdata_list = core.read_file(playerdata_filepath, 1)
        wardata = WarData(self.game_id)

        # get nation names and war roles
        attacker_nation_name = playerdata_list[self.owner_id - 1][1]
        defender_nation_name = playerdata_list[hostile_unit.owner_id - 1][1]
        war_name = wardata.are_at_war(self.owner_id, hostile_unit.owner_id, True)
        attacker_war_role = wardata.get_war_role(attacker_nation_name, war_name)
        defender_war_role = wardata.get_war_role(defender_nation_name, war_name)

        # calculate modifiers
        attacker_roll_modifier = 0
        defender_roll_modifier = 0
        attacker_damage_modifier = 0
        defender_damage_modifier = 0

        return hostile_unit

    def attack_improvement(self, hostile_improvement):
        '''
        Resolves unit vs improvement combat.
        '''

        return hostile_improvement

        


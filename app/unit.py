import copy
import json

from app import core
from app.region import Region
from app.improvement import Improvement
from app.nationdata import NationTable

class Unit:

    def __init__(self, region_id: str, game_id: str):
        """
        Initializes unit class. Calls load_attributes() to load data from game files.

        Params:
            region_id (str): Unique five letter string used to identify a region.
            game_id (str): Unique string used to identify a game.

        """
        self.region_id = region_id
        self.game_id = game_id
        self.load_attributes()

    def load_attributes(self) -> None:
        """
        Loads data from game files for this class.
        """
        
        # check if game id is valid
        regdata_filepath = f'gamedata/{self.game_id}/regdata.json'
        try:
            with open(regdata_filepath, 'r') as json_file:
                regdata_dict = json.load(json_file)
        except FileNotFoundError:
            print(f"Error: Unable to locate {regdata_filepath} during Unit class initialization.")
        
        # check if region id is valid
        try:
            unit_data = regdata_dict[self.region_id]["unitData"]
        except KeyError:
            print(f"Error: {self.region_id} not recognized during Unit class initialization.")
        self.data: dict = unit_data
        self.regdata_filepath = regdata_filepath

        self.name: str = self.data["name"]
        self.health: int = self.data["health"]
        self.owner_id: int = self.data["ownerID"]
        self.cords: list = self.data.get("coordinates", None)
        unit_data_dict = core.get_scenario_dict(self.game_id, "Units")
        if self.name is not None:
            self.type = unit_data_dict[self.name]["Unit Type"]
            self.hit_value = unit_data_dict[self.name]["Combat Value"]
            self.value = unit_data_dict[self.name]["Point Value"]
        else:
            self.type = None
            self.hit_value = None
            self.value = None

    def _save_changes(self) -> None:
        """
        Saves changes made to Unit object to game files.
        """
        with open(self.regdata_filepath, 'r') as json_file:
            regdata_dict = json.load(json_file)
        regdata_dict[self.region_id]["unitData"]["name"] = self.name
        regdata_dict[self.region_id]["unitData"]["health"] = self.health
        regdata_dict[self.region_id]["unitData"]["ownerID"] = self.owner_id
        with open(self.regdata_filepath, 'w') as json_file:
            json.dump(regdata_dict, json_file, indent=4)
    
    def set_owner_id(self, new_owner_id: int) -> None:
        """
        Changes the owner of a unit.
        """
        self.owner_id = new_owner_id
        self._save_changes()
    
    def abbrev(self) -> str:
        """
        Returns the unit name abbreviation or None if no unit is present.
        """

        # This function is used for only one purpose and that is rendering the units. Should be thrown into the dustbin of commit history next time I update unit rendering.
        unit_data_dict = core.get_scenario_dict(self.game_id, "Units")

        if self.name is not None:
            return unit_data_dict[self.name]["Abbreviation"]
        else:
            return None

    def clear(self) -> None:
        """
        Removes the unit in a region.
        """
        self.name = None
        self.health = 99
        self.owner_id = 0
        self.type = None
        self.hit_value = 99
        self._save_changes()

    # basic methods
    ################################################################################
    
    def set_unit(self, unit_name: str, owner_id: int) -> None:
        """
        Sets unit in region.

        Params:
            unit_name (str): Name of unit.
            owner_id (int): ID of player that owns this unit.
        """
        unit_data_dict = core.get_scenario_dict(self.game_id, "Units")
        self.name = unit_name
        self.health = unit_data_dict[unit_name]["Health"]
        self.owner_id = owner_id
        self.type = unit_data_dict[self.name]["Unit Type"]
        self.hit_value = unit_data_dict[self.name]["Combat Value"]
        self._save_changes()

    def heal(self, health_count: int) -> None:
        """
        Heals unit by x health. Will not heal beyond max health value.

        Params:
            health_count (int): Amount to increase health by.
        """
        unit_data_dict = core.get_scenario_dict(self.game_id, "Units")
        current_health = self.health
        max_health = unit_data_dict[self.name]["Health"]
        current_health += health_count
        if current_health > max_health:
            current_health = max_health
        self.health = current_health
        self._save_changes()

    def move(self, target_region: Region, *, withdraw=False) -> bool:
        """
        Attempts to move a unit to a new region.
        Returns True if move succeeded, otherwise False.

        Params:
            target_region (Region): Region object of target region (where this unit is moving to)
            withdraw: True if withdraw action. False otherwise.
        
        Returns:
            bool: True if action succeeded, False otherwise.
        """
        from app import combat
        from app.wardata import WarData
        target_region_id = target_region.region_id
        target_region_improvement = Improvement(target_region_id, self.game_id)
        target_region_unit = Unit(target_region_id, self.game_id)

        if withdraw:
            original_region_id = copy.deepcopy(self.region_id)
            self.region_id = target_region_unit.region_id
            self._save_changes()
            self.region_id = original_region_id
            self.clear()
            return True
        
        else:
            # to-do add checks from movement action to here when player log class is made
            # get war information
            wardata = WarData(self.game_id)

            # if target unit hostile conduct combat
            if target_region_unit.is_hostile(self.owner_id):
                combat.unit_vs_unit(self, target_region_unit)
                # reload objects
                self.load_attributes()
                target_region_unit.load_attributes()

            # if target improvement hostile conduct combat
            if self.name is not None and target_region_improvement.is_hostile(self.owner_id):
                combat.unit_vs_improvement(self, target_region_improvement)
                # reload objects
                self.load_attributes()
                target_region_improvement.load_attributes()

            # if no resistance and still alive complete move
            if not target_region_unit.is_hostile(self.owner_id) and not target_region_improvement.is_hostile(self.owner_id) and self.name is not None:
                # move unit
                original_player_id = copy.deepcopy(self.owner_id)
                original_region_id = copy.deepcopy(self.region_id)
                self.region_id = target_region_unit.region_id
                self._save_changes()
                self.region_id = original_region_id
                self.clear()
                # destroy improvement if needed
                if target_region_improvement.name is not None and target_region_improvement.name != 'Capital' and target_region.owner_id != original_player_id:
                    if original_player_id != 99:
                        playerdata_filepath = f'gamedata/{self.game_id}/playerdata.csv'
                        playerdata_list = core.read_file(playerdata_filepath, 1)
                        attacker_nation_name = playerdata_list[original_player_id - 1][1]
                        defender_nation_name = playerdata_list[target_region_improvement.owner_id - 1][1]
                        war_name = wardata.are_at_war(original_player_id, target_region_improvement.owner_id, True)
                        attacker_war_role = wardata.get_war_role(attacker_nation_name, war_name)
                        # award points
                        wardata.statistic_add(war_name, attacker_nation_name, "enemyImprovementsDestroyed")
                        wardata.statistic_add(war_name, defender_nation_name, "friendlyImprovementsDestroyed")
                        wardata.warscore_add(war_name, attacker_war_role, "enemyImprovementsDestroyed", 2)
                        # log and destroy
                        wardata.append_war_log(war_name, f"    {defender_nation_name} {target_region_improvement.name} has been destroyed!")
                    target_region_improvement.clear()
                # occupation step
                if target_region.owner_id != original_player_id:
                    target_region.set_occupier_id(original_player_id)
                else:
                    target_region.set_occupier_id(0)
                target_region._save_changes()

                return True

        return False

    # combat methods
    ################################################################################

    def is_hostile(self, other_player_id: int) -> bool:
        """
        Determines if this unit is hostile to the given player_id.

        Params:
            other_player_id (int): player_id to compare to
        
        Returns:
            bool: True if this unit is hostile to provided player_id. False otherwise.
        """
        from app.wardata import WarData
        wardata = WarData(self.game_id)

        # if no unit return False
        if self.owner_id == 0 or other_player_id == 0:
            return False

        # if player_ids are the same than return False
        if self.owner_id == other_player_id:
            return False
        
        # if other_player_id = 99 return True (defending unit is controlled by event)
        if other_player_id == 99:
            return True
        
        # check if at war
        if wardata.are_at_war(self.owner_id, other_player_id):
            return True
        else:
            return False
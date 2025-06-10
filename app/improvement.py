import json
import copy
import os

from app import core
from app.nationdata import Nation

class Improvement:

    def __init__(self, region_id: str, game_id: str):

        # check if game files exist
        regdata_filepath = f"gamedata/{game_id}/regdata.json"
        graph_filepath = f"maps/{core.get_map_str(game_id)}/graph.json"
        if not (os.path.exists(regdata_filepath) and os.path.exists(graph_filepath)):
            raise FileNotFoundError(f"Error: Unable to locate required game files during Improvement class initialization.")

        # define attributes
        self.region_id = region_id
        self.game_id = game_id
        self.regdata_filepath = regdata_filepath
        self.graph_filepath = graph_filepath
        self.load_attributes()

    def load_attributes(self) -> None:
        """
        Loads data from game files for this class.
        """

        # load game files
        improvement_data_dict = core.get_scenario_dict(self.game_id, "Improvements")
        with open(self.regdata_filepath, 'r') as json_file:
            regdata_dict = json.load(json_file)
        with open(self.graph_filepath, 'r') as json_file:
            graph_dict = json.load(json_file)

        # check if region exists
        if self.region_id not in regdata_dict:
            raise Exception(f"Error: Region ID {self.region_id} not found.")

        # set attributes
        self.data: dict = regdata_dict[self.region_id]["improvementData"]
        self.name: str = self.data["name"]
        self.health: int = self.data["health"]
        self.turn_timer: int = self.data["turnTimer"]
        if self.name is not None:
            self.hit_value = improvement_data_dict[self.name]["Combat Value"]
            self.missile_defense = improvement_data_dict[self.name]["Standard Missile Defense"]
            self.nuke_defense = improvement_data_dict[self.name]["Nuclear Missile Defense"]
        else:
            self.hit_value = None
            self.missile_defense = None
            self.nuke_defense = None
        self.coords: list = graph_dict[self.region_id]["improvementCords"]
        
        # get owner and occupier id attributes
        # TODO: improvement should become a child class of Region so we don't have to do this garbage
        from app.region import Region
        region_obj = Region(self.region_id, self.game_id)
        self.owner_id = region_obj.owner_id
        self.occupier_id = region_obj.occupier_id

    def _save_changes(self) -> None:
        """
        Saves changes made to Improvement object to game files.
        """

        with open(self.regdata_filepath, 'r') as json_file:
            regdata_dict = json.load(json_file)

        if self.name is not None and self.health < 0:
            self.health = 0

        self.data["name"] = self.name
        self.data["health"] = self.health
        self.data["turnTimer"] = self.turn_timer

        regdata_dict[self.region_id]["improvementData"] = self.data
        with open(self.regdata_filepath, 'w') as json_file:
            json.dump(regdata_dict, json_file, indent=4)
    
    # basic methods
    ################################################################################

    def set_improvement(self, improvement_name: str, health=0, player_research=[]) -> None:
        """
        Changes the improvement in a region.
        
        Params:
            improvement_nam (str): Name of improvement.
            health (int): Initial improvement health. Default is full health.
            player_research (list): List of player research. Fetched from playerdata.csv.
        """
        improvement_data_dict = core.get_scenario_dict(self.game_id, "Improvements")
        
        # removed old improvement
        self.clear()
        
        # initialize new improvement
        self.name = improvement_name
        if health == 0:
            self.health = improvement_data_dict[improvement_name]["Health"]
        else:
            self.health = health
        if self.name == 'Surveillance Center':
            pass
        
        self._save_changes()

    def heal(self, health_count: int) -> None:
        """
        Heals improvement by x health. Will not heal beyond max health value.

        Params:
            health_count (int): Amount of health to add.
        """
        improvement_data_dict = core.get_scenario_dict(self.game_id, "Improvements")
        
        current_health = self.health
        max_health = improvement_data_dict[self.name]["Health"]
        current_health += health_count
        if current_health > max_health:
            current_health = max_health
        self.health = current_health

        self._save_changes()

    def set_turn_timer(self, amount=4) -> None:
        """
        Sets the improvement turn timer.

        :param amount: Turns desired. Default is 4.
        """
        self.turn_timer = amount
        self._save_changes()
    
    def decrease_timer(self) -> None:
        """
        Decreases improvement turn timer by one.
        """
        if self.turn_timer != 99:
            self.turn_timer -= 1
            self._save_changes()

    def clear(self) -> None:
        """
        Removes the improvement in a region.
        """
        self.name = None
        self.health = 99
        self.turn_timer = 99
        self._save_changes()

    # income methods
    ################################################################################

    def calculate_yield(self, nation: Nation, improvement_income_dict: dict, active_games_dict: dict) -> dict:
        """
        Calculates the final yield of this improvement.

        Params:
            improvement_income_dict (dict): Contains the income and multiplier of this improvement type. From yield_dict.

        Returns:
            dict: Contains all yields from this improvement.
        """
        
        # load game info
        from app.region import Region
        region = Region(self.region_id, self.game_id)
        improvement_income_dict = copy.deepcopy(improvement_income_dict)  # deepcopy required because of modifiers below

        # get modifer from central banks
        if self.name != "Capital" and region.check_for_adjacent_improvement(improvement_names={"Central Bank"}):
            for resource_name in improvement_income_dict:
                improvement_income_dict[resource_name]["Income Multiplier"] += 0.2

        # get modifer from remnant government
        capital_boost = any("Capital Boost" in tag_data for tag_data in nation.tags.values())
        if capital_boost and region.check_for_adjacent_improvement(improvement_names = {'Capital'}):
            for resource_name in improvement_income_dict:
                if resource_name == "Political Power" or resource_name == "Military Capacity":
                    # do not boost political power or military capacity gains
                    continue
                improvement_income_dict[resource_name]["Income Multiplier"] += 0.2
        
        # get pandemic multiplier
        if "Pandemic" in active_games_dict[self.game_id]["Active Events"]:
            for resource_name in improvement_income_dict:
                multiplier = improvement_income_dict[resource_name]["Income Multiplier"]
                infection_penalty = 0
                if region.infection() > 0:
                    infection_penalty = region.infection() * 0.1
                quarantine_penalty = 0
                if region.is_quarantined():
                    quarantine_penalty = 0.5
                multiplier -= infection_penalty
                multiplier -= quarantine_penalty
                if multiplier < 0:
                    multiplier = 0
                improvement_income_dict[resource_name]["Income Multiplier"] = multiplier

        # get income modifiers from tags
        for tag_name, tag_data in nation.tags.items():
            if "Improvement Income" not in tag_data:
                continue
            for improvement_name, resource_data in tag_data["Improvement Income"].items():
                if improvement_name != self.name:
                    continue
                for resource_name, income_modifier in resource_data.items():
                    improvement_income_dict[resource_name]["Income"] += income_modifier
        
        # get income multiplier modifiers from tags
        for tag_name, tag_data in nation.tags.items():
            if "Improvement Income Multiplier" not in tag_data:
                continue
            for improvement_name, resource_data in tag_data["Improvement Income Multiplier"].items():
                if improvement_name != self.name:
                    continue
                for resource_name, income_modifier in resource_data.items():
                    improvement_income_dict[resource_name]["Income Multiplier"] += income_modifier

        # get capital resource if able
        # tba - find a way to not hard code this check
        if self.name == "Capital" and region.resource != "Empty":
            match region.resource:
                case "Coal":
                    if 'Coal Mining' in nation.completed_research:
                        improvement_income_dict[region.resource]["Income"] += 1
                case "Oil":
                    if 'Oil Drilling' in nation.completed_research:
                        improvement_income_dict[region.resource]["Income"] += 1
                case "Basic Materials":
                    improvement_income_dict[region.resource]["Income"] += 1
                case "Common Metals":
                    if 'Metal Extraction' in nation.completed_research:
                        improvement_income_dict[region.resource]["Income"] += 1
                case "Advanced Metals":
                    if 'Metallurgy' in nation.completed_research:
                        improvement_income_dict[region.resource]["Income"] += 1
                case "Uranium":
                    if 'Uranium Mining' in nation.completed_research:
                        improvement_income_dict[region.resource]["Income"] += 1
                case "Rare Earth Elements":
                    if 'Rare Earth Mining' in nation.completed_research:
                        improvement_income_dict[region.resource]["Income"] += 1
        
        # calculate final income
        final_yield_dict = {}
        for resource_name in improvement_income_dict:
            final_yield = improvement_income_dict[resource_name]["Income"] * improvement_income_dict[resource_name]["Income Multiplier"]
            final_yield_dict[resource_name] = final_yield

        return final_yield_dict
        

    # combat methods
    ################################################################################

    def is_hostile(self, other_player_id: int) -> bool:
        """
        Determines if this improvement is hostile to the given player_id.

        Params:
            other_player_id (int): player_id to compare to
        
        Returns:
            bool: True if this improvement is hostile to provided player_id. False otherwise.
        """

        # regions without an improvement cannot have a hostile improvement
        if self.name is None:
            return False
        
        # improvements with no health can never be hostile
        if self.health == 99 or self.health == 0:
            return False

        # defensive improvements in a region that is owned by you and is unoccupied is never hostile
        if self.owner_id == other_player_id and self.occupier_id == 0:
            return False
        # defensive improvements in a region you don't own are not hostile under the following conditions
        elif self.owner_id != other_player_id:
            # you already occupy the region
            if other_player_id != 0 and self.occupier_id == other_player_id:
                return False
        
        return True

    

import json

from app import core

class Improvement:

    def __init__(self, region_id: str, game_id: str):
        """
        Initializes improvement class. Calls load_attributes() to load data from game files.

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
        
        from app.region import Region
        
        # check if game id is valid
        regdata_filepath = f'gamedata/{self.game_id}/regdata.json'
        try:
            with open(regdata_filepath, 'r') as json_file:
                regdata_dict = json.load(json_file)
        except FileNotFoundError:
            print(f"Error: Unable to locate {regdata_filepath} during Region class initialization.")

        # check if region id is valid
        try:
            improvement_data = regdata_dict[self.region_id]["improvementData"]
        except KeyError:
            print(f"Error: {self.region_id} not recognized during Region class initialization.")

        # set attributes now that all checks have passed
        self.data = improvement_data
        self.regdata_filepath = regdata_filepath
        self.name = self.data["name"]
        self.health = self.data["health"]
        self.turn_timer = self.data["turnTimer"]
        improvement_data_dict = core.get_scenario_dict(self.game_id, "Improvements")
        if self.name is not None:
            self.hit_value = improvement_data_dict[self.name]["Combat Value"]
        else:
            self.hit_value = None
        region_obj = Region(self.region_id, self.game_id)
        self.owner_id = region_obj.owner_id
        self.occupier_id = region_obj.occupier_id

    def _save_changes(self) -> None:
        """
        Saves changes made to Improvement object to game files.
        """
        with open(self.regdata_filepath, 'r') as json_file:
            regdata_dict = json.load(json_file)
        self.data["name"] = self.name
        self.data["health"] = self.health
        self.data["turnTimer"] = self.turn_timer
        regdata_dict[self.region_id]["improvementData"] = self.data
        with open(self.regdata_filepath, 'w') as json_file:
            json.dump(regdata_dict, json_file, indent=4)
    
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
        if self.name == 'Strip Mine' and 'Open Pit Mining' in player_research:
            self.set_turn_timer(4)
        elif self.name == 'Strip Mine':
            self.set_turn_timer(8)
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

    

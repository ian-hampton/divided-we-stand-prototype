import json

from app import core

class Improvement:

    def __init__(self, region_id: str, game_id: str):
        
        # check if game id is valid
        regdata_filepath = f'gamedata/{game_id}/regdata.json'
        try:
            with open(regdata_filepath, 'r') as json_file:
                regdata_dict = json.load(json_file)
        except FileNotFoundError:
            print(f"Error: Unable to locate {regdata_filepath} during Region class initialization.")

        # check if region id is valid
        try:
            improvement_data = regdata_dict[region_id]["improvementData"]
        except KeyError:
            print(f"Error: {region_id} not recognized during Region class initialization.")

        # set attributes now that all checks have passed
        self.region_id = region_id
        self.data = improvement_data
        self.game_id = game_id
        self.regdata_filepath = regdata_filepath

    def _save_changes(self) -> None:
        '''
        Saves changes made to Improvement object to game files.
        '''
        with open(self.regdata_filepath, 'r') as json_file:
            regdata_dict = json.load(json_file)
        regdata_dict[self.region_id]["improvementData"] = self.data
        with open(self.regdata_filepath, 'w') as json_file:
            json.dump(regdata_dict, json_file, indent=4)

    def name(self) -> str:
        '''
        Returns the improvement name.
        Returns None if no improvement is present.
        '''
        return self.data["name"]
    
    def health(self) -> int:
        '''
        Returns the improvement health.
        Returns 99 if the improvement has no health bar.
        '''
        return self.data["health"]
    
    def turn_timer(self) -> int:
        '''
        Returns the improvement health.
        Returns 99 if the improvement has no health bar.
        '''
        return self.data["turnTimer"]
    
    def decrease_timer(self) -> None:
        '''
        Decreases improvement turn timer by one.
        '''
        if self.data["turnTimer"] != 99:
            self.data["turnTimer"] -= 1
            self._save_changes()

    def clear(self) -> None:
        '''
        Removes the improvement in a region.
        '''
        self.data["name"] = None
        self.data["health"] = 99
        self.data["turnTimer"] = 99
        self._save_changes()

    # basic methods
    ################################################################################

    def set_improvement(self, improvement_name: str, health=0) -> None:
        '''
        Changes the improvement in a region.
        
        :param improvement_name: Name of improvement.
        :param health: Initial improvement health. Default is full health.
        '''
        improvement_data_dict = core.get_scenario_dict(self.game_id, "Improvements")
        self.clear()
        self.data["name"] = improvement_name
        if health == 0:
            self.data["health"] = improvement_data_dict[improvement_name]["Health"]
        else:
            self.data["health"] == health
        self._save_changes()

    def heal(self, health_count: int) -> None:
        '''
        Heals improvement by x health.
        Will not heal beyond max health value.
        '''
        improvement_data_dict = core.get_scenario_dict(self.game_id, "Improvements")
        current_health = self.health()
        max_health = improvement_data_dict[self.name()]["Health"]
        current_health += health_count
        if current_health > max_health:
            current_health = max_health
        self.data["health"] = current_health
        self._save_changes()

    

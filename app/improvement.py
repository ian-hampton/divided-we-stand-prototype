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

    def set_improvement(self, improvement_name: str) -> None:
        '''
        Changes the improvement in a region.
        '''
        improvement_data_dict = core.get_scenario_dict(self.game_id, "Improvements")
        self.data["name"] = improvement_name
        self.data["health"] = improvement_data_dict[improvement_name]["Health"]
        self._save_changes()
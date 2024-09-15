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
    
    def owner_id(self) -> int:
        '''
        Returns the player_id of the unit owner.
        '''
        return self.data["ownerID"]
    
    def abbrev(self) -> str:
        '''
        Returns the improvement name abbreviation.
        Returns None if no improvement is present.
        '''
        unit_data_dict = core.get_scenario_dict(self.game_id, "Units")
        unit_name = self.data["name"]
        if unit_name is not None:
            return unit_data_dict[unit_name]["Abbreviation"]
        else:
            return None
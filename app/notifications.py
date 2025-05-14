import json
import os

class Notifications:

    def __init__(self, game_id: str):

        gamedata_filepath = f'gamedata/{game_id}/gamedata.json'
        
        if os.path.exists(gamedata_filepath):
            self.game_id: str = game_id
            self._reload()
        else:
            raise FileNotFoundError(f"Error: Unable to locate {gamedata_filepath} during notification class initialization.")

    def __iter__(self):
        return iter(self.ntf_dict.items()) 

    def _reload(self) -> None:
        
        gamedata_filepath = f'gamedata/{self.game_id}/gamedata.json'
        with open(gamedata_filepath, 'r') as json_file:
            gamedata_dict = json.load(json_file)

        self.ntf_dict: dict = gamedata_dict["notifications"]

    def _save_changes(self) -> None:
        """
        Saves Notifications to gamedata.json.
        """
        
        gamedata_filepath = f'gamedata/{self.game_id}/gamedata.json'
        with open(gamedata_filepath, 'r') as json_file:
            gamedata_dict = json.load(json_file)

        gamedata_dict["notifications"] = self.ntf_dict

        with open(gamedata_filepath, 'w') as json_file:
            json.dump(gamedata_dict, json_file, indent=4)

    def append(self, string: str, priority: int) -> None:
        """
        Adds a new string to Notifications.
        """
        self._reload()
        self.ntf_dict[string] = priority
        self._save_changes()

    def clear(self) -> None:
        """
        Clears Notifications.
        """
        self.ntf_dict = {}
        self._save_changes()
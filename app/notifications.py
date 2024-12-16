import json
from json.decoder import JSONDecodeError

class Notifications:

    def __init__(self, game_id: str):
        
        # check if game id is valid
        gamedata_filepath = f'gamedata/{game_id}/gamedata.json'
        try:
            with open(gamedata_filepath, 'r') as json_file:
                gamedata_dict = json.load(json_file)
        except FileNotFoundError:
            print(f"Error: Unable to locate {gamedata_filepath} during NotificationsList class initialization.")
        except JSONDecodeError:
            print(f"Error: {gamedata_filepath} is not a valid JSON file. Initializing with empty data.")

        # set attributes
        self.game_id: str = game_id
        self.gamedata_filepath = gamedata_filepath
        self.ntf_dict: dict = gamedata_dict["notifications"]

    def __iter__(self):
        return iter(self.ntf_dict.items()) 


    # private
    ################################################################################

    def _save_changes(self) -> None:
        """
        Saves Notifications to gamedata.json.
        """
        
        with open(self.gamedata_filepath, 'r') as json_file:
            gamedata_dict = json.load(json_file)

        gamedata_dict["notifications"] = self.ntf_dict

        with open(self.gamedata_filepath, 'w') as json_file:
            json.dump(gamedata_dict, json_file, indent=4)
    

    # public
    ################################################################################

    def append(self, string: str, priority: int) -> None:
        """
        Adds a new string to Notifications.
        """
        self.ntf_dict[string] = priority
        self._save_changes()

    def clear(self) -> None:
        """
        Clears Notifications.
        """
        self.ntf_dict = {}
        self._save_changes()
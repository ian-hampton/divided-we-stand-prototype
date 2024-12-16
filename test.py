import json
game_id = "game1"

gamedata_filepath = f'gamedata/{game_id}/gamedata.json'
gamedata_dict = {}
gamedata_dict["alliances"] = {}
gamedata_dict["notifications"] = {}
gamedata_dict["victoryConditionCompleted"] = {}
with open(gamedata_filepath, 'w') as json_file:
    json.dump(gamedata_dict, json_file, indent=4)
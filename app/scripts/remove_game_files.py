import json
import shutil

with open("active_games.json", 'r') as json_file:
    active_games_dict = json.load(json_file)

game_id = input("Enter Game ID: ")

if game_id in active_games_dict:
    shutil.rmtree(f"gamedata/{game_id}")
    del active_games_dict[game_id]
import os
import sys
import json

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
sys.path.append(parent_dir)
os.chdir(parent_dir)

from app.map import GameMaps
from app.region import Region
from app.improvement import Improvement
from app.unit import Unit

# This script tests region coloring and unit/improvement placement by outputting a fully populated map.
# Last updated 5/22/2025

# STEPS TO USE
# 1. Create a new game called "map code test". Select the map you want to test from the dropdown.
# 2. Complete the setup. The nation color of player #1 will be the color that is tested.
# 3. Run this script. Check gamedata directory for results.

print("Running...")

GAME_ID = None
with open('active_games.json', 'r') as json_file:
    active_games_dict = json.load(json_file)
for game_id, game_data in active_games_dict.items():
    if game_data["Game Name"] == "map code test":
        GAME_ID = game_id
        break

if GAME_ID is None:
    raise Exception

with open(f"gamedata/{GAME_ID}/regdata.json", 'r') as json_file:
    regdata_dict = json.load(json_file)
for region_id in regdata_dict.keys():
    region = Region(region_id, GAME_ID)
    region.data.owner_id = 1
    region._save_changes()
for region_id in regdata_dict.keys():
    improvement = Improvement(region_id, GAME_ID)
    improvement.set_improvement("Capital")
for region_id in regdata_dict.keys():
    unit = Unit(region_id, GAME_ID)
    unit.set_unit("Infantry", "1")

maps = GameMaps(GAME_ID)
maps.update_all()
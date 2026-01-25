"""
File: base.py
Author: Ian Hampton
Created Date: 22nd May 2025

This script tests region coloring and unit/improvement placement by outputting a fully populated map.

Steps:
1. Create a new game called "map code test". Select the map you want to test from the dropdown.
2. Complete the setup. The nation color of player #1 will be the color that is tested.
3. Run this script. Check gamedata directory for results.
"""

import os
import sys
import json

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
sys.path.append(parent_dir)
os.chdir(parent_dir)

from app.game.games import Games
from app.scenario.scenario import ScenarioInterface as SD
from app.map import GameMaps
from app.nation.nations import Nations
from app.region.regions import Regions

print("Running...")

for game in Games:
    if game.name == "map code test":
        GAME_ID = game.id
        break
if GAME_ID is None:
    raise Exception

SD.load(GAME_ID)
Nations.load(GAME_ID)
Regions.initialize(GAME_ID)

for region in Regions:
    region.data.owner_id = 1
    region.improvement.set("Capital")
    region.unit.set("Infantry", "TEST", 0, "1")

GameMaps(GAME_ID).update_all()
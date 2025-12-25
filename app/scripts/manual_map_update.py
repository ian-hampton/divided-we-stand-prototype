import os
import sys

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
sys.path.append(parent_dir)
os.chdir(parent_dir)

from app.game.games import Games
from app.scenario.scenario import ScenarioInterface as SD
from app.map import GameMaps
from app.region.regions import Regions
from app.nation.nations import Nations

GAME_ID = "game1"

game = Games.load(GAME_ID)
SD.load(GAME_ID)
Regions.initialize(GAME_ID)
Nations.load(GAME_ID)

print(f"Manually updating maps for game {GAME_ID}...")
maps = GameMaps(GAME_ID)
maps.update_all()
"""
File: test_movement.py
Author: Ian Hampton
Created Date: 24th January 2026
"""

import unittest
from unittest.mock import patch

import base

from app.scenario.scenario import ScenarioInterface as SD
from app.alliance.alliances import Alliances
from app.region.regions import Regions
from app.nation.nations import Nations
from app.notifications import Notifications
from app.truce.truces import Truces
from app.war.wars import Wars

GAME_ID = "HrQyxUeblAMjTJbTrxsp"
GAMEDATA_FILE = "tests/mock-files/gamedata.json"
REGDATA_FILE = "tests/mock-files/regdata.json"

class TestHealing(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """
        Initialize all dataclasses with test data. Required in order for tests to work!
        """
        from app.game.games import Games
        SD.load(GAME_ID)

        with patch.object(Alliances, "_gamedata_path", return_value=str(GAMEDATA_FILE)):
            Alliances.load(GAME_ID)

        with patch.object(Regions, "_regdata_path", return_value=str(REGDATA_FILE)):
            Regions.initialize(GAME_ID)

        with patch.object(Nations, "_gamedata_path", return_value=str(GAMEDATA_FILE)):
            Nations.load(GAME_ID)

        with patch.object(Notifications, "_gamedata_path", return_value=str(GAMEDATA_FILE)):
            Notifications.load(GAME_ID)

        with patch.object(Truces, "_gamedata_path", return_value=str(GAMEDATA_FILE)):
            Truces.load(GAME_ID)

        with patch.object(Wars, "_gamedata_path", return_value=str(GAMEDATA_FILE)):
            Wars.load(GAME_ID)

    def setUp(self):
        with patch.object(Regions, "_regdata_path", return_value=str(REGDATA_FILE)):
            Regions.initialize(GAME_ID)

    def test_movement_order(self):
        """
        Test movement order for correctness. Copy-pasted from movement action code.
        """
        from app.game.games import Games
        game = Games.load(GAME_ID)

        nations_moving_units = {
            "3": {},
            "4": {}
        }
        
        for nation in Nations:
            if nation.id in nations_moving_units:
                nations_moving_units[nation.id] = {
                    "Count": nation.get_used_mc(),
                    "Mobility": sum(1 for region in Regions if region.unit.owner_id == nation.id and region.unit.movement > 1),
                    "XP": sum(region.unit.xp for region in Regions if region.unit.owner_id == nation.id),
                    "Economy": float(nation.records.net_income[-1])
                }
        sorted_nations = sorted(nations_moving_units.items(), key=lambda item: (item[1]["Count"], -item[1]["Mobility"], -item[1]["XP"], -item[1]["Economy"]))

        assert sorted_nations[0][0] == "4"
        assert sorted_nations[1][0] == "3"
        
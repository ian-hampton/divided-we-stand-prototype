"""
File: test_combat.py
Author: Ian Hampton
Created Date: 2nd January 2026
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

from app.actions import WarAction, resolve_war_actions, UnitMoveAction, resolve_unit_move_actions

if __name__ == "__main__":
    unittest.main()

GAME_ID = "HrQyxUeblAMjTJbTrxsp"
GAMEDATA_FILE = "tests/mock-files/gamedata.json"
REGDATA_FILE = "tests/mock-files/regdata.json"

class TestCombat(unittest.TestCase):

    def test_initialize(self):
        """
        Initialize all dataclasses with test data.
        Required in order for tests to work!
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

    def test_war_declaration(self):
        """
        Need to intitialize a war so that we can test combat.
        """
        animosity_war_action = WarAction(GAME_ID, "4", "War Nation C using Animosity")
        assert animosity_war_action.is_valid() == True
        assert animosity_war_action.game_id == GAME_ID
        assert animosity_war_action.id == "4"
        assert animosity_war_action.target_nation == "Nation C"
        assert animosity_war_action.war_justification == "Animosity"
"""
File: test_action_make
Author: Ian Hampton
Created Date: 28th January 2026

Comprehensive series of unit tests for the remove improvement action.
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

class TestRemoveImprovement(unittest.TestCase):

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
        """
        Setup code for each individual test.
        """
        with patch.object(Nations, "_gamedata_path", return_value=str(GAMEDATA_FILE)):
            Nations.load(GAME_ID)
        with patch.object(Regions, "_regdata_path", return_value=str(REGDATA_FILE)):
            Regions.initialize(GAME_ID)

    def test_simple(self):
        """
        Simple removal action. Should pass.
        """
        from app.actions import ImprovementRemoveAction, resolve_improvement_remove_actions

        REGION_ID = "INEMP"

        # create and verify action
        a1 = ImprovementRemoveAction(GAME_ID, "4", f"Remove {REGION_ID}")
        assert a1.is_valid() == True
        assert a1.game_id == GAME_ID
        assert a1.id == "4"
        assert a1.target_region == REGION_ID

        # check nation
        nation = Nations.get("4")
        assert nation.improvement_counts["City"] == 3

        # check region
        region = Regions.load(REGION_ID)
        assert region.improvement.name == "City"
        assert region.improvement.health == 6

        # execute actions
        resolve_improvement_remove_actions(GAME_ID, [a1])

        # test nation
        assert f"Removed improvement in region {REGION_ID}." in nation.action_log
        assert nation.improvement_counts["City"] == 2

        # test region
        assert region.improvement.name == None
        assert region.improvement.health == 99

    def test_bad_region(self):
        """
        Removal action should fail due to improper region ID.
        """
        from app.actions import ImprovementRemoveAction, resolve_improvement_remove_actions

        REGION_ID = "NTCAS"

        # create and verify action
        a1 = ImprovementRemoveAction(GAME_ID, "4", f"Remove {REGION_ID}")
        assert a1.is_valid() == True
        assert a1.game_id == GAME_ID
        assert a1.id == "4"
        assert a1.target_region == REGION_ID

        # check region
        region = Regions.load(REGION_ID)
        assert region.improvement.name == "Coal Mine"
        assert region.improvement.health == 99

        # execute actions
        resolve_improvement_remove_actions(GAME_ID, [a1])

        # test nation
        nation = Nations.get("4")
        assert f"Failed to remove {region.improvement.name} in region {REGION_ID}. You do not own or control this region." in nation.action_log

        # test region
        assert region.improvement.name == "Coal Mine"
        assert region.improvement.health == 99

    def test_blocked_by_capital(self):
        """
        Removal action should fail if target region has a Capital.
        """
        from app.actions import ImprovementRemoveAction, resolve_improvement_remove_actions

        REGION_ID = "ALBUQ"

        # create and verify action
        a1 = ImprovementRemoveAction(GAME_ID, "4", f"Remove {REGION_ID}")
        assert a1.is_valid() == True
        assert a1.game_id == GAME_ID
        assert a1.id == "4"
        assert a1.target_region == REGION_ID

        # check region
        region = Regions.load(REGION_ID)
        assert region.improvement.name == "Capital"
        assert region.improvement.health == 12

        # execute actions
        resolve_improvement_remove_actions(GAME_ID, [a1])

        # test nation
        nation = Nations.get("4")
        assert f"Failed to remove {region.improvement.name} in region {REGION_ID}. You cannot remove a Capital improvement." in nation.action_log

        # test region
        assert region.improvement.name == "Capital"
        assert region.improvement.health == 12
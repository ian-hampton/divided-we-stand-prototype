"""
File: test_action_unit_disband.py
Author: Ian Hampton
Created Date: 31st January 2026

Comprehensive series of unit tests for the disband unit action.
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

class TestDisbandUnit(unittest.TestCase):

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
        Simple unit disband action. Should pass.
        """
        from app.actions import UnitDisbandAction, resolve_unit_disband_actions

        REGION_ID = "FRESN"

        # create and verify action
        a1 = UnitDisbandAction(GAME_ID, "4", f"Disband {REGION_ID}")
        assert a1.is_valid() == True
        assert a1.game_id == GAME_ID
        assert a1.id == "4"
        assert a1.target_region == REGION_ID

        # check region
        region = Regions.load(REGION_ID)
        assert region.data.owner_id == "4"
        assert region.data.occupier_id == "0"
        assert region.improvement.name == "Industrial Zone"
        assert region.improvement.health == 99
        assert region.unit.name == "Infantry"
        assert region.unit.health == 6
        assert region.unit.owner_id == "4"

        # resolve deployment actions
        resolve_unit_disband_actions(GAME_ID, [a1])

        # test region
        assert region.data.owner_id == "4"
        assert region.data.occupier_id == "0"
        assert region.improvement.name == "Industrial Zone"
        assert region.improvement.health == 99
        assert region.unit.name == None
        assert region.unit.health == 99
        assert region.unit.owner_id == "0"

        # test nation
        nation = Nations.get("4")
        assert f"Disbanded unit in region {REGION_ID}." in nation.action_log
        nation.update_military_capacity()
        assert nation.get_used_mc() == 5

    def test_bad_region(self):
        """
        Unit disband action fails due to not having a unit in the target region.
        """
        from app.actions import UnitDisbandAction, resolve_unit_disband_actions

        REGION_ID = "KANSA"

        # create and verify action
        a1 = UnitDisbandAction(GAME_ID, "4", f"Disband {REGION_ID}")
        assert a1.is_valid() == True
        assert a1.game_id == GAME_ID
        assert a1.id == "4"
        assert a1.target_region == REGION_ID

        # check region
        region = Regions.load(REGION_ID)
        assert region.data.owner_id == "0"
        assert region.data.occupier_id == "0"
        assert region.improvement.name == None
        assert region.improvement.health == 99
        assert region.unit.name == None
        assert region.unit.health == 99
        assert region.unit.owner_id == "0"

        # resolve deployment actions
        resolve_unit_disband_actions(GAME_ID, [a1])

        # test region
        assert region.data.owner_id == "0"
        assert region.data.occupier_id == "0"
        assert region.data.owner_id == "0"
        assert region.data.occupier_id == "0"
        assert region.improvement.name == None
        assert region.improvement.health == 99
        assert region.unit.name == None
        assert region.unit.health == 99
        assert region.unit.owner_id == "0"

        # test nation
        nation = Nations.get("4")
        assert f"Failed to disband {region.unit.name} in region {REGION_ID}. You do not own a unit in this region." in nation.action_log
        nation.update_military_capacity()
        assert nation.get_used_mc() == 6
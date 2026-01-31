"""
File: test_action_unit_deploy.py
Author: Ian Hampton
Created Date: 31st January 2026

Comprehensive series of unit tests for the deploy unit action.
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

class TestDeployUnit(unittest.TestCase):

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
        
        # reload game data
        with patch.object(Nations, "_gamedata_path", return_value=str(GAMEDATA_FILE)):
            Nations.load(GAME_ID)
        with patch.object(Regions, "_regdata_path", return_value=str(REGDATA_FILE)):
            Regions.initialize(GAME_ID)
        
        # set nation data
        nation = Nations.get("3")
        assert nation.get_used_mc() == 6
        nation._resources["Military Capacity"]["max"] = "100.00"    # force military capacity limit to be higher
        assert nation.get_max_mc() == 100
        nation.update_stockpile("Dollars", 100)
        nation.update_stockpile("Political Power", 50)
        nation.update_stockpile("Research", 50)
        nation.update_stockpile("Food", 50)
        nation.update_stockpile("Coal", 50)
        nation.update_stockpile("Oil", 50)
        nation.update_stockpile("Basic Materials", 50)
        nation.update_stockpile("Common Metals", 50)
        nation.update_stockpile("Advanced Metals", 50)
        nation.update_stockpile("Uranium", 50)
        nation.update_stockpile("Rare Earth Elements", 50)

    def test_simple(self):
        """
        Simple unit deployment action for an infantry. Should pass.
        """
        from app.actions import UnitDeployAction, resolve_unit_deployment_actions

        UNIT_NAME = "Infantry"
        REGION_ID = "COLBA"

        # create and verify action
        a1 = UnitDeployAction(GAME_ID, "3", f"Deploy {UNIT_NAME} {REGION_ID}")
        assert a1.is_valid() == True
        assert a1.game_id == GAME_ID
        assert a1.id == "3"
        assert a1.unit_name == UNIT_NAME
        assert a1.target_region == REGION_ID

        # check region
        region = Regions.load(REGION_ID)
        assert region.data.owner_id == "3"
        assert region.data.occupier_id == "0"
        assert region.improvement.name == None
        assert region.improvement.health == 99
        assert region.unit.name == None
        assert region.unit.health == 99
        assert region.unit.owner_id == "0"

        # resolve deployment actions
        resolve_unit_deployment_actions(GAME_ID, [a1])

        # test region
        assert region.data.owner_id == "3"
        assert region.data.occupier_id == "0"
        assert region.improvement.name == None
        assert region.improvement.health == 99
        assert region.unit.name == "Infantry"
        assert region.unit.health == 6
        assert region.unit.owner_id == "3"

        # test nation
        nation = Nations.get("3")
        costs_str = "5 dollars and 5 basic materials"
        assert f"Deployed {UNIT_NAME} in region {REGION_ID} for {costs_str}." in nation.action_log
        nation.update_military_capacity()
        assert nation.get_used_mc() == 7

        # test resources
        assert nation.get_stockpile("Dollars") == "95.00"
        assert nation.get_stockpile("Political Power") == "50.00"
        assert nation.get_stockpile("Research") == "50.00"
        assert nation.get_stockpile("Food") == "50.00"
        assert nation.get_stockpile("Coal") == "50.00"
        assert nation.get_stockpile("Oil") == "50.00"
        assert nation.get_stockpile("Basic Materials") == "45.00"
        assert nation.get_stockpile("Common Metals") == "50.00"
        assert nation.get_stockpile("Advanced Metals") == "50.00"
        assert nation.get_stockpile("Uranium") == "50.00"
        assert nation.get_stockpile("Rare Earth Elements") == "50.00"

    def test_xp_transfer(self):
        """
        Simple unit deployment action with an XP transfer. Should pass.
        """
        from app.actions import UnitDeployAction, resolve_unit_deployment_actions

        UNIT_NAME = "Infantry"
        REGION_ID = "OMAHA"

        # create and verify action
        a1 = UnitDeployAction(GAME_ID, "3", f"Deploy {UNIT_NAME} {REGION_ID}")
        assert a1.is_valid() == True
        assert a1.game_id == GAME_ID
        assert a1.id == "3"
        assert a1.unit_name == UNIT_NAME
        assert a1.target_region == REGION_ID

        # check region
        region = Regions.load(REGION_ID)
        region.unit.add_xp(10)
        assert region.data.owner_id == "3"
        assert region.data.occupier_id == "0"
        assert region.improvement.name == "Research Laboratory"
        assert region.improvement.health == 99
        assert region.unit.name == "Infantry"
        assert region.unit.health == 6
        assert region.unit.owner_id == "3"
        assert region.unit.xp == 10

        # resolve deployment actions
        resolve_unit_deployment_actions(GAME_ID, [a1])

        # test region
        assert region.data.owner_id == "3"
        assert region.data.occupier_id == "0"
        assert region.improvement.name == "Research Laboratory"
        assert region.improvement.health == 99
        assert region.unit.name == "Infantry"
        assert region.unit.health == 6
        assert region.unit.owner_id == "3"
        assert region.unit.xp == 5    # only 50% of the XP should carry over

        # test nation
        nation = Nations.get("3")
        costs_str = "5 dollars and 5 basic materials"
        assert f"Deployed {UNIT_NAME} in region {REGION_ID} for {costs_str}." in nation.action_log
        nation.update_military_capacity()
        assert nation.get_used_mc() == 6

        # test resources
        assert nation.get_stockpile("Dollars") == "95.00"
        assert nation.get_stockpile("Political Power") == "50.00"
        assert nation.get_stockpile("Research") == "50.00"
        assert nation.get_stockpile("Food") == "50.00"
        assert nation.get_stockpile("Coal") == "50.00"
        assert nation.get_stockpile("Oil") == "50.00"
        assert nation.get_stockpile("Basic Materials") == "45.00"
        assert nation.get_stockpile("Common Metals") == "50.00"
        assert nation.get_stockpile("Advanced Metals") == "50.00"
        assert nation.get_stockpile("Uranium") == "50.00"
        assert nation.get_stockpile("Rare Earth Elements") == "50.00"

    def test_enemy_region(self):
        """
        Unit deployment action that should fail due to being in hostile territory.
        """
        from app.actions import UnitDeployAction, resolve_unit_deployment_actions

        UNIT_NAME = "Infantry"
        REGION_ID = "STOCK"

        # create and verify action
        a1 = UnitDeployAction(GAME_ID, "3", f"Deploy {UNIT_NAME} {REGION_ID}")
        assert a1.is_valid() == True
        assert a1.game_id == GAME_ID
        assert a1.id == "3"
        assert a1.unit_name == UNIT_NAME
        assert a1.target_region == REGION_ID

        # check region
        region = Regions.load(REGION_ID)
        assert region.data.owner_id == "4"
        assert region.data.occupier_id == "0"
        assert region.improvement.name == None
        assert region.improvement.health == 99
        assert region.unit.name == None
        assert region.unit.health == 99
        assert region.unit.owner_id == "0"

        # resolve deployment actions
        resolve_unit_deployment_actions(GAME_ID, [a1])

        # test region
        assert region.data.owner_id == "4"
        assert region.data.occupier_id == "0"
        assert region.improvement.name == None
        assert region.improvement.health == 99
        assert region.unit.name == None
        assert region.unit.health == 99
        assert region.unit.owner_id == "0"

        # test nation
        nation = Nations.get("3")
        assert f"Failed to deploy {UNIT_NAME} in region {REGION_ID}. You do not control this region." in nation.action_log
        nation.update_military_capacity()
        assert nation.get_used_mc() == 6

        # test resources
        assert nation.get_stockpile("Dollars") == "100.00"
        assert nation.get_stockpile("Political Power") == "50.00"
        assert nation.get_stockpile("Research") == "50.00"
        assert nation.get_stockpile("Food") == "50.00"
        assert nation.get_stockpile("Coal") == "50.00"
        assert nation.get_stockpile("Oil") == "50.00"
        assert nation.get_stockpile("Basic Materials") == "50.00"
        assert nation.get_stockpile("Common Metals") == "50.00"
        assert nation.get_stockpile("Advanced Metals") == "50.00"
        assert nation.get_stockpile("Uranium") == "50.00"
        assert nation.get_stockpile("Rare Earth Elements") == "50.00"

    def test_bad_research(self):
        """
        Unit deployment action should fail due to lacking correct technology.
        """
        from app.actions import UnitDeployAction, resolve_unit_deployment_actions

        UNIT_NAME = "Special Forces"
        REGION_ID = "COLBA"

        # create and verify action
        a1 = UnitDeployAction(GAME_ID, "3", f"Deploy {UNIT_NAME} {REGION_ID}")
        assert a1.is_valid() == True
        assert a1.game_id == GAME_ID
        assert a1.id == "3"
        assert a1.unit_name == UNIT_NAME
        assert a1.target_region == REGION_ID

        # check region
        region = Regions.load(REGION_ID)
        assert region.data.owner_id == "3"
        assert region.data.occupier_id == "0"
        assert region.improvement.name == None
        assert region.improvement.health == 99
        assert region.unit.name == None
        assert region.unit.health == 99
        assert region.unit.owner_id == "0"

        # resolve deployment actions
        resolve_unit_deployment_actions(GAME_ID, [a1])

        # test region
        assert region.data.owner_id == "3"
        assert region.data.occupier_id == "0"
        assert region.improvement.name == None
        assert region.improvement.health == 99
        assert region.unit.name == None
        assert region.unit.health == 99
        assert region.unit.owner_id == "0"

        # test nation
        nation = Nations.get("3")
        assert f"Failed to deploy {UNIT_NAME} in region {REGION_ID}. You do not have the required research." in nation.action_log
        nation.update_military_capacity()
        assert nation.get_used_mc() == 6

        # test resources
        assert nation.get_stockpile("Dollars") == "100.00"
        assert nation.get_stockpile("Political Power") == "50.00"
        assert nation.get_stockpile("Research") == "50.00"
        assert nation.get_stockpile("Food") == "50.00"
        assert nation.get_stockpile("Coal") == "50.00"
        assert nation.get_stockpile("Oil") == "50.00"
        assert nation.get_stockpile("Basic Materials") == "50.00"
        assert nation.get_stockpile("Common Metals") == "50.00"
        assert nation.get_stockpile("Advanced Metals") == "50.00"
        assert nation.get_stockpile("Uranium") == "50.00"
        assert nation.get_stockpile("Rare Earth Elements") == "50.00"

    def test_blocked_by_capacity(self):
        """
        Unit deployment should fail due to insufficient military capacity.
        """
        from app.actions import UnitDeployAction, resolve_unit_deployment_actions

        UNIT_NAME = "Infantry"
        REGION_ID = "COLBA"

        # create and verify action
        a1 = UnitDeployAction(GAME_ID, "3", f"Deploy {UNIT_NAME} {REGION_ID}")
        assert a1.is_valid() == True
        assert a1.game_id == GAME_ID
        assert a1.id == "3"
        assert a1.unit_name == UNIT_NAME
        assert a1.target_region == REGION_ID

        # check region
        region = Regions.load(REGION_ID)
        assert region.data.owner_id == "3"
        assert region.data.occupier_id == "0"
        assert region.improvement.name == None
        assert region.improvement.health == 99
        assert region.unit.name == None
        assert region.unit.health == 99
        assert region.unit.owner_id == "0"

        # configure nation
        nation = Nations.get("3")
        nation._resources["Military Capacity"]["max"] = "6.00"

        # resolve deployment actions
        resolve_unit_deployment_actions(GAME_ID, [a1])

        # test region
        assert region.data.owner_id == "3"
        assert region.data.occupier_id == "0"
        assert region.improvement.name == None
        assert region.improvement.health == 99
        assert region.unit.name == None
        assert region.unit.health == 99
        assert region.unit.owner_id == "0"

        # test nation
        assert f"Failed to deploy {UNIT_NAME} in region {REGION_ID}. Insufficient military capacity." in nation.action_log
        nation.update_military_capacity()
        assert nation.get_used_mc() == 6

        # test resources
        assert nation.get_stockpile("Dollars") == "100.00"
        assert nation.get_stockpile("Political Power") == "50.00"
        assert nation.get_stockpile("Research") == "50.00"
        assert nation.get_stockpile("Food") == "50.00"
        assert nation.get_stockpile("Coal") == "50.00"
        assert nation.get_stockpile("Oil") == "50.00"
        assert nation.get_stockpile("Basic Materials") == "50.00"
        assert nation.get_stockpile("Common Metals") == "50.00"
        assert nation.get_stockpile("Advanced Metals") == "50.00"
        assert nation.get_stockpile("Uranium") == "50.00"
        assert nation.get_stockpile("Rare Earth Elements") == "50.00"

    def test_blocked_by_shortage(self):
        """
        Unit deployment should fail due to insufficient resources.
        """
        from app.actions import UnitDeployAction, resolve_unit_deployment_actions

        UNIT_NAME = "Infantry"
        REGION_ID = "COLBA"

        # create and verify action
        a1 = UnitDeployAction(GAME_ID, "3", f"Deploy {UNIT_NAME} {REGION_ID}")
        assert a1.is_valid() == True
        assert a1.game_id == GAME_ID
        assert a1.id == "3"
        assert a1.unit_name == UNIT_NAME
        assert a1.target_region == REGION_ID

        # check region
        region = Regions.load(REGION_ID)
        assert region.data.owner_id == "3"
        assert region.data.occupier_id == "0"
        assert region.improvement.name == None
        assert region.improvement.health == 99
        assert region.unit.name == None
        assert region.unit.health == 99
        assert region.unit.owner_id == "0"

        # configure nation
        nation = Nations.get("3")
        nation.update_stockpile("Basic Materials", 0, overwrite=True)

        # resolve deployment actions
        resolve_unit_deployment_actions(GAME_ID, [a1])

        # test region
        assert region.data.owner_id == "3"
        assert region.data.occupier_id == "0"
        assert region.improvement.name == None
        assert region.improvement.health == 99
        assert region.unit.name == None
        assert region.unit.health == 99
        assert region.unit.owner_id == "0"

        # test nation
        assert f"Failed to deploy {UNIT_NAME} in region {REGION_ID}. Insufficient resources." in nation.action_log
        nation.update_military_capacity()
        assert nation.get_used_mc() == 6

        # test resources
        assert nation.get_stockpile("Dollars") == "100.00"
        assert nation.get_stockpile("Political Power") == "50.00"
        assert nation.get_stockpile("Research") == "50.00"
        assert nation.get_stockpile("Food") == "50.00"
        assert nation.get_stockpile("Coal") == "50.00"
        assert nation.get_stockpile("Oil") == "50.00"
        assert nation.get_stockpile("Basic Materials") == "0.00"
        assert nation.get_stockpile("Common Metals") == "50.00"
        assert nation.get_stockpile("Advanced Metals") == "50.00"
        assert nation.get_stockpile("Uranium") == "50.00"
        assert nation.get_stockpile("Rare Earth Elements") == "50.00"
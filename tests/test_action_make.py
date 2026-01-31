"""
File: test_action_make
Author: Ian Hampton
Created Date: 28th January 2026

Comprehensive series of unit tests for the make missile action.
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


class TestMakeMissile(unittest.TestCase):

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
        nation.missile_count = 0
        nation.nuke_count = 0
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

    def test_make_standard(self):
        """
        Simple make action for 1 Standard Missile. Should pass.
        """
        from app.actions import MissileMakeAction, resolve_missile_make_actions

        MISSILE_NAME = "Standard Missile"
        MISSILE_QUANTITY = 1

        # create and verify action
        a1 = MissileMakeAction(GAME_ID, "3", f"Make {MISSILE_QUANTITY} {MISSILE_NAME}")
        assert a1.is_valid() == True
        assert a1.game_id == GAME_ID
        assert a1.id == "3"
        assert a1.quantity == MISSILE_QUANTITY
        assert a1.missile_type == MISSILE_NAME

        # set research
        nation = Nations.get("3")
        nation.completed_research["Missile Technology"] = True

        # execute actions
        resolve_missile_make_actions(GAME_ID, [a1])

        # test nation
        assert nation.missile_count == 1
        assert nation.nuke_count == 0
        assert f"Manufactured {MISSILE_QUANTITY} {MISSILE_NAME} for 3 common metals." in nation.action_log

        # test resources
        assert nation.get_stockpile("Dollars") == "100.00"
        assert nation.get_stockpile("Political Power") == "50.00"
        assert nation.get_stockpile("Research") == "50.00"
        assert nation.get_stockpile("Food") == "50.00"
        assert nation.get_stockpile("Coal") == "50.00"
        assert nation.get_stockpile("Oil") == "50.00"
        assert nation.get_stockpile("Basic Materials") == "50.00"
        assert nation.get_stockpile("Common Metals") == "47.00"
        assert nation.get_stockpile("Advanced Metals") == "50.00"
        assert nation.get_stockpile("Uranium") == "50.00"
        assert nation.get_stockpile("Rare Earth Elements") == "50.00"

    def test_make_nuclear(self):
        """
        Simple make action for 3 Nuclear Missiles. Should pass.
        """
        from app.actions import MissileMakeAction, resolve_missile_make_actions

        MISSILE_NAME = "Nuclear Missile"
        MISSILE_QUANTITY = 3

        # create and verify action
        a1 = MissileMakeAction(GAME_ID, "3", f"Make {MISSILE_QUANTITY} {MISSILE_NAME}")
        assert a1.is_valid() == True
        assert a1.game_id == GAME_ID
        assert a1.id == "3"
        assert a1.quantity == MISSILE_QUANTITY
        assert a1.missile_type == MISSILE_NAME

        # set research
        nation = Nations.get("3")
        nation.completed_research["Missile Technology"] = True
        nation.completed_research["Armor-Piercing Warheads"] = True
        nation.completed_research["Nuclear Warhead"] = True

        # execute actions
        resolve_missile_make_actions(GAME_ID, [a1])

        # test nation
        assert nation.missile_count == 0
        assert nation.nuke_count == 3
        assert f"Manufactured {MISSILE_QUANTITY} {MISSILE_NAME} for 6 advanced metals, 6 uranium and 6 rare earth elements." in nation.action_log

        # test resources
        assert nation.get_stockpile("Dollars") == "100.00"
        assert nation.get_stockpile("Political Power") == "50.00"
        assert nation.get_stockpile("Research") == "50.00"
        assert nation.get_stockpile("Food") == "50.00"
        assert nation.get_stockpile("Coal") == "50.00"
        assert nation.get_stockpile("Oil") == "50.00"
        assert nation.get_stockpile("Basic Materials") == "50.00"
        assert nation.get_stockpile("Common Metals") == "50.00"
        assert nation.get_stockpile("Advanced Metals") == "44.00"
        assert nation.get_stockpile("Uranium") == "44.00"
        assert nation.get_stockpile("Rare Earth Elements") == "44.00"

    def test_bad_research(self):
        """
        Simple make action that should fail due to lacking technology.
        """
        from app.actions import MissileMakeAction, resolve_missile_make_actions

        MISSILE_NAME = "Standard Missile"
        MISSILE_QUANTITY = 1

        # create and verify action
        a1 = MissileMakeAction(GAME_ID, "3", f"Make {MISSILE_QUANTITY} {MISSILE_NAME}")
        assert a1.is_valid() == True
        assert a1.game_id == GAME_ID
        assert a1.id == "3"
        assert a1.quantity == MISSILE_QUANTITY
        assert a1.missile_type == MISSILE_NAME

        # set research
        nation = Nations.get("3")

        # execute actions
        resolve_missile_make_actions(GAME_ID, [a1])

        # test nation
        assert nation.missile_count == 0
        assert nation.nuke_count == 0
        assert f"Failed to make {MISSILE_QUANTITY} {MISSILE_NAME}. You do not have the required research." in nation.action_log

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
        Simple make action that should fail due to lack of resources.
        """
        from app.actions import MissileMakeAction, resolve_missile_make_actions

        MISSILE_NAME = "Standard Missile"
        MISSILE_QUANTITY = 4

        # create and verify action
        a1 = MissileMakeAction(GAME_ID, "3", f"Make {MISSILE_QUANTITY} {MISSILE_NAME}")
        assert a1.is_valid() == True
        assert a1.game_id == GAME_ID
        assert a1.id == "3"
        assert a1.quantity == MISSILE_QUANTITY
        assert a1.missile_type == MISSILE_NAME

        # prepare nation
        nation = Nations.get("3")
        nation.completed_research["Missile Technology"] = True
        nation.update_stockpile("Common Metals", 10, overwrite=True)

        # execute actions
        resolve_missile_make_actions(GAME_ID, [a1])

        # test nation
        assert nation.missile_count == 0
        assert nation.nuke_count == 0
        assert f"Failed to make {MISSILE_QUANTITY} {MISSILE_NAME}. Insufficient resources." in nation.action_log

        # test resources
        assert nation.get_stockpile("Dollars") == "100.00"
        assert nation.get_stockpile("Political Power") == "50.00"
        assert nation.get_stockpile("Research") == "50.00"
        assert nation.get_stockpile("Food") == "50.00"
        assert nation.get_stockpile("Coal") == "50.00"
        assert nation.get_stockpile("Oil") == "50.00"
        assert nation.get_stockpile("Basic Materials") == "50.00"
        assert nation.get_stockpile("Common Metals") == "10.00"
        assert nation.get_stockpile("Advanced Metals") == "50.00"
        assert nation.get_stockpile("Uranium") == "50.00"
        assert nation.get_stockpile("Rare Earth Elements") == "50.00"
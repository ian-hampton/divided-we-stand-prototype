"""
File: test_action_war_declare.py
Author: Ian Hampton
Created Date: 29th January 2026

Unit tests for the war declaration actions.
TODO - Not finished. Not entirely comprehensive due to need to input war claims via terminal. Does not test secondary combatants.
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

class TestDeclareWar(unittest.TestCase):

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
        with patch.object(Notifications, "_gamedata_path", return_value=str(GAMEDATA_FILE)):
            Notifications.load(GAME_ID)
        with patch.object(Wars, "_gamedata_path", return_value=str(GAMEDATA_FILE)):
            Wars.load(GAME_ID)

    def test_simple_animosity(self):
        """
        Simple war declaration action using animosity. Should pass.
        """
        from app.actions import WarAction, resolve_war_actions

        # create and verify action
        a1 = WarAction(GAME_ID, "3", "War Nation D using Animosity")
        assert a1.is_valid() == True
        assert a1.game_id == GAME_ID
        assert a1.id == "3"
        assert a1.target_nation == "Nation D"
        assert a1.war_justification == "Animosity"

        # execute actions
        resolve_war_actions(GAME_ID, [a1])

        # fetch war
        war_name = Wars.get_war_name("3", "4")
        assert war_name is not None
        war = Wars.get(war_name)

        # test war
        assert war.start == 33
        assert war.end == 0
        assert war.outcome == "TBD"
        assert "3" in war.combatants
        assert "4" in war.combatants
        assert any(notification[1] == "Nation C declared war on Nation D." for notification in Notifications)

        # test main attacker
        nation_c = Nations.get("3")
        assert "Declared war on Nation D." in nation_c.action_log
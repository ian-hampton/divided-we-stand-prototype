"""
File: test_peace.py
Author: Ian Hampton
Created Date: 27th January 2026

Comprehensive series of unit tests for peace actions.
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

class TestPeace(unittest.TestCase):

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
        from app.actions import WarAction, resolve_war_actions

        # make sure game turn is set to 33 (some tests may change this)
        from app.game.games import Games
        Games.load(GAME_ID).turn = 33

        # reload game data
        with patch.object(Nations, "_gamedata_path", return_value=str(GAMEDATA_FILE)):
            Nations.load(GAME_ID)
        with patch.object(Notifications, "_gamedata_path", return_value=str(GAMEDATA_FILE)):
            Notifications.load(GAME_ID)
        with patch.object(Regions, "_regdata_path", return_value=str(REGDATA_FILE)):
            Regions.initialize(GAME_ID)
        with patch.object(Truces, "_gamedata_path", return_value=str(GAMEDATA_FILE)):
            Truces.load(GAME_ID)
        with patch.object(Wars, "_gamedata_path", return_value=str(GAMEDATA_FILE)):
            Wars.load(GAME_ID)

        from app.actions import WarAction, resolve_war_actions

        # verify war does not exist already
        war_name = Wars.get_war_name("3", "4")
        assert war_name is None

        # create and verify war declaration action
        a1 = WarAction(GAME_ID, "4", "War Nation C using Animosity")
        assert a1.is_valid() == True
        assert a1.game_id == GAME_ID
        assert a1.id == "4"
        assert a1.target_nation == "Nation C"
        assert a1.war_justification == "Animosity"

        # declare war
        resolve_war_actions(GAME_ID, [a1])
        war_name = Wars.get_war_name("3", "4")
        assert war_name is not None
        war = Wars.get(war_name)

        # verify war
        assert war.start == 33
        assert war.outcome == "TBD"
        assert war.attackers.total == 0
        assert war.defenders.total == 0
        attacker = war.get_combatant("4")
        assert attacker.name == "Nation D"
        assert attacker.role == "Main Attacker"
        assert attacker.justification == "Animosity"
        assert attacker.target_id == "3"
        assert attacker.claims == {}
        defender = war.get_combatant("3")
        assert defender.name == "Nation C"
        assert defender.role == "Main Defender"

        # add defender war justification
        defender.justification == "Border Skirmish"
        defender.target_id == "TBD"
        defender.claims == {
            "TOPEK": "4",
            "HAYSK": "4",
            "WICHI": "4"
        }

    def test_white_peace(self):
        """
        White peace occurs when both sides agree. Should pass.
        """
        from app.game.games import Games
        from app.actions import WhitePeaceAction, resolve_peace_actions

        # create and verify peace actions
        a1 = WhitePeaceAction(GAME_ID, "3", "White Peace Nation D")
        assert a1.is_valid() == True
        assert a1.game_id == GAME_ID
        assert a1.id == "3"
        assert a1.target_nation == "Nation D"
        a2 = WhitePeaceAction(GAME_ID, "4", "White Peace Nation C")
        assert a2.is_valid() == True
        assert a2.game_id == GAME_ID
        assert a2.id == "4"
        assert a2.target_nation == "Nation C"

        # load war
        war_name = Wars.get_war_name("3", "4")
        war = Wars.get(war_name)

        # change turn
        Games.load(GAME_ID).turn = 37

        # resolve peace actions
        resolve_peace_actions(GAME_ID, [], [a1, a2])
        
        # check war
        assert war.end == 37
        assert war.outcome == "White Peace"
        
        # check notifications
        assert any(notification[1] == f"{war_name} has ended with a white peace." for notification in Notifications)

        # check that attacker war justification not fullfilled
        nation_c = Nations.get("3")
        for tag_name in nation_c.tags:
            assert tag_name.startswith("Defeated by") == False

        # check that defender war justification not fullfilled
        Regions.load("TOPEK").data.owner_id == "4"
        Regions.load("HAYSK").data.owner_id == "4"
        Regions.load("WICHI").data.owner_id == "4"

    def test_bad_war(self):
        """
        Cannot make peace if you're not at war. Should fail.
        """
        from app.game.games import Games
        from app.actions import WhitePeaceAction, resolve_peace_actions

        # create and verify peace actions
        a1 = WhitePeaceAction(GAME_ID, "2", "White Peace Nation D")
        assert a1.is_valid() == True
        assert a1.game_id == GAME_ID
        assert a1.id == "2"
        assert a1.target_nation == "Nation D"
        a2 = WhitePeaceAction(GAME_ID, "4", "White Peace Nation B")
        assert a2.is_valid() == True
        assert a2.game_id == GAME_ID
        assert a2.id == "4"
        assert a2.target_nation == "Nation B"

        # load war
        war_name = Wars.get_war_name("3", "4")
        war = Wars.get(war_name)

        # change turn
        Games.load(GAME_ID).turn = 37

        # resolve peace actions
        resolve_peace_actions(GAME_ID, [], [a1, a2])
        
        # check war
        assert war.end == 0
        assert war.outcome == "TBD"

        # check action logs
        nation_b = Nations.get("2")
        nation_d = Nations.get("4")
        assert "Failed to surrender to Nation D. You are not at war with that nation." in nation_b.action_log
        assert "Failed to surrender to Nation B. You are not at war with that nation." in nation_d.action_log

        # check that attacker war justification not fullfilled
        nation_c = Nations.get("3")
        for tag_name in nation_c.tags:
            assert tag_name.startswith("Defeated by") == False

        # check that defender war justification not fullfilled
        Regions.load("TOPEK").data.owner_id == "4"
        Regions.load("HAYSK").data.owner_id == "4"
        Regions.load("WICHI").data.owner_id == "4"

    def test_bad_time(self):
        """
        Cannot make peace until at least 4 turns have passed. Should fail.
        """
        from app.game.games import Games
        from app.actions import WhitePeaceAction, resolve_peace_actions

        # create and verify peace actions
        a1 = WhitePeaceAction(GAME_ID, "3", "White Peace Nation D")
        assert a1.is_valid() == True
        assert a1.game_id == GAME_ID
        assert a1.id == "3"
        assert a1.target_nation == "Nation D"
        a2 = WhitePeaceAction(GAME_ID, "4", "White Peace Nation C")
        assert a2.is_valid() == True
        assert a2.game_id == GAME_ID
        assert a2.id == "4"
        assert a2.target_nation == "Nation C"

        # load war
        war_name = Wars.get_war_name("3", "4")
        war = Wars.get(war_name)

        # change turn
        Games.load(GAME_ID).turn = 35

        # resolve peace actions
        resolve_peace_actions(GAME_ID, [], [a1, a2])
        
        # check war
        assert war.end == 0
        assert war.outcome == "TBD"

        # check action logs
        nation_c = Nations.get("3")
        nation_d = Nations.get("4")
        assert "Failed to surrender to Nation D. At least four turns must pass before peace can be made." in nation_c.action_log
        assert "Failed to surrender to Nation C. At least four turns must pass before peace can be made." in nation_d.action_log

        # check that attacker war justification not fullfilled
        for tag_name in nation_c.tags:
            assert tag_name.startswith("Defeated by") == False

        # check that defender war justification not fullfilled
        Regions.load("TOPEK").data.owner_id == "4"
        Regions.load("HAYSK").data.owner_id == "4"
        Regions.load("WICHI").data.owner_id == "4"
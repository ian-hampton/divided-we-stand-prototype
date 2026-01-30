"""
File: test_action_alliance_kick.py
Author: Ian Hampton
Created Date: 30th January 2026

Comprehensive series of unit tests for alliance kick actions.
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

ALLIANCE_NAME = "Test"
ALLIANCE_TYPE = "Non-Aggression Pact"

class TestAllianceKick(unittest.TestCase):

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
        from app.actions import AllianceCreateAction, resolve_alliance_create_actions
        
        # reload game data
        with patch.object(Alliances, "_gamedata_path", return_value=str(GAMEDATA_FILE)):
            Alliances.load(GAME_ID)
        with patch.object(Nations, "_gamedata_path", return_value=str(GAMEDATA_FILE)):
            Nations.load(GAME_ID)
        with patch.object(Notifications, "_gamedata_path", return_value=str(GAMEDATA_FILE)):
            Notifications.load(GAME_ID)

        # create and verify actions
        a1 = AllianceCreateAction(GAME_ID, "3", f"Alliance Create {ALLIANCE_NAME} as {ALLIANCE_TYPE}")
        assert a1.is_valid() == True
        assert a1.game_id == GAME_ID
        assert a1.id == "3"
        assert a1.alliance_name == ALLIANCE_NAME
        assert a1.alliance_type == ALLIANCE_TYPE
        a2 = AllianceCreateAction(GAME_ID, "4", f"Alliance Create {ALLIANCE_NAME} as {ALLIANCE_TYPE}")
        assert a2.is_valid() == True
        assert a2.game_id == GAME_ID
        assert a2.id == "4"
        assert a2.alliance_name == ALLIANCE_NAME
        assert a2.alliance_type == ALLIANCE_TYPE
        a3 = AllianceCreateAction(GAME_ID, "2", f"Alliance Create {ALLIANCE_NAME} as {ALLIANCE_TYPE}")
        assert a3.is_valid() == True
        assert a3.game_id == GAME_ID
        assert a3.id == "2"
        assert a3.alliance_name == ALLIANCE_NAME
        assert a3.alliance_type == ALLIANCE_TYPE

        # add agendas to nations
        nation_b = Nations.get("2")
        nation_c = Nations.get("3")
        nation_d = Nations.get("4")
        nation_b.completed_research["Common Ground"] = True
        nation_c.completed_research["Common Ground"] = True
        nation_d.completed_research["Common Ground"] = True

        # execute actions
        resolve_alliance_create_actions(GAME_ID, [a1, a2, a3])

        # test alliance
        alliance = Alliances.get(ALLIANCE_NAME)
        assert alliance.name == ALLIANCE_NAME
        assert alliance.is_active == True
        assert alliance.current_members == {"Nation C": 33, "Nation D": 33, "Nation B": 33}
        assert alliance.founding_members == {"Nation C": 33, "Nation D": 33, "Nation B": 33}
        assert any(notification[1] == f"{ALLIANCE_NAME} has formed." for notification in Notifications)

    def test_kick(self):
        """
        Simple alliance kick action(s). Should pass.
        """
        from app.actions import AllianceKickAction, resolve_alliance_kick_actions

        # create and verify action
        a1 = AllianceKickAction(GAME_ID, "3", f"Alliance Kick Nation B from Test")
        assert a1.is_valid() == True
        a2 = AllianceKickAction(GAME_ID, "4", f"Alliance Kick Nation B from Test")
        assert a2.is_valid() == True

        # execute actions
        resolve_alliance_kick_actions(GAME_ID, [a1, a2])

        # test alliance
        alliance = Alliances.get(ALLIANCE_NAME)
        assert alliance.name == ALLIANCE_NAME
        assert alliance.is_active == True
        assert alliance.current_members == {"Nation C": 33, "Nation D": 33}
        assert alliance.founding_members == {"Nation C": 33, "Nation D": 33, "Nation B": 33}
        assert any(notification[1] == f"Nation B has been kicked from {ALLIANCE_NAME}!" for notification in Notifications)

    def test_kick_bad_majority(self):
        """
        Alliance kick that will fail due to not enough votes (need majority).
        """
        from app.actions import AllianceKickAction, resolve_alliance_kick_actions

        # create and verify action
        a1 = AllianceKickAction(GAME_ID, "3", f"Alliance Kick Nation B from Test")
        assert a1.is_valid() == True

        # execute actions
        resolve_alliance_kick_actions(GAME_ID, [a1])

        # test alliance
        alliance = Alliances.get(ALLIANCE_NAME)
        assert alliance.name == ALLIANCE_NAME
        assert alliance.is_active == True
        assert alliance.current_members == {"Nation C": 33, "Nation D": 33, "Nation B": 33}
        assert alliance.founding_members == {"Nation C": 33, "Nation D": 33, "Nation B": 33}

    def test_kick_bad_alliance(self):
        """
        Alliance kick that will fail due to player not being in the alliance.
        """
        from app.actions import AllianceKickAction, resolve_alliance_kick_actions

        # create and verify action
        a1 = AllianceKickAction(GAME_ID, "3", f"Alliance Kick Nation A from Test")
        assert a1.is_valid() == True
        a2 = AllianceKickAction(GAME_ID, "4", f"Alliance Kick Nation A from Test")
        assert a2.is_valid() == True

        # execute actions
        resolve_alliance_kick_actions(GAME_ID, [a1, a2])

        # test alliance
        alliance = Alliances.get(ALLIANCE_NAME)
        assert alliance.name == ALLIANCE_NAME
        assert alliance.is_active == True
        assert alliance.current_members == {"Nation C": 33, "Nation D": 33, "Nation B": 33}
        assert alliance.founding_members == {"Nation C": 33, "Nation D": 33, "Nation B": 33}

        # check action logs
        nation_c = Nations.get("3")
        nation_d = Nations.get("4")
        assert f"Failed to vote to kick Nation A from {ALLIANCE_NAME}. Target nation is not in the alliance." in nation_c.action_log
        assert f"Failed to vote to kick Nation A from {ALLIANCE_NAME}. Target nation is not in the alliance." in nation_d.action_log

    def test_kick_blocked_by_founder(self):
        """
        Alliance kick that will fail due to Alliance Centralization.
        """
        from app.actions import AllianceKickAction, resolve_alliance_kick_actions

        # create and verify action
        a1 = AllianceKickAction(GAME_ID, "3", f"Alliance Kick Nation B from Test")
        assert a1.is_valid() == True
        a2 = AllianceKickAction(GAME_ID, "4", f"Alliance Kick Nation B from Test")
        assert a2.is_valid() == True

        # give nation b the Alliance Centralization agenda
        nation_b = Nations.get("2")
        nation_b.completed_research["Alliance Centralization"] = True

        # execute actions
        resolve_alliance_kick_actions(GAME_ID, [a1, a2])

        # test alliance
        alliance = Alliances.get(ALLIANCE_NAME)
        assert alliance.name == ALLIANCE_NAME
        assert alliance.is_active == True
        assert alliance.current_members == {"Nation C": 33, "Nation D": 33, "Nation B": 33}
        assert alliance.founding_members == {"Nation C": 33, "Nation D": 33, "Nation B": 33}

        # check action logs
        nation_c = Nations.get("3")
        nation_d = Nations.get("4")
        assert f"Failed to vote to kick Nation B from {ALLIANCE_NAME}. Target nation is a founder of the alliance." in nation_c.action_log
        assert f"Failed to vote to kick Nation B from {ALLIANCE_NAME}. Target nation is a founder of the alliance." in nation_d.action_log
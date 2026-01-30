"""
File: test_action_alliance_etc.py
Author: Ian Hampton
Created Date: 29th January 2026

Comprehensive series of unit tests for all other alliance actions.
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

class TestAllianceEtc(unittest.TestCase):

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

        # add agendas to nations
        nation_c = Nations.get("3")
        nation_d = Nations.get("4")
        nation_c.completed_research["Common Ground"] = True
        nation_d.completed_research["Common Ground"] = True

        # execute actions
        resolve_alliance_create_actions(GAME_ID, [a1, a2])

        # test alliance
        alliance = Alliances.get(ALLIANCE_NAME)
        assert alliance.name == ALLIANCE_NAME
        assert alliance.is_active == True
        assert alliance.current_members == {"Nation C": 33, "Nation D": 33}
        assert alliance.founding_members == {"Nation C": 33, "Nation D": 33}
        assert any(notification[1] == f"{ALLIANCE_NAME} has formed." for notification in Notifications)

    def test_join_simple(self):
        """
        Simple alliance join action. Should pass.
        """
        from app.actions import AllianceJoinAction, resolve_alliance_join_actions

        # create and verify action
        a1 = AllianceJoinAction(GAME_ID, "2", f"Alliance Join {ALLIANCE_NAME}")
        assert a1.is_valid() == True
        assert a1.game_id == GAME_ID
        assert a1.id == "2"
        assert a1.alliance_name == ALLIANCE_NAME

        # add agendas to nations
        nation_b = Nations.get("2")
        nation_b.completed_research["Common Ground"] = True

        # execute actions
        resolve_alliance_join_actions(GAME_ID, [a1])

        # test alliance
        alliance = Alliances.get(ALLIANCE_NAME)
        assert alliance.name == ALLIANCE_NAME
        assert alliance.is_active == True
        assert alliance.current_members == {"Nation C": 33, "Nation D": 33, "Nation B": 33}
        assert alliance.founding_members == {"Nation C": 33, "Nation D": 33}
        assert any(notification[1] == f"Nation B has joined the {alliance.name}." for notification in Notifications)

        # test nation b
        assert f"Joined {alliance.name}." in nation_b.action_log

    def test_join_bad_research(self):
        """
        Alliance join action that will fail due to player not having the correct agenda.
        """
        from app.actions import AllianceJoinAction, resolve_alliance_join_actions

        # create and verify action
        a1 = AllianceJoinAction(GAME_ID, "2", f"Alliance Join {ALLIANCE_NAME}")
        assert a1.is_valid() == True
        assert a1.game_id == GAME_ID
        assert a1.id == "2"
        assert a1.alliance_name == ALLIANCE_NAME

        # add agendas to nations
        nation_b = Nations.get("2")

        # execute actions
        resolve_alliance_join_actions(GAME_ID, [a1])

        # test alliance
        alliance = Alliances.get(ALLIANCE_NAME)
        assert alliance.name == ALLIANCE_NAME
        assert alliance.is_active == True
        assert alliance.current_members == {"Nation C": 33, "Nation D": 33}
        assert alliance.founding_members == {"Nation C": 33, "Nation D": 33}

        # test nation b
        assert f"Failed to join {ALLIANCE_NAME} alliance. You do not have the required agenda." in nation_b.action_log

    def test_join_blocked_by_status(self):
        """
        Alliance join action that will fail due to player being a puppet state.
        """
        from app.actions import AllianceJoinAction, resolve_alliance_join_actions

        # create and verify action
        a1 = AllianceJoinAction(GAME_ID, "2", f"Alliance Join {ALLIANCE_NAME}")
        assert a1.is_valid() == True
        assert a1.game_id == GAME_ID
        assert a1.id == "2"
        assert a1.alliance_name == ALLIANCE_NAME

        # add agendas to nations
        nation_b = Nations.get("2")
        nation_b.completed_research["Common Ground"] = True
        nation_b.status = "Puppet State of Nation D"

        # execute actions
        resolve_alliance_join_actions(GAME_ID, [a1])

        # test alliance
        alliance = Alliances.get(ALLIANCE_NAME)
        assert alliance.name == ALLIANCE_NAME
        assert alliance.is_active == True
        assert alliance.current_members == {"Nation C": 33, "Nation D": 33}
        assert alliance.founding_members == {"Nation C": 33, "Nation D": 33}

        # test nation b
        assert f"Failed to join {ALLIANCE_NAME} alliance. Puppet states cannot join alliances." in nation_b.action_log

    def test_leave(self):
        """
        Simple alliance leave action. Should pass.
        """
        from app.actions import AllianceLeaveAction, resolve_alliance_leave_actions

        # create and verify action
        a1 = AllianceLeaveAction(GAME_ID, "3", f"Alliance Leave {ALLIANCE_NAME}")
        assert a1.is_valid() == True
        assert a1.game_id == GAME_ID
        assert a1.id == "3"
        assert a1.alliance_name == ALLIANCE_NAME

        # execute actions
        resolve_alliance_leave_actions(GAME_ID, [a1])

        # test alliance
        alliance = Alliances.get(ALLIANCE_NAME)
        assert alliance.name == ALLIANCE_NAME
        assert alliance.is_active == True
        assert alliance.current_members == {"Nation D": 33}
        assert alliance.founding_members == {"Nation C": 33, "Nation D": 33}
        assert any(notification[1] == f"Nation C has left the {alliance.name}." for notification in Notifications)

        # test nation c
        nation_c = Nations.get("3")
        assert f"Left {ALLIANCE_NAME}." in nation_c.action_log
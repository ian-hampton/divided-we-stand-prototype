"""
File: test_action_alliance_create.py
Author: Ian Hampton
Created Date: 29th January 2026

Comprehensive series of unit tests for the alliance create action.
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

class TestAllianceCreate(unittest.TestCase):

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
        with patch.object(Alliances, "_gamedata_path", return_value=str(GAMEDATA_FILE)):
            Alliances.load(GAME_ID)
        with patch.object(Nations, "_gamedata_path", return_value=str(GAMEDATA_FILE)):
            Nations.load(GAME_ID)

    def test_simple(self):
        """
        Simple alliance create actions for a Non-aggression Pact. Should pass.
        """
        from app.actions import AllianceCreateAction, resolve_alliance_create_actions

        ALLIANCE_NAME = "Test"
        ALLIANCE_TYPE = "Non-Aggression Pact"

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

        # test nation c
        assert f"Successfully formed {ALLIANCE_NAME}." in nation_c.action_log

        # test nation d
        assert f"Successfully formed {ALLIANCE_NAME}." in nation_d.action_log

    def test_trade_agreement(self):
        """
        Alliance create actions for a Trade Agreement. Should pass.
        """
        from app.actions import AllianceCreateAction, resolve_alliance_create_actions

        ALLIANCE_NAME = "Test"
        ALLIANCE_TYPE = "Trade Agreement"

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
        nation_c.completed_research["Trade Routes"] = True
        nation_d.completed_research["Trade Routes"] = True

        # execute actions
        resolve_alliance_create_actions(GAME_ID, [a1, a2])

        # independently calculate yield of non-aggression pact
        expected_alliance_yield = 0
        expected_alliance_yield += 0.5 * nation_c.improvement_counts["Settlement"]
        expected_alliance_yield += 0.5 * nation_c.improvement_counts["City"]
        expected_alliance_yield += 0.5 * nation_c.improvement_counts["Central Bank"]
        expected_alliance_yield += 0.5 * nation_c.improvement_counts["Capital"]
        expected_alliance_yield += 0.5 * nation_d.improvement_counts["Settlement"]
        expected_alliance_yield += 0.5 * nation_d.improvement_counts["City"]
        expected_alliance_yield += 0.5 * nation_d.improvement_counts["Central Bank"]
        expected_alliance_yield += 0.5 * nation_d.improvement_counts["Capital"]

        # test alliance
        alliance = Alliances.get(ALLIANCE_NAME)
        assert alliance.name == ALLIANCE_NAME
        assert alliance.is_active == True
        assert alliance.current_members == {"Nation C": 33, "Nation D": 33}
        assert alliance.founding_members == {"Nation C": 33, "Nation D": 33}
        assert alliance.calculate_yield()[0] == expected_alliance_yield
        assert any(notification[1] == f"{ALLIANCE_NAME} has formed." for notification in Notifications)

        # test nation c
        assert f"Successfully formed {ALLIANCE_NAME}." in nation_c.action_log

        # test nation d
        assert f"Successfully formed {ALLIANCE_NAME}." in nation_d.action_log

    def test_bad_research(self):
        """
        Alliance create action fails due to not having the needed agenda.
        """
        from app.actions import AllianceCreateAction, resolve_alliance_create_actions

        ALLIANCE_NAME = "Test"
        ALLIANCE_TYPE = "Non-Aggression Pact"

        # create and verify actions
        a1 = AllianceCreateAction(GAME_ID, "3", f"Alliance Create {ALLIANCE_NAME} as {ALLIANCE_TYPE}")
        assert a1.is_valid() == True
        assert a1.game_id == GAME_ID
        assert a1.id == "3"
        assert a1.alliance_name == ALLIANCE_NAME
        assert a1.alliance_type == ALLIANCE_TYPE

        # add agendas to nations
        nation_c = Nations.get("3")

        # execute actions
        resolve_alliance_create_actions(GAME_ID, [a1])

        # test nation c
        assert f"Failed to form {ALLIANCE_NAME} alliance. You do not have the required agenda." in nation_c.action_log

    def test_blocked_by_count(self):
        """
        Alliance create action fails due to not having enough founding members.
        """
        from app.actions import AllianceCreateAction, resolve_alliance_create_actions

        ALLIANCE_NAME = "Test"
        ALLIANCE_TYPE = "Non-Aggression Pact"

        # create and verify actions
        a1 = AllianceCreateAction(GAME_ID, "3", f"Alliance Create {ALLIANCE_NAME} as {ALLIANCE_TYPE}")
        assert a1.is_valid() == True
        assert a1.game_id == GAME_ID
        assert a1.id == "3"
        assert a1.alliance_name == ALLIANCE_NAME
        assert a1.alliance_type == ALLIANCE_TYPE

        # add agendas to nations
        nation_c = Nations.get("3")
        nation_c.completed_research["Common Ground"] = True

        # execute actions
        resolve_alliance_create_actions(GAME_ID, [a1])

        # test nation c
        assert f"Failed to form {ALLIANCE_NAME} alliance. Not enough players agreed to establish it." in nation_c.action_log
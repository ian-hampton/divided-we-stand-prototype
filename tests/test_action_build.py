"""
File: test_action_build
Author: Ian Hampton
Created Date: 26th January 2026

Comprehensive series of unit tests for the build improvement action.
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

class TestBuild(unittest.TestCase):

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
        nation = Nations.get("2")
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
        Simple build action. Should succeed.
        """
        from app.actions import ImprovementBuildAction, resolve_improvement_build_actions

        IMPROVEMENT_NAME = "Research Laboratory"
        REGION_ID = "ATHEN"
        
        # create and verify action
        a1 = ImprovementBuildAction(GAME_ID, "2", f"Build {IMPROVEMENT_NAME} {REGION_ID}")
        assert a1.is_valid() == True
        assert a1.game_id == GAME_ID
        assert a1.id == "2"
        assert a1.improvement_name == IMPROVEMENT_NAME
        assert a1.target_region == REGION_ID

        # set research
        nation = Nations.get("2")
        nation.completed_research["Laboratories"] = True

        # execute actions
        resolve_improvement_build_actions(GAME_ID, [a1])

        # test region
        region = Regions.load(REGION_ID)
        assert region.improvement.name == IMPROVEMENT_NAME
        assert region.improvement.health == 99

        # test nation
        assert nation.improvement_counts[IMPROVEMENT_NAME] == 1
        assert f"Built {IMPROVEMENT_NAME} in region {REGION_ID} for 5.0 basic materials." in nation.action_log

        # test resources
        assert nation.get_stockpile("Dollars") == "100.00"
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

    def test_complex(self):
        """
        Testing a more complicated build action that requires extensive research and a required resource. Should succeed.
        """
        from app.actions import ImprovementBuildAction, resolve_improvement_build_actions

        IMPROVEMENT_NAME = "Rare Earth Elements Mine"
        REGION_ID = "CHRLO"
        
        # create and verify action
        a1 = ImprovementBuildAction(GAME_ID, "2", f"Build {IMPROVEMENT_NAME} {REGION_ID}")
        assert a1.is_valid() == True
        assert a1.game_id == GAME_ID
        assert a1.id == "2"
        assert a1.improvement_name == IMPROVEMENT_NAME
        assert a1.target_region == REGION_ID

        # set research
        nation = Nations.get("2")
        nation.completed_research["Metal Extraction"] = True
        nation.completed_research["Metallurgy"] = True
        nation.completed_research["Uranium Mining"] = True
        nation.completed_research["Rare Earth Mining"] = True

        # execute actions
        resolve_improvement_build_actions(GAME_ID, [a1])

        # test region
        region = Regions.load(REGION_ID)
        assert region.improvement.name == IMPROVEMENT_NAME
        assert region.improvement.health == 99

        # test nation
        assert nation.improvement_counts[IMPROVEMENT_NAME] == 1
        assert f"Built {IMPROVEMENT_NAME} in region {REGION_ID} for 5.0 advanced metals." in nation.action_log

        # test resources
        assert nation.get_stockpile("Dollars") == "100.00"
        assert nation.get_stockpile("Political Power") == "50.00"
        assert nation.get_stockpile("Research") == "50.00"
        assert nation.get_stockpile("Food") == "50.00"
        assert nation.get_stockpile("Coal") == "50.00"
        assert nation.get_stockpile("Oil") == "50.00"
        assert nation.get_stockpile("Basic Materials") == "50.00"
        assert nation.get_stockpile("Common Metals") == "50.00"
        assert nation.get_stockpile("Advanced Metals") == "45.00"
        assert nation.get_stockpile("Uranium") == "50.00"
        assert nation.get_stockpile("Rare Earth Elements") == "50.00"

    def test_bad_region(self):
        """
        Testing a build action in an invalid region. Should fail.
        """
        from app.actions import ImprovementBuildAction, resolve_improvement_build_actions

        IMPROVEMENT_NAME = "Industrial Zone"
        REGION_ID = "TXPAN"
        
        # create and verify action
        a1 = ImprovementBuildAction(GAME_ID, "2", f"Build {IMPROVEMENT_NAME} {REGION_ID}")
        assert a1.is_valid() == True
        assert a1.game_id == GAME_ID
        assert a1.id == "2"
        assert a1.improvement_name == IMPROVEMENT_NAME
        assert a1.target_region == REGION_ID

        # set research
        nation = Nations.get("2")
        
        # execute actions
        resolve_improvement_build_actions(GAME_ID, [a1])

        # test region
        region = Regions.load(REGION_ID)
        assert region.improvement.name == "Research Laboratory"
        assert region.improvement.health == 99

        # test nation
        assert nation.improvement_counts[IMPROVEMENT_NAME] == 0
        assert f"Failed to build {IMPROVEMENT_NAME} in region {REGION_ID}. You do not own or control this region." in nation.action_log

    def test_bad_research(self):
        """
        Testing a build action when missing needed research. Should fail.
        """
        from app.actions import ImprovementBuildAction, resolve_improvement_build_actions

        IMPROVEMENT_NAME = "Farm"
        REGION_ID = "JACKS"
        
        # create and verify action
        a1 = ImprovementBuildAction(GAME_ID, "2", f"Build {IMPROVEMENT_NAME} {REGION_ID}")
        assert a1.is_valid() == True
        assert a1.game_id == GAME_ID
        assert a1.id == "2"
        assert a1.improvement_name == IMPROVEMENT_NAME
        assert a1.target_region == REGION_ID

        # set research
        nation = Nations.get("2")
        
        # execute actions
        resolve_improvement_build_actions(GAME_ID, [a1])

        # test region
        region = Regions.load(REGION_ID)
        assert region.improvement.name == None
        assert region.improvement.health == 99

        # test nation
        assert nation.improvement_counts[IMPROVEMENT_NAME] == 0
        assert f"Failed to build {IMPROVEMENT_NAME} in region {REGION_ID}. You do not have the required research." in nation.action_log

    def test_bad_resource(self):
        """
        Testing a build action in a region without required resource. Should fail.
        """
        from app.actions import ImprovementBuildAction, resolve_improvement_build_actions

        IMPROVEMENT_NAME = "Rare Earth Elements Mine"
        REGION_ID = "TALLA"
        
        # create and verify action
        a1 = ImprovementBuildAction(GAME_ID, "2", f"Build {IMPROVEMENT_NAME} {REGION_ID}")
        assert a1.is_valid() == True
        assert a1.game_id == GAME_ID
        assert a1.id == "2"
        assert a1.improvement_name == IMPROVEMENT_NAME
        assert a1.target_region == REGION_ID

        # set research
        nation = Nations.get("2")
        nation.completed_research["Metal Extraction"] = True
        nation.completed_research["Metallurgy"] = True
        nation.completed_research["Uranium Mining"] = True
        nation.completed_research["Rare Earth Mining"] = True

        # execute actions
        resolve_improvement_build_actions(GAME_ID, [a1])

        # test region
        region = Regions.load(REGION_ID)
        assert region.improvement.name == None
        assert region.improvement.health == 99

        # test nation
        assert nation.improvement_counts[IMPROVEMENT_NAME] == 0
        assert f"Failed to build {IMPROVEMENT_NAME} in region {REGION_ID}. The region does not have the resource required for this improvement." in nation.action_log

    def test_blocked_by_fallout(self):
        pass

    def test_blocked_by_shortage(self):
        pass

    def test_blocked_by_capital(self):
        """
        Testing a build action in a region with a Capital. Should fail.
        """
        from app.actions import ImprovementBuildAction, resolve_improvement_build_actions

        IMPROVEMENT_NAME = "Industrial Zone"
        REGION_ID = "BILOX"
        
        # create and verify action
        a1 = ImprovementBuildAction(GAME_ID, "2", f"Build {IMPROVEMENT_NAME} {REGION_ID}")
        assert a1.is_valid() == True
        assert a1.game_id == GAME_ID
        assert a1.id == "2"
        assert a1.improvement_name == IMPROVEMENT_NAME
        assert a1.target_region == REGION_ID

        # set research
        nation = Nations.get("2")
        
        # execute actions
        resolve_improvement_build_actions(GAME_ID, [a1])

        # test region
        region = Regions.load(REGION_ID)
        assert region.improvement.name == "Capital"
        assert region.improvement.health == 12

        # test nation
        assert nation.improvement_counts[IMPROVEMENT_NAME] == 0
        print(nation.action_log)
        assert f"Failed to build {IMPROVEMENT_NAME} in region {REGION_ID}. You cannot build over a Capital improvement." in nation.action_log
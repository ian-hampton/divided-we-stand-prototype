"""
File: test_missiles.py
Author: Ian Hampton
Created Date: 21st January 2026

TODO: Add tests for invalid missile launch targets and for missile defense.
TODO: Check war score.
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

class TestMissiles(unittest.TestCase):

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

        from app.actions import WarAction, resolve_war_actions

        # verify war does not exist already
        war_name = Wars.get_war_name("3", "4")
        assert war_name is None

        # create and verify war declaration action
        animosity_war_action = WarAction(GAME_ID, "4", "War Nation C using Animosity")
        assert animosity_war_action.is_valid() == True
        assert animosity_war_action.game_id == GAME_ID
        assert animosity_war_action.id == "4"
        assert animosity_war_action.target_nation == "Nation C"
        assert animosity_war_action.war_justification == "Animosity"

        # declare war
        actions_list = [animosity_war_action]
        resolve_war_actions(GAME_ID, actions_list)
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
        assert defender.justification == "TBD"
        assert defender.target_id == "TBD"
        assert defender.claims == {}

    def test_missile_vs_improvement_1(self):
        from app.actions import MissileLaunchAction, resolve_missile_launch_actions
        pass

    def test_missile_vs_improvement_2(self):
        from app.actions import MissileLaunchAction, resolve_missile_launch_actions
        pass

    def test_missile_vs_unit(self):
        from app.actions import MissileLaunchAction, resolve_missile_launch_actions
        pass

    def test_nuke(self):
        """
        Nuclear strike vs fully populated enemy region.

        Improvement and unit should both be destroyed. Fallout should be present.
        """
        from app.actions import MissileLaunchAction, resolve_missile_launch_actions
        
        # create and verify missile launch action
        a1 = MissileLaunchAction(GAME_ID, "4", "Launch Nuclear Missile DENVE")
        assert a1.is_valid() == True
        assert a1.game_id == GAME_ID
        assert a1.id == "4"
        assert a1.missile_type == "Nuclear Missile"
        assert a1.target_region == "DENVE"

        # pre-checks
        nation = Nations.get("Nation D")
        nation.nuke_count = 1
        assert nation.nuke_count == 1
        DENVE = Regions.reload("DENVE")
        assert DENVE.improvement.name == "Settlement"
        assert DENVE.unit.name == "Infantry"

        # execute missile launch actions
        resolve_missile_launch_actions(GAME_ID, [a1])

        # check player inventory
        assert nation.nuke_count == 0

        # check target region
        assert DENVE.improvement.name == None
        assert DENVE.unit.name == None
        assert DENVE.data.fallout == 4

    def test_nuke_vs_capital(self):
        """
        Nuclear strike vs enemy capital.

        Unit should be destroyed. Capital should remain but be at 0 health. Fallout should NOT be present.
        """
        from app.actions import MissileLaunchAction, resolve_missile_launch_actions
        
        # create and verify missile launch action
        a1 = MissileLaunchAction(GAME_ID, "4", "Launch Nuclear Missile NTHWY")
        assert a1.is_valid() == True
        assert a1.game_id == GAME_ID
        assert a1.id == "4"
        assert a1.missile_type == "Nuclear Missile"
        assert a1.target_region == "NTHWY"

        # pre-checks
        nation = Nations.get("Nation D")
        nation.nuke_count = 1
        assert nation.nuke_count == 1
        NTHWY = Regions.reload("NTHWY")
        assert NTHWY.data.owner_id == "3"
        assert NTHWY.improvement.name == "Capital"
        assert NTHWY.unit.name == "Artillery"
        assert NTHWY.unit.owner_id == "3"

        # execute missile launch actions
        resolve_missile_launch_actions(GAME_ID, [a1])

        # check player inventory
        assert nation.nuke_count == 0

        # check target region
        assert NTHWY.improvement.name == "Capital"
        assert NTHWY.improvement.health == 0
        assert NTHWY.unit.name == None
        assert NTHWY.data.fallout == 0
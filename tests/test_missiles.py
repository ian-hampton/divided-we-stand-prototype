"""
File: test_missiles.py
Author: Ian Hampton
Created Date: 21st January 2026

TODO: Add tests for invalid missile launch targets and for missile defense.
TODO: Check war score.
"""

import copy
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

        from app.scenario import scenario
        from app.scenario.scenario import ScenarioDataFile

        # make testing easier by patching scenario data so that missile damage chance is 100%
        class MissileMock:
            def __init__(self, d: dict):
                self.d = d
                self.required_research: str = d["Required Research"]
                self.type: str = d["Type"]
                self.improvement_damage: int = d.get("Improvement Damage", -1)
                self.unit_damage: int = d.get("Unit Damage", -1)
                self.improvement_damage_chance: float = 1.0
                self.unit_damage_chance: float = 1.0
                self.launch_cost: int = d["Launch Capacity"]
            @property
            def cost(self) -> dict:
                return copy.deepcopy(self.d.get("Build Costs", {}))
        
        scenario.ClassNameToFileName["MissileMock"] = "missiles"
        SD.missiles = ScenarioDataFile(MissileMock)

        # verify missile patch
        assert SD.missiles["Standard Missile"].improvement_damage_chance == 1.0
        assert SD.missiles["Standard Missile"].unit_damage_chance == 1.0

    def test_missile_vs_improvement(self):
        """
        Missile vs defenseless improvement with no health.
        Outcome: Improvement should be destroyed.
        """
        from app.actions import MissileLaunchAction, resolve_missile_launch_actions

        # create and verify missile launch action
        a1 = MissileLaunchAction(GAME_ID, "4", "Launch Standard Missile OLYMP")
        assert a1.is_valid() == True
        assert a1.game_id == GAME_ID
        assert a1.id == "4"
        assert a1.missile_type == "Standard Missile"
        assert a1.target_region == "OLYMP"

        # pre-checks
        nation = Nations.get("Nation D")
        nation.missile_count = 3
        assert nation.missile_count == 3
        OLYMP = Regions.reload("OLYMP")
        assert OLYMP.data.owner_id == "3"
        assert OLYMP.improvement.name == "Industrial Zone"
        assert OLYMP.unit.name == None

        # execute missile launch actions
        resolve_missile_launch_actions(GAME_ID, [a1])

        # check player inventory
        assert nation.missile_count == 2

        # check target region
        war_name = Wars.get_war_name("3", "4")
        war = Wars.get(war_name)
        assert OLYMP.improvement.name == None

    def test_missile_comprehensive(self):
        """
        Two missiles vs improvement and unit that both have health bars.
        Outcome: Improvement should be destroyed (will take 4 damage only has 3 health), unit should take 2 damage (has armor from entrenched)
        """
        from app.actions import MissileLaunchAction, resolve_missile_launch_actions
        
        # create and verify missile launch action
        a1 = MissileLaunchAction(GAME_ID, "4", "Launch Standard Missile DENVE")
        assert a1.is_valid() == True
        assert a1.game_id == GAME_ID
        assert a1.id == "4"
        assert a1.missile_type == "Standard Missile"
        assert a1.target_region == "DENVE"

        # pre-checks
        nation = Nations.get("Nation D")
        nation.missile_count = 3
        assert nation.missile_count == 3
        DENVE = Regions.reload("DENVE")
        assert DENVE.data.owner_id == "3"
        assert DENVE.improvement.name == "Settlement"
        assert DENVE.improvement.health == 3
        assert DENVE.unit.name == "Infantry"
        assert DENVE.unit.health == 8

        # execute missile launch actions
        resolve_missile_launch_actions(GAME_ID, [a1, a1])

        # check player inventory
        assert nation.missile_count == 1

        # check target region
        assert DENVE.improvement.name == None
        assert DENVE.unit.name == "Infantry"
        assert DENVE.unit.health == 6

    def test_nuke(self):
        """
        Nuclear strike vs fully populated enemy region.

        Improvement and unit should both be destroyed. Fallout should be present.
        """
        from app.actions import MissileLaunchAction, resolve_missile_launch_actions
        
        # create and verify missile launch action
        a1 = MissileLaunchAction(GAME_ID, "4", "Launch Nuclear Missile OMAHA")
        assert a1.is_valid() == True
        assert a1.game_id == GAME_ID
        assert a1.id == "4"
        assert a1.missile_type == "Nuclear Missile"
        assert a1.target_region == "OMAHA"

        # pre-checks
        nation = Nations.get("Nation D")
        nation.nuke_count = 1
        assert nation.nuke_count == 1
        OMAHA = Regions.reload("OMAHA")
        assert OMAHA.improvement.name == "Research Laboratory"
        assert OMAHA.unit.name == "Infantry"

        # execute missile launch actions
        resolve_missile_launch_actions(GAME_ID, [a1])

        # check player inventory
        assert nation.nuke_count == 0

        # check target region
        assert OMAHA.improvement.name == None
        assert OMAHA.unit.name == None
        assert OMAHA.data.fallout == 4

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
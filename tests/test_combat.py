"""
File: test_combat.py
Author: Ian Hampton
Created Date: 2nd January 2026
"""
import os, sys
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

class TestCombat(unittest.TestCase):

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
    
    def test_infantry_vs_infantry(self):
        """
        Nation D Infantry DURAN vs Nation C Infantry GJUNC
            Attacking Unit Gross Damage = 2 (+2 from base damage)
            Defending Unit Armor = 1 (+1 from holding position)
            Attacking Unit Net Damage = 1 (Attacker Gross Damage - Defender Armor)
            Attacking Unit will suffer 1 damage due to ineffective attack.
        """
        from app.actions import UnitMoveAction, resolve_unit_move_actions

        # create and verify movement action
        m1 = UnitMoveAction(GAME_ID, "4", "Move DURAN-GJUNC")
        assert m1.is_valid() == True
        assert m1.game_id == GAME_ID
        assert m1.id == "4"
        assert m1.current_region_id == "DURAN"
        assert m1.target_region_ids == ["GJUNC"]

        # execute movement and combat
        resolve_unit_move_actions(GAME_ID, [m1])

        # check attacker
        DURAN = Regions.load("DURAN")
        assert DURAN.unit.name == "Infantry"
        assert DURAN.unit.health == 7

        # check defender
        GJUNC = Regions.load("GJUNC")
        assert GJUNC.unit.name == "Infantry"
        assert DURAN.unit.health == 7
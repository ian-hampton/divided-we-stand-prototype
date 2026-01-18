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
    
    def test_in_vs_in(self):
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
        assert GJUNC.unit.health == 7

    def test_sf_vs_in_settlement(self):
        """
        Nation D Special Forces COSPR vs Nation C Infantry DENVE
            Attacking Unit Gross Damage = 3 (+3 from base damage)
            Defending Unit Armor = 0 (nullified by SF ability)
            Attacking Unit Net Damage = 3 (Attacker Gross Damage - Defender Armor)
        Nation D Special Forces COSPR vs Nation C Settlement DENVE
            Attacking Unit Gross Damage = 3 (+3 from base damage)
            Defending Improvement Armor = 0 (nullified by SF ability)
            Attacking Unit Net Damage = 3 (Attacker Gross Damage - Defender Armor)
            Attacking Unit will suffer 1 damage from the Settlement.
            Settlement will be destroyed.
        """
        from app.actions import UnitMoveAction, resolve_unit_move_actions

        # create and verify movement action
        m1 = UnitMoveAction(GAME_ID, "4", "Move COSPR-DENVE")
        assert m1.is_valid() == True
        assert m1.game_id == GAME_ID
        assert m1.id == "4"
        assert m1.current_region_id == "COSPR"
        assert m1.target_region_ids == ["DENVE"]

        # execute movement and combat
        resolve_unit_move_actions(GAME_ID, [m1])

        # check attacker
        COSPR = Regions.load("COSPR")
        assert COSPR.unit.name == "Special Forces"
        assert COSPR.unit.health == 15

        # check defender
        DENVE = Regions.load("DENVE")
        assert DENVE.unit.name == "Infantry"
        assert DENVE.unit.health == 5
        assert DENVE.improvement.name == None
        assert DENVE.improvement.health == 99

    def test_in_vs_undefended(self):
        """
        Basic move to an undefended territory to test occupation.
        """
        from app.actions import UnitMoveAction, resolve_unit_move_actions

        # create and verify movement action
        m1 = UnitMoveAction(GAME_ID, "4", "Move SANFR-SROSA")
        assert m1.is_valid() == True
        assert m1.game_id == GAME_ID
        assert m1.id == "4"
        assert m1.current_region_id == "SANFR"
        assert m1.target_region_ids == ["SROSA"]

        # execute movement and combat
        resolve_unit_move_actions(GAME_ID, [m1])

        # check SANFR
        SANFR = Regions.load("SANFR")
        assert SANFR.data.owner_id == "4"
        assert SANFR.data.occupier_id == "0"
        assert SANFR.unit.name == None
        assert SANFR.unit.health == 99
        assert SANFR.unit.owner_id == "0"
        assert SANFR.improvement.name == "Research Laboratory"
        assert SANFR.improvement.health == 99

        # check SROSA
        SROSA = Regions.load("SROSA")
        assert SROSA.data.owner_id == "3"
        assert SROSA.data.occupier_id == "4"
        assert SROSA.unit.name == "Infantry"
        assert SROSA.unit.health == 8
        assert SROSA.unit.owner_id == "4"
        assert SROSA.improvement.name == None
        assert SROSA.improvement.health == 99

    def test_mo_vs_undefended(self):
        """
        This test checks two things:
        1. Are units with multiple moves functioning as expected?
        2. Are defenseless improvements being pillaged?
        """

        from app.actions import UnitMoveAction, resolve_unit_move_actions

        # create and verify movement action
        m1 = UnitMoveAction(GAME_ID, "3", "Move PROVO-STEUT-NTEAZ")
        assert m1.is_valid() == True
        assert m1.game_id == GAME_ID
        assert m1.id == "3"
        assert m1.current_region_id == "PROVO"
        assert m1.target_region_ids == ["NTEAZ", "STEUT"]

        # execute movement and combat
        resolve_unit_move_actions(GAME_ID, [m1])

        # check PROVO
        PROVO = Regions.load("PROVO")
        assert PROVO.data.owner_id == "3"
        assert PROVO.data.occupier_id == "0"
        assert PROVO.unit.name == None
        assert PROVO.unit.health == 99
        assert PROVO.unit.owner_id == "0"
        assert PROVO.improvement.name == "Research Laboratory"
        assert PROVO.improvement.health == 99

        # check STEUT
        STEUT = Regions.load("STEUT")
        assert STEUT.data.owner_id == "4"
        assert STEUT.data.occupier_id == "3"
        assert STEUT.unit.name == None
        assert STEUT.unit.health == 99
        assert STEUT.unit.owner_id == "0"
        assert STEUT.improvement.name == None
        assert STEUT.improvement.health == 99

        # check NTEAZ
        NTEAZ = Regions.load("NTEAZ")
        assert NTEAZ.data.owner_id == "4"
        assert NTEAZ.data.occupier_id == "3"
        assert NTEAZ.unit.name == "Motorized Infantry"
        assert NTEAZ.unit.health == 8
        assert NTEAZ.unit.owner_id == "3"
        assert NTEAZ.improvement.name == None
        assert NTEAZ.improvement.health == 99
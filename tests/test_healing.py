"""
File: test_healing.py
Author: Ian Hampton
Created Date: 19th January 2026
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

class TestHealing(unittest.TestCase):

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

    def test_neutral_improvement(self):
        """
        Unowned improvements should NOT heal.
        """
        from app.checks import heals
        DULUT = Regions.reload("DULUT")
        heals.heal_improvement(DULUT)
        assert DULUT.improvement.health == 1

    def test_improvement_normal(self):
        """
        Improvements should heal if not attacked.
        """
        from app.checks import heals

        ALBUQ = Regions.reload("ALBUQ")
        ALBUQ.improvement.health = 1

        heals.heal_improvement(ALBUQ)

        assert ALBUQ.improvement.health == 2

    def test_improvement_attacked(self):
        """
        Improvements should NOT heal if attacked that turn.
        """
        from app.checks import heals

        ALBUQ = Regions.reload("ALBUQ")
        ALBUQ.improvement.health = 1
        ALBUQ.improvement.has_been_attacked = True
        
        heals.heal_improvement(ALBUQ)

        assert ALBUQ.improvement.health == 1

    def test_unit_normal(self):
        """
        Units should heal if not attacked.
        """
        from app.checks import heals

        COSPR = Regions.reload("COSPR")
        COSPR.unit.health = 1

        heals.heal_unit(COSPR)
        
        assert COSPR.unit.health == 2

    def test_unit_peacetime(self):
        """
        Units owned by a nation with Peacetime Recovery should heal twice as much during peacetime.
        """
        from app.checks import heals
        
        PROVO = Regions.reload("PROVO")
        PROVO.unit.health = 1

        heals.heal_unit(PROVO)

        assert PROVO.unit.health == 3

    def test_unit_attacked(self):
        """
        Units should NOT heal if attacked that turn.
        """
        from app.checks import heals

        COSPR = Regions.reload("COSPR")
        COSPR.unit.health = 1
        COSPR.unit.has_been_attacked = True

        heals.heal_unit(COSPR)
        
        assert COSPR.unit.health == 1
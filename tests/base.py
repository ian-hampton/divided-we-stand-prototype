"""
File: base.py
Author: Ian Hampton
Created Date: 1st January 2026

This is the core code required to run any tests on the turn procesor. You must import this before running any tests!
It mocks the Games class to prevent writes to disk and includes very basic load tests to make sure everything is initialized properly.
"""

import sys
import os
import unittest
from unittest.mock import patch

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import mock_games

from app.scenario.scenario import ScenarioInterface as SD
from app.alliance.alliances import Alliances
from app.region.regions import Regions
from app.nation.nations import Nations
from app.notifications import Notifications
from app.truce.truces import Truces
from app.war.wars import Wars

GAME_ID = "HrQyxUeblAMjTJbTrxsp"
ACTIONS = {}

class TestClassLoad(unittest.TestCase):

    def test_load_scenario(self):
        SD.load(GAME_ID)
        
        assert "Scorched Earth" in SD.agendas
        assert "Trade Agreement" in SD.alliances
        assert SD.improvements["Industrial Zone"].cost == {"Dollars": 5}
    
    def test_load_alliances(self):
        test_file = "tests/mock-files/gamedata.json"
        with patch.object(Alliances, "_gamedata_path", return_value=str(test_file)):
            Alliances.load(GAME_ID)

        assert "Test Trade Agreement" in Alliances._data
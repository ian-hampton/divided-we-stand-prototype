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
GAMEDATA_FILE = "tests/mock-files/gamedata.json"
REGDATA_FILE = "tests/mock-files/regdata.json"

class TestClassLoad(unittest.TestCase):

    def test_load_scenario(self):
        SD.load(GAME_ID)
        
        assert "Scorched Earth" in SD.agendas
        assert "Trade Agreement" in SD.alliances
        assert SD.improvements["Industrial Zone"].cost == {"Dollars": 5}
    
    def test_load_alliances(self):
        with patch.object(Alliances, "_gamedata_path", return_value=str(GAMEDATA_FILE)):
            Alliances.load(GAME_ID)

        alliance = Alliances.get("Test Trade Agreement")
        assert alliance.name == "Test Trade Agreement"
        assert alliance.turn_created == 17
        assert alliance.turn_ended == 20
        assert alliance.is_active == False

    def test_load_regions(self):
        SD.load(GAME_ID)
        with patch.object(Regions, "_regdata_path", return_value=str(REGDATA_FILE)):
            Regions.initialize(GAME_ID)

        NTHWY = Regions.load("NTHWY")
        assert NTHWY.data.owner_id == "3"
        assert NTHWY.data.occupier_id == "0"
        assert NTHWY.data.resource == "Empty"
        assert NTHWY.improvement.name == "Capital"
        assert NTHWY.improvement.health == 12
        assert NTHWY.unit.name == None

    def test_load_nations(self):
        SD.load(GAME_ID)
        with patch.object(Nations, "_gamedata_path", return_value=str(GAMEDATA_FILE)):
            Nations.load(GAME_ID)

        nation_1 = Nations.get("1")
        assert nation_1.name == "Nation A"
        assert nation_1.gov == "Republic"
        assert nation_1.fp == "Diplomatic"

    def test_load_notifications(self):
        with patch.object(Notifications, "_gamedata_path", return_value=str(GAMEDATA_FILE)):
            Notifications.load(GAME_ID)
        
        test_notification = [3, "Foreign Investment will end on turn 33."]
        assert test_notification in Notifications._data

    def test_load_truces(self):
        with patch.object(Truces, "_gamedata_path", return_value=str(GAMEDATA_FILE)):
            Truces.load(GAME_ID)
        
        assert "1" in Truces._data
        assert Truces.are_truced("3", "4") == False

    def test_load_wars(self):
        with patch.object(Wars, "_gamedata_path", return_value=str(GAMEDATA_FILE)):
            Wars.load(GAME_ID)

        # TODO - add example war data
        assert True == True
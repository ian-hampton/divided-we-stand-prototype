"""
File: test_basic.py
Author: Ian Hampton
Created Date: 2nd January 2026

Very basic and only tests data retrieval/loading. 
These tests alone are not enough to assume that all methods of the Alliance, Regions, etc classes are working properly.
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

class TestBasicLoad(unittest.TestCase):

    def test_load_game(self):
        from app.game.games import Games
        game = Games.load(GAME_ID)
        game.turn = 33

        assert game.name == "test"
        assert game.turn == 33
        assert game.status == 201
        assert game.info.version == "Development"
        assert game.stats.region_disputes == 0
        assert game.inactive_events == ["Foreign Aid", "Humiliation"]
        assert game.current_event == {}

    def test_load_scenario_interface(self):
        SD.load(GAME_ID)
        
        test_1 = "Scorched Earth"
        assert test_1 in SD.agendas
        assert SD.agendas[test_1].type == "Warfare"
        assert SD.agendas[test_1].cost == 15

        test_2 = "Trade Agreement"
        assert test_2 in SD.alliances
        assert SD.alliances[test_2].required_agenda == "Trade Routes"
        assert SD.alliances[test_2].capacity == True
        
        test_3 = "Industrial Zone"
        assert test_3 in SD.improvements
        assert SD.improvements[test_3].required_research == None
        assert SD.improvements[test_3].required_resource == "Basic Materials"
        assert SD.improvements[test_3].income == {"Basic Materials": 1}
        assert SD.improvements[test_3].cost == {"Dollars": 5}
        assert SD.improvements[test_3].upkeep == {}
    
    def test_load_alliances(self):
        with patch.object(Alliances, "_gamedata_path", return_value=str(GAMEDATA_FILE)):
            Alliances.load(GAME_ID)

        alliance = Alliances.get("Test Trade Agreement")
        assert alliance.type == "Trade Agreement"
        assert alliance.turn_created == 17
        assert alliance.turn_ended == 20
        assert alliance.is_active == False
        assert alliance.current_members == {}
        assert alliance.founding_members == {"Nation C": 17, "Nation D": 17}
        assert alliance.former_members == {"Nation A": 19, "Nation C": 20, "Nation D": 20}

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
        assert NTHWY.unit.name == "Artillery"
        assert NTHWY.unit.health == 6
        assert NTHWY.unit.owner_id == "3"

    def test_load_nations(self):
        SD.load(GAME_ID)
        with patch.object(Nations, "_gamedata_path", return_value=str(GAMEDATA_FILE)):
            Nations.load(GAME_ID)

        nation_1 = Nations.get("1")
        assert nation_1.name == "Nation A"
        assert nation_1.gov == "Republic"
        assert nation_1.fp == "Diplomatic"
        assert nation_1.stats.regions_owned == 5
        assert nation_1.records.development[-1] == 10

    def test_load_notifications(self):
        with patch.object(Notifications, "_gamedata_path", return_value=str(GAMEDATA_FILE)):
            Notifications.load(GAME_ID)
        
        test_notification = [3, "Foreign Investment will end on turn 33."]
        assert test_notification in Notifications._data

    def test_load_truces(self):
        with patch.object(Truces, "_gamedata_path", return_value=str(GAMEDATA_FILE)):
            Truces.load(GAME_ID)
        
        for i, truce in enumerate(Truces):
            if i == 0:
                assert truce.id == "1"
                assert truce.start_turn == 20
                assert truce.end_turn == 23
                assert truce.signatories == {"3": True, "4": True}
                assert truce.is_active == False
                assert Truces.are_truced("3", "4") == False

    def test_load_wars(self):
        with patch.object(Wars, "_gamedata_path", return_value=str(GAMEDATA_FILE)):
            Wars.load(GAME_ID)

        # TODO - add example war data
        assert True == True
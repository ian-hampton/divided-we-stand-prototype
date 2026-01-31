"""
File: test_action_claim.py
Author: Ian Hampton
Created Date: 29th January 2026

Comprehensive series of unit tests for the region claim action.
More tests could (should) be added, testing things like region dispute, failed encirclement, large encirclement, and exceptions to the expansion rules.
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

class TestRegionClaim(unittest.TestCase):

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
        with patch.object(Nations, "_gamedata_path", return_value=str(GAMEDATA_FILE)):
            Nations.load(GAME_ID)
        with patch.object(Regions, "_regdata_path", return_value=str(REGDATA_FILE)):
            Regions.initialize(GAME_ID)

        # set nation data
        nation = Nations.get("1")
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
        Simple region claim action. Should pass.
        """
        from app.actions import ClaimAction, resolve_claim_actions

        REGION_ID = "CHICA"

        # create and verify action
        a1 = ClaimAction(GAME_ID, "1", f"Claim {REGION_ID}")
        assert a1.is_valid() == True
        assert a1.game_id == GAME_ID
        assert a1.id == "1"
        assert a1.target_region == REGION_ID

        # execute actions
        resolve_claim_actions(GAME_ID, [a1])

        # check region
        region = Regions.load(REGION_ID)
        assert region.data.owner_id == "1"

        # check nation
        nation = Nations.get("1")
        assert f"Claimed region {REGION_ID} for 5.00 dollars." in nation.action_log
        assert nation.get_stockpile("Dollars") == "95.00"
        assert nation.get_stockpile("Political Power") == "50.00"
        assert nation.get_stockpile("Research") == "50.00"
        assert nation.get_stockpile("Food") == "50.00"
        assert nation.get_stockpile("Coal") == "50.00"
        assert nation.get_stockpile("Oil") == "50.00"
        assert nation.get_stockpile("Basic Materials") == "50.00"
        assert nation.get_stockpile("Common Metals") == "50.00"
        assert nation.get_stockpile("Advanced Metals") == "50.00"
        assert nation.get_stockpile("Uranium") == "50.00"
        assert nation.get_stockpile("Rare Earth Elements") == "50.00"

    def test_consecutive(self):
        """
        Consecutive claim action are allowed. Should pass.
        """
        from app.actions import ClaimAction, resolve_claim_actions

        # create and verify actions
        a1 = ClaimAction(GAME_ID, "1", "Claim CHICA")
        assert a1.is_valid() == True
        a2 = ClaimAction(GAME_ID, "1", "Claim PEORI")
        assert a2.is_valid() == True
        a3 = ClaimAction(GAME_ID, "1", "Claim CHAMP")
        assert a3.is_valid() == True

        # execute actions
        resolve_claim_actions(GAME_ID, [a1, a2, a3])

        # check regions
        CHICA = Regions.load("CHICA")
        assert CHICA.data.owner_id == "1"
        PEORI = Regions.load("PEORI")
        assert PEORI.data.owner_id == "1"
        CHAMP = Regions.load("CHAMP")
        assert CHAMP.data.owner_id == "1"

        # check nation
        nation = Nations.get("1")
        assert f"Claimed region CHICA for 5.00 dollars." in nation.action_log
        assert f"Claimed region PEORI for 5.00 dollars." in nation.action_log
        assert f"Claimed region CHAMP for 5.00 dollars." in nation.action_log
        assert nation.get_stockpile("Dollars") == "85.00"
        assert nation.get_stockpile("Political Power") == "50.00"
        assert nation.get_stockpile("Research") == "50.00"
        assert nation.get_stockpile("Food") == "50.00"
        assert nation.get_stockpile("Coal") == "50.00"
        assert nation.get_stockpile("Oil") == "50.00"
        assert nation.get_stockpile("Basic Materials") == "50.00"
        assert nation.get_stockpile("Common Metals") == "50.00"
        assert nation.get_stockpile("Advanced Metals") == "50.00"
        assert nation.get_stockpile("Uranium") == "50.00"
        assert nation.get_stockpile("Rare Earth Elements") == "50.00"

    def test_encirclement_rule(self):
        """
        Unclaimed regions fully encircled should also be claimed. Should pass.
        """
        from app.actions import ClaimAction, resolve_claim_actions

        # create and verify actions
        a1 = ClaimAction(GAME_ID, "1", "Claim CHICA")
        assert a1.is_valid() == True
        a2 = ClaimAction(GAME_ID, "1", "Claim PEORI")
        assert a2.is_valid() == True
        a3 = ClaimAction(GAME_ID, "1", "Claim CHAMP")
        assert a3.is_valid() == True
        a4 = ClaimAction(GAME_ID, "1", "Claim SBEND")
        assert a4.is_valid() == True
        a5 = ClaimAction(GAME_ID, "1", "Claim TERRE")
        assert a5.is_valid() == True
        a6 = ClaimAction(GAME_ID, "1", "Claim BLOOM")
        assert a6.is_valid() == True
        a7 = ClaimAction(GAME_ID, "1", "Claim WAYNE")
        assert a7.is_valid() == True

        # execute actions
        resolve_claim_actions(GAME_ID, [a1, a2, a3, a4, a5, a6, a7])

        # check regions
        CHICA = Regions.load("CHICA")
        assert CHICA.data.owner_id == "1"
        PEORI = Regions.load("PEORI")
        assert PEORI.data.owner_id == "1"
        CHAMP = Regions.load("CHAMP")
        assert CHAMP.data.owner_id == "1"
        SBEND = Regions.load("SBEND")
        assert SBEND.data.owner_id == "1"
        TERRE = Regions.load("TERRE")
        assert TERRE.data.owner_id == "1"
        BLOOM = Regions.load("BLOOM")
        assert BLOOM.data.owner_id == "1"
        WAYNE = Regions.load("WAYNE")
        assert WAYNE.data.owner_id == "1"

        # INDIA was encircled by the above actions
        INDIA = Regions.load("INDIA")
        assert INDIA.data.owner_id == "1"

        # check nation
        nation = Nations.get("1")
        assert nation.get_stockpile("Dollars") == "60.00"
        assert nation.get_stockpile("Political Power") == "50.00"
        assert nation.get_stockpile("Research") == "50.00"
        assert nation.get_stockpile("Food") == "50.00"
        assert nation.get_stockpile("Coal") == "50.00"
        assert nation.get_stockpile("Oil") == "50.00"
        assert nation.get_stockpile("Basic Materials") == "50.00"
        assert nation.get_stockpile("Common Metals") == "50.00"
        assert nation.get_stockpile("Advanced Metals") == "50.00"
        assert nation.get_stockpile("Uranium") == "50.00"
        assert nation.get_stockpile("Rare Earth Elements") == "50.00"

    def test_bad_region(self):
        """
        Region claim should fail for region already owned by someone else.
        """
        from app.actions import ClaimAction, resolve_claim_actions

        REGION_ID = "OMAHA"

        # create and verify action
        a1 = ClaimAction(GAME_ID, "1", f"Claim {REGION_ID}")
        assert a1.is_valid() == True
        assert a1.game_id == GAME_ID
        assert a1.id == "1"
        assert a1.target_region == REGION_ID

        # execute actions
        resolve_claim_actions(GAME_ID, [a1])

        # check region
        region = Regions.load(REGION_ID)
        assert region.data.owner_id == "3"

        # check nation
        nation = Nations.get("1")
        assert f"Failed to claim {REGION_ID}. This region is already owned by another nation." in nation.action_log
        assert nation.get_stockpile("Dollars") == "100.00"
        assert nation.get_stockpile("Political Power") == "50.00"
        assert nation.get_stockpile("Research") == "50.00"
        assert nation.get_stockpile("Food") == "50.00"
        assert nation.get_stockpile("Coal") == "50.00"
        assert nation.get_stockpile("Oil") == "50.00"
        assert nation.get_stockpile("Basic Materials") == "50.00"
        assert nation.get_stockpile("Common Metals") == "50.00"
        assert nation.get_stockpile("Advanced Metals") == "50.00"
        assert nation.get_stockpile("Uranium") == "50.00"
        assert nation.get_stockpile("Rare Earth Elements") == "50.00"

    def test_blocked_by_shortage(self):
        """
        Region claim should fail if player cannot afford it.
        """
        from app.actions import ClaimAction, resolve_claim_actions

        REGION_ID = "CHICA"

        # create and verify action
        a1 = ClaimAction(GAME_ID, "1", f"Claim {REGION_ID}")
        assert a1.is_valid() == True
        assert a1.game_id == GAME_ID
        assert a1.id == "1"
        assert a1.target_region == REGION_ID

        # change nation balance to zero dollars
        nation = Nations.get("1")
        nation.update_stockpile("Dollars", 0, overwrite=True)

        # execute actions
        resolve_claim_actions(GAME_ID, [a1])

        # check region
        region = Regions.load(REGION_ID)
        assert region.data.owner_id == "0"

        # check nation
        assert f"Failed to claim {REGION_ID}. Insufficient dollars." in nation.action_log
        assert nation.get_stockpile("Dollars") == "0.00"
        assert nation.get_stockpile("Political Power") == "50.00"
        assert nation.get_stockpile("Research") == "50.00"
        assert nation.get_stockpile("Food") == "50.00"
        assert nation.get_stockpile("Coal") == "50.00"
        assert nation.get_stockpile("Oil") == "50.00"
        assert nation.get_stockpile("Basic Materials") == "50.00"
        assert nation.get_stockpile("Common Metals") == "50.00"
        assert nation.get_stockpile("Advanced Metals") == "50.00"
        assert nation.get_stockpile("Uranium") == "50.00"
        assert nation.get_stockpile("Rare Earth Elements") == "50.00"

    def test_blocked_by_adjacency(self):
        """
        Region claim should fail if expansion rules are violated.
        """
        from app.actions import ClaimAction, resolve_claim_actions

        REGION_ID = "STEVE"

        # create and verify action
        a1 = ClaimAction(GAME_ID, "1", f"Claim {REGION_ID}")
        assert a1.is_valid() == True
        assert a1.game_id == GAME_ID
        assert a1.id == "1"
        assert a1.target_region == REGION_ID

        # execute actions
        resolve_claim_actions(GAME_ID, [a1])

        # check region
        region = Regions.load(REGION_ID)
        assert region.data.owner_id == "0"

        # check nation
        nation = Nations.get("1")
        assert f"Failed to claim {REGION_ID}. Region is not adjacent to enough regions under your control." in nation.action_log
        assert nation.get_stockpile("Dollars") == "100.00"
        assert nation.get_stockpile("Political Power") == "50.00"
        assert nation.get_stockpile("Research") == "50.00"
        assert nation.get_stockpile("Food") == "50.00"
        assert nation.get_stockpile("Coal") == "50.00"
        assert nation.get_stockpile("Oil") == "50.00"
        assert nation.get_stockpile("Basic Materials") == "50.00"
        assert nation.get_stockpile("Common Metals") == "50.00"
        assert nation.get_stockpile("Advanced Metals") == "50.00"
        assert nation.get_stockpile("Uranium") == "50.00"
        assert nation.get_stockpile("Rare Earth Elements") == "50.00"
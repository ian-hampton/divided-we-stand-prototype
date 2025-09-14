import copy
import csv
import importlib
import heapq
import json
import random
from collections import defaultdict, deque
from typing import List, Tuple

from app import core
from app.nation import Nation, Nations
from app.region import Region
from app.notifications import Notifications

class AllianceCreateAction:

    def __init__(self, game_id: str, nation_id: str, action_str: str):

        self.id = nation_id
        self.game_id = game_id
        self.action_str = action_str
        words = action_str.strip().split()

        index1 = words.index("as")
        index2 = words.index("as") + 1

        self.alliance_name = " ".join(words[2:index1]) if len(words) > 5 else None
        self.alliance_type = " ".join(words[index2:]) if len(words) > 5 else None
    
    def __str__(self):
        return f"[AllianceCreateAction] Alliance Create {self.alliance_name} as {self.alliance_type} ({self.id})"
    
    def is_valid(self) -> bool:
        
        if self.alliance_type is None or self.alliance_name is None:
            print(f"""Action "{self.action_str}" submitted by player {self.id} is invalid. Malformed action.""")
            return False
        
        self.alliance_type = _check_alliance_type(self.game_id, self.alliance_type)
        if self.alliance_type is None:
            print(f"""Action "{self.action_str}" submitted by player {self.id} is invalid. Bad alliance type.""")
            return False
        
        return True

class AllianceJoinAction:

    def __init__(self, game_id: str, nation_id: str, action_str: str):

        self.id = nation_id
        self.game_id = game_id
        self.action_str = action_str
        words = action_str.strip().split()

        self.alliance_name = " ".join(words[2:]) if len(words) > 2 else None
    
    def __str__(self):
        return f"[AllianceJoinAction] Alliance Join {self.alliance_name} ({self.id})"

    def is_valid(self) -> bool:
        
        if self.alliance_name is None:
            print(f"""Action "{self.action_str}" submitted by player {self.id} is invalid. Malformed action.""")
            return False
        
        self.alliance_name = _check_alliance_name(self.game_id, self.alliance_name)
        if self.alliance_name is None:
            print(f"""Action "{self.action_str}" submitted by player {self.id} is invalid. Bad alliance name.""")
            return False
        
        return True

class AllianceKickAction:

    def __init__(self, game_id: str, nation_id: str, action_str: str):

        self.id = nation_id
        self.game_id = game_id
        self.action_str = action_str
        words = action_str.strip().lower().split()

        index1 = words.index("from")
        index2 = words.index("from") + 1

        self.target_nation = " ".join(words[2:index1]) if len(words) > 5 else None
        self.alliance_name = " ".join(words[index2:]) if len(words) > 5 else None

    def __str__(self):
        return f"[AllianceKickAction] Alliance Kick {self.target_nation} from {self.alliance_name} ({self.id})"
    
    def is_valid(self) -> bool:
        
        if self.target_nation is None or self.alliance_name is None:
            print(f"""Action "{self.action_str}" submitted by player {self.id} is invalid. Malformed action.""")
            return False
        
        self.target_nation = _check_nation_name(self.game_id, self.target_nation)
        if self.target_nation is None:
            print(f"""Action "{self.action_str}" submitted by player {self.id} is invalid. Bad nation name.""")
            return False
        
        self.alliance_name = _check_alliance_name(self.game_id, self.alliance_name)
        if self.alliance_name is None:
            print(f"""Action "{self.action_str}" submitted by player {self.id} is invalid. Bad alliance name.""")
            return False
        
        return True

class AllianceLeaveAction:

    def __init__(self, game_id: str, nation_id: str, action_str: str):

        self.id = nation_id
        self.game_id = game_id
        self.action_str = action_str
        words = action_str.strip().split()

        self.alliance_name = " ".join(words[2:]) if len(words) > 2 else None

    def __str__(self):
        return f"[AllianceLeaveAction] Alliance Leave {self.alliance_name} ({self.id})"

    def is_valid(self) -> bool:
        
        if self.alliance_name is None:
            print(f"""Action "{self.action_str}" submitted by player {self.id} is invalid. Malformed action.""")
            return False
        
        self.alliance_name = _check_alliance_name(self.game_id, self.alliance_name)
        if self.alliance_name is None:
            print(f"""Action "{self.action_str}" submitted by player {self.id} is invalid. Bad alliance name.""")
            return False
        
        return True

class ClaimAction:

    def __init__(self, game_id: str, nation_id: str, action_str: str):

        self.id = nation_id
        self.game_id = game_id
        self.action_str = action_str
        words = action_str.strip().split()

        self.target_region = words[1].upper() if len(words) == 2 else None
    
    def __str__(self):
        return f"[ClaimAction] Claim {self.target_region} ({self.id})"

    def is_valid(self) -> bool:
        
        if self.target_region is None:
            print(f"""Action "{self.action_str}" submitted by player {self.id} is invalid. Malformed action.""")
            return False
        
        self.target_region = _check_region_id(self.target_region)
        if self.target_region is None:
            print(f"""Action "{self.action_str}" submitted by player {self.id} is invalid. Bad target region id.""")
            return False
        
        return True

class CrimeSyndicateAction:

    def __init__(self, game_id: str, nation_id: str, action_str: str):

        self.id = nation_id
        self.game_id = game_id
        self.action_str = action_str
        words = action_str.strip().split()

        self.target_nation = " ".join(words[1:]) if len(words) > 1 else None

    def __str__(self):
        return f"[CrimeSyndicateAction] Steal {self.target_nation} ({self.id})"

    def is_valid(self) -> bool:
        
        if self.target_nation is None:
            print(f"""Action "{self.action_str}" submitted by player {self.id} is invalid. Malformed action.""")
            return False
        
        self.target_nation = _check_nation_name(self.game_id, self.target_nation)
        if self.target_nation is None:
            print(f"""Action "{self.action_str}" submitted by player {self.id} is invalid. Bad nation name.""")
            return False
        
        return True
    
class EventAction:

    def __init__(self, game_id: str, nation_id: str, action_str: str):

        self.id = nation_id
        self.game_id = game_id
        self.action_str = action_str
    
    def __str__(self):
        return f"[EventAction] {self.action_str} ({self.id})"

    def is_valid(self) -> bool:
        
        return True

class ImprovementBuildAction:

    def __init__(self, game_id: str, nation_id: str, action_str: str):

        self.id = nation_id
        self.game_id = game_id
        self.action_str = action_str
        words = action_str.strip().split()

        self.improvement_name = " ".join(words[1:-1]) if len(words) > 2 else None
        self.target_region = words[-1].upper() if len(words) > 2 else None

    def __str__(self):
        return f"[ImprovementBuildAction] Build {self.improvement_name} {self.target_region} ({self.id})"

    def is_valid(self) -> bool:
        
        if self.improvement_name is None and self.target_region is None:
            print(f"""Action "{self.action_str}" submitted by player {self.id} is invalid. Malformed action.""")
            return False
        
        self.improvement_name = _check_improvement_name(self.game_id, self.improvement_name)
        if self.improvement_name is None:
            print(f"""Action "{self.action_str}" submitted by player {self.id} is invalid. Bad improvement name.""")
            return False
        
        self.target_region = _check_region_id(self.target_region)
        if self.target_region is None:
            print(f"""Action "{self.action_str}" submitted by player {self.id} is invalid. Bad target region id.""")
            return False
        
        return True

class ImprovementRemoveAction:

    def __init__(self, game_id: str, nation_id: str, action_str: str):

        self.id = nation_id
        self.game_id = game_id
        self.action_str = action_str
        words = action_str.strip().split()

        self.target_region = words[1].upper() if len(words) == 2 else None

    def __str__(self):
        return f"[ImprovementRemoveAction] Remove {self.target_region} ({self.id})"

    def is_valid(self) -> bool:
        
        if self.target_region is None:
            print(f"""Action "{self.action_str}" submitted by player {self.id} is invalid. Malformed action.""")
            return False
        
        self.target_region = _check_region_id(self.target_region)
        if self.target_region is None:
            print(f"""Action "{self.action_str}" submitted by player {self.id} is invalid. Bad target region id.""")
            return False
        
        return True

class MarketBuyAction:

    def __init__(self, game_id: str, nation_id: str, action_str: str):

        self.id = nation_id
        self.game_id = game_id
        self.action_str = action_str
        words = action_str.strip().split()

        self.quantity = words[1] if len(words) > 2 else None
        self.resource_name = " ".join(words[2:]) if len(words) > 2 else None

    def __str__(self):
        return f"[MarketBuyAction] Buy {self.quantity} {self.resource_name} ({self.id})"

    def is_valid(self) -> bool:
        
        if self.quantity is None or self.resource_name is None:
            print(f"""Action "{self.action_str}" submitted by player {self.id} is invalid. Malformed action.""")
            return False
        
        self.quantity = _check_quantity(self.quantity)
        if self.quantity is None:
            print(f"""Action "{self.action_str}" submitted by player {self.id} is invalid. Bad quantity.""")
            return False
        
        self.resource_name = _check_resource(self.resource_name)
        if self.resource_name is None:
            print(f"""Action "{self.action_str}" submitted by player {self.id} is invalid. Bad resource name.""")
            return False
        
        return True

class MarketSellAction:

    def __init__(self, game_id: str, nation_id: str, action_str: str):

        self.id = nation_id
        self.game_id = game_id
        self.action_str = action_str
        words = action_str.strip().split()

        self.quantity = words[1] if len(words) > 2 else None
        self.resource_name = " ".join(words[2:]) if len(words) > 2 else None

    def __str__(self):
        return f"[MarketSellAction] Sell {self.quantity} {self.resource_name} ({self.id})"

    def is_valid(self) -> bool:
        
        if self.quantity is None or self.resource_name is None:
            print(f"""Action "{self.action_str}" submitted by player {self.id} is invalid. Malformed action.""")
            return False
        
        self.quantity = _check_quantity(self.quantity)
        if self.quantity is None:
            print(f"""Action "{self.action_str}" submitted by player {self.id} is invalid. Bad quantity.""")
            return False
        
        self.resource_name = _check_resource(self.resource_name)
        if self.resource_name is None:
            print(f"""Action "{self.action_str}" submitted by player {self.id} is invalid. Bad resource name.""")
            return False
        
        return True

class MissileMakeAction:

    def __init__(self, game_id: str, nation_id: str, action_str: str):

        self.id = nation_id
        self.game_id = game_id
        self.action_str = action_str
        words = action_str.strip().split()

        self.quantity = words[1] if len(words) > 2 else None
        self.missile_type = " ".join(words[2:]) if len(words) > 2 else None

    def __str__(self):
        return f"[MissileMakeAction] Make {self.quantity} {self.missile_type} ({self.id})"

    def is_valid(self) -> bool:
        
        if self.quantity is None or self.missile_type is None:
            print(f"""Action "{self.action_str}" submitted by player {self.id} is invalid. Malformed action.""")
            return False
        
        self.quantity = _check_quantity(self.quantity)
        if self.quantity is None:
            print(f"""Action "{self.action_str}" submitted by player {self.id} is invalid. Bad quantity.""")
            return False
        
        self.missile_type = _check_missile(self.game_id, self.missile_type)
        if self.missile_type is None:
            print(f"""Action "{self.action_str}" submitted by player {self.id} is invalid. Bad missile type.""")
            return False
        
        return True

class MissileLaunchAction:

    def __init__(self, game_id: str, nation_id: str, action_str: str):

        self.id = nation_id
        self.game_id = game_id
        self.action_str = action_str
        words = action_str.strip().split()

        self.missile_type = " ".join(words[1:-1]) if len(words) > 2 else None
        self.target_region = words[-1].upper() if len(words) > 2 else None

    def __str__(self):
        return f"[MissileLaunchAction] Launch {self.missile_type} {self.target_region} ({self.id})"

    def is_valid(self) -> bool:
        
        if self.missile_type is None or self.target_region is None:
            print(f"""Action "{self.action_str}" submitted by player {self.id} is invalid. Malformed action.""")
            return False
        
        self.missile_type = _check_missile(self.game_id, self.missile_type)
        if self.missile_type is None:
            print(f"""Action "{self.action_str}" submitted by player {self.id} is invalid. Bad missile type.""")
            return False
        
        self.target_region = _check_region_id(self.target_region)
        if self.target_region is None:
            print(f"""Action "{self.action_str}" submitted by player {self.id} is invalid. Bad target region id.""")
            return False
        
        return True

class RepublicAction:

    def __init__(self, game_id: str, nation_id: str, action_str: str):

        self.id = nation_id
        self.game_id = game_id
        self.action_str = action_str
        words = action_str.strip().split()

        self.resource_name = " ".join(words[1:]) if len(words) > 1 else None

    def __str__(self):
        return f"[RepublicAction] Republic {self.resource_name} ({self.id})"

    def is_valid(self) -> bool:

        if self.resource_name is None:
            print(f"""Action "{self.action_str}" submitted by player {self.id} is invalid. Malformed action.""")
            return False
        
        self.resource_name = _check_resource(self.resource_name)
        if self.resource_name is None:
            print(f"""Action "{self.action_str}" submitted by player {self.id} is invalid. Bad resource name.""")
            return False
        
        return True

class ResearchAction:

    def __init__(self, game_id: str, nation_id: str, action_str: str):

        self.id = nation_id
        self.game_id = game_id
        self.action_str = action_str
        words = action_str.strip().split()

        self.research_name = " ".join(words[1:]) if len(words) > 1 else None

    def __str__(self):
        return f"[ResearchAction] Research {self.research_name} ({self.id})"

    def is_valid(self) -> bool:
        
        if self.research_name is None:
            print(f"""Action "{self.action_str}" submitted by player {self.id} is invalid. Malformed action.""")
            return False
        
        self.research_name = _check_research(self.game_id, self.research_name)
        if self.research_name is None:
            print(f"""Action "{self.action_str}" submitted by player {self.id} is invalid. Bad research name.""")
            return False
        
        return True

class SurrenderAction:

    def __init__(self, game_id: str, nation_id: str, action_str: str):

        self.id = nation_id
        self.game_id = game_id
        self.action_str = action_str
        words = action_str.strip().split()

        self.target_nation = " ".join(words[1:]) if len(words) > 1 else None

    def __str__(self):
        return f"[SurrenderAction] Surrender {self.target_nation} ({self.id})"

    def is_valid(self) -> bool:
        
        if self.target_nation is None:
            print(f"""Action "{self.action_str}" submitted by player {self.id} is invalid. Malformed action.""")
            return False
        
        self.target_nation = _check_nation_name(self.game_id, self.target_nation)
        if self.target_nation is None:
            print(f"""Action "{self.action_str}" submitted by player {self.id} is invalid. Bad nation name.""")
            return False
        
        return True

class UnitDeployAction:

    def __init__(self, game_id: str, nation_id: str, action_str: str):

        self.id = nation_id
        self.game_id = game_id
        self.action_str = action_str
        words = action_str.strip().split()

        self.unit_name = " ".join(words[1:-1]) if len(words) > 2 else None
        self.target_region = words[-1].upper() if len(words) > 2 else None

    def __str__(self):
        return f"[UnitDeployAction] Deploy {self.unit_name} {self.target_region} ({self.id})"

    def is_valid(self) -> bool:
        
        if self.unit_name is None or self.target_region is None:
            print(f"""Action "{self.action_str}" submitted by player {self.id} is invalid. Malformed action.""")
            return False
        
        self.unit_name = _check_unit(self.game_id, self.unit_name)
        if self.unit_name is None:
            print(f"""Action "{self.action_str}" submitted by player {self.id} is invalid. Bad unit name.""")
            return False

        self.target_region = _check_region_id(self.target_region)
        if self.target_region is None:
            print(f"""Action "{self.action_str}" submitted by player {self.id} is invalid. Bad target region id.""")
            return False
        
        return True

class UnitDisbandAction:

    def __init__(self, game_id: str, nation_id: str, action_str: str):

        self.id = nation_id
        self.game_id = game_id
        self.action_str = action_str
        words = action_str.strip().split()

        self.target_region = words[-1].upper() if len(words) > 1 else None

    def __str__(self):
        return f"[UnitDisbandAction] Disband {self.target_region} ({self.id})"

    def is_valid(self) -> bool:
        
        if self.target_region is None:
            print(f"""Action "{self.action_str}" submitted by player {self.id} is invalid. Malformed action.""")
            return False
        
        self.target_region = _check_region_id(self.target_region)
        if self.target_region is None:
            print(f"""Action "{self.action_str}" submitted by player {self.id} is invalid. Bad target region id.""")
            return False
        
        return True

class UnitMoveAction:

    def __init__(self, game_id: str, nation_id: str, action_str: str):

        self.id = nation_id
        self.game_id = game_id
        self.action_str = action_str
        words = action_str.strip().split()

        self.current_region_id = None
        self.target_region_ids = None
        
        if len(words) > 1:

            # get starting region
            regions = words[1].split("-")
            self.current_region_id = regions[0].upper()
            
            # list of target region ids will be a stack
            self.target_region_ids = []
            if len(regions) > 1:
                for region_id in regions[:0:-1]:
                    self.target_region_ids.append(region_id.upper())

    def __str__(self):
        return f"[UnitMoveAction] Move {self.current_region_id} {self.target_region_ids} ({self.id})"

    def is_valid(self) -> bool:
        
        if self.current_region_id is None or self.target_region_ids is None:
            print(f"""Action "{self.action_str}" submitted by player {self.id} is invalid. Malformed action.""")
            return False
        
        self.current_region_id = _check_region_id(self.current_region_id)
        if self.current_region_id is None:
            print(f"""Action "{self.action_str}" submitted by player {self.id} is invalid. Bad starting region id.""")
            return False
        
        for region_id in self.target_region_ids:
            region_id = _check_region_id(region_id)
            if region_id is None:
                print(f"""Action "{self.action_str}" submitted by player {self.id} is invalid. Bad destination region id: {region_id}.""")
                return False
        
        return True

class WarAction:

    def __init__(self, game_id: str, nation_id: str, action_str: str):

        self.id = nation_id
        self.game_id = game_id
        self.action_str = action_str
        words = action_str.strip().lower().split()

        nnei = words.index("using")
        wjsi = words.index("using") + 1

        self.target_nation = " ".join(words[1:nnei]) if len(words) > 3 else None
        self.war_justification = " ".join(words[wjsi:]) if len(words) > 3 else None

    def __str__(self):
        return f"[WarAction] War {self.target_nation} using {self.war_justification} ({self.id})"

    def is_valid(self) -> bool:
        
        if self.target_nation is None or self.war_justification is None:
            print(f"""Action "{self.action_str}" submitted by player {self.id} is invalid. Malformed action.""")
            return False
        
        self.target_nation = _check_nation_name(self.game_id, self.target_nation)
        if self.target_nation is None:
            print(f"""Action "{self.action_str}" submitted by player {self.id} is invalid. Bad nation name.""")
            return False
        
        self.war_justification = _check_war_justification(self.game_id, self.war_justification)
        if self.war_justification is None:
            print(f"""Action "{self.action_str}" submitted by player {self.id} is invalid. Bad war justification.""")
            return False
        
        return True

class WarJoinAction:

    def __init__(self, game_id: str, nation_id: str, action_str: str):

        self.id = nation_id
        self.game_id = game_id
        self.action_str = action_str
        words = action_str.strip().lower().split()

        wnei = words.index("as")
        wjsi = words.index("using") + 1

        self.war_name = " ".join(words[2:wnei]) if len(words) > 7 else None
        self.side = words[wnei + 1].title() if len(words) > 7 else None
        self.war_justification = " ".join(words[wjsi:]) if len(words) > 7 else None

    def __str__(self):
        return f"[WarJoinAction] War Join {self.war_name} as {self.side} using ({self.id})"
    
    def is_valid(self) -> bool:

        if self.war_name is None or self.side is None or self.war_justification is None:
            print(f"""Action "{self.action_str}" submitted by player {self.id} is invalid. Malformed action.""")
            return False
        
        self.war_name = _check_war_name(self.game_id, self.war_name)
        if self.war_name is None:
            print(f"""Action "{self.action_str}" submitted by player {self.id} is invalid. Bad war name.""")
            return False
        
        if self.side not in ["Attacker", "Defender"]:
            print(f"""Action "{self.action_str}" submitted by player {self.id} is invalid. Expecting "Attacker" or "Defender" for war side.""")
            return False
        
        self.war_justification = _check_war_justification(self.game_id, self.war_justification)
        if self.war_justification is None:
            print(f"""Action "{self.action_str}" submitted by player {self.id} is invalid. Bad war justification.""")
            return False
    
        return True

class WhitePeaceAction:

    def __init__(self, game_id: str, nation_id: str, action_str: str):

        self.id = nation_id
        self.game_id = game_id
        self.action_str = action_str
        words = action_str.strip().split()

        self.target_nation = " ".join(words[2:]) if len(words) > 2 else None

    def __str__(self):
        return f"[WhitePeaceAction] White Peace {self.target_nation} ({self.id})"
    
    def is_valid(self) -> bool:
        
        if self.target_nation is None:
            print(f"""Action "{self.action_str}" submitted by player {self.id} is invalid. Malformed action.""")
            return False
        
        self.target_nation = _check_nation_name(self.game_id, self.target_nation)
        if self.target_nation is None:
            print(f"""Action "{self.action_str}" submitted by player {self.id} is invalid. Bad nation name.""")
            return False
        
        return True

def validate_action(game_id: str, nation_id: str, action_str: str) -> any:
    """
    Creates action object and validates it.

    Params:
        nation_id (int): ID of nation/player.
        action_str (str): Raw action string.
    
    Returns:
        An action class or None if action canceled.
    """

    while True:
        
        action = _create_action(game_id, nation_id, action_str)
        if action is None:
            return

        if action.is_valid():
            return action
        
        action_str = input("Re-enter action or hit enter to skip: ")
        if action_str == "":
            return

def _create_action(game_id: str, nation_id: str, action_str: str) -> any:
    """
    Factory method helper function that creates the action object.

    Params:
        nation_id (int): ID of nation/player.
        action_str (str): Raw action string.
    
    Returns:
        An action class or None if action canceled.
    """

    actions = {
        "alliance create": AllianceCreateAction,
        "alliance join": AllianceJoinAction,
        "alliance kick": AllianceKickAction,
        "alliance leave": AllianceLeaveAction,
        "claim": ClaimAction,
        "steal": CrimeSyndicateAction,
        "event": EventAction,
        "build": ImprovementBuildAction,
        "remove": ImprovementRemoveAction,
        "buy": MarketBuyAction,
        "sell": MarketSellAction,
        "make": MissileMakeAction,
        "launch": MissileLaunchAction,
        "republic": RepublicAction,
        "research": ResearchAction,
        "surrender": SurrenderAction,
        "deploy": UnitDeployAction,
        "disband": UnitDisbandAction,
        "move": UnitMoveAction,
        "war": WarAction,
        "white peace": WhitePeaceAction
    }

    action_str = action_str.strip().lower()

    while True:

        if action_str == "":
            return
        
        for action_key in sorted(actions.keys(), key=len, reverse=True):
            if action_str.startswith(action_key):
                return actions[action_key](game_id, nation_id, action_str)
        
        scenario_action = _check_scenario_actions(game_id, nation_id, action_str)
        if scenario_action is not None:
            return scenario_action
        
        print(f"Action \"{action_str}\" submitted by player {nation_id} is invalid. Unrecognized action type.")
        action_str = input("Re-enter action or hit enter to skip: ")

def _check_scenario_actions(game_id: str, nation_id: str, action_str: str) -> any:
    
    from app.scenario import ScenarioData as SD
    
    scenario_actions = importlib.import_module(f"scenarios.{SD.scenario}.actions")

    return scenario_actions._create_action(game_id, nation_id, action_str)

def _check_alliance_type(game_id: str, input_str: str) -> str | None:
    
    from app.scenario import ScenarioData as SD

    for alliance_type, alliance_type_data in SD.alliances:
        if input_str.lower() == alliance_type.lower():
            return alliance_type
    
    return None

def _check_alliance_name(game_id: str, input_str: str) -> str | None:
    
    from app.alliance import Alliances

    for alliance in Alliances:
        if input_str.lower() == alliance.name.lower():
            return alliance.name
        
    return None

def _check_region_id(region_id: str) -> str | None:

    # region_id string is already converted to all uppercase, so we can just check if it exists or not 
    
    from app.region import Regions
    
    if region_id in Regions:
        return region_id
    
    return None

def _check_nation_name(game_id: str, input_str: str) -> str | None:

    from app.nation import Nations

    for nation in Nations:
        if input_str.lower() == nation.name.lower():
            return nation.name
        
    return None

def _check_improvement_name(game_id: str, input_str: str) -> str | None:

    from app.scenario import ScenarioData as SD

    improvement_errors = {
        "amm": "Advanced Metals Mine",
        "advanced metal mine": "Advanced Metals Mine",
        "barracks": "Boot Camp",
        "bootcamp": "Boot Camp",
        "bank": "Central Bank",
        "cmm": "Common Metals Mine",
        "common metal mine": "Common Metals Mine",
        "iz": "Industrial Zone",
        "inz": "Industrial Zone",
        "idz": "Industrial Zone",
        "indz": "Industrial Zone",
        "base": "Military Base",
        "mds": "Missile Defense System",
        "defense system": "Missile Defense System",
        "silo": "Missile Silo",
        "npp": "Nuclear Power Plant",
        "power plant": "Nuclear Power Plant",
        "well": "Oil Well",
        "ree": "Rare Earth Elements Mine",
        "reem": "Rare Earth Elements Mine",
        "ree mine": "Rare Earth Elements Mine",
        "rare earth element mine": "Rare Earth Elements Mine",
        "rare earth metal mine": "Rare Earth Elements Mine",
        "rare earth metals mine": "Rare Earth Elements Mine",
        "inst": "Research Institute",
        "institute": "Research Institute",
        "lab": "Research Laboratory",
        "research lab": "Research Laboratory",
        "laboratory": "Research Laboratory",
        "solar panel": "Solar Farm",
        "solar panels": "Solar Farm",
        "radioactive element mine ": "Uranium Mine",
        "radioactive elements mine ": "Uranium Mine",
        "wind turbine": "Wind Farm",
        "wind turbines": "Wind Farm"
    }

    for improvement_name, improvement_data in SD.improvements:
        if input_str.lower() == improvement_name.lower():
            return improvement_name
    
    return improvement_errors.get(input_str.lower())

def _check_quantity(quantity: str) -> int | None:
    
    try:
        quantity = int(quantity)       
        return quantity
    except:
        return None
    
def _check_resource(resource_name: str) -> str | None:

    # TODO - make this check reference game files
    resources = {
        "Dollars",
        "Political Power",
        "Research",
        "Food",
        "Coal",
        "Oil",
        "Basic Materials",
        "Common Metals",
        "Advanced Metals",
        "Uranium",
        "Rare Earth Elements"
    }

    resource_errors = {
        "tech": "Research",
        "basic material": "Basic Materials",
        "common metal": "Common Metals",
        "advanced metal": "Advanced Metals",
        "ree": "Rare Earth Elements",
        "rare earth element": "Rare Earth Elements",
        "rareearthelements": "Rare Earth Elements",
        "politicalpower": "Political Power",
        "commonmetals": "Common Metals",
        "advancedmetals": "Advanced Metals",
        "basicmaterials": "Basic Materials",
    }

    resource_name = resource_name.replace(":", "")
    if resource_name.title() in resources:
        return resource_name.title()
    
    resource_name = resource_name.lower()
    return resource_errors.get(resource_name)

def _check_missile(game_id: str, input_str: str) -> str | None:
    
    from app.scenario import ScenarioData as SD

    missile_errors = {
        "missile": "Standard Missile",
        "missiles": "Standard Missile",
        "standard missiles": "Standard Missile",
        "nuke": "Nuclear Missile",
        "nukes": "Nuclear Missile",
        "nuclear missiles": "Nuclear Missile"
    }

    for missile_type, missile_type_data in SD.missiles:
        if input_str.lower() == missile_type.lower():
            return missile_type
        
    return missile_errors.get(input_str.lower())

def _check_research(game_id: str, input_str: str) -> str | None:

    from app.scenario import ScenarioData as SD
    
    research_names = set(SD.agendas.names()).union(SD.technologies.names())

    for name in research_names:
        if input_str.lower() == name.lower():
            return name
        
    return None

def _check_unit(game_id: str, input_str: str) -> str | None:
    
    from app.scenario import ScenarioData as SD
    
    for unit_name, unit_data in SD.units:
        if (input_str.lower() == unit_name.lower()
            or input_str.upper() == unit_data.abbreviation):
            return unit_name
        
    return None

def _check_war_name(game_id: str, input_str: str) -> str | None:

    from app.war import Wars

    for war in Wars:
        if input_str.lower() == war.name.lower():
            return war.name
        
    return None

def _check_war_justification(game_id: str, input_str: str) -> str | None:

    from app.scenario import ScenarioData as SD
    
    for justification_name, justification_data in SD.war_justificiations:
        if input_str.lower() == justification_name.lower():
            return justification_name
        
    return None

def resolve_trade_actions(game_id: str) -> None:
    """
    Resolves trade actions between players via CLI.
    """

    from app.nation import Nations
    from app.region import Regions

    trade_action = input("Are there any trade actions this turn? (Y/n) ")

    while trade_action.upper().strip() != "N":
        
        # get nations
        nation_name_1 = input("Enter 1st nation name: ")
        nation_name_2 = input("Enter 2nd nation name: ")
        try:
            nation1 = Nations.get(nation_name_1)
            nation2 = Nations.get(nation_name_2)
        except:
            print("Invalid nation name(s) were given. Please try again.")
            continue

        # get trade fees
        nation1_fee = int(nation1.trade_fee[0]) / int(nation1.trade_fee[2])
        nation2_fee = int(nation2.trade_fee[0]) / int(nation2.trade_fee[2])

        # get trade resources
        trade_resources = []
        for resource_name in nation1._resources:
            if resource_name not in ["Energy", "Military Capacity"]:
                trade_resources.append(resource_name)
        
        # print table
        print(f"Trade Between {nation1.name} and {nation2.name}")
        print("{:<21s}{:<33s}{:<33s}".format("Resource", nation1.name, nation2.name))
        for resource_name in trade_resources:
            print("{:<21s}{:<33s}{:<33s}".format(resource_name, nation1.get_stockpile(resource_name), nation2.get_stockpile(resource_name)))
        
        # create trade deal dict
        trade_valid = True
        trade_deal = {}
        for resource_name in trade_resources:
            trade_deal[resource_name] = 0.00
        trade_deal["Nation1RegionsCeded"] = []
        trade_deal["Nation2RegionsCeded"] = []

        # resource trade
        resource_trade = input("Will any resources be traded in this deal? (Y/n) ")
        if resource_trade.upper().strip() != "N":
            for resource_name in trade_resources:
                resource_count = float(input(f"Enter {resource_name} amount: "))
                trade_deal[resource_name] = resource_count

        # region trade
        resource_trade = input("Will any regions be traded in this deal? (Y/n) ")
        if resource_trade.upper().strip() != "N":
            
            invalid_region_given = True
            while invalid_region_given:
                nation_region_trades_str = input(f'Enter regions {nation1.name} is trading away: ')
                nation_region_trades_str = nation_region_trades_str.upper().strip().replace(" ", "")
                nation_region_trades_list = nation_region_trades_str.split(',')
                invalid_region_given = False
                for region_id in nation_region_trades_list:
                    if region_id not in Regions:
                        invalid_region_given = True
                        print(f"{region_id} is invalid. Please try again.")
                        break
            trade_deal["Nation1RegionsCeded"].extend(nation_region_trades_list)
            
            invalid_region_given = True
            while invalid_region_given:
                nation_region_trades_str = input(f'Enter regions {nation2.name} is trading away: ')
                nation_region_trades_str = nation_region_trades_str.upper().strip().replace(" ", "")
                nation_region_trades_list = nation_region_trades_str.split(',')
                invalid_region_given = False
                for region_id in nation_region_trades_list:
                    if region_id not in Regions:
                        invalid_region_given = True
                        print(f"{region_id} is invalid. Please try again.")
                        break
            trade_deal["Nation2RegionsCeded"].extend(nation_region_trades_list)
        
        # process traded resources
        for resource_name in trade_resources:
            amount = trade_deal[resource_name]
            
            if amount > 0:
                # positive amount -> nation 2
                nation1.update_stockpile(resource_name, -1 * amount)
                nation2.update_stockpile(resource_name, amount)
                nation1.stats.resources_given += abs(amount)
                # pay trade fee
                nation1.update_stockpile("Dollars", -1 * abs(amount) * nation1_fee)
            
            elif amount < 0:
                # negative amount -> nation 1
                nation1.update_stockpile(resource_name, -1 * amount)
                nation2.update_stockpile(resource_name, amount)
                nation2.stats.resources_given += abs(amount)
                # pay trade fee
                nation2.update_stockpile("Dollars", -1 * abs(amount) * nation2_fee)

            # validate transaction
            if float(nation1.get_stockpile("Dollars")) < 0 or float(nation2.get_stockpile("Dollars")) < 0:
                trade_valid = False
                break
            if float(nation1.get_stockpile(resource_name)) < 0 or float(nation2.get_stockpile(resource_name)) < 0:
                trade_valid = False
                break

        # process traded regions
        if trade_valid:
            
            for region_id in trade_deal["Nation1RegionsCeded"]:
                
                region = Region(region_id)

                if region.improvement.name is not None:
                    nation1.improvement_counts[region.improvement.name] -= 1
                    nation2.improvement_counts[region.improvement.name] += 1

                region.data.owner_id = nation2.id
            
            for region_id in trade_deal["Nation2RegionsCeded"]:
                
                region = Region(region_id)

                if region.improvement.name is not None:
                    nation1.improvement_counts[region.improvement.name] += 1
                    nation2.improvement_counts[region.improvement.name] -= 1

                region.data.owner_id = nation1.id

        # save changes
        if trade_valid:
            Notifications.add(f'{nation1.name} traded with {nation2.name}.', 10)
        else:
            print(f'Trade between {nation1.name} and {nation2.name} failed. Insufficient resources.')

        trade_action = input("Are there any additional trade actions this turn? (Y/n) ")

def resolve_peace_actions(game_id: str, surrender_list: list[SurrenderAction], white_peace_list: list[WhitePeaceAction]) -> None:
    
    # get game data
    from app.nation import Nations
    from app.war import Wars
    current_turn_num = core.get_current_turn_num(game_id)

    # execute surrender actions
    for action in surrender_list:
        
        surrendering_nation = Nations.get(action.id)
        winning_nation = Nations.get(action.target_nation)

       # check if peace is possible
        if not _peace_action_valid(surrendering_nation, winning_nation, current_turn_num):
            continue

        # get war and war outcome
        war_name = Wars.get_war_name(surrendering_nation.id, winning_nation.id)
        war = Wars.get(war_name)
        c1 = war.get_combatant(surrendering_nation.id)
        if 'Attacker' in c1.role:
            outcome = "Defender Victory"
        else:
            outcome = "Attacker Victory"

        # end war
        war.end_conflict(outcome)
        Notifications.add(f"{surrendering_nation.name} surrendered to {winning_nation.name}.", 5)
        Notifications.add(f"{war_name} has ended.", 5)

    # execute white peace actions
    white_peace_dict = {}
    for action in white_peace_list:
        
        surrendering_nation = Nations.get(action.id)
        winning_nation = Nations.get(action.target_nation)

        # check if peace is possible
        if not _peace_action_valid(surrendering_nation, winning_nation, current_turn_num):
            continue

        # add white peace request to white_peace_dict
        war_name = Wars.get_war_name(surrendering_nation.id, winning_nation.id)
        if war_name in white_peace_dict:
            white_peace_dict[war_name] += 1
        else:
            white_peace_dict[war_name] = 1

    # process white peace if both sides agreed
    for war_name in white_peace_dict:
        if white_peace_dict[war_name] == 2:
            war = Wars.get(war_name)
            war.end_conflict("White Peace")
            Notifications.add(f'{war_name} has ended with a white peace.', 5)

def _peace_action_valid(surrendering_nation: Nation, winning_nation: Nation, current_turn_num: int) -> bool:

    from app.war import Wars

    # check that war exists
    war_name = Wars.get_war_name(surrendering_nation.id, winning_nation.id)
    if war_name is None:
        surrendering_nation.action_log.append(f"Failed to surrender to {winning_nation.name}. You are not at war with that nation.")
        return False

    # check that surrendee(?) has authority to surrender
    war = Wars.get(war_name)
    c1 = war.get_combatant(surrendering_nation.id)
    c2 = war.get_combatant(winning_nation.id)
    if 'Main' not in c1.role or 'Main' not in c2.role:
        surrendering_nation.action_log.append(f"Failed to surrender to {winning_nation.name}. You are not the main attacker/defender or {winning_nation.name} is not the main attacker/defender.")
        return False

    # check that it has been 4 turns since war began
    if current_turn_num - war.start < 4:
        surrendering_nation.action_log.append(f"Failed to surrender to {winning_nation.name}. At least four turns must pass before peace can be made.")
        return False

    return True

def resolve_research_actions(game_id: str, actions_list: list[ResearchAction]) -> None:
    
    from app.scenario import ScenarioData as SD
    from app.alliance import Alliances
    from app.nation import Nations

    for action in actions_list:
        
        nation = Nations.get(action.id)

        if action.research_name in nation.completed_research:
            nation.action_log.append(f"Failed to research {action.research_name}. You have already researched this.")
            continue

        if any("No Agenda Research" in tag_data for tag_data in nation.tags.values()):
            nation.action_log.append(f"Failed to research {action.research_name} due to an event penalty.")
            continue

        if action.research_name in SD.agendas:
            
            sd_agenda = SD.agendas[action.research_name]
            cost = sd_agenda.cost
            prereq = sd_agenda.prerequisite

            if prereq != None and prereq not in nation.completed_research:
                nation.action_log.append(f"Failed to research {action.research_name}. You do not have the prerequisite research.")
                continue

            cost += nation.calculate_agenda_cost_adjustment(action.research_name)

            if float(nation.get_stockpile("Political Power")) - cost < 0:
                nation.action_log.append(f"Failed to research {action.research_name}. Not enough political power.")
                continue

            nation.update_stockpile("Political Power", -1 * cost)
            nation.action_log.append(f"Researched {action.research_name} for {cost} political power.")
            nation.add_tech(action.research_name)

        else:
            
            sd_technology = SD.technologies[action.research_name]
            cost = sd_technology.cost
            prereq = sd_technology.prerequisite

            if prereq != None and prereq not in nation.completed_research:
                nation.action_log.append(f"Failed to research {action.research_name}. You do not have the prerequisite research.")
                continue

            multiplier = 1.0
            for alliance in Alliances:
                if alliance.is_active and nation.name in alliance.current_members and alliance.type == "Research Agreement":
                    for ally_name in alliance.current_members:
                        ally_nation = Nations.get(ally_name)
                        if ally_name == nation.name:
                            continue
                        if action.research_name in ally_nation.completed_research:
                            multiplier -= 0.2
                            break
            if multiplier < 0:
                multiplier = 0.2
            if multiplier != 1.0:
                cost *= multiplier
                cost = int(cost)

            if float(nation.get_stockpile("Research")) - cost < 0:
                nation.action_log.append(f"Failed to research {action.research_name}. Not enough technology.")
                continue

            nation.update_stockpile("Research", -1 * cost)
            nation.action_log.append(f"Researched {action.research_name} for {cost} technology.")
            nation.add_tech(action.research_name)
            nation.award_research_bonus(action.research_name)

def resolve_alliance_leave_actions(game_id: str, actions_list: list[AllianceLeaveAction]) -> None:
    
    from app.alliance import Alliances
    from app.nation import Nations

    for action in actions_list:

        nation = Nations.get(action.id)
        alliance = Alliances.get(action.alliance_name)

        alliance.remove_member(nation.name)
        Notifications.add(f"{nation.name} has left the {alliance.name}.", 8)
        nation.action_log.append(f"Left {action.alliance_name}.")

def resolve_alliance_kick_actions(game_id: str, actions_list: list[AllianceKickAction]) -> None:
    
    from app.alliance import Alliances
    from app.nation import Nations

    kick_actions_tally = defaultdict(lambda: defaultdict(int))
    
    for action in actions_list:
        
        nation = Nations.get(action.id)
        target_nation = Nations.get(action.target_nation)
        alliance = Alliances.get(action.alliance_name)

        if action.target_nation not in alliance.current_members:
            nation.action_log.append(f"Failed to vote to kick {action.target_nation} from {action.alliance_name}. You are not in the alliance.")
            continue

        if action.target_nation not in alliance.current_members:
            nation.action_log.append(f"Failed to vote to kick {action.target_nation} from {action.alliance_name}. Target nation is not in the alliance.")
            continue

        if action.target_nation in alliance.founding_members and "Alliance Centralization" in target_nation.completed_research:
            nation.action_log.append(f"Failed to vote to kick {action.target_nation} from {action.alliance_name}. Target nation is a founder of the alliance.")
            continue

        kick_actions_tally[alliance.name][action.target_nation] += 1
        nation.action_log.append(f"Voted to kick {action.target_nation} from {action.alliance_name}.")

    for alliance_name, kick_tally in kick_actions_tally.items():
        for target_nation_name, votes in kick_tally.items():
            alliance = Alliances.get(alliance_name)
            if votes >= len(alliance.current_members) - 1:
                alliance.remove_member(target_nation_name)
                Notifications.add(f"{action.target_nation} has been kicked from {action.alliance_name}!", 8)

def resolve_alliance_create_actions(game_id: str, actions_list: list[AllianceCreateAction]) -> None:
    
    from app.scenario import ScenarioData as SD
    from app.alliance import Alliances
    from app.nation import Nations

    alliance_creation_dict = {}
    
    for action in actions_list:

        nation = Nations.get(action.id)
        sd_alliance = SD.alliances[action.alliance_type]
        
        if sd_alliance.required_agenda not in nation.completed_research:
            nation.action_log.append(f"Failed to form {action.alliance_name} alliance. You do not have the required agenda.")
            continue

        if sd_alliance.capacity:
            alliance_count, alliance_capacity = nation.calculate_alliance_capacity()
            if (alliance_count + 1) > alliance_capacity:
                nation.action_log.append(f"Failed to form {action.alliance_name} alliance. You do not have enough alliance capacity.")
                continue

        if action.alliance_name in alliance_creation_dict:
            alliance_creation_dict[action.alliance_name]["members"].append(nation.name)
        else:
            entry = {}
            entry["type"] = action.alliance_type
            entry["members"] = [nation.name]
            alliance_creation_dict[action.alliance_name] = entry
        
    for alliance_name, alliance_data in alliance_creation_dict.items():
        
        # alliance creation success
        if len(alliance_data["members"]) >= 2:
            Alliances.create(alliance_name, alliance_data["type"], alliance_data["members"])
            Notifications.add(f"{alliance_name} has formed.", 8)
            for nation_name in alliance_data["members"]:
                nation = Nations.get(nation_name)
                nation.action_log.append(f"Successfully formed {action.alliance_name}.")
            continue

        # alliance creation failed
        nation_name = alliance_data["members"][0]
        nation = Nations.get(nation_name)
        nation.action_log.append(f"Failed to form {action.alliance_name} alliance. Not enough players agreed to establish it.")

def resolve_alliance_join_actions(game_id: str, actions_list: list[AllianceJoinAction]) -> None:
    
    from app.scenario import ScenarioData as SD
    from app.alliance import Alliances
    from app.nation import Nations

    for action in actions_list:
        
        nation = Nations.get(action.id)
        alliance = Alliances.get(action.alliance_name)
        sd_alliance = SD.alliances[alliance.type]

        if sd_alliance.required_agenda not in nation.completed_research:
            nation.action_log.append(f"Failed to join {action.alliance_name} alliance. You do not have the required agenda.")
            continue

        if sd_alliance.capacity:
            alliance_count, alliance_capacity = nation.calculate_alliance_capacity()
            if (alliance_count + 1) > alliance_capacity:
                nation.action_log.append(f"Failed to join {action.alliance_name} alliance. You do not have enough alliance capacity.")
                continue

        if "Puppet State" in nation.status:
            nation.action_log.append(f"Failed to join {action.alliance_name} alliance. Puppet states cannot join alliances.")
            continue

        if "Faustian Bargain" in nation.tags:
            nation.action_log.append(f"Failed to join {action.alliance_name} alliance. The collaborator cannot join alliances.")
            continue

        alliance.add_member(nation.name)
        Notifications.add(f"{nation.name} has joined the {alliance.name}.", 8)
        nation.action_log.append(f"Joined {alliance.name}.")

def resolve_claim_actions(game_id: str, actions_list: list[ClaimAction]) -> None:

    from app.nation import Nations
    with open('active_games.json', 'r') as json_file:
        active_games_dict = json.load(json_file)

    # initial validation
    minimum_spend: dict[str, int] = defaultdict(int)
    claim_actions_grouped: dict[str, dict[str, Region]] = defaultdict(dict)
    for action in actions_list:
        nation = Nations.get(action.id)
        region = Region(action.target_region)

        if region.data.owner_id == nation.id:
            nation.action_log.append(f"Failed to claim {action.target_region}. You already own this region.")
            continue

        if region.data.owner_id != "0":
            nation.action_log.append(f"Failed to claim {action.target_region}. This region is already owned by another nation.")
            continue

        if "Civil Disorder" in nation.tags:
            nation.action_log.append(f"Failed to claim {action.target_region} due to the Widespread Civil Disorder event.")
            continue

        minimum_spend[nation.id] += region.calculate_region_claim_cost(nation)
        if float(nation.get_stockpile("Dollars")) - minimum_spend[nation.id] < 0:
            nation.action_log.append(f"Failed to claim {region.region_id}. Insufficient dollars.")
            continue
        
        region.add_claim(nation.id)
        claim_actions_grouped[nation.id][region.region_id] = region

    # priority queue #1 - validate and pay for the claim actions of each nation
    claim_actions_validated: dict[str, Region] = {}
    for nation in Nations:
        validated_region_ids = _validate_all_claims(claim_actions_grouped[nation.id])
        for region_id in validated_region_ids:
            region = Region(region_id)
            if region.region_id in claim_actions_validated:
                claim_actions_validated[region.region_id].add_claim(action.id)
            else:
                region.add_claim(nation.id)
                claim_actions_validated[region.region_id] = region

    # resolve region disputes
    claim_actions_final: dict[str, Region] = {}
    for region in claim_actions_validated.values():
        
        if len(region.claim_list) == 1:
            claim_actions_final[region.region_id] = region
            continue

        for player_id in region.claim_list:
            nation = Nations.get(player_id)
            cost = region.calculate_region_claim_cost(nation)
            nation.action_log.append(f"Failed to claim {region.region_id} due to a region dispute. {cost:.2f} dollars wasted.")

        region.data.purchase_cost += 5
        active_games_dict[game_id]["Statistics"]["Region Disputes"] += 1

    # priority queue #2 - validate remaining claim actions together and resolve
    _resolve_all_claims(claim_actions_final)

    with open("active_games.json", 'w') as json_file:
        json.dump(active_games_dict, json_file, indent=4)

def _validate_all_claims(claimed_regions: dict[str, Region]) -> set:

    def get_priority(region: Region) -> int:

        nation_id = region.claim_list[0]
        
        # adjacent owned - region already owned by the nation before claim actions resolved OR successful claim
        adj_owned = set()
        for adj_region_id in region.graph.adjacent_regions:
            adj_region = Region(adj_region_id)
            if nation_id == adj_region.data.owner_id or adj_region.region_id in resolved:
                adj_owned.add(adj_region.region_id)

        # adjacent claim - region pending claim action resolution that belongs to this nation
        adj_claimed = set()
        for adj_region_id in region.graph.adjacent_regions:
            adj_region = claimed_regions.get(adj_region_id)
            if adj_region is not None and adj_region_id not in resolved and adj_region_id not in failed:
                adj_claimed.add(adj_region.region_id)

        return _validate_claim_action(nation_id, region, adj_owned, adj_claimed)
    
    heap: List[Tuple[int, Region]] = []
    priorities = {}
    resolved = set()
    failed = set()

    for region in claimed_regions.values():
        priority = get_priority(region)
        priorities[region.region_id] = priority
        heapq.heappush(heap, (priority, region))

    while heap:
        priority, region = heapq.heappop(heap)
        nation_id = region.claim_list[0]
        nation = Nations.get(nation_id)

        if priority != priorities[region.region_id] or region.region_id in resolved or region.region_id in failed:
            continue

        if priority == 99999:
            nation.action_log.append(f"Failed to claim {region.region_id}. Region is not adjacent to enough regions under your control.")
            failed.add(region.region_id)
            continue
        
        if priority > 0:
            heapq.heappush(heap, (priority, region))
            continue

        cost = region.calculate_region_claim_cost(nation)
        if float(nation.get_stockpile("Dollars")) - cost < 0:
            # nation could not afford region
            nation.action_log.append(f"Failed to claim {region.region_id}. Insufficient dollars.")
            failed.add(region.region_id)
        else:
            # region successfully paid for
            nation.update_stockpile("Dollars", -1 * cost)
            resolved.add(region.region_id)

        # update priority values for adjacent regions
        for adj_region_id in region.graph.adjacent_regions:
            if adj_region_id in claimed_regions and adj_region_id not in resolved and adj_region_id not in failed:
                adj_region = claimed_regions.get(adj_region_id)
                new_priority = get_priority(adj_region)
                priorities[adj_region_id] = new_priority
                heapq.heappush(heap, (new_priority, adj_region))

    return resolved

def _resolve_all_claims(verified_claim_actions: dict[str, Region]) -> None:

    def get_priority(region: Region) -> int:

        nation_id = region.claim_list[0]

        # adjacent owned - region already owned by the nation before claim actions resolved OR successful claim
        adj_owned = set()
        for adj_region_id in region.graph.adjacent_regions:
            adj_region = Region(adj_region_id)
            if nation_id == adj_region.data.owner_id:
                adj_owned.add(adj_region.region_id)
        
        # adjacent claim - region pending claim action resolution that belongs to this nation
        adj_claimed = set()
        for adj_region_id in region.graph.adjacent_regions:
            adj_region = verified_claim_actions.get(adj_region_id)
            if adj_region is not None and adj_region_id not in failed and nation_id == adj_region.claim_list[0]:
                adj_claimed.add(adj_region.region_id)

        return _validate_claim_action(nation_id, region, adj_owned, adj_claimed)
    
    def find_encircled_regions(region: Region, nation_id: str) -> set[Region]:
        """
        Checks for pockets of unclaimed regions that are entirely encircled by one nation as a result of a claim action.
        """
        
        encircled_regions: set[Region] = set()
        
        # checking every adjacent region with a seperate BFS because one claim can result in multiple encircled pockets
        for adj_region_id in region.graph.adjacent_regions:
            adj_region = Region(adj_region_id)
            
            # skip if already owned by someone
            if adj_region.data.owner_id != "0":
                continue

            # skip if this adjacent region does not lead to a seperate pocket
            if adj_region in encircled_regions:
                continue
            
            encircled = True
            unclaimed: set[Region] = set()

            visited = set([adj_region.region_id])
            queue: deque[Region] = deque([adj_region])

            while queue:

                current_region = queue.popleft()

                # pocket is not encircled if this region is owned by another player
                if current_region.data.owner_id not in ["0", nation_id]:
                    encircled = False
                    break

                # continue if already owned
                if current_region.data.owner_id == nation_id or current_region.region_id == region.region_id:
                    continue

                current_region.add_claim(nation_id)
                unclaimed.add(current_region)

                for temp_id in current_region.graph.adjacent_regions:
                    if temp_id not in visited:
                        visited.add(temp_id)
                        queue.append(Region(temp_id))

            if encircled:
                encircled_regions.update(unclaimed)
        
        return encircled_regions

    heap: List[Tuple[int, Region]] = []
    priorities = {}
    resolved = set()
    failed = set()
    
    for region in verified_claim_actions.values():
        priority = get_priority(region)
        priorities[region.region_id] = priority
        heapq.heappush(heap, (priority, region))

    while heap:
        priority, region = heapq.heappop(heap)
        nation_id = region.claim_list[0]
        nation = Nations.get(nation_id)

        if priority != priorities[region.region_id] or region.region_id in resolved or region.region_id in failed:
            continue

        if priority == 99999:
            nation.action_log.append(f"Failed to claim {region.region_id}. Region is not adjacent to enough regions under your control.")
            failed.add(region.region_id)
            continue
        
        if priority > 0:
            heapq.heappush(heap, (priority, region))
            continue

        # encirclement check - any unclaimed regions encircled by this claim must also be claimed
        encircled_cost = 0
        encircled_regions = find_encircled_regions(region, nation.id)
        for encircled_region in encircled_regions:
            if encircled_region.region_id in verified_claim_actions:
                continue
            encircled_cost += encircled_region.calculate_region_claim_cost(nation)
        
        if float(nation.get_stockpile("Dollars")) - encircled_cost < 0:
            # player cannot afford to claim the unclaimed regions it has encircled
            nation.update_stockpile("Dollars", region.calculate_region_claim_cost(nation))
            nation.action_log.append(f"Failed to claim {region.region_id}. You could not afford to pay for the unclaimed regions this claim action encircled.")
            failed.add(region.region_id)
        else:
            # claim region
            region.data.owner_id = nation_id
            if region.improvement.name is not None:
                nation.improvement_counts[region.improvement.name] += 1
            nation.action_log.append(f"Claimed region {region.region_id} for {region.calculate_region_claim_cost(nation):.2f} dollars.")
            resolved.add(region.region_id)
            # pay for and create claim actions for encircled regions (if any)
            for encircled_region in encircled_regions:
                if encircled_region.region_id in verified_claim_actions:
                    continue
                cost = encircled_region.calculate_region_claim_cost(nation)
                nation.update_stockpile("Dollars", -1 * cost)
                verified_claim_actions[encircled_region.region_id] = encircled_region
                encircled_priority = get_priority(encircled_region)
                priorities[encircled_region.region_id] = encircled_priority
                heapq.heappush(heap, (encircled_priority, encircled_region))

        # update priority values for adjacent regions
        for adj_region_id in region.graph.adjacent_regions:
            if adj_region_id in verified_claim_actions and adj_region_id not in resolved and adj_region_id not in failed:
                adj_region = verified_claim_actions.get(adj_region_id)
                new_priority = get_priority(adj_region)
                priorities[adj_region_id] = new_priority
                heapq.heappush(heap, (new_priority, adj_region))

def _validate_claim_action(nation_id: str, target_region: Region, adj_owned: set, adj_claimed: set) -> int:
        """
        Verifies if a specific claim action abides by expansion rules by examining the target region.

        Params:
        nation_id (str): Nation ID of the nation that entered the claim action.
            target_region (Region): Region object representing the target region of the claim action.
            adj_owned_count (set): Set of adjacent region_ids to target region owned by the nation.
            adj_claimed_count (set): Set of adjacent region_ids to target region also claimed by the nation.

        Returns:
            int: Priority value. Where 0 means the region is a valid claim.
        """

        def bfs_no_access():
            """
            Returns True if the target region meets the criteria to be claimed with only one adjacent owned region (for this specific player).

            If we find 2+ regions owned by the player that are adjacent to nearby unclaimed regions, we can assume that the player has a route to claim a second adjacent region to the target.
            If that is the case, the player could claim the target region while abiding by the conventional two owned adjacent regions restriction.
            Therefore, the player should not be allowed to claim the target region now.
            """
            
            friendly_regions_found = 0
            visited = set([target_region.region_id])
            queue: deque[Region] = deque()

            # populate queue with adjacent unclaimed regions
            for adj_region_id in target_region.graph.adjacent_regions:
                adj_region = Region(adj_region_id)
                visited.add(adj_region_id)
                if adj_region.data.owner_id != "0":
                    continue
                queue.append(adj_region)

            while queue:

                current_region = queue.popleft()

                # check if this region is owned by the player
                if current_region.data.owner_id == nation_id:
                    friendly_regions_found += 1
                if friendly_regions_found >= 2:
                    return False

                # regions owned by players constrain possible routes to the target region
                if current_region.data.owner_id != "0":
                    continue

                for adj_region_id in current_region.graph.adjacent_regions:
                    if adj_region_id not in visited:
                        visited.add(adj_region_id)
                        queue.append(Region(adj_region_id))
            
            return True
        
        adj_owned_count = len(adj_owned)
        adj_claimed_count = len(adj_claimed)

        # claim action always valid if the target region borders at least two owned regions
        if adj_owned_count >= 2:
            return 0
        
        # TODO - special case - valid with one if first 4 turns only

        # special case - valid with one if sea route
        for adj_region_id in target_region.graph.sea_routes:
            if adj_region_id in adj_owned:
                return 0

        # special case - valid with one if no other adjacent regions
        if adj_owned_count == 1 and len(target_region.graph.map) == 1:
            return 0
        
        # special case - valid with one if all other adjacent regions are unclaimable
        if adj_owned_count == 1 and adj_claimed_count == 0:
            if bfs_no_access():
                return 0

        if adj_owned_count < 2 and adj_claimed_count == 0:
            return 99999

        return 2 - adj_owned_count

def resolve_improvement_remove_actions(game_id: str, actions_list: list[ImprovementRemoveAction]) -> None:
    
    from app.nation import Nations

    for action in actions_list:
        
        nation = Nations.get(action.id)
        region = Region(action.target_region)

        if region.data.owner_id != action.id or region.data.occupier_id != "0":
            nation.action_log.append(f"Failed to remove {region.improvement.name} in region {action.target_region}. You do not own or control this region.")
            continue

        if region.improvement.name == "Capital":
            nation.action_log.append(f"Failed to remove {region.improvement.name} in region {action.target_region}. You cannot remove a Capital improvement.")
            continue

        if region.improvement.name is not None:
            nation.improvement_counts[region.improvement.name] -= 1
        region.improvement.clear()
        nation.action_log.append(f"Removed improvement in region {action.target_region}.")

def resolve_improvement_build_actions(game_id: str, actions_list: list[ImprovementBuildAction]) -> None:
    
    from app.scenario import ScenarioData as SD
    from app.nation import Nations

    for action in actions_list:
        
        nation = Nations.get(action.id)
        region = Region(action.target_region)

        if region.data.owner_id != action.id or region.data.occupier_id != "0":
            nation.action_log.append(f"Failed to build {action.improvement_name} in region {action.target_region}. You do not own or control this region.")
            continue

        if region.improvement.name == "Capital":
            nation.action_log.append(f"Failed to remove build {action.improvement_name} in region {action.target_region}. You cannot build over a Capital improvement.")
            continue
        
        required_research = SD.improvements[action.improvement_name].required_research
        if required_research is not None and required_research not in nation.completed_research:
            nation.action_log.append(f"Failed to build {action.improvement_name} in region {action.target_region}. You do not have the required research.")
            continue

        required_resource = SD.improvements[action.improvement_name].required_resource
        if required_resource is not None and required_resource != region.data.resource:
            nation.action_log.append(f"Failed to build {action.improvement_name} in region {action.target_region}. The region does not have the resource required for this improvement.")
            continue

        if region.data.fallout != 0:
            nation.action_log.append(f"Failed to build {action.improvement_name} in region {action.target_region}. Region cannot support an improvement due to nuclear missile detonation.")
            continue

        if action.improvement_name == "Colony" and "Faustian Bargain" not in nation.tags:
            nation.action_log.append(f"Failed to build {action.improvement_name} in region {action.target_region}. You are not the Collaborator.")
            continue

        build_cost_dict = SD.improvements[action.improvement_name].cost
        nation.apply_build_discount(build_cost_dict)

        valid = True
        for resource_name, cost in build_cost_dict.items():
            if float(nation.get_stockpile(resource_name)) - cost < 0:
                valid = False
                break
        if not valid:
            nation.action_log.append(f"Failed to build {action.improvement_name} in region {action.target_region}. Insufficient resources.")
            continue

        costs_list = []
        for resource_name, cost in build_cost_dict.items():
            costs_list.append(f"{cost} {resource_name.lower()}")
            nation.update_stockpile(resource_name, -1 * cost)
        
        if region.improvement.name is not None:
            nation.improvement_counts[region.improvement.name] -= 1
        nation.improvement_counts[action.improvement_name] += 1
        region.improvement.set(action.improvement_name)

        if len(costs_list) <= 2:
            costs_str = " and ".join(costs_list)
        else:
            costs_str = ", ".join(costs_list)
            costs_str = " and ".join(costs_str.rsplit(", ", 1))
        nation.action_log.append(f"Built {action.improvement_name} in region {action.target_region} for {costs_str}.")    

def resolve_missile_make_actions(game_id: str, actions_list: list[MissileMakeAction]) -> None:
    
    from app.nation import Nations
    # TODO - add missile data to scenario

    for action in actions_list:

        nation = Nations.get(action.id)

        if action.missile_type == "Standard Missile" and "Missile Technology" not in nation.completed_research:
            nation.action_log.append(f"Failed to manufacture {action.quantity}x {action.missile_type}. You do not have the Missile Technology technology.")
            continue
        elif action.missile_type == "Nuclear Missile" and "Nuclear Warhead" not in nation.completed_research:
            nation.action_log.append(f"Failed to manufacture {action.quantity}x {action.missile_type}. You do not have the Nuclear Warhead technology.")
            continue

        if action.missile_type == "Standard Missile":

            cost = 3 * action.quantity
            if float(nation.get_stockpile("Common Metals")) - cost < 0:
                nation.action_log.append(f"Failed to manufacture {action.quantity}x {action.missile_type}. Insufficient resources.")
                continue
            
            nation.update_stockpile("Common Metals", -1 * cost)

            nation.missile_count += action.quantity
        
        elif action.missile_type == "Nuclear Missile":

            cost = 2 * action.quantity
            if (float(nation.get_stockpile("Advanced Metals")) - cost < 0
                or float(nation.get_stockpile("Uranium")) - cost < 0
                or float(nation.get_stockpile("Rare Earth Elements")) - cost < 0):
                nation.action_log.append(f"Failed to manufacture {action.quantity}x {action.missile_type}. Insufficient resources.")
                continue
            
            nation.update_stockpile("Advanced Metals", -1 * cost)
            nation.update_stockpile("Uranium", -1 * cost)
            nation.update_stockpile("Rare Earth Elements", -1 * cost)

            nation.nuke_count += action.quantity

        nation.action_log.append(f"Manufactured {action.quantity}x {action.missile_type}.")

def resolve_government_actions(game_id: str, actions_list: list[RepublicAction]) -> None:
    
    from app.nation import Nations

    for action in actions_list:

        nation = Nations.get(action.id)

        if nation.gov != "Republic":
            nation.action_log.append(f"Failed to execute Republic government action. Your nation is not a Republic.")
            continue
        
        cost = 5
        if float(nation.get_stockpile("Political Power")) - cost < 0:
            nation.action_log.append(f"Failed to execute Republic government action. Insufficient political power.")
            continue

        nation.update_stockpile("Political Power", -1 * cost)

        new_tag = {
            f"{action.resource_name} Rate": 20,
            "Expire Turn": 99999
        }
        nation.tags["Republic Bonus"] = new_tag
        nation.action_log.append(f"Used Republic government action to boost {action.resource_name} income.")
        Notifications.add(f"{nation.name} used Republic government action to boost {action.resource_name} income.", 9)

def resolve_market_actions(game_id: str, crime_list: list[CrimeSyndicateAction], buy_list: list[MarketBuyAction], sell_list: list[MarketSellAction]) -> dict:
    
    from app.scenario import ScenarioData as SD
    from app.nation import Nations
    
    rmdata_filepath = f'gamedata/{game_id}/rmdata.csv'
    current_turn_num = core.get_current_turn_num(game_id)
    with open('active_games.json', 'r') as json_file:
        active_games_dict = json.load(json_file)

    rmdata_update_list = []
    steal_tracking_dict = active_games_dict[game_id]["Steal Action Record"]
    data = {}
    for resource_name, market_data in SD.market:
        data[resource_name] = {
        "Base Price": market_data.base_price,
        "Current Price": 0,
        "Bought": 0,
        "Sold": 0
    }

    # sum up recent transactions
    rmdata_recent_transaction_list = core.read_rmdata(rmdata_filepath, current_turn_num, 12, False)
    for transaction in rmdata_recent_transaction_list: 
        exchange = transaction[2]
        count = transaction[3]
        resource_name = transaction[4]
        if exchange == "Bought":
            data[resource_name]["Bought"] += count
        elif exchange == "Sold":
            data[resource_name]["Sold"] += count

    # calculate current prices
    for resource_name, resource_info in data.items():
        base_price = resource_info["Base Price"]
        recently_bought_total = resource_info["Bought"]
        recently_sold_total = resource_info["Sold"]
        current_price = base_price * (recently_bought_total + 25) / (recently_sold_total + 25)
        data[resource_name]["Current Price"] = round(current_price, 2)
    
    # factor in impact of events on current prices
    if "Market Inflation" in active_games_dict[game_id]["Active Events"]:
        for resource_name in data:
            new_price = data[resource_name]["Current Price"] * 2
            data[resource_name]["Current Price"] = round(new_price, 2)
    elif "Market Recession" in active_games_dict[game_id]["Active Events"]:
        for resource_name in data:
            new_price = data[resource_name]["Current Price"] * 0.5
            data[resource_name]["Current Price"] = round(new_price, 2)

    # create market results dict
    market_results = {}
    for nation in Nations:
        market_results[nation.name] = {}
        for resource_name in data:
            market_results[nation.name][resource_name] = 0
        market_results[nation.name]["Dollars"] = 0
        market_results[nation.name]["Thieves"] = []

    for action in buy_list:
        
        nation = Nations.get(action.id)
        price = data[action.resource_name]["Current Price"]
        rate = 1.0
        
        if "Embargo" in nation.tags:
            nation.action_log.append(f"Failed to buy {action.quantity} {action.resource_name}. Your nation is currently under an embargo.")
            continue

        for tag_name, tag_data in nation.tags.items():
            rate -= float(tag_data.get("Market Buy Modifier", 0))
        if "Improved Logistics" in nation.completed_research:
            rate -= 0.2

        cost = round(action.quantity * price * rate, 2)
        if float(nation.get_stockpile("Dollars")) - cost < 0:
            nation.action_log.append(f"Failed to buy {action.quantity} {action.resource_name}. Insufficient dollars.")
            continue

        nation.update_stockpile("Dollars", -1 * cost)
        new_entry = [current_turn_num, nation.name, 'Bought', action.quantity, action.resource_name]
        rmdata_update_list.append(new_entry)

        market_results[nation.name][action.resource_name] = action.quantity
        nation.action_log.append(f"Bought {action.quantity} {action.resource_name} from the resource market for {cost:.2f} dollars.")

    for action in sell_list:
        
        nation = Nations.get(action.id)
        price = float(data[action.resource_name]["Current Price"] * 0.5)
        rate = 1.0

        if "Embargo" in nation.tags:
            nation.action_log.append(f"Failed to sell {action.quantity} {action.resource_name}. Your nation is currently under an embargo.")
            continue

        for tag_name, tag_data in nation.tags.items():
            rate += float(tag_data.get("Market Sell Modifier", 0))

        if float(nation.get_stockpile(action.resource_name)) - action.quantity < 0:
            nation.action_log.append(f"Failed to sell {action.quantity} {action.resource_name}. Insufficient resources in stockpile.")
            continue

        nation.update_stockpile(action.resource_name, -1 * action.quantity)
        new_entry = [current_turn_num, nation.name, 'Sold', action.quantity, action.resource_name]
        rmdata_update_list.append(new_entry)

        dollars_earned = round(action.quantity * price * rate, 2)
        market_results[nation.name]["Dollars"] += dollars_earned
        nation.action_log.append(f"Sold {action.quantity} {action.resource_name} to the resource market for {dollars_earned:.2f} dollars.")

    # get crime syndicate steal actions
    for action in crime_list:
        for crime_action in crime_list:
            market_results[nation.name]["Thieves"].append(crime_action.id)
    for nation_name, nation_info in market_results.items():
        thieves_list = nation_info["Thieves"]
        if len(thieves_list) != 1:
            for thief_id in thieves_list:
                syndicate_nation = Nations.get(thief_id)
                syndicate_nation.action_log.append(f"Failed to steal from {crime_action.target_nation} due to other crime syndicate stealing attempts.")
            nation_info["Thieves"] = []

    # resolve crime syndicate steal actions
    for nation_name, nation_info in market_results.items():
        thieves_list = nation_info["Thieves"]
        if thieves_list == []:
            continue
        thief_id = thieves_list[0]
            
        nation = Nations.get(nation_name)
        syndicate_nation = Nations.get(thief_id)
        nation_name_of_last_victim = steal_tracking_dict[syndicate_nation.name]["Nation Name"]
        streak_of_last_victim = steal_tracking_dict[syndicate_nation.name]["Streak"]

        # calculate steal amount and update record
        modifier = 0.5
        if nation_name == nation_name_of_last_victim:
            for i in range(streak_of_last_victim):
                modifier *= 0.5
            modifier = round(modifier, 2)
            steal_tracking_dict[syndicate_nation.name]["Streak"] += 1
        else:
            steal_tracking_dict[syndicate_nation.name]["Nation Name"] = nation.name
            steal_tracking_dict[syndicate_nation.name]["Streak"] = 1

        # execute steal
        for entry, amount in nation_info.items():
            
            if entry == "Thieves":
                continue
            
            stolen_amount = int(amount * modifier)
            market_results[syndicate_nation.name][entry] += stolen_amount
            syndicate_nation.action_log.append(f"Stole {stolen_amount} {entry} from {nation.name}. ({int(modifier * 100)}%)")
            market_results[nation_name][entry] -= stolen_amount
            nation.action_log.append(f"{syndicate_nation.name} stole {stolen_amount} {entry} from you! ({int(modifier * 100)}%)")
        
        Notifications.add(f"{syndicate_nation.name} stole from {nation.name}.", 9)

    # update rmdata.csv
    rmdata_all_transaction_list = core.read_rmdata(rmdata_filepath, current_turn_num, False, False)
    with open(rmdata_filepath, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(core.rmdata_header)
        writer.writerows(rmdata_all_transaction_list)
        writer.writerows(rmdata_update_list)

    return market_results

def resolve_unit_disband_actions(game_id: str, actions_list: list[UnitDisbandAction]) -> None:
    
    from app.nation import Nations

    for action in actions_list:
        
        nation = Nations.get(action.id)
        region = Region(action.target_region)

        if str(region.unit.owner_id) != action.id:
            nation.action_log.append(f"Failed to disband {region.unit.name} in region {action.target_region}. You do not own this unit.")
            continue

        if region.unit.name is not None:
            nation.unit_counts[region.unit.name] -= 1
            nation.update_used_mc(-1)
        region.unit.clear()
        nation.action_log.append(f"Disbanded unit in region {action.target_region}.")

def resolve_unit_deployment_actions(game_id: str, actions_list: list[UnitDeployAction]) -> None:
    
    from app.scenario import ScenarioData as SD
    from app.nation import Nations

    for action in actions_list:

        region = Region(action.target_region)
        nation = Nations.get(action.id)
        sd_unit = SD.units[action.unit_name]

        if str(region.data.owner_id) != action.id or region.data.occupier_id != "0":
            nation.action_log.append(f"Failed to deploy {action.unit_name} in region {action.target_region}. You do not control this region.")
            continue
        
        if sd_unit.required_research not in nation.completed_research:
            nation.action_log.append(f"Failed to deploy {action.unit_name} in region {action.target_region}. You do not have the required research.")
            continue

        if nation.get_used_mc() == nation.get_max_mc():
            nation.action_log.append(f"Failed to deploy {action.unit_name} in region {action.target_region}. Insufficient military capacity.")
            continue

        build_cost_dict = sd_unit.cost
        if nation.gov == "Military Junta":
            for key in build_cost_dict:
                build_cost_dict[key] *= 0.8

        valid = True
        for resource_name, cost in build_cost_dict.items():
            if float(nation.get_stockpile(resource_name)) - cost < 0:
                valid = False
                break
        if not valid:
            nation.action_log.append(f"Failed to deploy {action.unit_name} in region {action.target_region}. Insufficient resources.")
            continue

        costs_list = []
        for resource_name, cost in build_cost_dict.items():
            costs_list.append(f"{cost} {resource_name.lower()}")
            nation.update_stockpile(resource_name, -1 * cost)

        if region.unit.name is not None:
            nation.unit_counts[region.unit.name] -= 1
            nation.update_used_mc(-1)
        nation.unit_counts[region.unit.name] += 1
        nation.update_used_mc(1)
        region.unit.set(action.unit_name, action.id)

        if len(costs_list) <= 2:
            costs_str = " and ".join(costs_list)
        else:
            costs_str = ", ".join(costs_list)
            costs_str = " and ".join(costs_str.rsplit(", ", 1))
        nation.action_log.append(f"Deployed {action.unit_name} in region {action.unit_name} in region {action.target_region} for {costs_str}.")

def resolve_war_actions(game_id: str, actions_list: list[WarAction]) -> None:
    
    from app.scenario import ScenarioData as SD
    from app.nation import Nations
    from app.war import Wars

    for action in actions_list:

        attacker_nation = Nations.get(action.id)
        defender_nation = Nations.get(action.target_nation)

        if not _war_action_valid(action, attacker_nation, defender_nation):
            continue

        region_claims_list = []

        if SD.war_justificiations[action.war_justification].has_war_claims:
            
            claim_cost = Wars.get_war_claims(attacker_nation.name, action.war_justification)
            if float(attacker_nation.get_stockpile("Political Power")) - claim_cost < 0:
                attacker_nation.action_log.append(f"Failed to declare a {action.war_justification} war on {defender_nation.name}. Not enough political power for war claims.")
                continue

            attacker_nation.update_stockpile("Political Power", -1 * claim_cost)

        Wars.create(attacker_nation.id, defender_nation.id, action.war_justification, region_claims_list)
        Notifications.add(f"{attacker_nation.name} declared war on {defender_nation.name}.", 4)
        attacker_nation.action_log.append(f"Declared war on {defender_nation.name}.")

def resolve_war_join_actions(game_id: str, actions_list: list[WarJoinAction]) -> None:

    from app.scenario import ScenarioData as SD
    from app.nation import Nations
    from app.war import Wars

    for action in actions_list:

        war = Wars.get(action.war_name)
        attacker_nation = Nations.get(action.id)

        war.add_combatant(attacker_nation, f"Secondary {action.side}", action.war_justification)
        combatant = war.get_combatant(action.id)
        region_claims_list = []

        # process war claims
        if SD.war_justificiations[action.war_justification].has_war_claims:

            combatant.target_id = "N/A"
            main_attacker_id, main_defender_id = war.get_main_combatant_ids()
            if {action.side} == "Attacker":
                defender_nation = Nations.get(main_attacker_id)
            elif {action.side} == "Defender":
                defender_nation = Nations.get(main_defender_id)
            
            claim_cost = Wars.get_war_claims(combatant.name, action.war_justification)
            if float(attacker_nation.get_stockpile("Political Power")) - claim_cost < 0:
                attacker_nation.action_log.append(f"Error: Not enough political power for war claims.")
                continue

            attacker_nation.update_stockpile("Political Power", -1 * claim_cost)
        
        # OR handle war justification that does not seize territory
        else:
            target_id = input(f"Enter nation_id of nation {combatant.name} is targeting with {action.war_justification}: ")
            combatant.target_id = target_id
            defender_nation = Nations.get(target_id)

        if not _war_action_valid(action, attacker_nation, defender_nation):
            continue

        # save
        Notifications.add(f"{attacker_nation.name} has joined {war.name} as a {action.side}!", 4)
        combatant.claims = Wars._claim_pairs(region_claims_list)

def _war_action_valid(action: WarAction | WarJoinAction, attacker_nation: Nation, defender_nation: Nation):
    
    from app.scenario import ScenarioData as SD
    from app.alliance import Alliances
    from app.truce import Truces
    from app.war import Wars

    # agenda check
    prereq = SD.war_justificiations[action.war_justification].required_agenda
    if prereq is not None and prereq not in attacker_nation.completed_research:
        attacker_nation.action_log.append(f"Failed to declare a {action.war_justification} war on {defender_nation.name}. You do not have the required agenda.")
        return False

    # military capacity check
    if attacker_nation.get_used_mc() == 0:
        attacker_nation.action_log.append(f"Failed to declare a {action.war_justification} war on {defender_nation.name}. You do not have any military units.")
        return False

    # existing war check
    existing_war = Wars.get_war_name(attacker_nation.id, defender_nation.id)
    if existing_war is not None:
        attacker_nation.action_log.append(f"Failed to declare a {action.war_justification} war on {defender_nation.name}. You are already at war with this nation.")
        return False
    
    # truce check
    if Truces.are_truced(attacker_nation.id, defender_nation.id):
        attacker_nation.action_log.append(f"Failed to declare a {action.war_justification} war on {defender_nation.name}. You have a truce with this nation.")
        return False

    # alliance check
    if Alliances.are_allied(attacker_nation.name, defender_nation.name):
        attacker_nation.action_log.append(f"Failed to declare a {action.war_justification} war on {defender_nation.name}. You have an alliance with this nation.")
        return False

    # alliance truce check
    if Alliances.former_ally_truce(attacker_nation.name, defender_nation.name):
        attacker_nation.action_log.append(f"Failed to declare a {action.war_justification} war on {defender_nation.name}. You have recently had an alliance with this nation.")
        return False
    
    # independence check
    if attacker_nation.status != "Independent Nation" and not SD.war_justificiations[action.war_justification].for_puppet_states:
        attacker_nation.action_log.append(f"Failed to declare a {action.war_justification} war on {defender_nation.name}. As a puppet state, you cannot use this war justification.")
        return False
    
    # target requirements check
    # TODO - more requirements can easily be added here in the future to improve modding
    target_requirements = SD.war_justificiations[action.war_justification].target_requirements
    for requirement, value in target_requirements.items():
        match requirement:
            case "Foreign Policy":
                if defender_nation.fp not in value:
                    attacker_nation.action_log.append(f"Failed to declare a {action.war_justification} war on {defender_nation.name}. Invalid foreign policy.")
                    return False
            case "isOverlord":
                if defender_nation.name not in attacker_nation.status:
                    attacker_nation.action_log.append(f"Failed to declare a {action.war_justification} war on {defender_nation.name}. You are not a puppet state of this nation.")
                    return False

    # tag check
    is_blocked = False
    for tag_name, tag_data in attacker_nation.tags.items():
        if f"Cannot Declare War On #{defender_nation.id}" in tag_data:
            is_blocked = True
            break
    if is_blocked:
        attacker_nation.action_log.append(f"Failed to declare a {action.war_justification} war on {defender_nation.name} due to {tag_name}.")
        return False

    return True

def resolve_missile_launch_actions(game_id: str, actions_list: list[MissileLaunchAction]) -> None:

    from app.scenario import ScenarioData as SD
    from app.nation import Nations
    from app.war import Wars

    # missile launch capacity is calculated in advance of actions because missile launches are simultaneous
    missiles_launched_list = [0] * len(Nations)
    launch_capacity_list = [0] * len(Nations)
    for nation in Nations:
        launch_capacity_list[int(nation.id) - 1] = nation.improvement_counts["Missile Silo"] * 3

    for action in actions_list:
        
        nation = Nations.get(action.id)
        target_region = Region(action.target_region)

        has_missile = True
        if action.missile_type == "Standard Missile" and nation.missile_count == 0:
            has_missile = False
        elif action.missile_type == "Nuclear Missile" and nation.nuke_count == 0:
            has_missile = False
        if not has_missile:
            nation.action_log.append(f"Failed to launch {action.missile_type} at {action.target_region}. You do not have a {action.missile_type} in storage.")
            continue

        is_valid_target = True
        if nation.id != str(target_region.data.owner_id):
            engagement_type = 1
            if Wars.get_war_name(nation.id, target_region.data.owner_id) is None:
                # cannot nuke a foreign region if it is owned by a nation you are not at war with
                is_valid_target = False
            if target_region.data.occupier_id != "0" and Wars.get_war_name(nation.id, target_region.data.occupier_id) is None:
                # cannot nuke a hostile nation's region if it is occupied by a non-hostile nation
                is_valid_target = False
            if target_region.unit.name is not None and Wars.get_war_name(nation.id, target_region.unit.owner_id) is None:
                # cannot nuke a hostile nation's region if a non-hostile unit is present
                is_valid_target = False
        elif nation.id == str(target_region.data.owner_id):
            engagement_type = 2
            if target_region.data.occupier_id == "0" or Wars.get_war_name(nation.id, target_region.data.occupier_id) is None:
                # only allowed to strike your own region if it is occupied by a hostile nation
                is_valid_target = False
        if not is_valid_target:
            nation.action_log.append(f"Failed to launch {action.missile_type} at {action.target_region}. Invalid target!")
            continue

        if action.missile_type == "Standard Missile":
            capacity_cost = 1
        elif action.missile_type == "Nuclear Missile":
            capacity_cost = 3
        if missiles_launched_list[int(nation.id) - 1] + capacity_cost > launch_capacity_list[int(nation.id) - 1]:
            nation.action_log.append(f"Failed to launch {action.missile_type} at {action.target_region}. Insufficient launch capacity!")
            continue

        # identify conflict
        if engagement_type == 1 and target_region.data.occupier_id == "0":
            # missile strike on hostile territory owned by the same hostile
            target_nation = Nations.get(str(target_region.data.owner_id))
            war_name = Wars.get_war_name(nation.id, str(target_region.data.owner_id))
        else:
            # any other situation
            target_nation = Nations.get(str(target_region.data.occupier_id))
            war_name = Wars.get_war_name(nation.id, str(target_region.data.occupier_id))

        # get combatants
        war = Wars.get(war_name)
        war.log.append(f"{nation.name} launched a {action.missile_type} at {target_region.region_id} in {target_nation.name}!")
        attacking_combatant = war.get_combatant(nation.id)
        defending_combatant = war.get_combatant(target_nation.id)

        # fire missile
        missiles_launched_list[int(nation.id) - 1] += capacity_cost
        if action.missile_type == "Standard Missile":
            nation.missile_count -= 1
        elif action.missile_type == "Nuclear Missile":
            nation.nuke_count -= 1
        
        # log launch and find best missile defense
        nation.action_log.append(f"Launched {action.missile_type} at {action.target_region}. See combat log for details.")
        defender_name = core.locate_best_missile_defense(game_id, target_nation, action.missile_type, action.target_region)
        
        # engage missile defense
        missile_intercepted = False
        missile_did_something = False
        if defender_name is not None:
            
            war.log.append(f"    A nearby {defender_name} attempted to defend {target_region.region_id}.")
            if defender_name in SD.units:
                if action.missile_type == "Standard Missile":
                    hit_value = SD.units[defender_name].missile_defense
                else:
                    hit_value = SD.units[defender_name].nuclear_defense
            else:
                if action.missile_type == "Standard Missile":
                    hit_value = SD.improvements[defender_name].missile_defense
                else:
                    hit_value = SD.improvements[defender_name].nuclear_defense
                if "Local Missile Defense" in nation.completed_research and defender_name not in ["Missile Defense System", "Missile Defense Network"]:
                    hit_value = SD.improvements[defender_name].hit_value

            missile_defense_roll = random.randint(1, 10)
            if missile_defense_roll >= hit_value:
                # incoming missile shot down
                missile_intercepted = True
                war.log.append(f"    {defender_name} missile defense rolled {missile_defense_roll} (needed {hit_value}+). Missile destroyed!")
            else:
                # incoming missile dodged defenses
                war.log.append(f"    {defender_name} missile defense rolled {missile_defense_roll} (needed {hit_value}+). Defenses missed!")

        # end action if missile was destroyed
        if missile_intercepted:
            continue

        # conduct missile strike
        if action.missile_type == 'Standard Missile':
            
            attacking_combatant.launched_missiles += 1

            # improvement damage
            if target_region.improvement.name is not None and target_region.improvement.health != 99:

                # initial roll against improvement
                missile_did_something = True
                accuracy_roll = random.randint(1, 10)
                war.log.append(f"    Missile rolled a {accuracy_roll} for accuracy (needed 4+).")

                if accuracy_roll > 3:
                
                    # apply damage
                    target_region.improvement.health -= 1
                    if target_region.improvement.health > 0:
                        # improvement survived
                        war.log.append(f"    Missile struck {target_region.improvement.name} in {target_region.region_id} and dealt 1 damage.")
                    else:
                        # improvement destroyed
                        war.attackers.destroyed_improvements += Wars.WARSCORE_FROM_DESTROY_IMPROVEMENT
                        if target_region.improvement.name != 'Capital':
                            attacking_combatant.destroyed_improvements += 1
                            defending_combatant.lost_improvements += 1
                            war.log.append(f"    Missile struck {target_region.improvement.name} in {target_region.region_id} and dealt 1 damage. Improvement destroyed!")
                            target_nation.improvement_counts[target_region.improvement.name] -= 1
                            target_region.improvement.clear()
                        else:
                            war.log.append(f"    Missile struck Capital in {target_region.region_id} and dealt 1 damage. Improvement devastated!")
                
                else:
                    war.log.append(f"    Missile missed {target_region.improvement.name}.")

            elif target_region.improvement.name is not None and target_region.improvement.health == 99:
                
                # initial roll against improvement
                missile_did_something = True
                accuracy_roll = random.randint(1, 10)
                war.log.append(f"    Missile rolled a {accuracy_roll} for accuracy (needed 8+).")

                if accuracy_roll > 7:

                    # improvement has no health so it is destroyed
                    war.attackers.destroyed_improvements += Wars.WARSCORE_FROM_DESTROY_IMPROVEMENT
                    attacking_combatant.destroyed_improvements += 1
                    defending_combatant.lost_improvements += 1
                    war.log.append(f"    Missile destroyed {target_region.improvement.name} in {target_region.region_id}!")
                    target_nation.improvement_counts[target_region.improvement.name] -= 1
                    target_region.improvement.clear()
                
                else:
                    war.log.append(f"    Missile missed {target_region.improvement.name}.")

            # unit damage
            if target_region.unit.name != None:

                # initial roll against unit
                missile_did_something = True
                accuracy_roll = random.randint(1, 10)
                war.log.append(f"    Missile rolled a {accuracy_roll} for accuracy (needed 4+).")

                if accuracy_roll > 3:
                    
                    # apply damage
                    target_region.unit.health -= 1
                    if target_region.unit.health > 0:
                        # unit survived
                        war.log.append(f"    Missile struck {target_region.unit.name} in {target_region.region_id} and dealt 1 damage.")
                    else:
                        # unit destroyed
                        war.attackers.destroyed_units += target_region.unit.value    # amount of warscore earned depends on unit value
                        attacking_combatant.destroyed_units += 1
                        defending_combatant.lost_units += 1
                        war.log.append(f"    Missile destroyed {target_region.unit.name} in {target_region.region_id}!")
                        target_nation.unit_counts[target_region.unit.name] -= 1
                        target_region.unit.clear()
                
                else:
                    war.log.append(f"    Missile missed {target_region.unit.name}.")

        elif action.missile_type == 'Nuclear Missile':
            
            attacking_combatant.launched_nukes += 1
            war.attackers.nuclear_strikes += Wars.WARSCORE_FROM_NUCLEAR_STRIKE
            if target_region.improvement.name != 'Capital':
                target_region.set_fallout()

            # destroy improvement if present
            if target_region.improvement.name is not None:
                missile_did_something = True
                war.attackers.destroyed_improvements += Wars.WARSCORE_FROM_DESTROY_IMPROVEMENT
                if target_region.improvement.name != 'Capital':
                    attacking_combatant.destroyed_improvements += 1
                    defending_combatant.lost_improvements += 1
                    war.log.append(f"    Missile destroyed {target_region.improvement.name} in {target_region.region_id}!")
                    target_nation.improvement_counts[target_region.improvement.name] -= 1
                    target_region.improvement.clear()
                else:
                    war.log.append(f"    Missile devastated Capital in {target_region.region_id}!")
                    target_region.improvement.health = 0

            # destroy unit if present
            if target_region.unit.name != None:
                missile_did_something = True
                war.attackers.destroyed_units += target_region.unit.value    # amount of warscore earned depends on unit value
                attacking_combatant.destroyed_units += 1
                defending_combatant.lost_units += 1
                war.log.append(f"    Missile destroyed {target_region.unit.name} in {target_region.region_id}!")
                target_nation.unit_counts[target_region.unit.name] -= 1
                target_region.unit.clear()

        # message for if missile hit nothing despite reaching its target
        if not missile_did_something:
            war.log.append(f"    Missile successfully struck {target_region.region_id} but did not damage anything of strategic value.")

def resolve_unit_move_actions(game_id: str, actions_list: list[UnitMoveAction]) -> None:
    
    from app.nation import Nations
    current_turn_num = core.get_current_turn_num(game_id)

    # generate movement order for the turn
    players_moving_units: list[str] = []
    for action in actions_list:
        if action.id not in players_moving_units:
            players_moving_units.append(action.id)
    random.shuffle(players_moving_units)
    ordered_actions_list: list[UnitMoveAction] = []
    for nation_id in players_moving_units:
        for action in actions_list:
            if action.id == nation_id:
                ordered_actions_list.append(action)

    # print movement order
    if len(players_moving_units) != 0: 
        print(f"Movement Order - Turn {current_turn_num}")
    for i, nation_id in enumerate(players_moving_units):
        nation = Nations.get(nation_id)
        print(f"{i + 1}. {nation.name}")

    for action in ordered_actions_list:
        
        while action.target_region_ids != []:
            target_region_id = action.target_region_ids.pop()

            nation = Nations.get(action.id)
            current_region = Region(action.current_region_id)
            target_region = Region(target_region_id)

            # current region checks
            if current_region.unit.name == None or action.id != current_region.unit.owner_id:
                nation.action_log.append(f"Failed to perform a move action from {action.current_region_id}. You do not control a unit there.")
                continue
            if target_region_id not in current_region.graph.adjacent_regions:
                nation.action_log.append(f"Failed to move {current_region.unit.name} {action.current_region_id} - {target_region_id}. Target region not adjacent to current region.")
                continue
            if target_region_id == action.current_region_id:
                continue

            # target region checks
            if target_region.data.owner_id == "0" and action.id != "99":
                nation.action_log.append(f"Failed to move {target_region.unit.name} {action.current_region_id} - {target_region_id}. You cannot move a unit to an unclaimed region.")
                continue

            # friendly fire check
            if target_region.unit.name != None and not target_region.unit.is_hostile(current_region.unit.owner_id):
                nation.action_log.append(f"Failed to move {current_region.unit.name} {action.current_region_id} - {target_region_id}. A friendly unit is present in the target region.")
                continue
            if not target_region.is_valid_move(current_region.unit.owner_id):
                nation.action_log.append(f"Failed to move {current_region.unit.name} {action.current_region_id} - {target_region_id}. Region is controlled by a player that is not an enemy.")
                continue

            # execute movement
            unit_name = current_region.unit.name
            movement_success = current_region.move_unit(target_region)
            nation = Nations.get(action.id)
            if movement_success:
                nation.action_log.append(f"Successfully moved {unit_name} {action.current_region_id} - {target_region_id}.")
                action.current_region_id = target_region_id
            else:
                nation.action_log.append(f"Failed to complete move {unit_name} {action.current_region_id} - {target_region_id}. Check combat log for details.")
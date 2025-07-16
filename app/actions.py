import csv
import json
import random
from collections import defaultdict

from app import core
from app.nationdata import Nation
from app.nationdata import NationTable
from app.alliance import AllianceTable
from app.war import WarTable
from app.notifications import Notifications
from app.region import Region
from app.improvement import Improvement
from app.unit import Unit

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
        
        self.target_region = _check_region_id(self.game_id, self.target_region)
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
        
        self.target_region = _check_region_id(self.game_id, self.target_region)
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
        
        self.target_region = _check_region_id(self.game_id, self.target_region)
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
        
        self.target_region = _check_region_id(self.game_id, self.target_region)
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

        self.target_region = _check_region_id(self.game_id, self.target_region)
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
        
        self.target_region = _check_region_id(self.game_id, self.target_region)
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
        
        self.current_region_id = _check_region_id(self.game_id, self.current_region_id)
        if self.current_region_id is None:
            print(f"""Action "{self.action_str}" submitted by player {self.id} is invalid. Bad starting region id.""")
            return False
        
        for i, region_id in enumerate(self.target_region_ids):
            region_id = _check_region_id(self.game_id, region_id)
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

        self.target_nation = " ".join(words[1:nnei]) if len(words) > 4 else None
        self.war_justification = " ".join(words[wjsi:]) if len(words) > 4 else None

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
        else:
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
        "Alliance Create": AllianceCreateAction,
        "Alliance Join": AllianceJoinAction,
        "Alliance Kick": AllianceKickAction,
        "Alliance Leave": AllianceLeaveAction,
        "Claim": ClaimAction,
        "Steal": CrimeSyndicateAction,
        "Event": EventAction,
        "Build": ImprovementBuildAction,
        "Remove": ImprovementRemoveAction,
        "Buy": MarketBuyAction,
        "Sell": MarketSellAction,
        "Make": MissileMakeAction,
        "Launch": MissileLaunchAction,
        "Republic": RepublicAction,
        "Research": ResearchAction,
        "Surrender": SurrenderAction,
        "Deploy": UnitDeployAction,
        "Disband": UnitDisbandAction,
        "Move": UnitMoveAction,
        "War": WarAction,
        "White Peace": WhitePeaceAction
    }

    while True:

        if action_str == "":
            return
        
        words = action_str.strip().split()
        action_key = words[0].title()
        if action_key == "Alliance" and len(words) >= 2:
            action_key = f"{words[0].title()} {words[1].title()}"
        if action_key == "White" and len(words) >= 2:
            action_key = f"{words[0].title()} {words[1].title()}"
        
        if action_key in actions:
            return actions[action_key](game_id, nation_id, action_str)
        else:
            print(f"""Action "{action_str}" submitted by player {nation_id} is invalid. Unrecognized action type.""")
            action_str = input("Re-enter action or hit enter to skip: ")
            if action_str == "":
                return

def _check_alliance_type(game_id: str, alliance_type: str) -> str | None:
    
    misc_scenario_dict = core.get_scenario_dict(game_id, "Misc")
    alliance_types = set(misc_scenario_dict["allianceTypes"].keys())

    if alliance_type.title() in alliance_types:
        return alliance_type.title()
        
    return None

def _check_alliance_name(game_id: str, alliance_name: str) -> str | None:
    
    alliance_table = AllianceTable(game_id)

    for alliance in alliance_table:
        if alliance.name.lower() == alliance_name.lower():
            return alliance.name
        
    return None

def _check_region_id(game_id: str, region_id: str) -> str | None:

    with open(f'gamedata/{game_id}/regdata.json', 'r') as json_file:
        regdata_dict = json.load(json_file)

    if region_id in regdata_dict:
        return region_id
    
    return None

def _check_nation_name(game_id: str, nation_name: str) -> str | None:

    nation_table = NationTable(game_id)

    for nation in nation_table:
        if nation.name.lower() == nation_name.lower():
            return nation.name
        
    return None

def _check_improvement_name(game_id: str, improvement_name: str) -> str | None:

    improvement_scenario_dict = core.get_scenario_dict(game_id, "Improvements")
    improvement_names = set(improvement_scenario_dict.keys())

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

    if improvement_name.title() in improvement_names:
        return improvement_name.title()
    
    return improvement_errors.get(improvement_name.lower())

def _check_quantity(quantity: str) -> int | None:
    
    try:
        quantity = int(quantity)       
        return quantity
    except:
        return None
    
def _check_resource(resource_name: str) -> str | None:

    # to do - make this check reference game files
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

def _check_missile(game_id: str, missile_type: str) -> str | None:
    
    misc_scenario_dict = core.get_scenario_dict(game_id, "Misc")
    missile_types = set(misc_scenario_dict["missiles"].keys())

    missile_errors = {
        "missile": "Standard Missile",
        "missiles": "Standard Missile",
        "standard missiles": "Standard Missile",
        "nuke": "Nuclear Missile",
        "nukes": "Nuclear Missile",
        "nuclear missiles": "Nuclear Missile"
    }

    if missile_type.title() in missile_types:
        return missile_type.title()
        
    return missile_errors.get(missile_type.lower())

def _check_research(game_id: str, research_name: str) -> str | None:

    agenda_scenario_dict = core.get_scenario_dict(game_id, "Agendas")
    technology_scenario_dict = core.get_scenario_dict(game_id, "Technologies")
    research_names = set(agenda_scenario_dict.keys()).union(technology_scenario_dict.keys())

    if research_name.title() in research_names:
        return research_name.title()
        
    return None

def _check_unit(game_id: str, unit_str: str) -> str | None:
    
    unit_scenario_dict = core.get_scenario_dict(game_id, "Units")
    unit_names = set(unit_scenario_dict.keys())
    
    if unit_str.title() in unit_names:
        return unit_str.title()
    
    for unit_name, unit_data in unit_scenario_dict.items():
        if unit_data["Abbreviation"] == unit_str.upper():
            return unit_name
        
    return None

def _check_war_name(game_id: str, war_name_str: str) -> str | None:

    war_table = WarTable(game_id)
    for war in war_table:
        if war_name_str.lower() == war.name.lower():
            return war.name
        
    return None

def _check_war_justification(game_id: str, war_justification_str: str) -> str | None:

    misc_scenario_dict = core.get_scenario_dict(game_id, "Misc")
    war_justification_list = list(misc_scenario_dict["warJustifications"].keys())
    
    for war_justification in war_justification_list:
        if war_justification.lower() == war_justification_str.lower():
            return war_justification
        
    return None

def resolve_trade_actions(game_id: str) -> None:
    """
    Resolves trade actions between players via CLI.
    """

    nation_table = NationTable(game_id)
    notifications = Notifications(game_id)
    with open(f'gamedata/{game_id}/regdata.json', 'r') as json_file:
        regdata_dict = json.load(json_file)

    trade_action = input("Are there any trade actions this turn? (Y/n) ")

    while trade_action.upper().strip() != "N":
        
        # get nations
        nation_name_1 = input("Enter 1st nation name: ")
        nation_name_2 = input("Enter 2nd nation name: ")
        try:
            nation1 = nation_table.get(nation_name_1)
            nation2 = nation_table.get(nation_name_2)
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
        trade_deal = {
            "Nation1RegionsCeded": [],
            "Nation2RegionsCeded": []
        }
        for resource_name in trade_resources:
            trade_deal[resource_name] = 0.00

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
                    if region_id not in regdata_dict:
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
                    if region_id not in regdata_dict:
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
                nation1.resources_given += abs(amount)
                # pay trade fee
                nation1.update_stockpile("Dollars", -1 * abs(amount) * nation1_fee)
            
            elif amount < 0:
                # negative amount -> nation 1
                nation1.update_stockpile(resource_name, -1 * amount)
                nation2.update_stockpile(resource_name, amount)
                nation2.resources_given += abs(amount)
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
                
                region = Region(region_id, game_id)
                region_improvement = Improvement(region_id, game_id)

                if region_improvement.name is not None:
                    nation1.improvement_counts[region_improvement.name] -= 1
                    nation2.improvement_counts[region_improvement.name] += 1

                region.set_owner_id(nation2.id)
            
            for region_id in trade_deal["Nation2RegionsCeded"]:
                
                region = Region(region_id, game_id)
                region_improvement = Improvement(region_id, game_id)

                if region_improvement.name is not None:
                    nation1.improvement_counts[region_improvement.name] += 1
                    nation2.improvement_counts[region_improvement.name] -= 1

                region.set_owner_id(nation1.id)

        # save changes
        if trade_valid:
            nation_table.save(nation1)
            nation_table.save(nation2)
            notifications.append(f'{nation1.name} traded with {nation2.name}.', 9)
        else:
            print(f'Trade between {nation1.name} and {nation2.name} failed. Insufficient resources.')

        trade_action = input("Are there any additional trade actions this turn? (Y/n) ")

def resolve_peace_actions(game_id: str, surrender_list: list[SurrenderAction], white_peace_list: list[WhitePeaceAction]) -> None:
    
    # get game data
    nation_table = NationTable(game_id)
    war_table = WarTable(game_id)
    notifications = Notifications(game_id)
    current_turn_num = core.get_current_turn_num(game_id)

    # execute surrender actions
    for action in surrender_list:
        
        surrendering_nation = nation_table.get(action.id)
        winning_nation = nation_table.get(action.target_nation)

       # check if peace is possible
        if not _peace_action_valid(war_table, nation_table, surrendering_nation, winning_nation, current_turn_num):
            continue

        # get war and war outcome
        war_name = war_table.get_war_name(surrendering_nation.id, winning_nation.id)
        war = war_table.get(war_name)
        c1 = war.get_combatant(surrendering_nation.id)
        if 'Attacker' in c1.role:
            outcome = "Defender Victory"
        else:
            outcome = "Attacker Victory"

        # save nation data
        nation_table.save(surrendering_nation)

        # end war
        war.end_conflict(outcome)
        war_table.save(war)
        notifications.append(f"{surrendering_nation.name} surrendered to {winning_nation.name}.", 4)
        notifications.append(f"{war_name} has ended.", 4)

    # execute white peace actions
    white_peace_dict = {}
    for action in white_peace_list:
        
        surrendering_nation = nation_table.get(action.id)
        winning_nation = nation_table.get(action.target_nation)

        # check if peace is possible
        if not _peace_action_valid(war_table, nation_table, surrendering_nation, winning_nation, current_turn_num):
            continue

        # add white peace request to white_peace_dict
        war_name = war_table.get_war_name(surrendering_nation.id, winning_nation.id)
        if war_name in white_peace_dict:
            white_peace_dict[war_name] += 1
        else:
            white_peace_dict[war_name] = 1

    # process white peace if both sides agreed
    for war_name in white_peace_dict:
        if white_peace_dict[war_name] == 2:
            war = war_table.get(war_name)
            war.end_conflict("White Peace")
            war_table.save(war)
            notifications.append(f'{war_name} has ended with a white peace.', 4)

def _peace_action_valid(war_table: WarTable, nation_table: NationTable, surrendering_nation: Nation, winning_nation: Nation, current_turn_num: int) -> bool:

    # check that war exists
    war_name = war_table.get_war_name(surrendering_nation.id, winning_nation.id)
    if war_name is None:
        surrendering_nation.action_log.append(f"Failed to surrender to {winning_nation.name}. You are not at war with that nation.")
        nation_table.save(surrendering_nation)
        return False

    # check that surrendee(?) has authority to surrender
    war = war_table.get(war_name)
    c1 = war.get_combatant(surrendering_nation.id)
    c2 = war.get_combatant(winning_nation.id)
    if 'Main' not in c1.role or 'Main' not in c2.role:
        surrendering_nation.action_log.append(f"Failed to surrender to {winning_nation.name}. You are not the main attacker/defender or {winning_nation.name} is not the main attacker/defender.")
        nation_table.save(surrendering_nation)
        return False

    # check that it has been 4 turns since war began
    if current_turn_num - war.start < 4:
        surrendering_nation.action_log.append(f"Failed to surrender to {winning_nation.name}. At least four turns must pass before peace can be made.")
        nation_table.save(surrendering_nation)
        return False

    return True

def resolve_research_actions(game_id: str, actions_list: list[ResearchAction]) -> None:
    
    # get game data
    nation_table = NationTable(game_id)
    alliance_table = AllianceTable(game_id)
    agenda_data_dict = core.get_scenario_dict(game_id, "Agendas")
    research_data_dict = core.get_scenario_dict(game_id, "Technologies")

    # execute actions
    for action in actions_list:
        
        nation = nation_table.get(action.id)

        # duplication check
        if action.research_name in nation.completed_research:
            nation.action_log.append(f"Failed to research {action.research_name}. You have already researched this.")
            nation_table.save(nation)
            continue

        # event check
        if any("No Agenda Research" in tag_data for tag_data in nation.tags.values()):
            nation.action_log.append(f"Failed to research {action.research_name} due to an event penalty.")
            nation_table.save(nation)
            continue

        if action.research_name in agenda_data_dict:
            
            cost = agenda_data_dict[action.research_name]['Cost']
            prereq = agenda_data_dict[action.research_name]['Prerequisite']
            agenda_type = agenda_data_dict[action.research_name]['Agenda Type']

            # prereq check
            if prereq != None and prereq not in nation.completed_research:
                nation.action_log.append(f"Failed to research {action.research_name}. You do not have the prerequisite research.")
                nation_table.save(nation)
                continue

            # agenda cost adjustment
            cost += nation.calculate_agenda_cost_adjustment(action.research_name)

            # pay cost
            nation.update_stockpile("Political Power", -1 * cost)
            if float(nation.get_stockpile("Political Power")) < 0:
                nation_table.reload()
                nation = nation_table.get(action.id)
                nation.action_log.append(f"Failed to research {action.research_name}. Not enough political power.")
                nation_table.save(nation)
                continue

            # gain agenda
            nation.action_log.append(f"Researched {action.research_name} for {cost} political power.")
            nation.add_tech(action.research_name)

        else:

            cost = research_data_dict[action.research_name]['Cost']
            prereq = research_data_dict[action.research_name]['Prerequisite']

            # prereq check
            if prereq != None and prereq not in nation.completed_research:
                nation.action_log.append(f"Failed to research {action.research_name}. You do not have the prerequisite research.")
                nation_table.save(nation)
                continue

            # technology cost adjustment
            multiplier = 1.0
            for alliance in alliance_table:
                if alliance.is_active and nation.name in alliance.current_members and alliance.type == "Research Agreement":
                    for ally_name in alliance.current_members:
                        ally_nation = nation_table.get(ally_name)
                        if ally_name == nation.name:
                            continue
                        if action.research_name in ally_nation.completed_research:
                            multiplier -= 0.2
                            break
            if multiplier < 0:
                multiplier = 0.2

            # pay cost
            if multiplier != 1.0:
                cost *= multiplier
                cost = int(cost)
            nation.update_stockpile("Research", -1 * cost)
            if float(nation.get_stockpile("Research")) < 0:
                nation_table.reload()
                nation = nation_table.get(action.id)
                nation.action_log.append(f"Failed to research {action.research_name}. Not enough technology.")
                nation_table.save(nation)
                continue

            # gain technology
            nation.action_log.append(f"Researched {action.research_name} for {cost} technology.")
            nation.add_tech(action.research_name)
            nation.award_research_bonus(action.research_name)
            
        nation_table.save(nation)

def resolve_alliance_leave_actions(game_id: str, actions_list: list[AllianceLeaveAction]) -> None:
    
    # get game data
    nation_table = NationTable(game_id)
    alliance_table = AllianceTable(game_id)
    notifications = Notifications(game_id)

    # process actions
    for action in actions_list:

        nation = nation_table.get(action.id)
        alliance = alliance_table.get(action.alliance_name)

        # remove player from alliance
        alliance.remove_member(nation.name)
        alliance_table.save(alliance)
        notifications.append(f"{nation.name} has left the {alliance.name}.", 7)
        nation.action_log.append(f"Left {action.alliance_name}.")
        nation_table.save(nation)

def resolve_alliance_kick_actions(game_id: str, actions_list: list[AllianceKickAction]) -> None:
    
    # get game data
    nation_table = NationTable(game_id)
    alliance_table = AllianceTable(game_id)
    notifications = Notifications(game_id)

    # execute actions
    kick_actions_tally = defaultdict(lambda: defaultdict(int))
    for action in actions_list:
        nation = nation_table.get(action.id)
        target_nation = nation_table.get(action.target_nation)
        alliance = alliance_table.get(action.alliance_name)

        # check that nation is in alliance
        if action.target_nation not in alliance.current_members:
            nation.action_log.append(f"Failed to vote to kick {action.target_nation} from {action.alliance_name}. You are not in the alliance.")
            nation_table.save(nation)
            continue

        # check that target nation is in alliance
        if action.target_nation not in alliance.current_members:
            nation.action_log.append(f"Failed to vote to kick {action.target_nation} from {action.alliance_name}. Target nation is not in the alliance.")
            nation_table.save(nation)
            continue

        # cannot kick target nation if founder and alliance centralization
        if action.target_nation in alliance.founding_members and "Alliance Centralization" in target_nation.completed_research:
            nation.action_log.append(f"Failed to vote to kick {action.target_nation} from {action.alliance_name}. Target nation is a founder of the alliance.")
            nation_table.save(nation)
            continue

        # add kick action to tally
        kick_actions_tally[alliance.name][action.target_nation] += 1
        nation.action_log.append(f"Voted to kick {action.target_nation} from {action.alliance_name}.")
        nation_table.save(nation)

    # check tally
    for alliance_name, kick_tally in kick_actions_tally.items():
        for target_nation_name, votes in kick_tally.items():
            alliance = alliance_table.get(alliance_name)

            # kick player from alliance if vote is unanimous
            if votes >= len(alliance.current_members) - 1:
                alliance.remove_member(target_nation_name)
                alliance_table.save(alliance)
                notifications.append(f"{action.target_nation} has been kicked from {action.alliance_name}!", 7)

def resolve_alliance_create_actions(game_id: str, actions_list: list[AllianceCreateAction]) -> None:
    
    # get game data
    nation_table = NationTable(game_id)
    alliance_table = AllianceTable(game_id)
    notifications = Notifications(game_id)

    # process actions
    alliance_creation_dict = {}
    for action in actions_list:

        nation = nation_table.get(action.id)

        # required research check
        # tba - tie this to scenario files
        research_check_success = True
        match action.alliance_type:
            case "Non-Aggression Pact" | "Defense Pact":
                if "Common Ground" not in nation.completed_research:
                   research_check_success = False
            case "Trade Agreement":
                if "Trade Routes" not in nation.completed_research:
                   research_check_success = False 
            case "Research Agreement":
                if "Technology Exchange" not in nation.completed_research:
                   research_check_success = False 
        if not research_check_success:
            nation.action_log.append(f"Failed to form {action.alliance_name} alliance. You do not have the required agenda.")
            nation_table.save(nation)
            continue

        # check alliance capacity
        if action.alliance_type != 'Non-Aggression Pact':
            alliance_count, alliance_capacity = core.get_alliance_count(game_id, nation)
            if (alliance_count + 1) > alliance_capacity:
                nation.action_log.append(f"Failed to form {action.alliance_name} alliance. You do not have enough alliance capacity.")
                nation_table.save(nation)
                continue

        # check that an alliance with this name does not already exist
        if action.alliance_name in alliance_table.data:
            nation.action_log.append(f"Failed to form {action.alliance_name} alliance. An alliance with that name has already been created.")
            nation_table.save(nation)
            continue

        # update alliance_creation_dict
        if action.alliance_name in alliance_creation_dict:
            alliance_creation_dict[action.alliance_name]["members"].append(nation.name)
        else:
            entry = {}
            entry["type"] = action.alliance_type
            entry["members"] = [nation.name]
            alliance_creation_dict[action.alliance_name] = entry
        
    # create the alliance if more than two founders
    for alliance_name, alliance_data in alliance_creation_dict.items():
        if len(alliance_data["members"]) > 1:
            # alliance creation success
            alliance = alliance_table.create(alliance_name, alliance_data["type"], alliance_data["members"])
            notifications.append(f"{alliance.name} has formed.", 7)
            for nation_name in alliance_data["members"]:
                # update log
                nation = nation_table.get(nation_name)
                nation.action_log.append(f"Successfully formed {action.alliance_name}.")
                nation_table.save(nation)
        else:
            # alliance creation failed
            nation_name = alliance_data["members"][0]
            nation = nation_table.get(nation_name)
            nation.action_log.append(f"Failed to form {action.alliance_name} alliance. Not enough players agreed to establish it.")
            nation_table.save(nation)   

def resolve_alliance_join_actions(game_id: str, actions_list: list[AllianceJoinAction]) -> None:
    
    # get game data
    nation_table = NationTable(game_id)
    alliance_table = AllianceTable(game_id)
    notifications = Notifications(game_id)

    # process actions
    for action in actions_list:
        
        nation = nation_table.get(action.id)
        alliance = alliance_table.get(action.alliance_name)

        # required research check
        # tba - tie this to scenario data
        research_check_success = True
        match alliance.type:
            case "Non-Aggression Pact" | "Defense Pact":
                if "Common Ground" not in nation.completed_research:
                   research_check_success = False
            case "Trade Agreement":
                if "Trade Routes" not in nation.completed_research:
                   research_check_success = False 
            case "Research Agreement":
                if "Technology Exchange" not in nation.completed_research:
                   research_check_success = False 
        if not research_check_success:
            nation.action_log.append(f"Failed to join {action.alliance_name} alliance. You do not have the required agenda.")
            nation_table.save(nation)
            continue

        # check alliance capacity
        if alliance.type != "Non-Aggression Pact":
            alliance_count, alliance_capacity = core.get_alliance_count(game_id, nation)
            if (alliance_count + 1) > alliance_capacity:
                nation.action_log.append(f"Failed to join {action.alliance_name} alliance. You do not have enough alliance capacity.")
                nation_table.save(nation)
                continue

        # check if puppet state
        if "Puppet State" in nation.status:
            nation.action_log.append(f"Failed to join {action.alliance_name} alliance. Puppet states cannot join alliances.")
            nation_table.save(nation)
            continue

        # check events
        if "Faustian Bargain" in nation.tags:
            nation.action_log.append(f"Failed to join {action.alliance_name} alliance. The collaborator cannot join alliances.")
            nation_table.save(nation)
            continue

        # add player to the alliance
        alliance.add_member(nation.name)
        alliance_table.save(alliance)
        notifications.append(f"{nation.name} has joined the {alliance.name}.", 7)
        nation.action_log.append(f"Joined {alliance.name}.")
        nation_table.save(nation)

def resolve_claim_actions(game_id: str, actions_list: list[ClaimAction]) -> None:
    
    # get game data
    nation_table = NationTable(game_id)
    with open('active_games.json', 'r') as json_file:
        active_games_dict = json.load(json_file)

    # execute actions
    region_queue: list[Region] = []
    for action in actions_list:
        nation = nation_table.get(action.id)
        region = Region(action.target_region, game_id)

        # ownership check
        if region.owner_id != 0:
            nation.action_log.append(f"Failed to claim {action.target_region}. This region is already owned by another nation.")
            nation_table.save(nation)
            continue

        # event check
        if "Civil Disorder" in nation.tags:
            nation.action_log.append(f"Failed to claim {action.target_region} due to the Widespread Civil Disorder event.")
            nation_table.save(nation)
            continue

        # adjacency check
        # to be added
        
        # attempt to pay for region
        nation.update_stockpile("Dollars", -1 * region.purchase_cost)
        nation.update_stockpile("Political Power", -1 * nation.region_claim_political_power_cost())
        if float(nation.get_stockpile("Dollars")) < 0 or float(nation.get_stockpile("Political Power")) < 0:
            nation_table.reload()
            nation = nation_table.get(action.id)
            nation.action_log.append(f"Failed to claim {action.target_region}. Insufficient resources.")
            nation_table.save(nation)
            continue

        # all checks passed add to region_queue
        if region not in region_queue:
            region.add_claim(action.id)
            region_queue.append(region)
        else:
            index = region_queue.index(region)
            existing_region = region_queue[index]
            existing_region.add_claim(action.id)
            region_queue[index] = existing_region

        # update nation data
        nation_table.save(nation)

    # resolve claims
    for region in region_queue:

        if len(region.claim_list) == 1:

            # region purchase successful
            player_id = region.claim_list[0]
            nation = nation_table.get(player_id)
            region.set_owner_id(int(player_id))
            # update improvement count if needed
            region_improvement = Improvement(region.region_id, game_id)
            if region_improvement.name is not None:
                nation.improvement_counts[region_improvement.name] += 1
            # update nation data
            nation.action_log.append(f"Claimed region {region.region_id} for {region.purchase_cost} dollars.")
            nation_table.save(nation)
        
        else:

            # region is disputed
            region.increase_purchase_cost()
            active_games_dict[game_id]["Statistics"]["Region Disputes"] += 1
            for player_id in region.claim_list:
                nation = nation_table.get(player_id)
                nation.action_log.append(f"Failed to claim {region.region_id} due to a region dispute.")
                nation_table.save(nation)
    
    # update active games
    with open('active_games.json', 'w') as json_file:
        json.dump(active_games_dict, json_file, indent=4)

def resolve_improvement_remove_actions(game_id: str, actions_list: list[ImprovementRemoveAction]) -> None:
    
    # get game data
    nation_table = NationTable(game_id)

    for action in actions_list:
        nation = nation_table.get(action.id)
        region = Region(action.target_region, game_id)
        region_improvement = Improvement(action.target_region, game_id)

        # ownership check
        if str(region.owner_id) != action.id or region.occupier_id != 0:
            nation.action_log.append(f"Failed to remove {region_improvement.name} in region {action.target_region}. You do not own or control this region.")
            nation_table.save(nation)
            continue

        # capital check
        if region_improvement.name == "Capital":
            nation.action_log.append(f"Failed to remove {region_improvement.name} in region {action.target_region}. You cannot remove a Capital improvement.")
            nation_table.save(nation)
            continue

        # remove improvement
        if region_improvement.name is not None:
            nation.improvement_counts[region_improvement.name] -= 1
        region_improvement.clear()
        nation.action_log.append(f"Removed improvement in region {action.target_region}.")

        # update nation data
        nation_table.save(nation)

def resolve_improvement_build_actions(game_id: str, actions_list: list[ImprovementBuildAction]) -> None:
    
    # get game data
    nation_table = NationTable(game_id)
    improvement_data_dict = core.get_scenario_dict(game_id, "Improvements")

    # execute actions
    for action in actions_list:
        nation = nation_table.get(action.id)
        region = Region(action.target_region, game_id)
        region_improvement = Improvement(action.target_region, game_id)

        # ownership check
        if str(region.owner_id) != action.id or region.occupier_id != 0:
            nation.action_log.append(f"Failed to build {action.improvement_name} in region {action.target_region}. You do not own or control this region.")
            nation_table.save(nation)
            continue

        # capital check
        if region_improvement.name == "Capital":
            nation.action_log.append(f"Failed to remove build {action.improvement_name} in region {action.target_region}. You cannot build over a Capital improvement.")
            nation_table.save(nation)
            continue
        
        # required research check
        required_research = improvement_data_dict[action.improvement_name]["Required Research"]
        if required_research is not None and required_research not in nation.completed_research:
            nation.action_log.append(f"Failed to build {action.improvement_name} in region {action.target_region}. You do not have the required research.")
            nation_table.save(nation)
            continue

        # required region resource check
        required_resource = improvement_data_dict[action.improvement_name]["Required Resource"]
        if required_resource is not None and required_resource != region.resource:
            nation.action_log.append(f"Failed to build {action.improvement_name} in region {action.target_region}. The region does not have the resource required for this improvement.")
            nation_table.save(nation)
            continue

        # nuke check
        if region.fallout != 0:
            nation.action_log.append(f"Failed to build {action.improvement_name} in region {action.target_region}. Region cannot support an improvement due to nuclear missile detonation.")
            nation_table.save(nation)
            continue

        # event check
        if action.improvement_name == "Colony" and "Faustian Bargain" not in nation.tags:
            nation.action_log.append(f"Failed to build {action.improvement_name} in region {action.target_region}. You are not the Collaborator.")
            nation_table.save(nation)
            continue

        # calculate build cost
        build_cost_dict = improvement_data_dict[action.improvement_name]["Build Costs"]
        nation.apply_build_discount(build_cost_dict)

        # pay for improvement
        costs_list = []
        for resource_name, cost in build_cost_dict.items():
            valid = True
            costs_list.append(f"{cost} {resource_name.lower()}")
            nation.update_stockpile(resource_name, -1 * cost)
            if float(nation.get_stockpile(resource_name)) < 0:
                valid = False
                break
        if not valid:
            nation_table.reload()
            nation = nation_table.get(action.id)
            nation.action_log.append(f"Failed to build {action.improvement_name} in region {action.target_region}. Insufficient resources.")
            nation_table.save(nation)
            continue

        # add cost log string
        if len(costs_list) <= 2:
            costs_str = " and ".join(costs_list)
        else:
            costs_str = ", ".join(costs_list)
            costs_str = " and ".join(costs_str.rsplit(", ", 1))
        nation.action_log.append(f"Built {action.improvement_name} in region {action.target_region} for {costs_str}.")

        # place improvement
        if region_improvement.name is not None:
            nation.improvement_counts[region_improvement.name] -= 1
            mc = improvement_data_dict[action.improvement_name]["Income"].get("Military Capacity")
            if mc is not None:
                nation.update_max_mc(-1 * mc)
        region_improvement.set_improvement(action.improvement_name, player_research=nation.completed_research)
        
        # update nation data
        nation.improvement_counts[action.improvement_name] += 1
        mc = improvement_data_dict[action.improvement_name]["Income"].get("Military Capacity")
        if mc is not None:
            nation.update_max_mc(mc)
        nation_table.save(nation)

def resolve_missile_make_actions(game_id: str, actions_list: list[MissileMakeAction]) -> None:
    
    # get game data
    nation_table = NationTable(game_id)
    # tba - add missile data to scenario

    # execute actions
    for action in actions_list:

        nation = nation_table.get(action.id)

        # required technology check
        if action.missile_type == "Standard Missile" and "Missile Technology" not in nation.completed_research:
            nation.action_log.append(f"Failed to manufacture {action.quantity}x {action.missile_type}. You do not have the Missile Technology technology.")
            nation_table.save(nation)
            continue
        elif action.missile_type == "Nuclear Missile" and "Nuclear Warhead" not in nation.completed_research:
            nation.action_log.append(f"Failed to manufacture {action.quantity}x {action.missile_type}. You do not have the Nuclear Warhead technology.")
            nation_table.save(nation)
            continue
        
        # pay for missile(s)
        if action.missile_type == "Standard Missile":
            nation.update_stockpile("Common Metals", -3 * action.quantity)
            if float(nation.get_stockpile("Common Metals")) < 0:
                nation_table.reload()
                nation = nation_table.get(action.id)
                nation.action_log.append(f"Failed to manufacture {action.quantity}x {action.missile_type}. Insufficient resources.")
                nation_table.save(nation)
                continue
        elif action.missile_type == "Nuclear Missile":
            nation.update_stockpile("Advanced Metals", -2 * action.quantity)
            nation.update_stockpile("Uranium", -2 * action.quantity)
            nation.update_stockpile("Rare Earth Elements", -2 * action.quantity)
            if (
                float(nation.get_stockpile("Advanced Metals")) < 0
                or float(nation.get_stockpile("Uranium")) < 0
                or float(nation.get_stockpile("Rare Earth Elements")) < 0
               ):
                nation_table.reload()
                nation = nation_table.get(action.id)
                nation.action_log.append(f"Failed to manufacture {action.quantity}x {action.missile_type}. Insufficient resources.")
                nation_table.save(nation)
                continue

        # execute action
        if action.missile_type == "Standard Missile":
            nation.missile_count += action.quantity
        elif action.missile_type == "Nuclear Missile":
            nation.nuke_count += action.quantity

        # update nation data
        nation.action_log.append(f"Manufactured {action.quantity}x {action.missile_type}.")
        nation_table.save(nation)

def resolve_government_actions(game_id: str, actions_list: list[RepublicAction]) -> None:
    
    # get game data
    nation_table = NationTable(game_id)
    notifications = Notifications(game_id)

    # execute republic actions
    for action in actions_list:

        nation = nation_table.get(action.id)

        # government check
        if nation.gov != "Republic":
            nation.action_log.append(f"Failed to execute Republic government action. Your nation is not a Republic.")
            nation_table.save(nation)
            continue

        # pay for action
        nation.update_stockpile("Political Power", -5)
        if float(nation.get_stockpile("Political Power")) < 0:
            nation_table.reload()
            nation = nation_table.get(action.id)
            nation.action_log.append(f"Failed to execute Republic government action. Insufficient political power.")
            nation_table.save(nation)
            continue

        # add tag
        new_tag = {}
        new_tag[f"{action.resource_name} Rate"] = 20
        new_tag["Expire Turn"] = 99999
        nation.tags["Republic Bonus"] = new_tag

        # update nation data
        nation.action_log.append(f"Used Republic government action to boost {action.resource_name} income.")
        nation_table.save(nation)

        notifications.append(f"{nation.name} used Republic government action to boost {action.resource_name} income.", 8)

def resolve_event_actions(game_id: str, actions_list: list[EventAction]) -> None:
    
    # note: event actions are currently not validated ahead of time hence the length of this function
    # tba - handle event actions better using scenario data so that this function can be cleaner

    # get game data
    nation_table = NationTable(game_id)
    current_turn_num = core.get_current_turn_num(game_id)
    research_data_dict = core.get_scenario_dict(game_id, "Technologies")
    trucedata_filepath = f'gamedata/{game_id}/trucedata.csv'
    trucedata_list = core.read_file(trucedata_filepath, 1)
    with open('active_games.json', 'r') as json_file:
        active_games_dict = json.load(json_file)

    for action in actions_list:

        nation = nation_table.get(action.id)

        # "Event Host Peace Talks [ID]"
        if "Host Peace Talks" in action.action_str:

            # mediator check
            if "Mediator" not in nation.tags:
                nation.action_log.append(f"Failed to Host Peace Talks. You are not the Mediator.")
                nation_table.save(nation)
                continue

            for truce in trucedata_list:
                
                truce_id = str(truce[0])
                mediator_in_truce = truce[int(action.id)]
                truce_expire_turn = int(truce[len(truce)])

                if truce_id in action.action_str[-2:]:
                    
                    # already extended check
                    if truce_id in nation.tags["Mediator"]["Truces Extended"]:
                        nation.action_log.append(f"Failed to Host Peace Talks for Truce #{truce[0]}. Truce has already been extended.")
                        break
                    
                    # player involved check
                    if mediator_in_truce:
                        nation.action_log.append(f"Failed to Host Peace Talks for Truce #{truce[0]}. Mediator is involved in this truce.")
                        break
                
                    # truce not yet expired check
                    if current_turn_num >= truce_expire_turn:
                        nation.action_log.append(f"Failed to Host Peace Talks for Truce #{truce[0]}. Truce has already expired.")
                        break

                    # pay for action
                    nation.update_stockpile("Political Power", -5)
                    if float(nation.get_stockpile("Political Power")) < 0:
                        nation_table.reload()
                        nation = nation_table.get(action.id)
                        nation.action_log.append(f"Failed to Host Peace Talks for Truce #{truce[0]}. Insufficient political power.")
                        break
                    
                    # resolve action
                    truce[len(truce)] = truce_expire_turn + 4
                    nation.tags["Mediator"]["Truces Extended"].append(truce_id)
                    nation.action_log.append(f"Used Host Peace Talks on Truce #{truce[0]}.")
                    break
        
        # "Event Cure Research [Count]"
        elif "Cure Research" in action.action_str:
            
            # required event check
            if "Pandemic" not in active_games_dict[game_id]["Active Events"]:
                nation.action_log.append(f"Failed to do Cure Research action. Pandemic event is not active.")
                nation_table.save(nation)
                continue

            # pay for action
            event_action_data = action.action_str.split(" ")
            count = int(event_action_data[-1])
            nation.update_stockpile("Research", -1 * count)
            if float(nation.get_stockpile("Research")) < 0:
                nation_table.reload()
                nation = nation_table.get(action.id)
                nation.action_log.append(f"Failed to spend {count} technology on Cure Research. Insufficient technology.")
                nation_table.save(nation)
                continue

            # resolve action
            research_amount = count
            active_games_dict[game_id]['Active Events']["Pandemic"]["Completed Cure Research"] += research_amount
            nation.action_log.append(f"Used Cure Research to spend {count} technology in exchange for {research_amount} cure progress.")

        # "Event Fundraise [Count]"
        elif "Fundraise" in action.action_str:
            
            # required event check
            if "Pandemic" not in active_games_dict[game_id]["Active Events"]:
                nation.action_log.append(f"Failed to do Fundraise action. Pandemic event is not active.")
                nation_table.save(nation)
                continue
            
            # pay for action
            event_action_data = action.action_str.split(" ")
            count = int(event_action_data[-1])
            nation.update_stockpile("Dollars", -1 * count)
            if float(nation.get_stockpile("Dollars")) < 0:
                nation_table.reload()
                nation = nation_table.get(action.id)
                nation.action_log.append(f"Failed to spend {count} dollars on Fundraise. Insufficient dollars.")
                nation_table.save(nation)
                continue
            
            # resolve action
            research_amount = count // 3
            active_games_dict[game_id]['Active Events']["Pandemic"]["Completed Cure Research"] += research_amount
            nation.action_log.append(f"Used Fundraise to spend {count} dollars in exchange for {research_amount} cure progress.")

        # "Event Inspect [Region ID]"
        elif "Inspect" in action.action_str:
            
            # required event check
            if "Pandemic" not in active_games_dict[game_id]["Active Events"]:
                nation.action_log.append(f"Failed to do Inspect action. Pandemic event is not active.")
                nation_table.save(nation)
                continue
            
            # pay for action
            event_action_data = action.action_str.split(" ")
            region_id = event_action_data[-1]
            nation.update_stockpile("Dollars", -5)
            if float(nation.get_stockpile("Dollars")) < 0:
                nation_table.reload()
                nation = nation_table.get(action.id)
                nation.action_log.append(f"Failed to Inspect {region_id}. Insufficient dollars.")
                nation_table.save(nation)
                continue

            # resolve action
            region = Region(region_id, game_id)
            nation.action_log.append(f"Used Inspect action for 5 dollars. Region {region_id} has an infection score of {region.infection()}.")

        # "Event Create Quarantine [Region ID]"
        elif "Create Quarantine" in action.action_str:
            
            # required event check
            if "Pandemic" not in active_games_dict[game_id]["Active Events"]:
                nation.action_log.append(f"Failed to do Create Quarantine action. Pandemic event is not active.")
                nation_table.save(nation)
                continue
            
            # pay for action
            nation.update_stockpile("Political Power", -1)
            if float(nation.get_stockpile("Political Power")) < 0:
                nation_table.reload()
                nation = nation_table.get(action.id)
                nation.action_log.append(f"Failed to quarantine {region_id}. Insufficient political power.")
                nation_table.save(nation)
                continue

            # execute action
            event_action_data = action.action_str.split(" ")
            region_id = event_action_data[-1]
            region.set_quarantine()
            nation.action_log.append(f"Quarantined {region_id} for 1 political power.")

        # "Event End Quarantine [Region ID]"
        elif "End Quarantine" in action.action_str:
            
            # required event check
            if "Pandemic" not in active_games_dict[game_id]["Active Events"]:
                nation.action_log.append(f"Failed to do End Quarantine action. Pandemic event is not active.")
                nation_table.save(nation)
                continue
            
            # pay for action
            nation.update_stockpile("Political Power", -1)
            if float(nation.get_stockpile("Political Power")) < 0:
                nation_table.reload()
                nation = nation_table.get(action.id)
                nation.action_log.append(f"Failed to quarantine {region_id}. Insufficient political power.")
                nation_table.save(nation)
                continue

            # execute action
            event_action_data = action.action_str.split(" ")
            region_id = event_action_data[-1]
            region.set_quarantine(False)
            nation.action_log.append(f"Ended quarantine in {region_id} for 1 political power.")

        # "Event Open Borders"
        elif "Open Borders" in action.action_str:
            
            # required event check
            if "Pandemic" not in active_games_dict[game_id]["Active Events"]:
                nation.action_log.append(f"Failed to do Open Borders action. Pandemic event is not active.")
                nation_table.save(nation)
                continue
            
            # pay for action
            nation.update_stockpile("Political Power", -10)
            if float(nation.get_stockpile("Political Power")) < 0:
                nation_table.reload()
                nation = nation_table.get(action.id)
                nation.action_log.append(f"Failed to do Open Borders action. Insufficient political power.")
                nation_table.save(nation)
                continue

            # execute action
            active_games_dict[game_id]['Active Events']["Pandemic"]["Closed Borders List"].remove(nation.id)
            nation.action_log.append("Spent 10 political power to Open Borders.")

        # "Event Close Borders"
        elif "Close Borders" in action.action_str:
            
            # required event check
            if "Pandemic" not in active_games_dict[game_id]["Active Events"]:
                nation.action_log.append(f"Failed to do Close Borders action. Pandemic event is not active.")
                nation_table.save(nation)
                continue
            
            # pay for action
            nation.update_stockpile("Political Power", -10)
            if float(nation.get_stockpile("Political Power")) < 0:
                nation_table.reload()
                nation = nation_table.get(action.id)
                nation.action_log.append(f"Failed to do Close Borders action. Insufficient political power.")
                nation_table.save(nation)
                continue

            # execute action
            active_games_dict[game_id]['Active Events']["Pandemic"]["Closed Borders List"].append(nation.id)
            nation.action_log.append("Spent 10 political power to Close Borders.")

        # Event Outsource Technology [Research Name]
        elif "Outsource Technology" in action.action_str:
            
            # collaborator check
            if "Faustian Bargain" not in nation.tags:
                nation.action_log.append(f"Failed to Outsource Technology. You are not the collaborator.")
                nation_table.save(nation)
                continue
            
            # test research name
            event_action_list = action.action_str.split(" ")
            research_name = event_action_list[3:]
            research_name = " ".join(research_name)
            if research_name not in research_data_dict:
                nation.action_log.append(f"Failed to do Outsource Technology action. Technology name \"{research_name}\" not recognized.")
                nation_table.save(nation)
                continue
            if research_name in nation.completed_research:
                nation.action_log.append(f"Failed to do Outsource Technology action. You already have {research_name}.")
                nation_table.save(nation)
                continue
            research_prereq = research_data_dict[research_name]['Prerequisite']
            if research_prereq != None and research_prereq not in nation.completed_research:
                nation.action_log.append(f"Failed to do Outsource Technology action. You do not have the prerequisite for {research_name}.")
                nation_table.save(nation)
                continue

            # pay for action
            nation.update_stockpile("Political Power", -10)
            if float(nation.get_stockpile("Political Power")) < 0:
                nation_table.reload()
                nation = nation_table.get(action.id)
                nation.action_log.append(f"Failed to do Outsource Technology action. Insufficient political power.")
                nation_table.save(nation)
                continue

            # execute action
            nation.add_tech(research_name)
            nation.award_research_bonus(research_name)
            nation.action_log.append(f"Used Outsource Technology to research {research_name}.")

        # Event Military Reinforcements [Region ID #1],[Region ID #2]
        elif "Military Reinforcements" in action.action_str:
            
            # collaborator check
            if "Faustian Bargain" not in nation.tags:
                nation.action_log.append(f"Failed to Military Reinforcements. You are not the collaborator.")
                nation_table.save(nation)
                continue

            # pay cost
            nation.update_stockpile("Political Power", -10)
            if float(nation.get_stockpile("Political Power")) < 0:
                nation_table.reload()
                nation = nation_table.get(action.id)
                nation.action_log.append(f"Failed to do Military Reinforcements action. Insufficient political power.")
                nation_table.save(nation)
                continue

            # execute action
            event_action_data = action.action_str.split(" ")
            region_id_str = event_action_data[-1]
            region_id_list = region_id_str.split(",")
            for region_id in region_id_list:
                
                region = Region(region_id, game_id)
                region_unit = Unit(region_id, game_id)
                
                if region.owner_id != int(action.id):
                    nation.action_log.append(f"Failed to use Military Reinforcements to deploy Mechanized Infantry {region_id}. You do not own that region.")
                    nation_table.save(nation)
                    continue
                
                if region_unit.owner_id != int(action.id):
                    nation.action_log.append(f"Failed to use Military Reinforcements to deploy Mechanized Infantry {region_id}. A hostile unit is present.")
                    nation_table.save(nation)
                    continue
                
                if region_unit.name != None:
                    nation.unit_counts[region_unit.name] -= 1
                region_unit.set_unit("Mechanized Infantry", int(action.id))
                nation.unit_counts["Mechanized Infantry"] += 1
                nation.action_log.append(f"Used Military Reinforcements to deploy Mechanized Infantry {region_id}.")

        nation_table.save(nation)

    with open(trucedata_filepath, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(core.trucedata_header)
        writer.writerows(trucedata_list)

    with open('active_games.json', 'w') as json_file:
        json.dump(active_games_dict, json_file, indent=4)

def resolve_market_actions(game_id: str, crime_list: list[CrimeSyndicateAction], buy_list: list[MarketBuyAction], sell_list: list[MarketSellAction]) -> dict:
    
    # get game data
    nation_table = NationTable(game_id)
    notifications = Notifications(game_id)
    rmdata_filepath = f'gamedata/{game_id}/rmdata.csv'
    current_turn_num = core.get_current_turn_num(game_id)
    with open('active_games.json', 'r') as json_file:
        active_games_dict = json.load(json_file)
    

    rmdata_update_list = []
    steal_tracking_dict = active_games_dict[game_id]["Steal Action Record"]
    # tba - grab this from scenario files
    data = {
        "Food": {
            "Base Price": 3,
            "Current Price": 0,
            "Bought": 0,
            "Sold": 0
        },
        "Research": {
            "Base Price": 5,
            "Current Price": 0,
            "Bought": 0,
            "Sold": 0
        },
        "Coal": {
            "Base Price": 3,
            "Current Price": 0,
            "Bought": 0,
            "Sold": 0
        },
        "Oil": {
            "Base Price": 3,
            "Current Price": 0,
            "Bought": 0,
            "Sold": 0
        },
        "Basic Materials": {
            "Base Price": 3,
            "Current Price": 0,
            "Bought": 0,
            "Sold": 0
        },
        "Common Metals": {
            "Base Price": 5,
            "Current Price": 0,
            "Bought": 0,
            "Sold": 0
        },
        "Advanced Metals": {
            "Base Price": 10,
            "Current Price": 0,
            "Bought": 0,
            "Sold": 0
        },
        "Uranium": {
            "Base Price": 10,
            "Current Price": 0,
            "Bought": 0,
            "Sold": 0
        },
        "Rare Earth Elements": {
            "Base Price": 20,
            "Current Price": 0,
            "Bought": 0,
            "Sold": 0
        },
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
    for nation in nation_table:
        market_results[nation.name] = {}
        for resource_name in data:
            market_results[nation.name][resource_name] = 0
        market_results[nation.name]["Dollars"] = 0
        market_results[nation.name]["Thieves"] = []

    # resolve market buying actions
    for action in buy_list:
        
        nation = nation_table.get(action.id)
        price = data[action.resource_name]["Current Price"]
        rate = 1.0
        
        # embargo event check
        if "Embargo" in nation.tags:
            nation.action_log.append(f"Failed to buy {action.quantity} {action.resource_name}. Your nation is currently under an embargo.")
            nation_table.save(nation)
            continue

        # add discounts
        for tag_name, tag_data in nation.tags.items():
            rate -= float(tag_data.get("Market Buy Modifier", 0))
        if "Improved Logistics" in nation.completed_research:
            rate -= 0.2
        if "Foreign Investment" in nation.tags:
            rate -= 0.2

        # pay for resource
        cost = round(action.quantity * price * rate, 2)
        nation.update_stockpile("Dollars", -1 * cost)
        if float(nation.get_stockpile("Dollars")) < 0:
            nation_table.reload()
            nation = nation_table.get(action.id)
            nation.action_log.append(f"Failed to buy {action.quantity} {action.resource_name}. Insufficient dollars.")
            nation_table.save(nation)
            continue

        # update rmdata
        new_entry = [current_turn_num, nation.name, 'Bought', action.quantity, action.resource_name]
        rmdata_update_list.append(new_entry)

        # update nation data
        market_results[nation.name][action.resource_name] = action.quantity
        nation.action_log.append(f"Bought {action.quantity} {action.resource_name} from the resource market for {cost:.2f} dollars.")
        nation_table.save(nation)

    # resolve market selling actions
    for action in sell_list:
        
        nation = nation_table.get(action.id)
        price = float(data[action.resource_name]["Current Price"] * 0.5)
        rate = 1.0

        # embargo event check
        if "Embargo" in nation.tags:
            nation.action_log.append(f"Failed to sell {action.quantity} {action.resource_name}. Your nation is currently under an embargo.")
            nation_table.save(nation)
            continue

        # add increases
        for tag_name, tag_data in nation.tags.items():
            rate += float(tag_data.get("Market Sell Modifier", 0))

        # remove resources from stockpile
        nation.update_stockpile(action.resource_name, -1 * action.quantity)
        if float(nation.get_stockpile(action.resource_name)) < 0:
            nation_table.reload()
            nation = nation_table.get(action.id)
            nation.action_log.append(f"Failed to sell {action.quantity} {action.resource_name}. Insufficient resources in stockpile.")
            nation_table.save(nation)
            continue

        # update rmdata
        new_entry = [current_turn_num, nation.name, 'Sold', action.quantity, action.resource_name]
        rmdata_update_list.append(new_entry)

        # update nation data
        dollars_earned = round(action.quantity * price * rate, 2)
        market_results[nation.name]["Dollars"] += dollars_earned
        nation.action_log.append(f"Sold {action.quantity} {action.resource_name} to the resource market for {dollars_earned:.2f} dollars.")
        nation_table.save(nation)

    # process crime syndicate steal actions
    for action in crime_list:
        for crime_action in crime_list:
            market_results[nation.name]["Thieves"].append(crime_action.id)
    for nation_name, nation_info in market_results.items():
        thieves_list = nation_info["Thieves"]
        if len(thieves_list) != 1:
            for thief_id in thieves_list:
                syndicate_nation = nation_table.get(thief_id)
                syndicate_nation.action_log.append(f"Failed to steal from {crime_action.target_nation} due to other crime syndicate stealing attempts.")
                nation_table.save(syndicate_nation)
            nation_info["Thieves"] = []

    # resolve crime syndicate steal actions
    for nation_name, nation_info in market_results.items():
        thieves_list = nation_info["Thieves"]
        if thieves_list == []:
            continue
        thief_id = thieves_list[0]
            
        # retrieve records
        nation = nation_table.get(nation_name)
        syndicate_nation = nation_table.get(thief_id)
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
        
        notifications.append(f"{syndicate_nation.name} stole from {nation.name}.", 8)

    # update rmdata.csv
    rmdata_all_transaction_list = core.read_rmdata(rmdata_filepath, current_turn_num, False, False)
    with open(rmdata_filepath, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(core.rmdata_header)
        writer.writerows(rmdata_all_transaction_list)
        writer.writerows(rmdata_update_list)

    return market_results

def resolve_unit_disband_actions(game_id: str, actions_list: list[UnitDisbandAction]) -> None:
    
    # get game data
    nation_table = NationTable(game_id)

    for action in actions_list:
        nation = nation_table.get(action.id)
        region_unit = Unit(action.target_region, game_id)

        # ownership check
        if str(region_unit.owner_id) != action.id:
            nation.action_log.append(f"Failed to disband {region_unit.name} in region {action.target_region}. You do not own this unit.")
            nation_table.save(nation)
            continue

        # remove unit
        if region_unit.name is not None:
            nation.unit_counts[region_unit.name] -= 1
            nation.update_used_mc(-1)
        region_unit.clear()
        
        # update nation data
        nation.action_log.append(f"Disbanded unit in region {action.target_region}.")
        nation.update_used_mc(1)
        nation_table.save(nation)

def resolve_unit_deployment_actions(game_id: str, actions_list: list[UnitDeployAction]) -> None:
    
    # get game data
    nation_table = NationTable(game_id)
    unit_scenario_dict = core.get_scenario_dict(game_id, "Units")

    # execute actions
    for action in actions_list:
        region = Region(action.target_region, game_id)
        region_unit = Unit(action.target_region, game_id)
        nation = nation_table.get(action.id)

        # ownership check
        if str(region.owner_id) != action.id or region.occupier_id != 0:
            nation.action_log.append(f"Failed to deploy {action.unit_name} in region {action.target_region}. You do not control this region.")
            nation_table.save(nation)
            continue
        
        # required research check
        if unit_scenario_dict[action.unit_name]['Required Research'] not in nation.completed_research:
            nation.action_log.append(f"Failed to deploy {action.unit_name} in region {action.target_region}. You do not have the required research.")
            nation_table.save(nation)
            continue

        # capacity check
        if nation.get_used_mc() == nation.get_max_mc():
            nation.action_log.append(f"Failed to deploy {action.unit_name} in region {action.target_region}. Insufficient military capacity.")
            nation_table.save(nation)
            continue

        # calculate deployment cost
        build_cost_dict = unit_scenario_dict[action.unit_name]["Build Costs"]
        if nation.gov == 'Military Junta':
            for key in build_cost_dict:
                build_cost_dict[key] *= 0.8

        # pay for unit
        costs_list = []
        for resource_name, cost in build_cost_dict.items():
            valid = True
            costs_list.append(f"{cost} {resource_name.lower()}")
            nation.update_stockpile(resource_name, -1 * cost)
            if float(nation.get_stockpile(resource_name)) < 0:
                valid = False
                break
        if not valid:
            nation_table.reload()
            nation = nation_table.get(action.id)
            nation.action_log.append(f"Failed to deploy {action.unit_name} in region {action.target_region}. Insufficient resources.")
            nation_table.save(nation)
            continue

        # add cost log string
        if len(costs_list) <= 2:
            costs_str = " and ".join(costs_list)
        else:
            costs_str = ", ".join(costs_list)
            costs_str = " and ".join(costs_str.rsplit(", ", 1))
        nation.action_log.append(f"Deployed {action.unit_name} in region {action.unit_name} in region {action.target_region} for {costs_str}.")

        # deploy unit
        if region_unit.name is not None:
            nation.unit_counts[region_unit.name] -= 1
            nation.update_used_mc(-1)
        region_unit.set_unit(action.unit_name, int(action.id))

        # update nation data
        nation.unit_counts[region_unit.name] += 1
        nation.update_used_mc(1)
        nation_table.save(nation)

def resolve_war_actions(game_id: str, actions_list: list[WarAction]) -> None:
    
    # get game data
    nation_table = NationTable(game_id)
    war_table = WarTable(game_id)
    alliance_table = AllianceTable(game_id)
    notifications = Notifications(game_id)

    # execute actions
    for action in actions_list:

        attacker_nation = nation_table.get(action.id)
        defender_nation = nation_table.get(action.target_nation)

        # agenda check
        valid_war_justification = False
        match action.war_justification:
            case "Animosity" | "Border Skirmish":
                valid_war_justification = True
            case "Conquest":
                if "Ideological Wars" in attacker_nation.completed_research:
                    valid_war_justification = True
            case "Containment":
                if "Ideological Wars" in attacker_nation.completed_research and defender_nation.fp != "Diplomatic":
                    valid_war_justification = True
            case "Independence":
                if "Puppet State" in attacker_nation.status and defender_nation.name in attacker_nation.status:
                    valid_war_justification = True
            case "Subjugation":
                if "Dominion" in attacker_nation.completed_research:
                    valid_war_justification = True
        if not valid_war_justification:
            attacker_nation.action_log.append(f"Failed to declare a {action.war_justification} war on {defender_nation.name}. You do not have the required agenda.")
            nation_table.save(attacker_nation)
            continue

        # military capacity check
        if attacker_nation.get_used_mc() == 0:
            attacker_nation.action_log.append(f"Failed to declare a {action.war_justification} war on {defender_nation.name}. You do not have any military units.")
            nation_table.save(attacker_nation)
            continue

        # independence check
        if attacker_nation.status != "Independent Nation" and action.war_justification != "Independence":
            attacker_nation.action_log.append(f"Failed to declare a {action.war_justification} war on {defender_nation.name}. As a puppet state, you cannot declare war.")
            nation_table.save(attacker_nation)
            continue

        # existing war check
        existing_war = war_table.get_war_name(attacker_nation.id, defender_nation.id)
        if existing_war is not None:
            attacker_nation.action_log.append(f"Failed to declare a {action.war_justification} war on {defender_nation.name}. You are already at war with this nation.")
            nation_table.save(attacker_nation)
            continue
        
        # truce check
        if core.check_for_truce(game_id, attacker_nation.id, defender_nation.id):
            attacker_nation.action_log.append(f"Failed to declare a {action.war_justification} war on {defender_nation.name}. You have a truce with this nation.")
            nation_table.save(attacker_nation)
            continue

        # alliance check
        if alliance_table.are_allied(attacker_nation.name, defender_nation.name):
            attacker_nation.action_log.append(f"Failed to declare a {action.war_justification} war on {defender_nation.name}. You have an alliance with this nation.")
            nation_table.save(attacker_nation)
            continue

        # alliance truce check
        if alliance_table.former_ally_truce(attacker_nation.name, defender_nation.name):
            attacker_nation.action_log.append(f"Failed to declare a {action.war_justification} war on {defender_nation.name}. You have recently had an alliance with this nation.")
            nation_table.save(attacker_nation)
            continue

        # tag check
        is_blocked = False
        for tag_name, tag_data in attacker_nation.tags.items():
            if f"Cannot Declare War On #{defender_nation.id}" in tag_data:
                is_blocked = True
                break
        if is_blocked:
            attacker_nation.action_log.append(f"Failed to declare a {action.war_justification} war on {defender_nation.name} due to {tag_name}.")
            nation_table.save(attacker_nation)
            continue

        # validate war claims
        region_claims_list = []
        if action.war_justification in ["Border Skirmish", "Conquest"]:
            
            # get claims and calculate political power cost
            claim_cost = -1
            while claim_cost == -1:
                region_claims_str = input(f"List the regions that {attacker_nation.name} is claiming using {action.war_justification}: ")
                region_claims_list = region_claims_str.split(',')
                claim_cost = core.validate_war_claims(game_id, action.war_justification, region_claims_list)

            # pay political power cost
            attacker_nation.update_stockpile("Political Power", -1 * claim_cost)
            if float(attacker_nation.get_stockpile("Political Power")) < 0:
                nation_table.reload()
                attacker_nation = nation_table.get(action.id)
                attacker_nation.action_log.append(f"Failed to declare a {action.war_justification} war on {defender_nation.name}. Not enough political power for war claims.")
                nation_table.save(attacker_nation)
                continue

        # resolve action
        war_name = war_table.create(attacker_nation.id, defender_nation.id, action.war_justification, region_claims_list)
        notifications.append(f"{attacker_nation.name} declared war on {defender_nation.name}.", 3)
        attacker_nation.action_log.append(f"Declared war on {defender_nation.name}.")
        nation_table.save(attacker_nation)

def resolve_war_join_actions(game_id: str, actions_list: list[WarJoinAction]) -> None:

    #TODO: write functions so that this isn't all copy pasted

    # get game data
    nation_table = NationTable(game_id)
    war_table = WarTable(game_id)
    alliance_table = AllianceTable(game_id)
    notifications = Notifications(game_id)

    # execute actions
    for action in actions_list:

        war = war_table.get(action.war_name)
        attacker_nation = nation_table.get(action.id)

        # add combatant
        combatant = war.add_combatant(attacker_nation, f"Secondary {action.side}", action.war_justification)

        ### process combatant (copied from add_missing_justifications) ###

        # process war claims
        region_claims_list = []
        if action.war_justification in ["Border Skirmish", "Conquest"]:

            combatant.target = "N/A"
            main_attacker_id, main_defender_id = war.get_main_combatant_ids()
            if {action.side} == "Attacker":
                defender_nation = nation_table.get(main_attacker_id)
            elif {action.side} == "Defender":
                defender_nation = nation_table.get(main_defender_id)
            
            # get claims and calculate political power cost
            claim_cost = -1
            while claim_cost == -1:
                region_claims_str = input(f"List the regions that {combatant.name} is claiming using {action.war_justification}: ")
                region_claims_list = region_claims_str.split(',')
                claim_cost = core.validate_war_claims(game_id, action.war_justification, region_claims_list)

            # pay political power cost
            attacker_nation.update_stockpile("Political Power", -1 * claim_cost)
            if float(attacker_nation.get_stockpile("Political Power")) < 0:
                nation_table.reload()
                attacker_nation = nation_table.get(combatant.id)
                attacker_nation.action_log.append(f"Error: Not enough political power for war claims.")
                nation_table.save(attacker_nation)
                continue
        
        # OR handle war justification that does not seize territory
        else:
            
            # get target id
            target_id = input(f"Enter nation_id of nation {combatant.name} is targeting with {action.war_justification}: ")
            combatant.target = str(target_id)
            defender_nation = nation_table.get(combatant.target)

        ### check if combatant can actually join war (copied from resolve_war_actions) ###

        # agenda check
        valid_war_justification = False
        match action.war_justification:
            case "Animosity" | "Border Skirmish":
                valid_war_justification = True
            case "Conquest":
                if "Ideological Wars" in attacker_nation.completed_research:
                    valid_war_justification = True
            case "Containment":
                if "Ideological Wars" in attacker_nation.completed_research and defender_nation.fp != "Diplomatic":
                    valid_war_justification = True
            case "Independence":
                if "Puppet State" in attacker_nation.status and defender_nation.name in attacker_nation.status:
                    valid_war_justification = True
            case "Subjugation":
                if "Dominion" in attacker_nation.completed_research:
                    valid_war_justification = True
        if not valid_war_justification:
            attacker_nation.action_log.append(f"Failed to declare a {action.war_justification} war on {defender_nation.name}. You do not have the required agenda.")
            nation_table.save(attacker_nation)
            continue

        # military capacity check
        if attacker_nation.get_used_mc() == 0:
            attacker_nation.action_log.append(f"Failed to declare a {action.war_justification} war on {defender_nation.name}. You do not have any military units.")
            nation_table.save(attacker_nation)
            continue

        # independence check
        if attacker_nation.status != "Independent Nation" and action.war_justification != "Independence":
            attacker_nation.action_log.append(f"Failed to declare a {action.war_justification} war on {defender_nation.name}. As a puppet state, you cannot declare war.")
            nation_table.save(attacker_nation)
            continue

        # existing war check
        existing_war = war_table.get_war_name(attacker_nation.id, defender_nation.id)
        if existing_war is not None:
            attacker_nation.action_log.append(f"Failed to declare a {action.war_justification} war on {defender_nation.name}. You are already at war with this nation.")
            nation_table.save(attacker_nation)
            continue
        
        # truce check
        if core.check_for_truce(game_id, attacker_nation.id, defender_nation.id):
            attacker_nation.action_log.append(f"Failed to declare a {action.war_justification} war on {defender_nation.name}. You have a truce with this nation.")
            nation_table.save(attacker_nation)
            continue

        # alliance check
        if alliance_table.are_allied(attacker_nation.name, defender_nation.name):
            attacker_nation.action_log.append(f"Failed to declare a {action.war_justification} war on {defender_nation.name}. You have an alliance with this nation.")
            nation_table.save(attacker_nation)
            continue

        # alliance truce check
        if alliance_table.former_ally_truce(attacker_nation.name, defender_nation.name):
            attacker_nation.action_log.append(f"Failed to declare a {action.war_justification} war on {defender_nation.name}. You have recently had an alliance with this nation.")
            nation_table.save(attacker_nation)
            continue

        # tag check
        is_blocked = False
        for tag_name, tag_data in attacker_nation.tags.items():
            if f"Cannot Declare War On #{defender_nation.id}" in tag_data:
                is_blocked = True
                break
        if is_blocked:
            attacker_nation.action_log.append(f"Failed to declare a {action.war_justification} war on {defender_nation.name} due to {tag_name}.")
            nation_table.save(attacker_nation)
            continue

        ### save ###
        notifications.append(f"{attacker_nation.name} has joined {war.name} as a {action.side}!", 3)
        nation_table.save(attacker_nation)
        combatant.claims = region_claims_list
        war.save_combatant(combatant)

def resolve_missile_launch_actions(game_id: str, actions_list: list[MissileLaunchAction]) -> None:
    
    # get game data
    nation_table = NationTable(game_id)
    war_table = WarTable(game_id)
    improvement_scenario_dict = core.get_scenario_dict(game_id, "Improvements")
    unit_scenario_dict = core.get_scenario_dict(game_id, "Units")

    # calculate missile launch capacity
    # note - this is calculated in advance of actions because missile launches are simultaneous
    missiles_launched_list = [0] * len(nation_table)
    launch_capacity_list = [0] * len(nation_table)
    for nation in nation_table:
        launch_capacity_list[int(nation.id) - 1] = nation.improvement_counts["Missile Silo"] * 3

    # execute actions
    for action in actions_list:
        nation = nation_table.get(action.id)
        target_region = Region(action.target_region, game_id)
        target_region_improvement = Improvement(action.target_region, game_id)
        target_region_unit = Unit(action.target_region, game_id)

        # check if player actually has a missile to launch
        has_missile = True
        if action.missile_type == "Standard Missile" and nation.missile_count == 0:
            has_missile = False
        elif action.missile_type == "Nuclear Missile" and nation.nuke_count == 0:
            has_missile = False
        if not has_missile:
            nation.action_log.append(f"Failed to launch {action.missile_type} at {action.target_region}. You do not have a {action.missile_type} in storage.")
            nation_table.save(nation)
            continue

        # check if target region is valid
        is_valid_target = True
        if nation.id != str(target_region.owner_id):
            engagement_type = 1
            if war_table.get_war_name(nation.id, str(target_region.owner_id)) is None:
                # cannot nuke a foreign region if it is owned by a nation you are not at war with
                is_valid_target = False
            if target_region.occupier_id != 0 and war_table.get_war_name(nation.id, str(target_region.occupier_id)) is None:
                # cannot nuke a hostile nation's region if it is occupied by a non-hostile nation
                is_valid_target = False
            if target_region_unit.name is not None and war_table.get_war_name(nation.id, str(target_region_unit.owner_id)) is None:
                # cannot nuke a hostile nation's region if a non-hostile unit is present
                is_valid_target = False
        elif nation.id == str(target_region.owner_id):
            engagement_type = 2
            if target_region.occupier_id == 0 or war_table.get_war_name(nation.id, str(target_region.occupier_id)) is None:
                # only allowed to strike your own region if it is occupied by a hostile nation
                is_valid_target = False
        if not is_valid_target:
            nation.action_log.append(f"Failed to launch {action.missile_type} at {action.target_region}. Invalid target!")
            nation_table.save(nation)
            continue

        # launch capacity check
        if action.missile_type == "Standard Missile":
            capacity_cost = 1
        elif action.missile_type == "Nuclear Missile":
            capacity_cost = 3
        if missiles_launched_list[int(nation.id) - 1] + capacity_cost > launch_capacity_list[int(nation.id) - 1]:
            nation.action_log.append(f"Failed to launch {action.missile_type} at {action.target_region}. Insufficient launch capacity!")
            nation_table.save(nation)
            continue

        # identify conflict
        if engagement_type == 1 and target_region.occupier_id == 0:
            # missile strike on hostile territory owned by the same hostile
            target_nation = nation_table.get(str(target_region.owner_id))
            war_name = war_table.get_war_name(nation.id, str(target_region.owner_id))
        else:
            # any other situation
            target_nation = nation_table.get(str(target_region.occupier_id))
            war_name = war_table.get_war_name(nation.id, str(target_region.occupier_id))

        # get combatants
        war = war_table.get(war_name)
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
            if defender_name in unit_scenario_dict:
                hit_value = unit_scenario_dict[defender_name][f"{action.missile_type} Defense"]
            else:
                hit_value = improvement_scenario_dict[defender_name][f"{action.missile_type} Defense"]
                if "Local Missile Defense" in nation.completed_research and defender_name not in ["Missile Defense System", "Missile Defense Network"]:
                    hit_value = improvement_scenario_dict[defender_name][f"Hit Value"]

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
            war_table.save(war)
            nation_table.save(nation)
            continue

        # conduct missile strike
        if action.missile_type == 'Standard Missile':
            
            attacking_combatant.launched_missiles += 1

            # improvement damage
            if target_region_improvement.name is not None and target_region_improvement.health != 99:

                # initial roll against improvement
                missile_did_something = True
                accuracy_roll = random.randint(1, 10)
                war.log.append(f"    Missile rolled a {accuracy_roll} for accuracy (needed 4+).")

                if accuracy_roll > 3:
                
                    # apply damage
                    target_region_improvement.health -= 1
                    if target_region_improvement.health > 0:
                        # improvement survived
                        war.log.append(f"    Missile struck {target_region_improvement.name} in {target_region.region_id} and dealt 1 damage.")
                        target_region_improvement._save_changes()
                    else:
                        # improvement destroyed
                        war.attacker_destroyed_improvements += war.warscore_destroy_improvement
                        if target_region_improvement.name != 'Capital':
                            attacking_combatant.destroyed_improvements += 1
                            defending_combatant.lost_improvements += 1
                            war.log.append(f"    Missile struck {target_region_improvement.name} in {target_region.region_id} and dealt 1 damage. Improvement destroyed!")
                            target_nation.improvement_counts[target_region_improvement.name] -= 1
                            target_region_improvement.clear()
                        else:
                            war.log.append(f"    Missile struck Capital in {target_region.region_id} and dealt 1 damage. Improvement devastated!")
                            target_region_improvement._save_changes()
                
                else:
                    war.log.append(f"    Missile missed {target_region_improvement.name}.")

            elif target_region_improvement.name is not None and target_region_improvement.health == 99:
                
                # initial roll against improvement
                missile_did_something = True
                accuracy_roll = random.randint(1, 10)
                war.log.append(f"    Missile rolled a {accuracy_roll} for accuracy (needed 8+).")

                if accuracy_roll > 7:

                    # improvement has no health so it is destroyed
                    war.attacker_destroyed_improvements += war.warscore_destroy_improvement
                    attacking_combatant.destroyed_improvements += 1
                    defending_combatant.lost_improvements += 1
                    war.log.append(f"    Missile destroyed {target_region_improvement.name} in {target_region.region_id}!")
                    target_nation.improvement_counts[target_region_improvement.name] -= 1
                    target_region_improvement.clear()
                
                else:
                    war.log.append(f"    Missile missed {target_region_improvement.name}.")

            # unit damage
            if target_region_unit.name != None:

                # initial roll against unit
                missile_did_something = True
                accuracy_roll = random.randint(1, 10)
                war.log.append(f"    Missile rolled a {accuracy_roll} for accuracy (needed 4+).")

                if accuracy_roll > 3:
                    
                    # apply damage
                    target_region_unit.health -= 1
                    if target_region_unit.health > 0:
                        # unit survived
                        war.log.append(f"    Missile struck {target_region_unit.name} in {target_region.region_id} and dealt 1 damage.")
                        target_region_unit._save_changes()
                    else:
                        # unit destroyed
                        war.attacker_destroyed_units += target_region_unit.value    # amount of warscore earned depends on unit value
                        attacking_combatant.destroyed_units += 1
                        defending_combatant.lost_units += 1
                        war.log.append(f"    Missile destroyed {target_region_unit.name} in {target_region.region_id}!")
                        target_nation.unit_counts[target_region_unit.name] -= 1
                        target_region_unit.clear()
                
                else:
                    war.log.append(f"    Missile missed {target_region_unit.name}.")

        elif action.missile_type == 'Nuclear Missile':
            
            attacking_combatant.launched_nukes += 1
            war.attacker_nuclear_strikes += war.warscore_nuclear_strike
            if target_region_improvement.name != 'Capital':
                target_region.set_fallout()

            # destroy improvement if present
            if target_region_improvement.name is not None:
                missile_did_something = True
                war.attacker_destroyed_improvements += war.warscore_destroy_improvement
                if target_region_improvement.name != 'Capital':
                    attacking_combatant.destroyed_improvements += 1
                    defending_combatant.lost_improvements += 1
                    war.log.append(f"    Missile destroyed {target_region_improvement.name} in {target_region.region_id}!")
                    target_nation.improvement_counts[target_region_improvement.name] -= 1
                    target_region_improvement.clear()
                else:
                    war.log.append(f"    Missile devastated Capital in {target_region.region_id}!")
                    target_region_improvement.health = 0
                    target_region_improvement._save_changes()

            # destroy unit if present
            if target_region_unit.name != None:
                missile_did_something = True
                war.attacker_destroyed_units += target_region_unit.value    # amount of warscore earned depends on unit value
                attacking_combatant.destroyed_units += 1
                defending_combatant.lost_units += 1
                war.log.append(f"    Missile destroyed {target_region_unit.name} in {target_region.region_id}!")
                target_nation.unit_counts[target_region_unit.name] -= 1
                target_region_unit.clear()

        # message for if missile hit nothing despite reaching its target
        if not missile_did_something:
            war.log.append(f"    Missile successfully struck {target_region.region_id} but did not damage anything of strategic value.")

        # save war and nation data
        war.save_combatant(attacking_combatant)
        war.save_combatant(defending_combatant)
        war_table.save(war)
        nation_table.save(nation)
        nation_table.save(target_nation)

def resolve_unit_move_actions(game_id: str, actions_list: list[UnitMoveAction]) -> None:
    
    # get game data
    nation_table = NationTable(game_id)
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
        nation = nation_table.get(nation_id)
        print(f"{i + 1}. {nation.name}")

    # execute actions
    for action in actions_list:
        while action.target_region_ids != []:
            
            target_region_id = action.target_region_ids.pop()
            nation = nation_table.get(action.id)

            # load current region objects
            current_region = Region(action.current_region_id, game_id)
            current_region_unit = Unit(action.current_region_id, game_id)

            # load target region objects
            target_region = Region(target_region_id, game_id)
            target_region_unit = Unit(target_region_id, game_id)

            # current region checks
            if current_region_unit.name == None or action.id != str(current_region_unit.owner_id):
                nation.action_log.append(f"Failed to perform a move action from {action.current_region_id}. You do not control a unit there.")
                nation_table.save(nation)
                continue
            if target_region_id not in current_region.adjacent_regions:
                nation.action_log.append(f"Failed to move {current_region_unit.name} {action.current_region_id} - {target_region_id}. Target region not adjacent to current region.")
                nation_table.save(nation)
                continue
            if target_region_id == action.current_region_id:
                continue

            # target region checks
            if target_region.owner_id == 0:
                nation.action_log.append(f"Failed to move {target_region_unit.name} {action.current_region_id} - {target_region_id}. You cannot move a unit to an unclaimed region.")
                nation_table.save(nation)
                continue

            # illegal move check
            if target_region_unit.name != None and not target_region_unit.is_hostile(current_region_unit.owner_id):
                nation.action_log.append(f"Failed to move {current_region_unit.name} {action.current_region_id} - {target_region_id}. A friendly unit is present in the target region.")
                nation_table.save(nation)
                continue
            if not target_region.is_valid_move(current_region_unit.owner_id):
                nation.action_log.append(f"Failed to move {current_region_unit.name} {action.current_region_id} - {target_region_id}. Region is controlled by a player that is not an enemy.")
                nation_table.save(nation)
                continue

            # execute movement order
            unit_name = current_region_unit.name
            movement_success = current_region_unit.move(target_region)
            nation_table.reload()
            nation = nation_table.get(action.id)
            if movement_success:
                nation.action_log.append(f"Successfully moved {unit_name} {action.current_region_id} - {target_region_id}.")
                action.current_region_id = target_region_id
            else:
                nation.action_log.append(f"Failed to complete move {unit_name} {action.current_region_id} - {target_region_id}. Check combat log for details.")
            nation_table.save(nation)
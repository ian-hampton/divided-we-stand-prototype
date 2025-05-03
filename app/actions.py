import csv
import json
import random

from app import core
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

        self.alliance_type = " ".join(words[2:4]) if len(words) > 4 else None
        self.alliance_name = " ".join(words[4:]) if len(words) > 4 else None
    
    def __str__(self):
        return f"[AllianceCreateAction] Alliance Join {self.alliance_type} {self.alliance_name} ({self.id})"
    
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

        self.starting_region = None
        self.target_regions = None
        if len(words) > 1:
            regions = words[1].split("-")
            self.starting_region = regions[0].upper()
            self.target_regions = []
            if len(regions) > 1:
                for region_id in regions[1:]:
                    self.target_regions.append(region_id.upper())

    def __str__(self):
        return f"[UnitMoveAction] Move {self.starting_region} {self.target_regions} ({self.id})"

    def is_valid(self) -> bool:
        
        if self.starting_region is None or self.target_regions is None:
            print(f"""Action "{self.action_str}" submitted by player {self.id} is invalid. Malformed action.""")
            return False
        
        self.starting_region = _check_region_id(self.game_id, self.starting_region)
        if self.starting_region is None:
            print(f"""Action "{self.action_str}" submitted by player {self.id} is invalid. Bad starting region id.""")
            return False
        
        for i, region_id in enumerate(self.target_regions):
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
        nation_table = NationTable(self.game_id)
        misc_scenario_dict = core.get_scenario_dict(game_id, "Misc")
        war_justification_list = list(misc_scenario_dict["warJustifications"].keys())

        self.target_nation = None
        for nation in nation_table:
            if nation.name.lower() in action_str.lower():
                self.target_nation = nation.name
                break

        self.war_justification = None
        for war_justification in war_justification_list:
            if war_justification.lower() in action_str.lower():
                self.war_justification = war_justification
                break

    def __str__(self):
        return f"[WarAction] War {self.target_nation} {self.war_justification} ({self.id})"

    def is_valid(self) -> bool:
        
        if self.target_nation is None or self.war_justification is None:
            print(f"""Action "{self.action_str}" submitted by player {self.id} is invalid. Malformed action.""")
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
        "barrier":"Crude Barrier",
        "iz": "Industrial Zone",
        "inz": "Industrial Zone",
        "idz": "Industrial Zone",
        "indz": "Industrial Zone",
        "base": "Military Base",
        "outpost": "Military Outpost",
        "mdn": "Missile Defense Network",
        "defense network": "Missile Defense Network",
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
        "Technology",
        "Coal",
        "Oil",
        "Basic Materials",
        "Common Metals",
        "Advanced Metals",
        "Uranium",
        "Rare Earth Elements"
    }

    resource_errors = {
        "tech": "Technology",
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

    if missile_type.title() in missile_types:
        return missile_type.title()
        
    return None

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
                nation1.update_stockpile("Dollars", abs(amount) * nation1_fee)
            
            elif amount < 0:
                # negative amount -> nation 1
                nation1.update_stockpile(resource_name, -1 * amount)
                nation2.update_stockpile(resource_name, amount)
                nation2.resources_given += abs(amount)
                # pay trade fee
                nation2.update_stockpile("Dollars", abs(amount) * nation2_fee)

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

def resolve_peace_actions(game_id: str, actions_list: list[SurrenderAction | WhitePeaceAction]) -> None:
    pass

def resolve_research_actions(game_id: str, actions_list: list[ResearchAction]) -> None:
    
    # get game data
    nation_table = NationTable(game_id)
    alliance_table = AllianceTable(game_id)
    agenda_data_dict = core.get_scenario_dict(game_id, "Agendas")
    research_data_dict = core.get_scenario_dict(game_id, "Technologies")
    with open('active_games.json', 'r') as json_file:
        active_games_dict = json.load(json_file)

    # execute actions
    for action in actions_list:
        
        nation = nation_table.get(action.id)

        # duplication check
        if action.research_name in nation.completed_research:
            nation.action_log.append(f"Failed to research {action.research_name}. You have already researched this.")
            nation_table.save(nation)
            continue

        # event check
        if "Humiliation" in active_games_dict[game_id]["Active Events"]:
            chosen_nation_name = active_games_dict[game_id]["Active Events"]["Humiliation"]["Chosen Nation Name"]
            if nation.name == chosen_nation_name and action.research_name in agenda_data_dict:
                nation.action_log.append(f"Failed to research {action.research_name} due to Humiliation event.")
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
            agenda_cost_adjustment = {
                "Diplomacy": {
                    "Diplomatic": -5,
                    "Commercial": 0,
                    "Isolationist": 5,
                    "Imperialist": 0
                },
                "Economy": {
                    "Diplomatic": 0,
                    "Commercial": -5,
                    "Isolationist": 0,
                    "Imperialist": 5
                },
                "Security": {
                    "Diplomatic": 0,
                    "Commercial": 5,
                    "Isolationist": -5,
                    "Imperialist": 0,
                },
                "Warfare": {
                    "Diplomatic": 5,
                    "Commercial": 0,
                    "Isolationist": 0,
                    "Imperialist": -5,
                }
            }
            cost += agenda_cost_adjustment[agenda_type][nation.fp]

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
            nation.update_stockpile("Technology", -1 * cost)
            if float(nation.get_stockpile("Technology")) < 0:
                nation_table.reload()
                nation = nation_table.get(action.id)
                nation.action_log.append(f"Failed to research {action.research_name}. Not enough technology.")
                nation_table.save(nation)
                continue

            # gain technology
            nation.action_log.append(f"Researched {action.research_name} for {cost} technology.")
            nation.add_tech(action.research_name)

            # totalitarian bonus
            totalitarian_discounts = {'Energy', 'Infrastructure'}
            if nation.gov == 'Totalitarian' and research_data_dict[action.research_name]["Research Type"] in totalitarian_discounts:
                nation.update_stockpile("Political Power", 2)
                nation.action_log.append(f'Gained 2 political power for researching {action.research_name}.')

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
            case 'Non-Aggression Pact':
                if 'Peace Accords' not in nation.completed_research:
                   research_check_success = False 
            case 'Defense Pact':
                if 'Defensive Agreements' not in nation.completed_research:
                   research_check_success = False 
            case 'Trade Agreement':
                if 'Trade Routes' not in nation.completed_research:
                   research_check_success = False 
            case 'Research Agreement':
                if 'Research Exchange' not in nation.completed_research:
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
        research_check_success = False
        match alliance.type:
            case 'Non-Aggression Pact':
                if 'Peace Accords' in nation.completed_research:
                    research_check_success = True
            case 'Defense Pact':
                if 'Defensive Agreements' in nation.completed_research:
                    research_check_success = True
            case 'Trade Agreement':
                if 'Trade Routes' in nation.completed_research:
                    research_check_success = True
            case 'Research Agreement':
                if 'Research Exchange' in nation.completed_research:
                    research_check_success = True
        if not research_check_success:
            nation.action_log.append(f"Failed to join {action.alliance_name} alliance. You do not have the required agenda.")
            nation_table.save(nation)
            continue

        # check alliance capacity
        if alliance.type != 'Non-Aggression Pact':
            alliance_count, alliance_capacity = core.get_alliance_count(game_id, nation)
            if (alliance_count + 1) > alliance_capacity:
                nation.action_log.append(f"Failed to join {action.alliance_name} alliance. You do not have enough alliance capacity.")
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
        if "Widespread Civil Disorder" in active_games_dict[game_id]["Active Events"]:
            nation.action_log.append(f"Failed to claim {action.target_region} due to the Widespread Civil Disorder event.")
            nation_table.save(nation)
            continue

        # adjacency check
        # to be added
        
        # attempt to pay for region
        nation.update_stockpile("Dollars", -1 * region.purchase_cost)
        pp_cost = 0
        if nation.gov == "Remnant":
            pp_cost = 0.20
        nation.update_stockpile("Political Power", -1 * pp_cost)
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

        # calculate build cost
        build_cost_dict = improvement_data_dict[action.improvement_name]["Build Costs"]
        if nation.gov == "Remnant":
            for key in build_cost_dict:
                build_cost_dict[key] *= 0.9

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
            nation.update_stockpile("Common Metals", -5 * action.quantity)
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

        # adjust income rates
        nation.reset_income_rates()
        nation.update_rate(action.resource_name, 20)
        nation.action_log.append(f"Used Republic government action to boost {action.resource_name} income.")
        nation_table.save(nation)
        notifications.append(f"{nation.name} used Republic government action to boost {action.resource_name} income.", 8)

def resolve_event_actions(game_id: str, actions_list: list[EventAction]) -> None:
    
    # note: event actions are currently not validated ahead of time
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

            # required event check
            if "Nominate Mediator" not in active_games_dict[game_id]["Active Events"]:
                nation.action_log.append(f"Failed to Host Peace Talks. Nominate Mediator event is not active.")
                nation_table.save(nation)
                continue

            # mediator check
            if active_games_dict[game_id]["Active Events"]["Nominate Mediator"]["Chosen Nation Name"] != nation.name:
                nation.action_log.append(f"Failed to Host Peace Talks. You are not the Mediator.")
                nation_table.save(nation)
                continue

            for truce in trucedata_list:
                
                truce_id = str(truce[0])
                mediator_in_truce = truce[int(action.id)]
                truce_expire_turn = int(truce[11])

                if truce_id in action.action_str[-2:]:
                    
                    # already extended check
                    if truce_id in active_games_dict[game_id]["Active Events"]["Nominate Mediator"]["Extended Truces List"]:
                        nation.action_log.append(f"Failed to Host Peace Talks for Truce #{truce[0]}. Truce has already been extended.")
                        break
                    
                    # player involved check
                    if mediator_in_truce:
                        nation.action_log.append(f"Failed to Host Peace Talks for Truce #{truce[0]}. Mediator is involved in this truce.")
                        break
                
                    # truce not yet expired check
                    if truce_expire_turn < current_turn_num:
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
                    truce[11] = truce_expire_turn + 4
                    active_games_dict[game_id]["Active Events"]["Nominate Mediator"]["Extended Truces List"].append(truce_id)
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
            nation.update_stockpile("Technology", -1 * count)
            if float(nation.get_stockpile("Technology")) < 0:
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

        # Event Search For Artifacts [Region ID]
        elif "Search For Artifacts" in action.action_str:
            
            # required event check
            if "Faustian Bargain" not in active_games_dict[game_id]["Active Events"]:
                nation.action_log.append(f"Failed to do Search For Artifacts action. Faustian Bargain event is not active.")
                nation_table.save(nation)
                continue
            
            # collaborator check
            if active_games_dict[game_id]["Active Events"]["Faustian Bargain"]["Chosen Nation Name"] != nation.name:
                nation.action_log.append(f"Failed to Search For Artifacts. You are not the collaborator.")
                nation_table.save(nation)
                continue

            # ownership check
            event_action_data = action.action_str.split(" ")
            region_id = event_action_data[-1]
            region = Region(region_id, game_id)
            if region.owner_id != int(action.id):
                nation.action_log.append(f"Failed to do Search For Artifacts action on {region_id}. You do not own that region.")
                nation_table.save(nation)
                continue

            # pay for action
            nation.update_stockpile("Dollars", -3)
            if float(nation.get_stockpile("Dollars")) < 0:
                nation_table.reload()
                nation = nation_table.get(action.id)
                nation.action_log.append(f"Failed to do Search For Artifacts action. Insufficient dollars.")
                nation_table.save(nation)
                continue

            # execute action
            if random.randint(1, 10) > 5:
                nation.update_stockpile("Political Power", 1)
                nation.action_log.append(f"Spent 3 dollars to Search For Artifacts on region {region_id}. Artifacts found! Gained 1 political power.")
            else:
                nation.action_log.append(f"Spent 3 dollars to Search For Artifacts on region {region_id}. No artifacts found!")

        # Event Lease Region [Region ID]
        elif "Lease Region" in action.action_str:
            
            # required event check
            if "Faustian Bargain" not in active_games_dict[game_id]["Active Events"]:
                nation.action_log.append(f"Failed to do Lease Region action. Faustian Bargain event is not active.")
                nation_table.save(nation)
                continue
            
            # collaborator check
            if active_games_dict[game_id]["Active Events"]["Faustian Bargain"]["Chosen Nation Name"] != nation.name:
                nation.action_log.append(f"Failed to Lease Region. You are not the collaborator.")
                nation_table.save(nation)
                continue

            # ownership check
            event_action_data = action.action_str.split(" ")
            region_id = event_action_data[-1]
            region = Region(region_id, game_id)
            if region.owner_id != int(action.id):
                nation.action_log.append(f"Failed to do Search For Artifacts action on {region_id}. You do not own that region.")
                nation_table.save(nation)
                continue

            # execute action
            active_games_dict[game_id]["Active Events"]["Faustian Bargain"]["Leased Regions List"].append(region_id)
            nation.action_log.append(f"Leased region {region_id} to the foreign nation.")

        # Event Outsource Technology [Research Name]
        elif "Outsource Technology" in action.action_str:
            
            # required event check
            if "Faustian Bargain" not in active_games_dict[game_id]["Active Events"]:
                nation.action_log.append(f"Failed to do Outsource Technology action. Faustian Bargain event is not active.")
                nation_table.save(nation)
                continue
            
            # collaborator check
            if active_games_dict[game_id]["Active Events"]["Faustian Bargain"]["Chosen Nation Name"] != nation.name:
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
            if nation.gov == "Totalitarian":
                nation.update_stockpile("Political Power", 2)
            nation.action_log.append(f"Used Outsource Technology to research {research_name}.")

        # Event Military Reinforcements [Unit Name] [Region ID #1],[Region ID #2]
        elif "Military Reinforcements" in action.action_str:
            
            # required event check
            if "Faustian Bargain" not in active_games_dict[game_id]["Active Events"]:
                nation.action_log.append(f"Failed to do Military Reinforcements action. Faustian Bargain event is not active.")
                nation_table.save(nation)
                continue
            
            # collaborator check
            if active_games_dict[game_id]["Active Events"]["Faustian Bargain"]["Chosen Nation Name"] != nation.name:
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
            unit_type = event_action_data[3:-1]
            unit_type = " ".join(unit_type)
            region_id_list = region_id_str.split(",")
            for region_id in region_id_list:
                
                region = Region(region_id, game_id)
                region_unit = Unit(region_id, game_id)
                
                if region.owner_id != int(action.id):
                    nation.action_log.append(f"Failed to use Military Reinforcements to deploy {unit_type} {region_id}. You do not own that region.")
                    nation_table.save(nation)
                    continue
                
                if region_unit.owner_id != int(action.id):
                    nation.action_log.append(f"Failed to use Military Reinforcements to deploy {unit_type} {region_id}. A hostile unit is present.")
                    nation_table.save(nation)
                    continue
                
                if region_unit.name != None:
                    nation.unit_counts[region_unit.name] -= 1
                region_unit.set_unit(unit_type, int(action.id))
                nation.unit_counts[unit_type] += 1
                nation.action_log.append(f"Used Military Reinforcements to deploy {unit_type} {region_id}.")

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
        "Technology": {
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
            "Base Price": 5,
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
        for affected_resource_name in active_games_dict[game_id]["Active Events"]["Market Inflation"]["Affected Resources"]:
            new_price = data[affected_resource_name]["Current Price"] * 2
            data[resource_name]["Current Price"] = round(new_price, 2)
    elif "Market Recession" in active_games_dict[game_id]["Active Events"]:
        for affected_resource_name in active_games_dict[game_id]["Active Events"]["Market Recession"]["Affected Resources"]:
            new_price = data[affected_resource_name]["Current Price"] * 0.5
            data[resource_name]["Current Price"] = round(new_price, 0.5)

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

        # add discounts
        if nation.gov == "Protectorate":
            rate -= 0.2
        if "Foreign Investment" in active_games_dict[game_id]["Active Events"]:
            chosen_nation_name = active_games_dict[game_id]["Active Events"]["Foreign Investment"]["Chosen Nation Name"]
            if nation.name == chosen_nation_name:
                discounted_rate -= 0.2
        
        # event check
        if "Embargo" in active_games_dict[game_id]["Active Events"]:
            chosen_nation_name = active_games_dict[game_id]["Active Events"]["Embargo"]["Chosen Nation Name"]
            if nation.name == chosen_nation_name:
                nation.action_log.append(f"Failed to buy {action.quantity} {action.resource_name}. Your nation is currently under an embargo.")
                nation_table.save(nation)
                continue

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

        # event check
        if "Embargo" in active_games_dict[game_id]["Active Events"]:
            chosen_nation_name = active_games_dict[game_id]["Active Events"]["Embargo"]["Chosen Nation Name"]
            if nation.name == chosen_nation_name:
                nation.action_log.append(f"Failed to sell {action.quantity} {action.resource_name}. Your nation is currently under an embargo.")
                nation_table.save(nation)
                continue

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
                if "Early Expansion" in attacker_nation.completed_research:
                    valid_war_justification = True
            case "Annexation":
                if "New Empire" in attacker_nation.completed_research:
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

def resolve_missile_launch_actions(game_id: str, actions_list: list[MissileLaunchAction]) -> None:
    pass

def resolve_unit_move_actions(game_id: str, actions_list: list[UnitMoveAction]) -> None:
    pass
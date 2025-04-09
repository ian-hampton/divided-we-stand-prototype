import json

from app import core
from app.nationdata import NationTable
from app.alliance import AllianceTable

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
        
        self.alliance_name = _check_alliance_name(self.game_id, self.alliance_name)
        if self.alliance_name is None:
            print(f"""Action "{self.action_str}" submitted by player {self.id} is invalid. Bad alliance name.""")
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
    pass

def resolve_peace_actions(game_id: str, actions_list: list[SurrenderAction | WhitePeaceAction]) -> None:
    pass

def resolve_research_actions(game_id: str, actions_list: list[ResearchAction]) -> None:
    pass

def resolve_alliance_leave_actions(game_id: str, actions_list: list[AllianceLeaveAction]) -> None:
    pass

def resolve_alliance_create_actions(game_id: str, actions_list: list[AllianceCreateAction]) -> None:
    pass

def resolve_alliance_join_actions(game_id: str, actions_list: list[AllianceJoinAction]) -> None:
    pass

def resolve_claim_actions(game_id: str, actions_list: list[ClaimAction]) -> None:
    pass

def resolve_improvement_remove_actions(game_id: str, actions_list: list[ImprovementRemoveAction]) -> None:
    pass

def resolve_improvement_build_actions(game_id: str, actions_list: list[ImprovementBuildAction]) -> None:
    pass

def resolve_missile_make_actions(game_id: str, actions_list: list[MissileMakeAction]) -> None:
    pass

def resolve_government_actions(game_id: str, actions_list: list[RepublicAction]) -> None:
    pass

def resolve_event_actions(game_id: str, actions_list: list[EventAction]) -> None:
    pass

def resolve_market_actions(game_id: str, actions_list: list[CrimeSyndicateAction | MarketBuyAction | MarketSellAction]) -> None:
    pass

def resolve_unit_disband_actions(game_id: str, actions_list: list[UnitDisbandAction]) -> None:
    pass

def resolve_unit_deployment_actions(game_id: str, actions_list: list[UnitDeployAction]) -> None:
    pass

def resolve_war_actions(game_id: str, actions_list: list[WarAction]) -> None:
    pass

def resolve_missile_launch_actions(game_id: str, actions_list: list[MissileLaunchAction]) -> None:
    pass

def resolve_unit_move_actions(game_id: str, actions_list: list[UnitMoveAction]) -> None:
    pass
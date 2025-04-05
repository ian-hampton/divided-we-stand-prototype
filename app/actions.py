import core
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

    def is_valid(self) -> bool:
        
        if self.alliance_type or self.alliance_name:
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

    def is_valid(self) -> bool:
        pass

class AllianceLeaveAction:

    def __init__(self, game_id: str, nation_id: str, action_str: str):

        self.id = nation_id
        self.game_id = game_id
        self.action_str = action_str
        words = action_str.strip().split()

        self.alliance_name = " ".join(words[2:]) if len(words) > 2 else None

    def is_valid(self) -> bool:
        pass

class ClaimAction:

    def __init__(self, game_id: str, nation_id: str, action_str: str):

        self.id = nation_id
        self.game_id = game_id
        self.action_str = action_str
        words = action_str.strip().split()

        self.target_region = words[1].upper() if len(words) == 2 else None

    def is_valid(self) -> bool:
        pass

class CrimeSyndicateAction:

    def __init__(self, game_id: str, nation_id: str, action_str: str):

        self.id = nation_id
        self.game_id = game_id
        self.action_str = action_str
        words = action_str.strip().split()

        self.target_nation = " ".join(words[1:]) if len(words) > 1 else None

    def is_valid(self) -> bool:
        pass

class ImprovementBuildAction:

    def __init__(self, game_id: str, nation_id: str, action_str: str):

        self.id = nation_id
        self.game_id = game_id
        self.action_str = action_str
        words = action_str.strip().split()

        self.improvement_name: str = " ".join(words[1:-1]) if len(words) > 2 else None
        self.target_region: str = words[-1].upper() if len(words) > 2 else None

    def is_valid(self) -> bool:
        pass

class ImprovementRemoveAction:

    def __init__(self, game_id: str, nation_id: str, action_str: str):

        self.id = nation_id
        self.game_id = game_id
        self.action_str = action_str
        words = action_str.strip().split()

        self.target_region = words[1].upper() if len(words) == 2 else None

    def is_valid(self) -> bool:
        pass

class MarketBuyAction:

    def __init__(self, game_id: str, nation_id: str, action_str: str):

        self.id = nation_id
        self.game_id = game_id
        self.action_str = action_str
        words = action_str.strip().split()

        self.quantity = int(words[1]) if len(words) > 2 else None
        self.resource_name = words[2:] if len(words) > 2 else None

    def is_valid(self) -> bool:
        pass

class MarketSellAction:

    def __init__(self, game_id: str, nation_id: str, action_str: str):

        self.id = nation_id
        self.game_id = game_id
        self.action_str = action_str
        words = action_str.strip().split()

        self.quantity = int(words[1]) if len(words) > 2 else None
        self.resource_name = words[2:] if len(words) > 2 else None

    def is_valid(self) -> bool:
        pass

class MissileMakeAction:

    def __init__(self, game_id: str, nation_id: str, action_str: str):

        self.id = nation_id
        self.game_id = game_id
        self.action_str = action_str
        words = action_str.strip().split()

        self.quantity = int(words[1]) if len(words) > 2 else None
        self.missile_type = words[2:] if len(words) > 2 else None

    def is_valid(self) -> bool:
        pass

class MissileLaunchAction:

    def __init__(self, game_id: str, nation_id: str, action_str: str):

        self.id = nation_id
        self.game_id = game_id
        self.action_str = action_str
        words = action_str.strip().split()

        self.missile_type = words[1:-1] if len(words) > 2 else None
        self.target_region = words[-1].upper() if len(words) > 2 else None

    def is_valid(self) -> bool:
        pass

class RepublicAction:

    def __init__(self, game_id: str, nation_id: str, action_str: str):

        self.id = nation_id
        self.game_id = game_id
        self.action_str = action_str
        words = action_str.strip().split()

        self.resource_name = words[1:] if len(words) > 1 else None

    def is_valid(self) -> bool:
        pass

class ResearchAction:

    def __init__(self, game_id: str, nation_id: str, action_str: str):

        self.id = nation_id
        self.game_id = game_id
        self.action_str = action_str
        words = action_str.strip().split()

        self.research_name = words[1:] if len(words) > 1 else None

    def is_valid(self) -> bool:
        pass

class SurrenderAction:

    def __init__(self, game_id: str, nation_id: str, action_str: str):

        self.id = nation_id
        self.game_id = game_id
        self.action_str = action_str
        words = action_str.strip().split()

        self.target_nation = words[1:] if len(words) > 1 else None

    def is_valid(self) -> bool:
        pass

class UnitDeployAction:

    def __init__(self, game_id: str, nation_id: str, action_str: str):

        self.id = nation_id
        self.game_id = game_id
        self.action_str = action_str
        words = action_str.strip().split()

        self.unit_name = words[1:-1] if len(words) > 2 else None
        self.target_region = words[-1].upper() if len(words) > 2 else None

    def is_valid(self) -> bool:
        pass

class UnitDisbandAction:

    def __init__(self, game_id: str, nation_id: str, action_str: str):

        self.id = nation_id
        self.game_id = game_id
        self.action_str = action_str
        words = action_str.strip().split()

        self.target_region = words[-1].upper() if len(words) > 1 else None

    def is_valid(self) -> bool:
        pass

class UnitMoveAction:

    def __init__(self, game_id: str, nation_id: str, action_str: str):

        self.id = nation_id
        self.game_id = game_id
        self.action_str = action_str
        words = action_str.strip().split()

        self.starting_region = None
        self.target_regions = []
        if len(words) > 1:
            regions = words[1].split("-")
            self.starting_region = regions[0].upper()
            self.target_regions = []
            if len(regions) > 1:
                for region_id in regions[1:]:
                    self.target_regions.append(region_id.upper())

    def is_valid(self) -> bool:
        pass

class WarAction:

    def __init__(self, game_id: str, nation_id: str, action_str: str):

        self.id = nation_id
        self.game_id = game_id
        self.action_str = action_str
        nation_table = NationTable(self.game_id)
        misc_scenario_dict = core.get_scenario_dict(game_id, "Misc")
        war_justification_list = list(misc_scenario_dict["warJustifications"].keys())

        self.nation_name = None
        for nation in nation_table:
            if nation.name.lower() in action_str.lower():
                self.nation_name = nation.name
                break

        self.war_justification = None
        for war_justification in war_justification_list:
            if war_justification.lower() in action_str.lower():
                self.war_justification = war_justification
                break

    def is_valid(self) -> bool:
        pass

class WhitePeaceAction:

    def __init__(self, game_id: str, nation_id: str, action_str: str):

        self.id = nation_id
        self.game_id = game_id
        self.action_str = action_str
        words = action_str.strip().split()
        self.target_nation = words[2:] if len(words) > 2 else None
    
    def is_valid(self) -> bool:
        pass

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
        "War": Warning,
        "White Peace": WhitePeaceAction
    }

    while True:
        
        words = action_str.strip().split()
        action_key = words[0].title()
        if action_key == "Alliance" and len(words) >= 2:
            action_key = f"{words[0].title()} {words[1].title()}"
        
        if action_key in action_key:
            return actions[action_key](nation_id, game_id, action_str)
        else:
            print(f"""Action "{action_str}" submitted by player {nation_id} is invalid. Unrecognized action type.""")
            action_str = input("Re-enter action or hit enter to skip: ")
            if action_str == "":
                return

def _check_alliance_type(game_id: str, alliance_name: str):
    
    misc_scenario_dict = core.get_scenario_dict(game_id, "Misc")
    alliance_types = list(misc_scenario_dict["allianceTypes"].keys())

    for alliance_type in alliance_types:
        if alliance_type.lower() == alliance_name.lower():
            return alliance_type
        
    return None

def _check_alliance_name (game_id: str, alliance_name: str):
    
    alliance_table = AllianceTable(game_id)

    for alliance in alliance_table:
        if alliance.name.lower() == alliance_name.lower():
            return alliance.name
        
    return None
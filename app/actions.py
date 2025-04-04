class AllianceCreateAction:

    def __init__(self, nation_id: str, action_str: str):

        self.id: str = nation_id
        self.alliance_type: str = None
        self.alliance_name: str = None

    def is_valid(self) -> bool:
        pass

class AllianceJoinAction:

    def __init__(self, nation_id: str, action_str: str):

        self.id: str = nation_id
        self.alliance_name: str = None

    def is_valid(self) -> bool:
        pass

class AllianceLeaveAction:

    def __init__(self, nation_id: str, action_str: str):

        self.id: str = nation_id
        self.alliance_name: str = None

    def is_valid(self) -> bool:
        pass

class ClaimAction:

    def __init__(self, nation_id: str, action_str: str):

        self.id: str = nation_id
        self.target_region: str = None

    def is_valid(self) -> bool:
        pass

class CrimeSyndicateAction:

    def __init__(self, nation_id: str, action_str: str):

        self.id: str = nation_id
        self.target_nation: str = None

    def is_valid(self) -> bool:
        pass

class ImprovementBuildAction:

    def __init__(self, nation_id: str, action_str: str):

        self.id: str = nation_id
        self.improvement_name: str = None
        self.target_region: str = None

    def is_valid(self) -> bool:
        pass

class ImprovementRemoveAction:

    def __init__(self, nation_id: str, action_str: str):

        self.id: str = nation_id
        self.target_region: str = None

    def is_valid(self) -> bool:
        pass

class MarketBuyAction:

    def __init__(self, nation_id: str, action_str: str):

        self.id: str = nation_id
        self.quantity: int = None
        self.resource_name: str = None

    def is_valid(self) -> bool:
        pass

class MarketSellAction:

    def __init__(self, nation_id: str, action_str: str):

        self.id: str = nation_id
        self.quantity: int = None
        self.resource_name: str = None

    def is_valid(self) -> bool:
        pass

class MissileMakeAction:

    def __init__(self, nation_id: str, action_str: str):

        self.id: str = nation_id
        self.quantity: int = None
        self.missile_type: str = None

    def is_valid(self) -> bool:
        pass

class MissileLaunchAction:

    def __init__(self, nation_id: str, action_str: str):

        self.id: str = nation_id
        self.missile_type: str = None
        self.target_region: str = None

    def is_valid(self) -> bool:
        pass

class RepublicAction:

    def __init__(self, nation_id: str, action_str: str):

        self.id: str = nation_id
        self.resource_name: str = None

    def is_valid(self) -> bool:
        pass

class ResearchAction:

    def __init__(self, nation_id: str, action_str: str):

        self.id: str = nation_id
        self.research_name: str = None

    def is_valid(self) -> bool:
        pass

class SurrenderAction:

    def __init__(self, nation_id: str, action_str: str):

        self.id: str = nation_id
        self.target_nation: str = None

    def is_valid(self) -> bool:
        pass

class UnitDeployAction:

    def __init__(self, nation_id: str, action_str: str):

        self.id: str = nation_id
        self.unit_name: str = None
        self.target_region: str = None

    def is_valid(self) -> bool:
        pass

class UnitDisbandAction:

    def __init__(self, nation_id: str, action_str: str):

        self.id: str = nation_id
        self.target_region: str = None

    def is_valid(self) -> bool:
        pass

class UnitMoveAction:

    def __init__(self, nation_id: str, action_str: str):

        self.id: str = nation_id
        self.starting_region: str = None
        self.target_regions: list[str] = []

    def is_valid(self) -> bool:
        pass

class WarAction:

    def __init__(self, nation_id: str, action_str: str):

        self.id: str = nation_id
        self.nation_name: str = None
        self.war_justification: str = None

    def is_valid(self) -> bool:
        pass

class WhitePeaceAction:

    def __init__(self, nation_id: str, action_str: str):

        self.id: str = nation_id
        self.target_nation: str = None
    
    def is_valid(self) -> bool:
        pass

def validate_action(nation_id: str, action_str: str) -> any:
    """
    Creates action object and validates it.

    Params:
        nation_id (int): ID of nation/player.
        action_str (str): Raw action string.
    
    Returns:
        An action class or None if action canceled.
    """

    while True:
        
        action = _create_action(nation_id, action_str)
        if action is None:
            return
        
        if action.is_valid():
            return action
        else:
            action_str = input("Re-enter action or hit enter to skip: ")
            if action_str == "":
                return

def _create_action(nation_id: str, action_str: str) -> any:
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
        
        words = action_str.split()
        action_key = words[0].title()
        if action_key == "Alliance" and len(words) >= 2:
            action_key = f"{words[0].title()} {words[1].title()}"
        
        if action_key in action_key:
            return actions[action_key](nation_id, action_str)
        else:
            print(f"""Action "{action_str}" submitted by player {nation_id} is invalid. Unrecognized action type.""")
            action_str = input("Re-enter action or hit enter to skip: ")
            if action_str == "":
                return
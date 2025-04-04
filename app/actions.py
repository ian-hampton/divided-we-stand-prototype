class AllianceCreateAction:

    def __init__(self, nation_id: str, action: str):

        self.id: str = nation_id
        self.alliance_type: str = None
        self.alliance_name: str = None

    def is_valid(self) -> bool:
        pass

class AllianceJoinAction:

    def __init__(self, nation_id: str, action: str):

        self.id: str = nation_id
        self.alliance_name: str = None

    def is_valid(self) -> bool:
        pass

class AllianceLeaveAction:

    def __init__(self, nation_id: str, action: str):

        self.id: str = nation_id
        self.alliance_name: str = None

    def is_valid(self) -> bool:
        pass

class ClaimAction:

    def __init__(self, nation_id: str, action: str):

        self.id: str = nation_id
        self.target_region: str = None

    def is_valid(self) -> bool:
        pass

class CrimeSyndicateAction:

    def __init__(self, nation_id: str, action: str):

        self.id: str = nation_id
        self.target_nation: str = None

    def is_valid(self) -> bool:
        pass

class ImprovementBuildAction:

    def __init__(self, nation_id: str, action: str):

        self.id: str = nation_id
        self.improvement_name: str = None
        self.target_region: str = None

    def is_valid(self) -> bool:
        pass

class ImprovementRemoveAction:

    def __init__(self, nation_id: str, action: str):

        self.id: str = nation_id
        self.target_region: str = None

    def is_valid(self) -> bool:
        pass

class MarketBuyAction:

    def __init__(self, nation_id: str, action: str):

        self.id: str = nation_id
        self.quantity: int = None
        self.resource_name: str = None

    def is_valid(self) -> bool:
        pass

class MarketSellAction:

    def __init__(self, nation_id: str, action: str):

        self.id: str = nation_id
        self.quantity: int = None
        self.resource_name: str = None

    def is_valid(self) -> bool:
        pass

class MissileMakeAction:

    def __init__(self, nation_id: str, action: str):

        self.id: str = nation_id
        self.quantity: int = None
        self.missile_type: str = None

    def is_valid(self) -> bool:
        pass

class MissileLaunchAction:

    def __init__(self, nation_id: str, action: str):

        self.id: str = nation_id
        self.missile_type: str = None
        self.target_region: str = None

    def is_valid(self) -> bool:
        pass

class RepublicAction:

    def __init__(self, nation_id: str, action: str):

        self.id: str = nation_id
        self.resource_name: str = None

    def is_valid(self) -> bool:
        pass

class ResearchAction:

    def __init__(self, nation_id: str, action: str):

        self.id: str = nation_id
        self.research_name: str = None

    def is_valid(self) -> bool:
        pass

class SurrenderAction:

    def __init__(self, nation_id: str, action: str):

        self.id: str = nation_id
        self.target_nation: str = None

    def is_valid(self) -> bool:
        pass

class UnitDeployAction:

    def __init__(self, nation_id: str, action: str):

        self.id: str = nation_id
        self.unit_name: str = None
        self.target_region: str = None

    def is_valid(self) -> bool:
        pass

class UnitDisbandAction:

    def __init__(self, nation_id: str, action: str):

        self.id: str = nation_id
        self.target_region: str = None

    def is_valid(self) -> bool:
        pass

class UnitMoveAction:

    def __init__(self, nation_id: str, action: str):

        self.id: str = nation_id
        self.starting_region: str = None
        self.target_regions: list[str] = []

    def is_valid(self) -> bool:
        pass

class WarAction:

    def __init__(self, nation_id: str, action: str):

        self.id: str = nation_id
        self.nation_name: str = None
        self.war_justification: str = None

    def is_valid(self) -> bool:
        pass

class WhitePeaceAction:

    def __init__(self, nation_id: str, action: str):

        self.id: str = nation_id
        self.target_nation: str = None
    
    def is_valid(self) -> bool:
        pass
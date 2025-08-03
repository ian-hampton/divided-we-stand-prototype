class HostPeaceTalksAction:

    def __init__(self, game_id: str, nation_id: str, action_str: str):
        
        self.id = nation_id
        self.game_id = game_id
        self.action_str = action_str
        words = action_str.strip().split()

        self.truce_id = words[3].upper() if len(words) == 4 else None

    def is_valid(self) -> bool:

        if self.truce_id is None:
            print(f"""Action "{self.action_str}" submitted by player {self.id} is invalid. Malformed action.""")
            return False

        return True
    
class CureResearchAction:

    def __init__(self, game_id: str, nation_id: str, action_str: str):
        
        self.id = nation_id
        self.game_id = game_id
        self.action_str = action_str
        words = action_str.strip().split()

        self.amount = int(words[2]) if len(words) == 3 else None

    def is_valid(self) -> bool:

        if self.amount is None:
            print(f"""Action "{self.action_str}" submitted by player {self.id} is invalid. Malformed action.""")
            return False

        return True
    
class CureFundraiseAction:

    def __init__(self, game_id: str, nation_id: str, action_str: str):
        
        self.id = nation_id
        self.game_id = game_id
        self.action_str = action_str
        words = action_str.strip().split()

        self.amount = int(words[2]) if len(words) == 3 else None

    def is_valid(self) -> bool:

        if self.amount is None:
            print(f"""Action "{self.action_str}" submitted by player {self.id} is invalid. Malformed action.""")
            return False

        return True
    
class InspectRegionAction:

    def __init__(self, game_id: str, nation_id: str, action_str: str):
        
        self.id = nation_id
        self.game_id = game_id
        self.action_str = action_str
        words = action_str.strip().split()

        self.target_region = words[1].upper() if len(words) == 2 else None

    def is_valid(self) -> bool:

        from app import actions

        if self.target_region is None:
            print(f"""Action "{self.action_str}" submitted by player {self.id} is invalid. Malformed action.""")
            return False
        
        self.target_region = actions._check_region_id(self.game_id, self.target_region)
        if self.target_region is None:
            print(f"""Action "{self.action_str}" submitted by player {self.id} is invalid. Bad target region id.""")
            return False

        return True
    
class QuarantineCreateAction:

    def __init__(self, game_id: str, nation_id: str, action_str: str):
        
        self.id = nation_id
        self.game_id = game_id
        self.action_str = action_str
        words = action_str.strip().split()

        self.target_region = words[2].upper() if len(words) == 3 else None

    def is_valid(self) -> bool:

        from app import actions

        if self.target_region is None:
            print(f"""Action "{self.action_str}" submitted by player {self.id} is invalid. Malformed action.""")
            return False
        
        self.target_region = actions._check_region_id(self.game_id, self.target_region)
        if self.target_region is None:
            print(f"""Action "{self.action_str}" submitted by player {self.id} is invalid. Bad target region id.""")
            return False

        return True
    
class QuarantineEndAction:

    def __init__(self, game_id: str, nation_id: str, action_str: str):
        
        self.id = nation_id
        self.game_id = game_id
        self.action_str = action_str
        words = action_str.strip().split()

        self.target_region = words[2].upper() if len(words) == 3 else None

    def is_valid(self) -> bool:

        from app import actions

        if self.target_region is None:
            print(f"""Action "{self.action_str}" submitted by player {self.id} is invalid. Malformed action.""")
            return False
        
        self.target_region = actions._check_region_id(self.game_id, self.target_region)
        if self.target_region is None:
            print(f"""Action "{self.action_str}" submitted by player {self.id} is invalid. Bad target region id.""")
            return False

        return True
    
class BordersOpenAction:

    def __init__(self, game_id: str, nation_id: str, action_str: str):
        
        self.id = nation_id
        self.game_id = game_id
        self.action_str = action_str

    def is_valid(self) -> bool:

        if self.action_str.title().strip() != "Open Borders":
            return False

        return True
    
class BordersCloseAction:

    def __init__(self, game_id: str, nation_id: str, action_str: str):
        
        self.id = nation_id
        self.game_id = game_id
        self.action_str = action_str

    def is_valid(self) -> bool:

        if self.action_str.title().strip() != "Close Borders":
            return False

        return True

    def is_valid(self) -> bool:
        return True
    
class OutsourceTechnologyAction:

    def __init__(self, game_id: str, nation_id: str, action_str: str):
        
        self.id = nation_id
        self.game_id = game_id
        self.action_str = action_str
        words = action_str.strip().split()

        self.research_name = " ".join(words[2:]) if len(words) > 2 else None

    def is_valid(self) -> bool:

        from app import actions

        if self.research_name is None:
            print(f"""Action "{self.action_str}" submitted by player {self.id} is invalid. Malformed action.""")
            return False
        
        self.research_name = actions._check_research(self.game_id, self.research_name)
        if self.research_name is None:
            print(f"""Action "{self.action_str}" submitted by player {self.id} is invalid. Bad research name.""")
            return False
        
        return True
    
class MilitaryReinforcementsAction:

    def __init__(self, game_id: str, nation_id: str, action_str: str):
        
        self.id = nation_id
        self.game_id = game_id
        self.action_str = action_str
        words = action_str.strip().split()

        self.target_region_ids = [region_id.upper() for region_id in words[2:]] if len(words) > 2 else None

    def is_valid(self) -> bool:

        from app import actions

        if self.target_region_ids is None:
            print(f"""Action "{self.action_str}" submitted by player {self.id} is invalid. Malformed action.""")
            return False
        
        for region_id in self.target_region_ids:
            region_id = actions._check_region_id(self.game_id, region_id)
            if region_id is None:
                print(f"""Action "{self.action_str}" submitted by player {self.id} is invalid. Bad destination region id: {region_id}.""")
                return False

        return True
    
def _create_action(game_id: str, nation_id: str, action_str: str) -> any:
    """
    Factory method for scenario actions.

    Params:
        nation_id (int): ID of nation/player.
        action_str (str): Raw action string.
    
    Returns:
        An action class or None if no match found.
    """

    words = action_str.strip().split()
    action_key = words[0].title()

    if action_key == "Host" and len(words) >= 3:
        action_key = "Host Peace Talks"
    elif action_key == "Cure" and len(words) >= 2:
        action_key = f"{words[0].title()} {words[1].title()}"
    elif action_key == "Quarantine" and len(words) >= 2:
        action_key = f"{words[0].title()} {words[1].title()}"
    elif action_key == "Open" and len(words) >= 2:
        action_key = "Open Borders"
    elif action_key == "Close" and len(words) >= 2:
        action_key = "Close Borders"
    elif action_key == "Outsource" and len(words) >= 2:
        action_key = "Outsource Technology"
    elif action_key == "Military" and len(words) >= 2:
        action_key = "Military Reinforcements"

    actions = {
        "Host Peace Talks": HostPeaceTalksAction,
        "Cure Research": CureResearchAction,
        "Cure Fundraise": CureFundraiseAction,
        "Inspect": InspectRegionAction,
        "Quarantine Create": QuarantineCreateAction,
        "Quarantine End": QuarantineEndAction,
        "Open Borders": BordersOpenAction,
        "Close Borders": BordersCloseAction,
        "Outsource Technology": OutsourceTechnologyAction,
        "Military Reinforcements": MilitaryReinforcementsAction
    }

    if action_key in actions:
        return actions[action_key](game_id, nation_id, action_str)
    
    return None
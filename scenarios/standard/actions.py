import csv
import json
import importlib

from app import core
from app.region import Region
from app.nation import Nations
from app.notifications import Notifications
from app.war import Wars

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

    actions = {
        "host peace talks": HostPeaceTalksAction,
        "cure research": CureResearchAction,
        "cure fundraise": CureFundraiseAction,
        "inspect": InspectRegionAction,
        "quarantine create": QuarantineCreateAction,
        "quarantine end": QuarantineEndAction,
        "open borders": BordersOpenAction,
        "close borders": BordersCloseAction,
        "outsource technology": OutsourceTechnologyAction,
        "military reinforcements": MilitaryReinforcementsAction
    }

    action_str = action_str.strip().lower()

    for action_key in sorted(actions.keys(), key=len, reverse=True):
        if action_str.startswith(action_key):
            return actions[action_key](game_id, nation_id, action_str)
    
    return None

def resolve_event_actions(game_id: str, actions_dict: dict) -> None:
    
    resolve_peace_talk_actions(game_id, actions_dict.get("HostPeaceTalksAction", []))
    resolve_cure_research_actions(game_id, actions_dict.get("CureResearchAction", []))
    resolve_cure_fundraise_actions(game_id, actions_dict.get("CureFundraiseAction", []))
    resolve_inspect_region_actions(game_id, actions_dict.get("InspectRegionAction", []))
    resolve_quarantine_create_actions(game_id, actions_dict.get("QuarantineCreateAction", []))
    resolve_quarantine_end_actions(game_id, actions_dict.get("QuarantineEndAction", []))
    resolve_open_borders_actions(game_id, actions_dict.get("BordersOpenAction", []))
    resolve_close_borders_actions(game_id, actions_dict.get("BordersCloseAction", []))
    resolve_outsource_technology_actions(game_id, actions_dict.get("OutsourceTechnologyAction", []))
    resolve_military_reinforcements_actions(game_id, actions_dict.get("MilitaryReinforcementsAction", []))

def resolve_peace_talk_actions(game_id: str, actions_list: list[HostPeaceTalksAction]) -> None:

    from app.truce import Truces
    current_turn_num = core.get_current_turn_num(game_id)

    for action in actions_list:

        nation = Nations.get(action.id)

        if "Mediator" not in nation.tags:
            nation.action_log.append(f"{action.action_str} failed. You are not the Mediator.")
            continue

        for truce in Truces:

            if truce.id == action.truce_id:
                
                if truce.id in nation.tags["Mediator"]["Truces Extended"]:
                    nation.action_log.append(f"Failed to Host Peace Talks for Truce #{action.truce_id}. Truce has already been extended.")
                    break
                
                if action.id in truce.signatories:
                    nation.action_log.append(f"Failed to Host Peace Talks for Truce #{action.truce_id}. Mediator is involved in this truce.")
                    break
            
                if truce.end_turn <= current_turn_num:
                    nation.action_log.append(f"Failed to Host Peace Talks for Truce #{action.truce_id}. Truce has already expired.")
                    break

                if float(nation.get_stockpile("Political Power")) - 5 < 0:
                    nation.action_log.append(f"Failed to Host Peace Talks for Truce #{action.truce_id}. Insufficient political power.")
                    break

                nation.update_stockpile("Political Power", -5)
                truce.end_turn += 4
                nation.tags["Mediator"]["Truces Extended"].append(truce.id)
                nation.action_log.append(f"Used Host Peace Talks on Truce #{action.truce_id}.")
                break

def resolve_cure_research_actions(game_id: str, actions_list: list[CureResearchAction]) -> None:

    with open("active_games.json", 'r') as json_file:
        active_games_dict = json.load(json_file)
    scenario = active_games_dict[game_id]["Information"]["Scenario"].lower()
    events = importlib.import_module(f"scenarios.{scenario}.events")

    if "Pandemic" not in active_games_dict[game_id]["Active Events"]:
        return

    event_data = active_games_dict[game_id]["Active Events"]["Pandemic"]
    event = events.load_event(game_id, "Pandemic", event_data, temp=True)

    for action in actions_list:

        nation = Nations.get(action.id)

        if "Pandemic" not in active_games_dict[game_id]["Active Events"]:
            nation.action_log.append(f"{action.action_str} failed. Corresponding event is not active.")
            continue

        if float(nation.get_stockpile("Research")) - action.amount < 0:
            nation.action_log.append(f"Failed to spend {action.amount} technology on Cure Research. Insufficient technology.")
            continue

        nation.update_stockpile("Research", -1 * action.amount)
        event.cure_current += action.amount
        nation.action_log.append(f"Used Cure Research to spend {action.amount} technology in exchange for {action.amount} cure progress.")
    
    active_games_dict[game_id]["Active Events"]["Pandemic"] = event.export()
    with open("active_games.json", 'w') as json_file:
        json.dump(active_games_dict, json_file, indent=4)

def resolve_cure_fundraise_actions(game_id: str, actions_list: list[CureFundraiseAction]) -> None:

    with open("active_games.json", 'r') as json_file:
        active_games_dict = json.load(json_file)
    scenario = active_games_dict[game_id]["Information"]["Scenario"].lower()
    events = importlib.import_module(f"scenarios.{scenario}.events")

    if "Pandemic" not in active_games_dict[game_id]["Active Events"]:
        return

    event_data = active_games_dict[game_id]["Active Events"]["Pandemic"]
    event = events.load_event(game_id, "Pandemic", event_data, temp=True)

    for action in actions_list:

        nation = Nations.get(action.id)

        if "Pandemic" not in active_games_dict[game_id]["Active Events"]:
            nation.action_log.append(f"{action.action_str} failed. Corresponding event is not active.")
            continue

        if float(nation.get_stockpile("Dollars")) - action.amount< 0:
            nation.action_log.append(f"Failed to spend {action.amount} dollars on Fundraise. Insufficient dollars.")
            continue

        nation.update_stockpile("Dollars", -1 * action.amount)
        event.cure_current += action.amount // 3
        nation.action_log.append(f"Used Fundraise to spend {action.amount} dollars in exchange for {action.amount // 3} cure progress.")
    
    active_games_dict[game_id]["Active Events"]["Pandemic"] = event.export()
    with open("active_games.json", 'w') as json_file:
        json.dump(active_games_dict, json_file, indent=4)

def resolve_inspect_region_actions(game_id: str, actions_list: list[InspectRegionAction]) -> None:

    with open("active_games.json", 'r') as json_file:
        active_games_dict = json.load(json_file)

    for action in actions_list:

        nation = Nations.get(action.id)

        if "Pandemic" not in active_games_dict[game_id]["Active Events"]:
            nation.action_log.append(f"{action.action_str} failed. Corresponding event is not active.")
            continue
        
        if float(nation.get_stockpile("Dollars")) - 5 < 0:
            nation.action_log.append(f"Failed to Inspect {action.target_region}. Insufficient dollars.")
            continue

        nation.update_stockpile("Dollars", -5)
        region = Region(action.target_region)
        nation.action_log.append(f"Used Inspect action for 5 dollars. Region {action.target_region} has an infection score of {region.data.infection}.")

def resolve_quarantine_create_actions(game_id: str, actions_list: list[QuarantineCreateAction]) -> None:

    with open("active_games.json", 'r') as json_file:
        active_games_dict = json.load(json_file)

    for action in actions_list:

        nation = Nations.get(action.id)

        if "Pandemic" not in active_games_dict[game_id]["Active Events"]:
            nation.action_log.append(f"{action.action_str} failed. Corresponding event is not active.")
            continue

        
        if float(nation.get_stockpile("Political Power")) - 1 < 0:
            nation.action_log.append(f"Failed to quarantine {action.target_region}. Insufficient political power.")
            continue

        nation.update_stockpile("Political Power", -1)
        region = Region(action.target_region)
        region.data.quarantine = True
        nation.action_log.append(f"Quarantined {action.target_region} for 1 political power.")

def resolve_quarantine_end_actions(game_id: str, actions_list: list[QuarantineEndAction]) -> None:

    with open("active_games.json", 'r') as json_file:
        active_games_dict = json.load(json_file)

    for action in actions_list:

        nation = Nations.get(action.id)

        if "Pandemic" not in active_games_dict[game_id]["Active Events"]:
            nation.action_log.append(f"{action.action_str} failed. Corresponding event is not active.")
            continue

        if float(nation.get_stockpile("Political Power")) - 1 < 0:
            nation.action_log.append(f"Failed to end quarantine {action.target_region}. Insufficient political power.")
            continue

        nation.update_stockpile("Political Power", -1)
        region = Region(action.target_region)
        region.data.quarantine = False
        nation.action_log.append(f"Ended quarantine {action.target_region} for 1 political power.")

def resolve_open_borders_actions(game_id: str, actions_list: list[BordersOpenAction]) -> None:

    with open("active_games.json", 'r') as json_file:
        active_games_dict = json.load(json_file)
    scenario = active_games_dict[game_id]["Information"]["Scenario"].lower()
    events = importlib.import_module(f"scenarios.{scenario}.events")

    if "Pandemic" not in active_games_dict[game_id]["Active Events"]:
        return

    event_data = active_games_dict[game_id]["Active Events"]["Pandemic"]
    event = events.load_event(game_id, "Pandemic", event_data, temp=True)

    for action in actions_list:

        nation = Nations.get(action.id)

        if "Pandemic" not in active_games_dict[game_id]["Active Events"]:
            nation.action_log.append(f"{action.action_str} failed. Corresponding event is not active.")
            continue

        if float(nation.get_stockpile("Political Power")) - 10 < 0:
            nation.action_log.append(f"Failed to do Open Borders action. Insufficient political power.")
            continue
        
        nation.update_stockpile("Political Power", -10)
        event.closed_borders.remove(nation.id)
        nation.action_log.append("Spent 10 political power to Open Borders.")
    
    active_games_dict[game_id]["Active Events"]["Pandemic"] = event.export()
    with open("active_games.json", 'w') as json_file:
        json.dump(active_games_dict, json_file, indent=4)

def resolve_close_borders_actions(game_id: str, actions_list: list[BordersCloseAction]) -> None:

    with open("active_games.json", 'r') as json_file:
        active_games_dict = json.load(json_file)
    scenario = active_games_dict[game_id]["Information"]["Scenario"].lower()
    events = importlib.import_module(f"scenarios.{scenario}.events")

    if "Pandemic" not in active_games_dict[game_id]["Active Events"]:
        return

    event_data = active_games_dict[game_id]["Active Events"]["Pandemic"]
    event = events.load_event(game_id, "Pandemic", event_data, temp=True)

    for action in actions_list:

        nation = Nations.get(action.id)

        if "Pandemic" not in active_games_dict[game_id]["Active Events"]:
            nation.action_log.append(f"{action.action_str} failed. Corresponding event is not active.")
            continue

        if float(nation.get_stockpile("Political Power")) - 10 < 0:
            nation.action_log.append(f"Failed to do Close Borders action. Insufficient political power.")
            continue
        
        nation.update_stockpile("Political Power", -10)
        event.closed_borders.append(nation.id)
        nation.action_log.append("Spent 10 political power to Close Borders.")
    
    active_games_dict[game_id]["Active Events"]["Pandemic"] = event.export()
    with open("active_games.json", 'w') as json_file:
        json.dump(active_games_dict, json_file, indent=4)

def resolve_outsource_technology_actions(game_id: str, actions_list: list[OutsourceTechnologyAction]) -> None:

    research_data_dict = core.get_scenario_dict(game_id, "Technologies")

    for action in actions_list:

        nation = Nations.get(action.id)

        if "Faustian Bargain" not in nation.tags:
            nation.action_log.append(f"Failed to Outsource Technology. You are not the collaborator.")
            continue
        
        if action.research_name not in research_data_dict:
            nation.action_log.append(f"Failed to do Outsource Technology action. Technology name \"{action.research_name}\" not recognized.")
            continue
        
        if action.research_name in nation.completed_research:
            nation.action_log.append(f"Failed to do Outsource Technology action. You already have {action.research_name}.")
            continue
        
        research_prereq = research_data_dict[action.research_name]['Prerequisite']
        if research_prereq != None and research_prereq not in nation.completed_research:
            nation.action_log.append(f"Failed to do Outsource Technology action. You do not have the prerequisite for {action.research_name}.")
            continue

        if float(nation.get_stockpile("Political Power")) -10 < 0:
            nation.action_log.append(f"Failed to do Outsource Technology action. Insufficient political power.")
            continue
        
        nation.update_stockpile("Political Power", -10)
        nation.add_tech(action.research_name)
        nation.award_research_bonus(action.research_name)
        nation.action_log.append(f"Used Outsource Technology to research {action.research_name}.")

def resolve_military_reinforcements_actions(game_id: str, actions_list: list[MilitaryReinforcementsAction]) -> None:

    for action in actions_list:

        nation = Nations.get(action.id)

        if "Faustian Bargain" not in nation.tags:
            nation.action_log.append(f"Failed to do Military Reinforcements. You are not the collaborator.")
            continue
        
        if float(nation.get_stockpile("Political Power")) -10 < 0:
            nation.action_log.append(f"Failed to do Military Reinforcements. Insufficient political power.")
            continue

        nation.update_stockpile("Political Power", -10)

        for region_id in action.target_region_ids:
            
            region = Region(region_id)
            
            if region.data.owner_id != action.id:
                nation.action_log.append(f"Failed to use Military Reinforcements to deploy Mechanized Infantry {region_id}. You do not own that region.")
                continue
            
            if region.unit.owner_id != action.id:
                nation.action_log.append(f"Failed to use Military Reinforcements to deploy Mechanized Infantry {region_id}. A hostile unit is present.")
                continue
            
            if region.unit.name is not None:
                nation.unit_counts[region.unit.name] -= 1
            nation.unit_counts["Mechanized Infantry"] += 1
            region.unit.set("Mechanized Infantry", action.id)
            nation.action_log.append(f"Used Military Reinforcements to deploy Mechanized Infantry {region_id}.")
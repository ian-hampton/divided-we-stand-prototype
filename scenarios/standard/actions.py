import csv
import json
import importlib

from app import core
from app.nationdata import Nation
from app.nationdata import NationTable
from app.alliance import AllianceTable
from app.war import WarTable
from app.notifications import Notifications
from app.region import Region
from app.improvement import Improvement
from app.unit import Unit

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

    nation_table = NationTable(game_id)
    trucedata_filepath = f'gamedata/{game_id}/trucedata.csv'
    trucedata_list = core.read_file(trucedata_filepath, 1)
    current_turn_num = core.get_current_turn_num(game_id)

    for action in actions_list:

        nation = nation_table.get(action.id)

        if "Mediator" not in nation.tags:
            nation.action_log.append(f"{action.action_str} failed. You are not the Mediator.")
            nation_table.save(nation)
            continue

        for truce in trucedata_list:
                
            truce_id = str(truce[0])
            mediator_in_truce = truce[int(action.id)]
            truce_expire_turn = int(truce[len(truce)])

            if truce_id == action.truce_id:
                
                if truce_id in nation.tags["Mediator"]["Truces Extended"]:
                    nation.action_log.append(f"Failed to Host Peace Talks for Truce #{action.truce_id}. Truce has already been extended.")
                    break
                
                if mediator_in_truce:
                    nation.action_log.append(f"Failed to Host Peace Talks for Truce #{action.truce_id}. Mediator is involved in this truce.")
                    break
            
                if current_turn_num >= truce_expire_turn:
                    nation.action_log.append(f"Failed to Host Peace Talks for Truce #{action.truce_id}. Truce has already expired.")
                    break

                nation.update_stockpile("Political Power", -5)
                if float(nation.get_stockpile("Political Power")) < 0:
                    nation_table.reload()
                    nation = nation_table.get(action.id)
                    nation.action_log.append(f"Failed to Host Peace Talks for Truce #{action.truce_id}. Insufficient political power.")
                    break
                
                truce[len(truce)] = truce_expire_turn + 4
                nation.tags["Mediator"]["Truces Extended"].append(truce_id)
                nation.action_log.append(f"Used Host Peace Talks on Truce #{action.truce_id}.")
                break

        nation_table.save(nation)

    with open(trucedata_filepath, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(core.trucedata_header)
        writer.writerows(trucedata_list)

def resolve_cure_research_actions(game_id: str, actions_list: list[CureResearchAction]) -> None:

    nation_table = NationTable(game_id)
    with open("active_games.json", 'r') as json_file:
        active_games_dict = json.load(json_file)
    scenario = active_games_dict[game_id]["Information"]["Scenario"].lower()
    events = importlib.import_module(f"scenarios.{scenario}.events")

    if "Pandemic" not in active_games_dict[game_id]["Active Events"]:
        return

    event_data = active_games_dict[game_id]["Active Events"]["Pandemic"]
    event = events.load_event(game_id, "Pandemic", event_data, temp=True)

    for action in actions_list:

        nation = nation_table.get(action.id)

        if "Pandemic" not in active_games_dict[game_id]["Active Events"]:
            nation.action_log.append(f"{action.action_str} failed. Corresponding event is not active.")
            nation_table.save(nation)
            continue

        nation.update_stockpile("Research", -1 * action.amount)
        if float(nation.get_stockpile("Research")) < 0:
            nation_table.reload()
            nation = nation_table.get(action.id)
            nation.action_log.append(f"Failed to spend {action.amount} technology on Cure Research. Insufficient technology.")
            nation_table.save(nation)
            continue

        event.cure_current += action.amount
        nation.action_log.append(f"Used Cure Research to spend {action.amount} technology in exchange for {action.amount} cure progress.")

        nation_table.save(nation)
    
    active_games_dict[game_id]["Active Events"]["Pandemic"] = event.export()
    with open("active_games.json", 'w') as json_file:
        json.dump(active_games_dict, json_file, indent=4)

def resolve_cure_fundraise_actions(game_id: str, actions_list: list[CureFundraiseAction]) -> None:

    nation_table = NationTable(game_id)
    with open("active_games.json", 'r') as json_file:
        active_games_dict = json.load(json_file)
    scenario = active_games_dict[game_id]["Information"]["Scenario"].lower()
    events = importlib.import_module(f"scenarios.{scenario}.events")

    if "Pandemic" not in active_games_dict[game_id]["Active Events"]:
        return

    event_data = active_games_dict[game_id]["Active Events"]["Pandemic"]
    event = events.load_event(game_id, "Pandemic", event_data, temp=True)

    for action in actions_list:

        nation = nation_table.get(action.id)

        if "Pandemic" not in active_games_dict[game_id]["Active Events"]:
            nation.action_log.append(f"{action.action_str} failed. Corresponding event is not active.")
            nation_table.save(nation)
            continue

        nation.update_stockpile("Dollars", -1 * action.amount)
        if float(nation.get_stockpile("Dollars")) < 0:
            nation_table.reload()
            nation = nation_table.get(action.id)
            nation.action_log.append(f"Failed to spend {action.amount} dollars on Fundraise. Insufficient dollars.")
            nation_table.save(nation)
            continue

        event.cure_current += action.amount // 3
        nation.action_log.append(f"Used Fundraise to spend {action.amount} dollars in exchange for {action.amount // 3} cure progress.")

        nation_table.save(nation)
    
    active_games_dict[game_id]["Active Events"]["Pandemic"] = event.export()
    with open("active_games.json", 'w') as json_file:
        json.dump(active_games_dict, json_file, indent=4)

def resolve_inspect_region_actions(game_id: str, actions_list: list[InspectRegionAction]) -> None:

    nation_table = NationTable(game_id)
    with open("active_games.json", 'r') as json_file:
        active_games_dict = json.load(json_file)

    for action in actions_list:

        nation = nation_table.get(action.id)

        if "Pandemic" not in active_games_dict[game_id]["Active Events"]:
            nation.action_log.append(f"{action.action_str} failed. Corresponding event is not active.")
            nation_table.save(nation)
            continue

        nation.update_stockpile("Dollars", -5)
        if float(nation.get_stockpile("Dollars")) < 0:
            nation_table.reload()
            nation = nation_table.get(action.id)
            nation.action_log.append(f"Failed to Inspect {action.target_region}. Insufficient dollars.")
            nation_table.save(nation)
            continue

        region = Region(action.target_region, game_id)
        nation.action_log.append(f"Used Inspect action for 5 dollars. Region {action.target_region} has an infection score of {region.infection()}.")

        nation_table.save(nation)

def resolve_quarantine_create_actions(game_id: str, actions_list: list[QuarantineCreateAction]) -> None:

    nation_table = NationTable(game_id)
    with open("active_games.json", 'r') as json_file:
        active_games_dict = json.load(json_file)

    for action in actions_list:

        nation = nation_table.get(action.id)

        if "Pandemic" not in active_games_dict[game_id]["Active Events"]:
            nation.action_log.append(f"{action.action_str} failed. Corresponding event is not active.")
            nation_table.save(nation)
            continue

        nation.update_stockpile("Political Power", -1)
        if float(nation.get_stockpile("Political Power")) < 0:
            nation_table.reload()
            nation = nation_table.get(action.id)
            nation.action_log.append(f"Failed to quarantine {action.target_region}. Insufficient political power.")
            nation_table.save(nation)
            continue

        region = Region(action.target_region, game_id)
        region.set_quarantine()
        nation.action_log.append(f"Quarantined {action.target_region} for 1 political power.")

        nation_table.save(nation)

def resolve_quarantine_end_actions(game_id: str, actions_list: list[QuarantineEndAction]) -> None:

    nation_table = NationTable(game_id)
    with open("active_games.json", 'r') as json_file:
        active_games_dict = json.load(json_file)

    for action in actions_list:

        nation = nation_table.get(action.id)

        if "Pandemic" not in active_games_dict[game_id]["Active Events"]:
            nation.action_log.append(f"{action.action_str} failed. Corresponding event is not active.")
            nation_table.save(nation)
            continue

        nation.update_stockpile("Political Power", -1)
        if float(nation.get_stockpile("Political Power")) < 0:
            nation_table.reload()
            nation = nation_table.get(action.id)
            nation.action_log.append(f"Failed to end quarantine {action.target_region}. Insufficient political power.")
            nation_table.save(nation)
            continue

        region = Region(action.target_region, game_id)
        region.set_quarantine(False)
        nation.action_log.append(f"Ended quarantine {action.target_region} for 1 political power.")

        nation_table.save(nation)

def resolve_open_borders_actions(game_id: str, actions_list: list[BordersOpenAction]) -> None:

    nation_table = NationTable(game_id)
    with open("active_games.json", 'r') as json_file:
        active_games_dict = json.load(json_file)
    scenario = active_games_dict[game_id]["Information"]["Scenario"].lower()
    events = importlib.import_module(f"scenarios.{scenario}.events")

    if "Pandemic" not in active_games_dict[game_id]["Active Events"]:
        return

    event_data = active_games_dict[game_id]["Active Events"]["Pandemic"]
    event = events.load_event(game_id, "Pandemic", event_data, temp=True)

    for action in actions_list:

        nation = nation_table.get(action.id)

        if "Pandemic" not in active_games_dict[game_id]["Active Events"]:
            nation.action_log.append(f"{action.action_str} failed. Corresponding event is not active.")
            nation_table.save(nation)
            continue

        nation.update_stockpile("Political Power", -10)
        if float(nation.get_stockpile("Political Power")) < 0:
            nation_table.reload()
            nation = nation_table.get(action.id)
            nation.action_log.append(f"Failed to do Open Borders action. Insufficient political power.")
            nation_table.save(nation)
            continue

        event.closed_borders.remove(nation.id)
        nation.action_log.append("Spent 10 political power to Open Borders.")

        nation_table.save(nation)
    
    active_games_dict[game_id]["Active Events"]["Pandemic"] = event.export()
    with open("active_games.json", 'w') as json_file:
        json.dump(active_games_dict, json_file, indent=4)

def resolve_close_borders_actions(game_id: str, actions_list: list[BordersCloseAction]) -> None:

    nation_table = NationTable(game_id)
    with open("active_games.json", 'r') as json_file:
        active_games_dict = json.load(json_file)
    scenario = active_games_dict[game_id]["Information"]["Scenario"].lower()
    events = importlib.import_module(f"scenarios.{scenario}.events")

    if "Pandemic" not in active_games_dict[game_id]["Active Events"]:
        return

    event_data = active_games_dict[game_id]["Active Events"]["Pandemic"]
    event = events.load_event(game_id, "Pandemic", event_data, temp=True)

    for action in actions_list:

        nation = nation_table.get(action.id)

        if "Pandemic" not in active_games_dict[game_id]["Active Events"]:
            nation.action_log.append(f"{action.action_str} failed. Corresponding event is not active.")
            nation_table.save(nation)
            continue

        nation.update_stockpile("Political Power", -10)
        if float(nation.get_stockpile("Political Power")) < 0:
            nation_table.reload()
            nation = nation_table.get(action.id)
            nation.action_log.append(f"Failed to do Close Borders action. Insufficient political power.")
            nation_table.save(nation)
            continue

        event.closed_borders.append(nation.id)
        nation.action_log.append("Spent 10 political power to Close Borders.")

        nation_table.save(nation)
    
    active_games_dict[game_id]["Active Events"]["Pandemic"] = event.export()
    with open("active_games.json", 'w') as json_file:
        json.dump(active_games_dict, json_file, indent=4)

def resolve_outsource_technology_actions(game_id: str, actions_list: list[OutsourceTechnologyAction]) -> None:

    nation_table = NationTable(game_id)
    research_data_dict = core.get_scenario_dict(game_id, "Technologies")

    for action in actions_list:

        nation = nation_table.get(action.id)

        if "Faustian Bargain" not in nation.tags:
            nation.action_log.append(f"Failed to Outsource Technology. You are not the collaborator.")
            nation_table.save(nation)
            continue
        
        if action.research_name not in research_data_dict:
            nation.action_log.append(f"Failed to do Outsource Technology action. Technology name \"{action.research_name}\" not recognized.")
            nation_table.save(nation)
            continue
        
        if action.research_name in nation.completed_research:
            nation.action_log.append(f"Failed to do Outsource Technology action. You already have {action.research_name}.")
            nation_table.save(nation)
            continue
        
        research_prereq = research_data_dict[action.research_name]['Prerequisite']
        if research_prereq != None and research_prereq not in nation.completed_research:
            nation.action_log.append(f"Failed to do Outsource Technology action. You do not have the prerequisite for {action.research_name}.")
            nation_table.save(nation)
            continue

        nation.update_stockpile("Political Power", -10)
        if float(nation.get_stockpile("Political Power")) < 0:
            nation_table.reload()
            nation = nation_table.get(action.id)
            nation.action_log.append(f"Failed to do Outsource Technology action. Insufficient political power.")
            nation_table.save(nation)
            continue

        nation.add_tech(action.research_name)
        nation.award_research_bonus(action.research_name)
        nation.action_log.append(f"Used Outsource Technology to research {action.research_name}.")

        nation_table.save(nation)

def resolve_military_reinforcements_actions(game_id: str, actions_list: list[MilitaryReinforcementsAction]) -> None:

    nation_table = NationTable(game_id)

    for action in actions_list:

        nation = nation_table.get(action.id)

        if "Faustian Bargain" not in nation.tags:
            nation.action_log.append(f"Failed to do Military Reinforcements. You are not the collaborator.")
            nation_table.save(nation)
            continue
        
        nation.update_stockpile("Political Power", -10)
        if float(nation.get_stockpile("Political Power")) < 0:
            nation_table.reload()
            nation = nation_table.get(action.id)
            nation.action_log.append(f"Failed to do Military Reinforcements. Insufficient political power.")
            nation_table.save(nation)
            continue

        # execute action
        for region_id in action.target_region_ids:
            
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
            
            if region_unit.name is not None:
                nation.unit_counts[region_unit.name] -= 1
            region_unit.set_unit("Mechanized Infantry", int(action.id))
            nation.unit_counts["Mechanized Infantry"] += 1
            nation.action_log.append(f"Used Military Reinforcements to deploy Mechanized Infantry {region_id}.")

        nation_table.save(nation)
import json
import random

from app import core
from app.nationdata import NationTable
from app.war import WarTable
from app.notifications import Notifications


class Event:

    def __init__(self, game_id: str, event_data: dict, *, temp = False):

        # load event data
        self.name: str = event_data["Name"]
        self.type: str = event_data["Type"]
        self.duration: int = event_data["Duration"]
        self.candidates: list = event_data.get("Candidates", [])
        self.targets: list = event_data.get("Targets", [])
        self.expire_turn: int = event_data.get("Expiration", -1)
        self.state = None

        # load game data
        if not temp:
            self.game_id = game_id
            self.nation_table = NationTable(self.game_id)
            self.war_table = WarTable(self.game_id)
            self.notifications = Notifications(self.game_id)
            self.current_turn_num = core.get_current_turn_num(self.game_id)
            with open("active_games.json", 'r') as json_file:
                self.active_games_dict = json.load(json_file)
            with open(f'gamedata/{game_id}/regdata.json', 'r') as json_file:
                self.regdata_dict = json.load(json_file)

        # GAME DATA NOTES
        #  - be sure to set temp to true if the event is only being loaded to check for conditions or expiration
        #  - you will need to explicitly save changes to NationTable, WarTable, etc inside the event class methods!
        #  - do not save any changes to active_games.json, they will be lost!

        # EVENT STATES
        #  "Current"     event is pending input from players
        #  "Active"      event is ongoing but does not require attention from players
        #  "Inactive"    event is completed and is ready to be archived

    def export(self) -> dict:
        
        return {
            "Name": self.name,
            "Type": self.type,
            "Duration": self.duration,
            "Candidates": self.candidates,
            "Targets": self.targets,
            "Expiration": self.expire_turn
        }

class Assassination(Event):
    
    def __init__(self, game_id: str, event_data: dict):
        Event.__init__(self, game_id, event_data)

    def activate(self):

        victim_player_id = random.randint(1, len(self.nation_table)) 
        victim_nation = self.nation_table.get(str(victim_player_id))
        self.targets.append(victim_nation.id)

        self.notifications.append(f"{victim_nation.name} has been randomly selected as the target for the {self.name} event!", 2)

        self.state = "Current"

    def resolve(self):
        pass
    
    def has_conditions_met(self) -> bool:
        return True

class CorruptionScandal(Event):
    
    def __init__(self, game_id: str, event_data: dict):
        Event.__init__(self, game_id, event_data)

    def activate(self):
        pass

    def has_conditions_met(self) -> bool:

        if not _no_ranking_tie(self.game_id, "netIncome"):
            return False
        
        return True

class Coup(Event):
    
    def __init__(self, game_id: str, event_data: dict):
        Event.__init__(self, game_id, event_data)

    def activate(self):
        pass

    def has_conditions_met(self) -> bool:

        if _is_first_event(self.game_id):
            return False
        
        return True

class DecayingInfrastructure(Event):
    
    def __init__(self, game_id: str, event_data: dict):
        Event.__init__(self, game_id, event_data)

    def activate(self):
        pass

    def has_conditions_met(self) -> bool:

        if _is_first_event(self.game_id):
            return False
        
        return True

class Desertion(Event):
    
    def __init__(self, game_id: str, event_data: dict):
        Event.__init__(self, game_id, event_data)

    def activate(self):
        pass

    def has_conditions_met(self) -> bool:

        if not _at_least_x_ongoing_wars(self.game_id, 1):
            return False

        return True

class DiplomaticSummit(Event):
    
    def __init__(self, game_id: str, event_data: dict):
        Event.__init__(self, game_id, event_data)

    def activate(self):
        pass

    def has_conditions_met(self) -> bool:
        return True

class ForeignAid(Event):
    
    def __init__(self, game_id: str, event_data: dict):
        Event.__init__(self, game_id, event_data)

    def activate(self):
        pass

    def has_conditions_met(self) -> bool:
        return True

class ForeignInterference(Event):
    
    def __init__(self, game_id: str, event_data: dict):
        Event.__init__(self, game_id, event_data)

    def activate(self):
        pass

    def has_conditions_met(self) -> bool:

        if _is_first_event(self.game_id):
            return False
        
        return True

class LostNuclearWeapons(Event):
    
    def __init__(self, game_id: str, event_data: dict):
        Event.__init__(self, game_id, event_data)

    def activate(self):
        pass

    def has_conditions_met(self) -> bool:
        return True

class SecurityBreach(Event):
    
    def __init__(self, game_id: str, event_data: dict):
        Event.__init__(self, game_id, event_data)

    def activate(self):
        pass

    def has_conditions_met(self) -> bool:

        if not _no_ranking_tie(self.game_id, "researchCount"):
            return False
        
        return True

class MarketInflation(Event):
    
    def __init__(self, game_id: str, event_data: dict):
        Event.__init__(self, game_id, event_data)

    def activate(self):
        pass

    def has_conditions_met(self) -> bool:
        return True

class MarketRecession(Event):
    
    def __init__(self, game_id: str, event_data: dict):
        Event.__init__(self, game_id, event_data)

    def activate(self):
        pass

    def has_conditions_met(self) -> bool:
        return True

class ObserverStatusInvitation(Event):
    
    def __init__(self, game_id: str, event_data: dict):
        Event.__init__(self, game_id, event_data)

    def activate(self):
        pass

    def has_conditions_met(self) -> bool:
        return True

class PeacetimeRewards(Event):
    
    def __init__(self, game_id: str, event_data: dict):
        Event.__init__(self, game_id, event_data)

    def activate(self):
        pass

    def has_conditions_met(self) -> bool:

        if not _at_least_x_nations_at_peace_for_y_turns(self.game_id, 1, 12):
            return False
        
        return True

class PowerPlantMeltdown(Event):
    
    def __init__(self, game_id: str, event_data: dict):
        Event.__init__(self, game_id, event_data)

    def activate(self):
        pass

    def has_conditions_met(self) -> bool:

        if not _global_count_of_x_improvement_at_least_y(self.game_id, "Nuclear Power Plant", 1):
            return False

        return True

class ShiftingAttitudes(Event):
    
    def __init__(self, game_id: str, event_data: dict):
        Event.__init__(self, game_id, event_data)

    def activate(self):
        pass

    def has_conditions_met(self) -> bool:

        if _is_first_event(self.game_id):
            return False
        
        return True

class UnitedNationsPeacekeepingMandate(Event):
    
    def __init__(self, game_id: str, event_data: dict):
        Event.__init__(self, game_id, event_data)

    def activate(self):
        pass

    def has_conditions_met(self) -> bool:

        if not _at_least_x_ongoing_wars(self.game_id, 3):
            return False
        
        return True

class WidespreadCivilDisorder(Event):
    
    def __init__(self, game_id: str, event_data: dict):
        Event.__init__(self, game_id, event_data)

    def activate(self):
        pass

    def has_conditions_met(self) -> bool:

        if _is_first_event(self.game_id):
            return False
        
        return True

class Embargo(Event):
    
    def __init__(self, game_id: str, event_data: dict):
        Event.__init__(self, game_id, event_data)

    def activate(self):
        pass

    def has_conditions_met(self) -> bool:
        return True

class Humiliation(Event):
    
    def __init__(self, game_id: str, event_data: dict):
        Event.__init__(self, game_id, event_data)

    def activate(self):
        pass

    def has_conditions_met(self) -> bool:
        return True

class ForeignInvestment(Event):
    
    def __init__(self, game_id: str, event_data: dict):
        Event.__init__(self, game_id, event_data)

    def activate(self):
        pass

    def has_conditions_met(self) -> bool:
        return True

class NominateMediator(Event):
    
    def __init__(self, game_id: str, event_data: dict):
        Event.__init__(self, game_id, event_data)

    def activate(self):
        pass

    def has_conditions_met(self) -> bool:
        return True

class SharedFate(Event):
    
    def __init__(self, game_id: str, event_data: dict):
        Event.__init__(self, game_id, event_data)

    def activate(self):
        pass

    def has_conditions_met(self) -> bool:
        return True

class ThreatContainment(Event):
    
    def __init__(self, game_id: str, event_data: dict):
        Event.__init__(self, game_id, event_data)

    def activate(self):
        pass

    def has_conditions_met(self) -> bool:
        return True

class ForeignInvasion(Event):
    
    def __init__(self, game_id: str, event_data: dict):
        Event.__init__(self, game_id, event_data)

    def activate(self):
        pass

    def has_conditions_met(self) -> bool:

        if _is_first_event(self.game_id):
            return False
        
        if not _no_major_events(self.game_id):
            return False
        
        return True

class Pandemic(Event):
    
    def __init__(self, game_id: str, event_data: dict):
        Event.__init__(self, game_id, event_data)
        self.intensify: int = event_data.get("Intensify Value", -1)
        self.spread: int = event_data.get("Spread Value", -1)
        self.cure_current: int = event_data.get("Completed Cure Research", -1)
        self.cure_threshold: int = event_data.get("Needed Cure Research", -1)
        self.closed_borders: list = event_data.get("Closed Borders List", [])

    def activate(self):
        pass

    def export(self) -> dict:
        pass

    def has_conditions_met(self) -> bool:

        if _is_first_event(self.game_id):
            return False
        
        if not _no_major_events(self.game_id):
            return False
        
        return True

class FaustianBargain(Event):
    
    def __init__(self, game_id: str, event_data: dict):
        Event.__init__(self, game_id, event_data)

    def activate(self):
        pass

    def has_conditions_met(self) -> bool:

        if _is_first_event(self.game_id):
            return False
        
        if not _no_major_events(self.game_id):
            return False
        
        return True

def load_event(game_id: str, event_name: str, new=False) -> any:
    """
    Creates an event object based on the event name.

    Params:
        game_id (str): Game ID string.
        event_name (str): Event name string.

    Returns:
        any: An event object corresponding to the event name, or raises an exception if none found.
    """

    events = {
        "Assassination": Assassination,
        "Corruption Scandal": CorruptionScandal,
        "Coup": Coup,
        "Decaying Infrastructure": DecayingInfrastructure,
        "Desertion": Desertion,
        "Diplomatic Summit": DiplomaticSummit,
        "Foreign Aid": ForeignAid,
        "Foreign Interference": ForeignInterference,
        "Lost Nuclear Weapons": LostNuclearWeapons,
        "Security Breach": SecurityBreach,
        "Market Inflation": MarketInflation,
        "Market Recession": MarketRecession,
        "Observer Status Invitation": ObserverStatusInvitation,
        "Peacetime Rewards": PeacetimeRewards,
        "Power Plant Meltdown": PowerPlantMeltdown,
        "Shifting Attitudes": ShiftingAttitudes,
        "United Nations Peacekeeping Mandate": UnitedNationsPeacekeepingMandate,
        "Widespread Civil Disorder": WidespreadCivilDisorder,
        "Embargo": Embargo,
        "Humiliation": Humiliation,
        "Foreign Investment": ForeignInvestment,
        "Nominate Mediator": NominateMediator,
        "Shared Fate": SharedFate,
        "Threat Containment": ThreatContainment,
        "Foreign Invasion": ForeignInvasion,
        "Pandemic": Pandemic,
        "Faustian Bargain": FaustianBargain
    }

    if event_name in events:
        event_scenario_dict = core.get_scenario_dict(game_id, "events")
        event_data = event_scenario_dict[event_name]
        if new:
            event_data["Name"] = event_name
        return events[event_name](game_id, event_data)
    else:
        raise Exception(f"Error: {event_name} event not recognized.")
    
def _is_first_event(game_id: str) -> bool:

    with open("active_games.json", 'r') as json_file:
        active_games_dict = json.load(json_file)
    
    already_chosen_events = set(active_games_dict[game_id]["Inactive Events"]) | set(key for key in active_games_dict[game_id]["Active Events"])

    if len(already_chosen_events) != 0:
        return False
    
    return True

def _no_major_events(game_id: str) -> bool:

    with open("active_games.json", 'r') as json_file:
        active_games_dict = json.load(json_file)
    
    event_scenario_dict = core.get_scenario_dict(game_id, "events")
    already_chosen_events = set(active_games_dict[game_id]["Inactive Events"]) | set(key for key in active_games_dict[game_id]["Active Events"])
   
    for event_name, event_data in event_scenario_dict.items():
        if event_name in already_chosen_events and event_data["Type"] == "Major Event":
            return False
        
    return True

def _no_ranking_tie(game_id: str, ranking: str) -> bool:

    nation_table = NationTable(game_id)
    
    top_three = nation_table.get_top_three(ranking)
    if top_three[0][1] == top_three[1][1]:
        return False
    
    return True

def _at_least_x_ongoing_wars(game_id: str, count: int) -> bool:

    war_table = WarTable(game_id)
    
    ongoing_war_count = 0
    for war in war_table:
        if war.outcome == "TBD":
            ongoing_war_count += 1
    
    if ongoing_war_count < count:
        return False
    
    return True

def _at_least_x_nations_at_peace_for_y_turns(game_id: str, nation_count: int, turn_count: int) -> bool:
    
    nation_table = NationTable(game_id)
    war_table = WarTable(game_id)
    
    at_peace_count = 0
    for nation in nation_table:
        if war_table.at_peace_for_x(nation.id) >= turn_count:
            at_peace_count += 1
    
    if at_peace_count < nation_count:
        return False
    
    return True

def _global_count_of_x_improvement_at_least_y(game_id: str, improvement_name: str, count: int) -> bool:

    nation_table = NationTable(game_id)
    
    global_total = 0
    for nation in nation_table:
        global_total += nation.improvement_counts[improvement_name]
    
    if global_total < count:
        return False
    
    return True
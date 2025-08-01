import json
import random

from app import core
from app import actions
from app.nationdata import Nation
from app.nationdata import NationTable
from app.war import WarTable
from app.notifications import Notifications
from app.region import Region
from app.improvement import Improvement
from app.unit import Unit


class Event:

    def __init__(self, game_id: str, event_data: dict, *, temp = False):

        # load event data
        self.name: str = event_data["Name"]
        self.type: str = event_data["Type"]
        self.duration: int = event_data["Duration"]
        self.candidates: list = event_data.get("Candidates", [])
        self.targets: list = event_data.get("Targets", [])
        self.expire_turn: int = event_data.get("Expiration", -1)
        self.state: str = ""

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
    
    def _gain_free_research(self, research_name: str, nation: Nation) -> bool:
        """
        Returns updated playerdata_List and a bool that is True if the research was valid, False otherwise.
        """

        tech_scenario_dict = core.get_scenario_dict(self.game_id, "Technologies")
        
        # prereq check
        try:
            prereq = tech_scenario_dict[research_name]["Prerequisite"]
            if prereq != None and prereq not in nation.completed_research:
                return False
        except:
            return False
        
        # gain technology
        nation.add_tech(research_name)
        nation.award_research_bonus(research_name)

        return True

    def _collect_basic_decisions(self) -> dict:
        """
        Simple function to collect decisions from players in the terminal.
        """

        decision_dict = {}
        for player_id in self.targets:
            nation = self.nation_table.get(player_id)
            while True:
                decision = input(f"Enter {nation.name} decision: ")
                if decision in self.choices:
                    break
            decision_dict[player_id] = decision
        
        return decision_dict

    def _get_votes_nation(self) -> dict:
        
        vote_tally_dict = {}
    
        for nation_id in self.targets:
            
            nation = self.nation_table.get(nation_id)
            
            while True:
                
                decision = input(f"Enter {nation.name} vote: ")
                decision = decision.strip()
                if decision == "Abstain":
                    break

                decision_data = decision.split()
                vote_count = int(decision_data[0])
                target_name = " ".join(decision_data[1:])

                if vote_count > float(nation.get_stockpile("Political Power")):
                    continue
                if target_name.lower() not in self.nation_table._name_to_id:
                    continue
                
                if target_name in vote_tally_dict:
                    vote_tally_dict[target_name] += vote_count
                else:
                    vote_tally_dict[target_name] = vote_count
                
                nation.update_stockpile("Political Power", -1 * vote_count)
                self.nation_table.save(nation)
                break
        
        return vote_tally_dict

    def _get_votes_option(self) -> dict[str, int]:

        vote_tally_dict = {}
        
        for nation_id in self.targets:
            
            nation = self.nation_table.get(nation_id)
            
            while True:
                
                decision = input(f"Enter {nation.name} vote: ")
                decision = decision.strip()
                if decision == "Abstain":
                    break
                
                # expecting something like "# OPTION NAME"
                decision_data = decision.split()
                vote_count = int(decision_data[0])
                option_name = " ".join(decision_data[1:])

                if vote_count > float(nation.get_stockpile("Political Power")):
                    continue
                if option_name not in self.choices:
                    continue
                
                if option_name in vote_tally_dict:
                    vote_tally_dict[option_name] += vote_count
                else:
                    vote_tally_dict[option_name] = vote_count
                
                nation.update_stockpile("Political Power", -1 * vote_count)
                self.nation_table.save(nation)
                break
        
        return vote_tally_dict

    def _determine_vote_winner(self) -> str | None:

        if len(self.vote_tally) == 0:
            return None

        sorted_vote_tally = dict(sorted(self.vote_tally.items(), key=lambda item: item[1], reverse=True))

        if len(sorted_vote_tally) == 1:
            winning_outcome_data = list(sorted_vote_tally.items())[:1]
            return winning_outcome_data[0][0]

        top_two = list(sorted_vote_tally.items())[:2]
        if top_two[0][1] == top_two[1][1]:
            return None
        
        return top_two[0][0]

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
        
        self.choices = ["Find the Perpetrator", "Find a Scapegoat"]
        print(f"Available Options: {" or ".join(self.choices)}")
        decision_dict = self._collect_basic_decisions()

        for nation_id, decision in decision_dict.items():
            
            nation = self.nation_table.get(nation_id)
            
            if decision == "Find the Perpetrator":
                nation.update_stockpile("Political Power", 5)
                self.state = "Inactive"
            
            elif decision == "Find a Scapegoat":
                while True:
                    scapegoat_nation_name = input("Enter the nation name to scapegoat: ")
                    try:
                        scapegoat = self.nation_table.get(scapegoat_nation_name)
                        break
                    except:
                        print("Unrecognized nation name, try again.")
                new_tag = {
                    "Combat Roll Bonus": scapegoat.id,
                    "Expire Turn": self.current_turn_num + self.duration + 1
                }
                nation.tags["Assassination Scapegoat"] = new_tag
                self.state = "Active"
                self.duration = self.current_turn_num + self.duration + 1

        self.nation_table.save(nation)
    
    def has_conditions_met(self) -> bool:
        return True

class CorruptionScandal(Event):
    
    def __init__(self, game_id: str, event_data: dict):
        Event.__init__(self, game_id, event_data)

    def activate(self):
        
        top_three_economy = self.nation_table.get_top_three("netIncome")
        victim_nation_name = top_three_economy[0][0]
        victim_nation = self.nation_table.get(victim_nation_name)
        self.notifications.append(f"{victim_nation.name} has been randomly selected as the target for the {self.name} event!", 2)

        new_tag = {
            "Dollars Rate": -20,
            "Political Power Rate": -20,
            "Expire Turn": self.current_turn_num + self.duration + 1
        }
        victim_nation.tags["Corruption Scandal"] = new_tag
        
        self.nation_table.save(victim_nation)

        self.state = "Active"
        self.duration = self.current_turn_num + self.duration + 1

    def has_conditions_met(self) -> bool:

        if not _no_ranking_tie(self.game_id, "netIncome"):
            return False
        
        return True

class Coup(Event):
    
    def __init__(self, game_id: str, event_data: dict):
        Event.__init__(self, game_id, event_data)

    def activate(self):
        
        lowest_economy = self.nation_table.get_lowest_in_record("netIncome")
        victim_nation_name = lowest_economy[0]
        victim_nation = self.nation_table.get(victim_nation_name)

        old_government = victim_nation.gov
        gov_list = ["Republic", "Technocracy", "Oligarchy", "Totalitarian", "Remnant", "Protectorate", "Military Junta", "Crime Syndicate"]
        gov_list.remove(old_government)
        random.shuffle(gov_list)
        new_government = gov_list.pop()
        
        victim_nation.gov = new_government
        victim_nation.update_stockpile("Political Power", 0, overwrite=True)
        self.nation_table.save(victim_nation)
        self.notifications.append(f"{victim_nation_name}'s {old_government} government has been defeated by a coup. A new {new_government} government has taken power.", 2)

        self.state = "Inactive"

    def has_conditions_met(self) -> bool:

        if _is_first_event(self.game_id):
            return False
        
        return True

class DecayingInfrastructure(Event):
    
    def __init__(self, game_id: str, event_data: dict):
        Event.__init__(self, game_id, event_data)

    def activate(self):
        
        top_three = self.nation_table.get_top_three("nationSize")
        top_three_ids = set()
        for nation_name, nation_size in top_three:
            temp = self.nation_table.get(nation_name)
            top_three_ids.add(temp.id)

        for region_id in self.regdata_dict:
            region_improvement = Improvement(region_id, self.game_id)
            if str(region_improvement.owner_id) in top_three_ids and region_improvement.name is not None and region_improvement.name != "Capital":
                decay_roll = random.randint(1, 10)
                if decay_roll >= 9:
                    nation = self.nation_table.get(str(region_improvement.owner_id))
                    nation.improvement_counts[region_improvement.name] -= 1
                    self.nation_table.save(nation)
                    self.notifications.append(f"{nation.name} {region_improvement.name} in {region_id} has decayed.", 2)
                    region_improvement.clear()

        self.state = "Inactive"

    def has_conditions_met(self) -> bool:

        if _is_first_event(self.game_id):
            return False
        
        return True

class Desertion(Event):
    
    def __init__(self, game_id: str, event_data: dict):
        Event.__init__(self, game_id, event_data)

    def activate(self):
        
        # retrieve lowest warscore for each nation
        lowest_warscore_dict = {}
        for nation in self.nation_table:
            if self.war_table.is_at_peace(nation.id):
                continue
            lowest_warscore = 99999
            for war in self.war_table:
                if war.outcome != "TBD" or nation.id not in war.combatants:
                    continue
                nation_combatant_data = war.get_combatant(nation.id)
                score = war.attacker_total if "Attacker" in nation_combatant_data.role else score = war.defender_total
                if score < lowest_warscore:
                    lowest_warscore = score
            lowest_warscore_dict[nation.id] = lowest_warscore
        
        # all nations with the lowest warscore are targets of this event
        min_value = min(lowest_warscore_dict.values())
        filtered_dict = {}
        for nation_id, defection_data in lowest_warscore_dict.items():
            if defection_data["lowestScore"] == min_value:
                filtered_dict[nation_id] = defection_data
        self.targets = list(filtered_dict.keys())
        
        # check all regions owned by targets
        for region_id in self.regdata_dict:
            region_unit = Unit(region_id, self.game_id)
            if region_unit.owner_id not in self.targets:
                continue
            defection_roll = random.randint(1, 10)
            if defection_roll >= 9:
                nation = self.nation_table.get(str(region_unit.owner_id))
                nation.unit_counts[region_unit.name] -= 1
                self.nation_table.save(nation)
                self.notifications.append(f"{nation.name} {region_unit.name} {region_id} has deserted.", 2)
                region_unit.clear()
        
        self.state = "Inactive"

    def has_conditions_met(self) -> bool:

        if not _at_least_x_ongoing_wars(self.game_id, 1):
            return False

        return True

class DiplomaticSummit(Event):
    
    def __init__(self, game_id: str, event_data: dict):
        Event.__init__(self, game_id, event_data)

    def activate(self):
        
        self.notifications.append(f"New Event: {self.name}!", 2)
        for i in range(1, len(self.nation_table) + 1):
            self.targets.append(str(i))
        
        self.state = "Current"

    def resolve(self):

        summit_attendance_list = []
        
        self.choices = ["Attend", "Decline"]
        print(f"Available Options: {" or ".join(self.choices)}")
        decision_dict = self._collect_basic_decisions()

        for nation_id, decision in decision_dict.items():
            
            nation = self.nation_table.get(nation_id)
            
            if decision == "Attend":
                nation.update_stockpile("Political Power", 5)
                summit_attendance_list.append(nation.id)
            
            elif decision == "Decline":
                valid_research = False
                while not valid_research:
                    research_name = input(f"Enter {nation.name} military technology decision: ")
                    valid_research = self._gain_free_research(research_name, nation)
            
            self.nation_table.save(nation)
        
        if len(summit_attendance_list) < 2:
            self.state = "Inactive"
            return

        for nation_id in summit_attendance_list:
            nation = self.nation_table.get(nation_id)
            new_tag = {
                "Expire Turn": self.current_turn_num + self.duration + 1
            }
            for attendee_id in summit_attendance_list:
                new_tag[f"Cannot Declare War On #{attendee_id}"] = True
            nation.tags["Summit"] = new_tag
            self.nation_table.save(nation)
        
        self.state = "Active"
        self.duration = self.current_turn_num + self.duration + 1

    def has_conditions_met(self) -> bool:
        return True

class ForeignAid(Event):
    
    def __init__(self, game_id: str, event_data: dict):
        Event.__init__(self, game_id, event_data)

    def activate(self):
        
        for record_name in ["militaryStrength", "nationSize", "netIncome", "researchCount", "transactionCount"]:
            top_three = self.nation_table.get_top_three(record_name)
            for nation_name, score in top_three:
                if score != 0 and nation_name not in self.targets:
                    self.targets.append(nation_name)

        for nation_name in self.targets:
            nation = self.nation_table.get(nation_name)
            count = nation.improvement_counts["Settlement"] + nation.improvement_counts["City"]
            if count > 0:
                amount = count * 5
                nation.update_stockpile("Dollars", amount)
                self.notifications.append(f"{nation_name} has received {amount} dollars worth of foreign aid.", 2)

        self.state = "Inactive"

    def has_conditions_met(self) -> bool:
        return True

class ForeignInterference(Event):
    
    def __init__(self, game_id: str, event_data: dict):
        Event.__init__(self, game_id, event_data)

    def activate(self):
        
        self.notifications.append(f"New Event: {self.name}!", 2)
        for i in range(1, len(self.nation_table) + 1):
            self.targets.append(str(i))
        
        self.state = "Current"

    def resolve(self):

        self.choices = ["Accept", "Decline"]
        print(f"Available Options: {" or ".join(self.choices)}")
        decision_dict = self._collect_basic_decisions()

        war_actions: list[actions.WarAction] = []
        for nation_id, decision in decision_dict.items():
            
            nation = self.nation_table.get(nation_id)
            
            if decision == "Accept":
                action_valid = False
                while not action_valid:
                    enemy_nation_name = input("Enter nation you wish to declare war on: ")
                    chosen_war_justification = input("Enter desired war justification: ")
                    action_str = f"War {enemy_nation_name} {chosen_war_justification}"
                    war_action = actions.WarAction(self.game_id, nation_id, action_str)
                    if war_action.is_valid():
                        action_valid = True
                new_tag = {
                    "Foreign Interference Target": enemy_nation_name,
                    "Expire Turn": 99999
                }
                for resource_name in nation._resources:
                    if resource_name in ["Political Power", "Military Capacity"]:
                        continue
                    new_tag[f"{resource_name} Rate"] = 10
                nation.tags["Foreign Interference"] = new_tag
            
            elif decision == "Decline":
                nation.update_stockpile("Political Power", 5)
            
            self.nation_table.save(nation)

        actions.resolve_war_actions(self.game_id, war_actions)
        self.state = "Inactive"

    def has_conditions_met(self) -> bool:

        if _is_first_event(self.game_id):
            return False
        
        return True

class LostNuclearWeapons(Event):
    
    def __init__(self, game_id: str, event_data: dict):
        Event.__init__(self, game_id, event_data)

    def activate(self):

        victim_player_id = random.randint(1, len(self.nation_table)) 
        victim_nation = self.nation_table.get(str(victim_player_id))
        self.targets.append(victim_nation.id)

        self.notifications.append(f"{victim_nation.name} has been randomly selected as the target for the {self.name} event!", 2)

        self.state = "Current"

    def resolve(self):
        
        self.choices = ["Claim", "Scuttle"]
        print(f"Available Options: {" or ".join(self.choices)}")
        decision_dict = self._collect_basic_decisions()

        for nation_id, decision in decision_dict.items():
            
            nation = self.nation_table.get(nation_id)
            
            if decision == "Claim":
                valid_region_id = False
                while not valid_region_id:
                    silo_location_id = input("Enter region id for Missile Silo: ")
                    silo_location_id = silo_location_id.upper()
                    if silo_location_id in self.regdata_dict:
                        valid_region_id = True
                nation.improvement_counts["Missile Silo"] += 1
                region_improvement = Improvement(valid_region_id, self.game_id)
                region_improvement.set_improvement("Missile Silo")
                nation.nuke_count += 3
            
            elif decision == "Scuttle":
                nation.update_stockpile("Research", 15)
            
            self.nation_table.save(nation)
            self.notifications.append(f"{nation.name} chose to {decision.lower()} the old military installation.", 2)
        
        self.state = "Inactive"

    def has_conditions_met(self) -> bool:
        return True

class SecurityBreach(Event):
    
    def __init__(self, game_id: str, event_data: dict):
        Event.__init__(self, game_id, event_data)

    def activate(self):

        top_three = self.nation_table.get_top_three("researchCount")
        victim_nation_name = top_three[0][0]
        self.targets.append(victim_nation_name)

        self.notifications.append(f"{victim_nation_name} has suffered a {self.name}!", 2)

        self.state = "Current"

    def resolve(self):

        victim_name = self.targets[0]
        victim_nation = self.nation_table.get(victim_name)

        for nation in self.nation_table:
            
            if nation.name == victim_name:
                continue

            valid_research = False
            while not valid_research:
                research_name = input(f"Enter {nation.name} technology decision: ")
                if research_name not in victim_nation.completed_research:
                    continue
                valid_research = self._gain_free_research(research_name, nation)
            
            self.nation_table.save(nation)

        new_tag = {
            "Research Rate": -20,
            "Expire Turn": self.current_turn_num + self.duration + 1
        }
        victim_nation.tags["Security Breach"] = new_tag
        self.nation_table.save(victim_nation)
        
        self.state = "Active"
        self.duration = self.current_turn_num + self.duration + 1

    def has_conditions_met(self) -> bool:

        if not _no_ranking_tie(self.game_id, "researchCount"):
            return False
        
        return True

class MarketInflation(Event):
    
    def __init__(self, game_id: str, event_data: dict):
        Event.__init__(self, game_id, event_data)

    def activate(self):
        self.state = "Active"
        self.duration = self.current_turn_num + self.duration + 1

    def has_conditions_met(self) -> bool:
        return True

class MarketRecession(Event):
    
    def __init__(self, game_id: str, event_data: dict):
        Event.__init__(self, game_id, event_data)

    def activate(self):
        self.state = "Active"
        self.duration = self.current_turn_num + self.duration + 1

    def has_conditions_met(self) -> bool:
        return True

class ObserverStatusInvitation(Event):
    
    def __init__(self, game_id: str, event_data: dict):
        Event.__init__(self, game_id, event_data)

    def activate(self):
        
        self.notifications.append(f"New Event: {self.name}!", 2)
        for i in range(1, len(self.nation_table) + 1):
            self.targets.append(str(i))
        
        self.state = "Current"

    def resolve(self):
        
        self.choices = ["Accept", "Decline"]
        print(f"Available Options: {" or ".join(self.choices)}")
        decision_dict = self._collect_basic_decisions()

        for nation_id, decision in decision_dict.items():
            
            nation = self.nation_table.get(nation_id)
            
            if decision == "Accept":
                new_tag = {
                    "Expire Turn": 99999
                }
                nation.tags["Observer Status"] = new_tag
            
            elif decision == "Decline":
                valid_research = False
                while not valid_research:
                    research_name = input(f"Enter {nation.name} military technology decision: ")
                    valid_research = self._gain_free_research(research_name, nation)
            
            self.nation_table.save(nation)
        
        self.state = "Inactive"

    def has_conditions_met(self) -> bool:
        return True

class PeacetimeRewards(Event):
    
    def __init__(self, game_id: str, event_data: dict):
        Event.__init__(self, game_id, event_data)

    def activate(self):
        
        names = []
        for nation in self.nation_table:
            if self.war_table.at_peace_for_x(nation.id) >= 12:
                self.targets.append(nation.id)
                names.append(nation.name)
        nations_receiving_award_str = ", ".join(names)
        
        self.notifications.append(f"New Event: {self.name}!", 2)
        self.notifications.append(f"Receiving reward: {nations_receiving_award_str}.", 2)
        
        self.state = "Current"

    def resolve(self):
        
        for nation_id in self.targets:
            nation = self.nation_table.get(nation_id)
            valid_research = False
            while not valid_research:
                research_name = input(f"Enter {nation.name} technology decision: ")
                valid_research = self._gain_free_research(research_name, nation)
            self.nation_table.save(nation)

        self.state = "Inactive"

    def has_conditions_met(self) -> bool:

        if not _at_least_x_nations_at_peace_for_y_turns(self.game_id, 1, 12):
            return False
        
        return True

class PowerPlantMeltdown(Event):
    
    def __init__(self, game_id: str, event_data: dict):
        Event.__init__(self, game_id, event_data)

    def activate(self):
        
        for region_id in self.regdata_dict:
            region_improvement = Improvement(region_id, self.game_id)
            if region_improvement.name == "Nuclear Power Plant":
                self.targets.append(region_id)
        random.shuffle(self.targets)
        meltdown_region_id = self.targets.pop()

        nation = self.nation_table.get(str(meltdown_region_id))
        region = Region(meltdown_region_id, self.game_id)
        region_improvement = Improvement(meltdown_region_id, self.game_id)
        region_unit = Unit(meltdown_region_id, self.game_id)

        nation.improvement_counts["Nuclear Power Plant"] -= 1
        region_improvement.clear()
        if region_unit.name is not None:
            nation.unit_counts[region_unit.name] -= 1
            region_unit.clear()
        region.set_fallout(99999)
        nation.update_stockpile("Political Power", 0, overwrite=True)
        
        self.nation_table.save(nation)
        self.notifications.append(f"The {nation.name} Nuclear Power Plant in {meltdown_region_id} has melted down!", 2)
        
        self.state = "Inactive"

    def has_conditions_met(self) -> bool:

        if not _global_count_of_x_improvement_at_least_y(self.game_id, "Nuclear Power Plant", 1):
            return False

        return True

class ShiftingAttitudes(Event):
    
    def __init__(self, game_id: str, event_data: dict):
        Event.__init__(self, game_id, event_data)

    def activate(self):
        
        self.notifications.append(f"New Event: {self.name}!", 2)
        for i in range(1, len(self.nation_table) + 1):
            self.targets.append(str(i))
        
        self.state = "Current"

    def resolve(self):

        choices = ["Change", "Keep"]
        print(f"Available Options: {" or ".join(choices)}")
        decision_dict = self._collect_basic_decisions()

        for nation_id, decision in decision_dict.items():
            
            nation = self.nation_table.get(nation_id)
            
            if decision == "Change":
                new_fp = input(f"Enter new foreign policy: ")
                nation.fp = new_fp
            
            elif decision == "Keep":
                new_tag = {
                    "Political Power Rate": -20,
                    "Expire Turn": self.current_turn_num + self.duration + 1
                }
                nation.tags["Shifting Attitudes"] = new_tag
                valid_research = False
                while not valid_research:
                    research_name = input(f"Enter {nation.name} technology decision: ")
                    valid_research = self._gain_free_research(research_name, nation)
            
            self.nation_table.save(nation)
        
        self.state = "Inactive"

    def has_conditions_met(self) -> bool:

        if _is_first_event(self.game_id):
            return False
        
        return True

class UnitedNationsPeacekeepingMandate(Event):
    
    def __init__(self, game_id: str, event_data: dict):
        Event.__init__(self, game_id, event_data)

    def activate(self):

        for war in self.war_table:
            if war.outcome == "TBD":
                war.end_conflict("White Peace")
                self.notifications.append(f"{war.name} has ended with a white peace due to United Nations Peacekeeping Mandate.", 2)

        self.state = "Inactive"

    def has_conditions_met(self) -> bool:

        if not _at_least_x_ongoing_wars(self.game_id, 3):
            return False
        
        return True

class WidespreadCivilDisorder(Event):
    
    def __init__(self, game_id: str, event_data: dict):
        Event.__init__(self, game_id, event_data)

    def activate(self):

        self.notifications.append(f"New Event: {self.name}!", 2)

        for nation in self.nation_table:
            new_tag = {
                "Expire Turn": self.current_turn_num + self.duration + 1
            }
            nation.tags["Civil Disorder"] = new_tag
            self.nation_table.save(nation)

        self.state = "Active"
        self.duration = self.current_turn_num + self.duration + 1

    def has_conditions_met(self) -> bool:

        if _is_first_event(self.game_id):
            return False
        
        return True

class Embargo(Event):
    
    def __init__(self, game_id: str, event_data: dict):
        Event.__init__(self, game_id, event_data)

    def activate(self):
        
        self.notifications.append(f"New Event: {self.name}!", 2)
        for i in range(1, len(self.nation_table) + 1):
            self.targets.append(str(i))
        
        self.state = "Current"

    def resolve(self):

        print("""Available Options: "# Nation Name" or "Abstain" """)
        self.vote_tally = self._get_votes_nation()
        nation_name = self._determine_vote_winner()

        if nation_name is None:
            self.notifications.append(f"Vote tied. No nation has been embargoed.", 2)
            self.state = "Inactive"
            return
        
        nation = self.nation_table.get(nation_name)
        new_tag = {
            "Expire Turn": self.current_turn_num + self.duration + 1
        }
        nation.tags["Embargo"] = new_tag
        self.nation_table.save(nation)
        
        self.notifications.append(f"Having received {self.vote_tally[nation_name]} votes, {nation_name} has been embargoed", 2)
        
        self.state = "Active"
        self.duration = self.current_turn_num + self.duration + 1     

    def has_conditions_met(self) -> bool:
        return True

class Humiliation(Event):
    
    def __init__(self, game_id: str, event_data: dict):
        Event.__init__(self, game_id, event_data)

    def activate(self):
        
        self.notifications.append(f"New Event: {self.name}!", 2)
        for i in range(1, len(self.nation_table) + 1):
            self.targets.append(str(i))
        
        self.state = "Current"

    def resolve(self):

        print("""Available Options: "# Nation Name" or "Abstain" """)
        self.vote_tally = self._get_votes_nation()
        nation_name = self._determine_vote_winner()

        if nation_name is None:
            self.notifications.append(f"Vote tied. No nation has been humiliated.", 2)
            self.state = "Inactive"
            return

        nation = self.nation_table.get(nation_name)
        new_tag = {
            "No Agenda Research": True,
            "Expire Turn": self.current_turn_num + self.duration + 1
        }
        nation.tags["Humiliation"] = new_tag
        self.nation_table.save(nation)
        
        self.notifications.append(f"Having received {self.vote_tally[nation_name]} votes, {nation_name} has been humiliated.", 2)

        self.state = "Active"
        self.duration = self.current_turn_num + self.duration + 1 

    def has_conditions_met(self) -> bool:
        return True

class ForeignInvestment(Event):
    
    def __init__(self, game_id: str, event_data: dict):
        Event.__init__(self, game_id, event_data)

    def activate(self):
        
        self.notifications.append(f"New Event: {self.name}!", 2)
        for i in range(1, len(self.nation_table) + 1):
            self.targets.append(str(i))
        
        self.state = "Current"

    def resolve(self):

        print("""Available Options: "# Nation Name" or "Abstain" """)
        self.vote_tally = self._get_votes_nation()
        nation_name = self._determine_vote_winner()

        if nation_name is None:
            self.notifications.append(f"Vote tied. No nation will recieve the foreign investment.", 2)
            self.state = "Inactive"
            return

        nation = self.nation_table.get(nation_name)
        new_tag = {
            "Expire Turn": self.current_turn_num + self.duration + 1
        }
        nation.tags["Foreign Investment"] = new_tag
        self.nation_table.save(nation)
        
        self.notifications.append(f"Having received {self.vote_tally[nation_name]} votes, {nation_name} has recieved the foreign investment.", 2)

        self.state = "Active"
        self.duration = self.current_turn_num + self.duration + 1 

    def has_conditions_met(self) -> bool:
        return True

class NominateMediator(Event):
    
    def __init__(self, game_id: str, event_data: dict):
        Event.__init__(self, game_id, event_data)

    def activate(self):
        
        self.notifications.append(f"New Event: {self.name}!", 2)
        for i in range(1, len(self.nation_table) + 1):
            self.targets.append(str(i))
        
        self.state = "Current"

    def resolve(self):

        print("""Available Options: "# Nation Name" or "Abstain" """)
        self.vote_tally = self._get_votes_nation()
        nation_name = self._determine_vote_winner()

        if nation_name is None:
            self.notifications.append(f"Vote tied. No nation has been elected Mediator.", 2)
            self.state = "Inactive"
            return

        nation = self.nation_table.get(nation_name)
        new_tag = {
            "Alliance Political Power Bonus": 0.25,
            "Truces Extended": [],
            "Expire Turn": self.current_turn_num + self.duration + 1
        }
        nation.tags["Mediator"] = new_tag
        self.nation_table.save(nation)

        self.notifications.append(f"Having received {self.vote_tally[nation_name]} votes, {nation_name} has been elected Mediator.", 2)

        self.state = "Active"
        self.duration = self.current_turn_num + self.duration + 1 

    def has_conditions_met(self) -> bool:
        return True

class SharedFate(Event):
    
    def __init__(self, game_id: str, event_data: dict):
        Event.__init__(self, game_id, event_data)

    def activate(self):
        
        self.notifications.append(f"New Event: {self.name}!", 2)
        for i in range(1, len(self.nation_table) + 1):
            self.targets.append(str(i))
        
        self.state = "Current"

    def resolve(self):

        self.choices = ["Cooperation", "Conflict", "Abstain"]
        print(f"Available Options: {" or ".join(self.choices)}")
        self.vote_tally = self._get_votes_option()
        option_name = self._determine_vote_winner()

        if option_name is None:
            self.notifications.append(f"Vote tied. No option was resolved.", 2)
            self.state = "Inactive"
            return

        if option_name == "Cooperation":
            for nation in self.nation_table:
                new_tag = {
                    "Alliance Limit Modifier": 1,
                    "Expire Turn": 99999
                }
                nation.tags["Shared Fate"] = new_tag
                self.nation_table.save(nation)
            self.notifications.append(f"Cooperation won in a {self.vote_tally.get("Cooperation")} - {self.vote_tally.get("Conflict")} decision.", 2)

        elif option_name == "Conflict":
            for nation in self.nation_table:
                new_tag = {
                    "Improvement Income": {
                        "Boot Camp": {
                            "Military Capacity": 1
                        }
                    },
                    "Expire Turn": 99999
                }
                nation.tags["Shared Fate"] = new_tag
                self.nation_table.save(nation)
            self.notifications.append(f"Conflict won in a {self.vote_tally.get("Conflict")} - {self.vote_tally.get("Cooperation")} decision.", 2)

        self.state = "Active"
        self.duration = self.current_turn_num + self.duration + 1 

    def has_conditions_met(self) -> bool:
        return True

class ThreatContainment(Event):
    
    def __init__(self, game_id: str, event_data: dict):
        Event.__init__(self, game_id, event_data)

    def activate(self):
        
        self.notifications.append(f"New Event: {self.name}!", 2)
        for i in range(1, len(self.nation_table) + 1):
            self.targets.append(str(i))
        
        self.state = "Current"

    def resolve(self):

        print("""Available Options: "# Nation Name" or "Abstain" """)
        self.vote_tally = self._get_votes_nation()
        nation_name = self._determine_vote_winner()

        if nation_name is None:
            self.notifications.append(f"Vote tied. No nation has been sanctioned.", 2)
            self.state = "Inactive"
            return
        
        nation = self.nation_table.get(nation_name)
        new_tag = {
            "Military Capacity Rate": -20,
            "Trade Fee Modifier": -1,
            "Expire Turn": self.current_turn_num + self.duration + 1
        }
        nation.tags["Threat Containment"] = new_tag
        self.nation_table.save(nation)

        self.notifications.append(f"Having received {self.vote_tally[nation_name]} votes, {nation_name} has been sanctioned.", 2)

        self.state = "Active"
        self.duration = self.current_turn_num + self.duration + 1

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
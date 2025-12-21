import random

from app.game.games import Games
from app.scenario.scenario import ScenarioInterface as SD
from app import actions
from app.alliance.alliances import Alliances
from app.region import Regions
from app.nation.nation import Nation
from app.nation.nations import Nations, LeaderboardRecordNames
from app.notifications import Notifications
from app.war import Wars

from app import palette


class Event:

    def __init__(self, game_id: str, event_name: str, event_data: dict):

        self.name: str = event_name
        self.type: str = event_data["Type"]
        self.duration: int = event_data["Duration"]
        self.targets: list = event_data.get("Targets", [])
        self.expire_turn: int = event_data.get("Expiration", -1)

        self.game_id = game_id
        self.game = Games.load(self.game_id)
        self.state = -1

        # EVENT STATES
        #  2  event is pending input from players
        #  1  event is active and does not require attention from players
        #  0  event is completed and ready to be archived

    def export(self) -> dict:
        
        return {
            "Name": self.name,
            "Type": self.type,
            "Duration": self.duration,
            "Targets": self.targets,
            "Expiration": self.expire_turn
        }
    
    def run_before(self, actions_dict: dict[str, list]) -> None:
        self.state = 1

    def run_after(self) -> None:
        self.state = 1
    
    def _gain_free_research(self, research_name: str, nation: Nation) -> bool:
        """
        Returns updated playerdata_List and a bool that is True if the research was valid, False otherwise.
        """

        prereq = SD.technologies[research_name].prerequisite
        if prereq is not None and prereq not in nation.completed_research:
            return False

        nation.add_tech(research_name)
        nation.award_research_bonus(research_name)

        return True

    def _collect_basic_decisions(self) -> dict:
        """
        Simple function to collect decisions from players in the terminal.
        """

        decision_dict = {}
        for player_id in self.targets:
            nation = Nations.get(player_id)
            while True:
                decision = input(f"Enter {nation.name} decision: ")
                if decision in self.choices:
                    break
            decision_dict[player_id] = decision
        
        return decision_dict

    def _get_votes_nation(self) -> dict:
        
        vote_tally_dict = {}
    
        for nation_id in self.targets:
            
            nation = Nations.get(nation_id)
            
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
                try:
                    target_nation = Nations.get(target_name)
                except:
                    continue
                
                if target_name in vote_tally_dict:
                    vote_tally_dict[target_name] += vote_count
                else:
                    vote_tally_dict[target_name] = vote_count
                
                nation.update_stockpile("Political Power", -1 * vote_count)
                break
        
        return vote_tally_dict

    def _get_votes_option(self) -> dict[str, int]:

        vote_tally_dict = {}
        
        for nation_id in self.targets:
            
            nation = Nations.get(nation_id)
            
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
    
    def __init__(self, game_id: str, event_name: str, event_data: dict):
        Event.__init__(self, game_id, event_name, event_data)

    def activate(self):

        victim_player_id = Nations.get_random_id()
        victim_nation = Nations.get(victim_player_id)
        self.targets.append(victim_nation.id)

        Notifications.add(f"{victim_nation.name} has been randomly selected as the target for the {self.name} event!", 3)

        self.state = 2

    def resolve(self):
        
        self.choices = ["Find the Perpetrator", "Find a Scapegoat"]
        print(f"Available Options: {" or ".join(self.choices)}")
        decision_dict = self._collect_basic_decisions()

        for nation_id, decision in decision_dict.items():
            
            nation = Nations.get(nation_id)
            
            if decision == "Find the Perpetrator":
                nation.update_stockpile("Political Power", 5)
                self.state = 0
            
            elif decision == "Find a Scapegoat":
                while True:
                    scapegoat_nation_name = input("Enter the nation name to scapegoat: ")
                    try:
                        scapegoat = Nations.get(scapegoat_nation_name)
                        break
                    except:
                        print("Unrecognized nation name, try again.")
                new_tag = {
                    "Combat Roll Bonus": scapegoat.id,
                    "Expire Turn": self.game.turn + self.duration + 1
                }
                nation.tags["Assassination Scapegoat"] = new_tag
                self.state = 1
                self.expire_turn = self.game.turn + self.duration + 1
    
    def has_conditions_met(self) -> bool:
        return True

class CorruptionScandal(Event):
    
    def __init__(self, game_id: str, event_name: str, event_data: dict):
        Event.__init__(self, game_id, event_name, event_data)

    def activate(self):
        
        top_three_economy = Nations.get_top_three("net_income")
        victim_nation_name = top_three_economy[0][0]
        victim_nation = Nations.get(victim_nation_name)
        Notifications.add(f"{victim_nation.name} has been randomly selected as the target for the {self.name} event!", 3)

        new_tag = {
            "Dollars Rate": -20,
            "Political Power Rate": -20,
            "Expire Turn": self.game.turn + self.duration + 1
        }
        victim_nation.tags["Corruption Scandal"] = new_tag

        self.state = 1
        self.expire_turn = self.game.turn + self.duration + 1

    def has_conditions_met(self) -> bool:

        if not _no_ranking_tie(self.game_id, "net_income"):
            return False
        
        return True

class Coup(Event):
    
    def __init__(self, game_id: str, event_name: str, event_data: dict):
        Event.__init__(self, game_id, event_name, event_data)

    def activate(self):
        
        lowest_economy = Nations.get_lowest_in_record("net_income")
        victim_nation_name = lowest_economy[0]
        victim_nation = Nations.get(victim_nation_name)

        old_government = victim_nation.gov
        gov_list = ["Republic", "Technocracy", "Oligarchy", "Totalitarian", "Remnant", "Protectorate", "Military Junta", "Crime Syndicate"]
        gov_list.remove(old_government)
        random.shuffle(gov_list)
        new_government = gov_list.pop()
        
        victim_nation.gov = new_government
        victim_nation.update_stockpile("Political Power", 0, overwrite=True)
        Notifications.add(f"{victim_nation_name}'s {old_government} government has been defeated by a coup. A new {new_government} government has taken power.", 3)

        self.state = 0

    def has_conditions_met(self) -> bool:

        if _is_first_event(self.game_id):
            return False
        
        return True

class DecayingInfrastructure(Event):
    
    def __init__(self, game_id: str, event_name: str, event_data: dict):
        Event.__init__(self, game_id, event_name, event_data)

    def activate(self):

        top_three = Nations.get_top_three("nation_size")
        top_three_ids = set()
        for nation_name, nation_size in top_three:
            temp = Nations.get(nation_name)
            top_three_ids.add(temp.id)

        for region in Regions:
            if region.data.owner_id in top_three_ids and region.improvement.name is not None and region.improvement.name != "Capital":
                decay_roll = random.randint(1, 10)
                if decay_roll >= 9:
                    nation = Nations.get(region.data.owner_id)
                    nation.improvement_counts[region.improvement.name] -= 1
                    Notifications.add(f"{nation.name} {region.improvement.name} in {region.id} has decayed.", 3)
                    region.improvement.clear()

        self.state = 0

    def has_conditions_met(self) -> bool:

        if _is_first_event(self.game_id):
            return False
        
        return True

class Desertion(Event):
    
    def __init__(self, game_id: str, event_name: str, event_data: dict):
        Event.__init__(self, game_id, event_name, event_data)

    def activate(self):

        # retrieve lowest warscore for each nation
        lowest_warscore_dict = {}
        for nation in Nations:
            if Wars.is_at_peace(nation.id):
                continue
            lowest_warscore = 99999
            for war in Wars:
                if war.outcome != "TBD" or nation.id not in war.combatants:
                    continue
                nation_combatant_data = war.get_combatant(nation.id)
                score = war.attackers.total if "Attacker" in nation_combatant_data.role else war.defenders.total
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
        for region_id in Regions:
            region = Regions.load(region_id)
            if region.unit.owner_id not in self.targets:
                continue
            defection_roll = random.randint(1, 10)
            if defection_roll >= 9:
                nation = Nations.get(region.unit.owner_id)
                nation.unit_counts[region.unit.name] -= 1
                Notifications.add(f"{nation.name} {region.unit.name} {region_id} has deserted.", 3)
                region.unit.clear()
        
        self.state = 0

    def has_conditions_met(self) -> bool:

        if not _at_least_x_ongoing_wars(self.game_id, 1):
            return False

        return True

class DiplomaticSummit(Event):
    
    def __init__(self, game_id: str, event_name: str, event_data: dict):
        Event.__init__(self, game_id, event_name, event_data)

    def activate(self):
        
        Notifications.add(f"New Event: {self.name}!", 3)
        for nation in Nations:
            self.targets.append(nation.id)
        
        self.state = 2

    def resolve(self):

        summit_attendance_list = []
        
        self.choices = ["Attend", "Decline"]
        print(f"Available Options: {" or ".join(self.choices)}")
        decision_dict = self._collect_basic_decisions()

        for nation_id, decision in decision_dict.items():
            
            nation = Nations.get(nation_id)
            
            if decision == "Attend":
                nation.update_stockpile("Political Power", 5)
                summit_attendance_list.append(nation.id)
            
            elif decision == "Decline":
                valid_research = False
                while not valid_research:
                    research_name = input(f"Enter {nation.name} military technology decision: ")
                    valid_research = self._gain_free_research(research_name, nation)
        
        if len(summit_attendance_list) < 2:
            self.state = 0
            return

        for nation_id in summit_attendance_list:
            nation = Nations.get(nation_id)
            new_tag = {
                "Expire Turn": self.game.turn + self.duration + 1
            }
            for attendee_id in summit_attendance_list:
                new_tag[f"Cannot Declare War On #{attendee_id}"] = True
            nation.tags["Summit"] = new_tag
        
        self.state = 1
        self.expire_turn = self.game.turn + self.duration + 1

    def has_conditions_met(self) -> bool:
        return True

class ForeignAid(Event):
    
    def __init__(self, game_id: str, event_name: str, event_data: dict):
        Event.__init__(self, game_id, event_name, event_data)

    def activate(self):
        
        for record in LeaderboardRecordNames:
            top_three = Nations.get_top_three(record)
            for nation_name, score in top_three:
                if score != 0 and nation_name not in self.targets:
                    self.targets.append(nation_name)

        for nation_name in self.targets:
            nation = Nations.get(nation_name)
            count = nation.improvement_counts["Settlement"] + nation.improvement_counts["City"]
            if count > 0:
                amount = count * 5
                nation.update_stockpile("Dollars", amount)
                Notifications.add(f"{nation_name} has received {amount} dollars worth of foreign aid.", 3)

        self.state = 0

    def has_conditions_met(self) -> bool:
        return True

class ForeignInterference(Event):
    
    def __init__(self, game_id: str, event_name: str, event_data: dict):
        Event.__init__(self, game_id, event_name, event_data)

    def activate(self):
        
        Notifications.add(f"New Event: {self.name}!", 3)
        for nation in Nations:
            self.targets.append(nation.id)
        
        self.state = 2

    def resolve(self):

        self.choices = ["Accept", "Decline"]
        print(f"Available Options: {" or ".join(self.choices)}")
        decision_dict = self._collect_basic_decisions()

        war_actions: list[actions.WarAction] = []
        for nation_id, decision in decision_dict.items():
            
            nation = Nations.get(nation_id)
            
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

        actions.resolve_war_actions(self.game_id, war_actions)
        self.state = 0

    def has_conditions_met(self) -> bool:

        if _is_first_event(self.game_id):
            return False
        
        return True

class LostNuclearWeapons(Event):
    
    def __init__(self, game_id: str, event_name: str, event_data: dict):
        Event.__init__(self, game_id, event_name, event_data)

    def activate(self):

        victim_player_id = Nations.get_random_id()
        victim_nation = Nations.get(victim_player_id)
        self.targets.append(victim_nation.id)

        Notifications.add(f"{victim_nation.name} has been randomly selected as the target for the {self.name} event!", 3)

        self.state = 2

    def resolve(self):
        
        self.choices = ["Claim", "Scuttle"]
        print(f"Available Options: {" or ".join(self.choices)}")
        decision_dict = self._collect_basic_decisions()

        for nation_id, decision in decision_dict.items():
            
            nation = Nations.get(nation_id)
            
            if decision == "Claim":
                valid_region_id = False
                while not valid_region_id:
                    silo_location_id = input("Enter region id for Missile Silo: ")
                    silo_location_id = silo_location_id.upper()
                    if silo_location_id in set(Regions.ids()):
                        valid_region_id = True
                nation.improvement_counts["Missile Silo"] += 1
                region = Regions.load(valid_region_id)
                region.improvement.set("Missile Silo")
                nation.nuke_count += 3
            
            elif decision == "Scuttle":
                nation.update_stockpile("Research", 15)
            
            Notifications.add(f"{nation.name} chose to {decision.lower()} the old military installation.", 3)
        
        self.state = 0

    def has_conditions_met(self) -> bool:
        return True

class SecurityBreach(Event):
    
    def __init__(self, game_id: str, event_name: str, event_data: dict):
        Event.__init__(self, game_id, event_name, event_data)

    def activate(self):

        top_three = Nations.get_top_three("technology_count")
        victim_nation_name = top_three[0][0]
        self.targets.append(victim_nation_name)

        Notifications.add(f"{victim_nation_name} has suffered a {self.name}!", 3)

        self.state = 2

    def resolve(self):

        victim_name = self.targets[0]
        victim_nation = Nations.get(victim_name)

        for nation in Nations:
            
            if nation.name == victim_name:
                continue

            valid_research = False
            while not valid_research:
                research_name = input(f"Enter {nation.name} technology decision: ")
                if research_name not in victim_nation.completed_research:
                    continue
                valid_research = self._gain_free_research(research_name, nation)

        new_tag = {
            "Research Rate": -20,
            "Expire Turn": self.game.turn + self.duration + 1
        }
        victim_nation.tags["Security Breach"] = new_tag
        
        self.state = 1
        self.expire_turn = self.game.turn + self.duration + 1

    def has_conditions_met(self) -> bool:

        if not _no_ranking_tie(self.game_id, "technology_count"):
            return False
        
        return True

class MarketInflation(Event):
    
    def __init__(self, game_id: str, event_name: str, event_data: dict):
        Event.__init__(self, game_id, event_name, event_data)

    def activate(self):
        self.state = 1
        self.expire_turn = self.game.turn + self.duration + 1

    def has_conditions_met(self) -> bool:
        return True

class MarketRecession(Event):
    
    def __init__(self, game_id: str, event_name: str, event_data: dict):
        Event.__init__(self, game_id, event_name, event_data)

    def activate(self):
        self.state = 1
        self.expire_turn = self.game.turn + self.duration + 1

    def has_conditions_met(self) -> bool:
        return True

class ObserverStatusInvitation(Event):
    
    def __init__(self, game_id: str, event_name: str, event_data: dict):
        Event.__init__(self, game_id, event_name, event_data)

    def activate(self):
        
        Notifications.add(f"New Event: {self.name}!", 3)
        for nation in Nations:
            self.targets.append(nation.id)
        
        self.state = 2

    def resolve(self):
        
        self.choices = ["Accept", "Decline"]
        print(f"Available Options: {" or ".join(self.choices)}")
        decision_dict = self._collect_basic_decisions()

        for nation_id, decision in decision_dict.items():
            
            nation = Nations.get(nation_id)
            
            if decision == "Accept":
                new_tag = {
                    "Political Power Income": 0.5,
                    "Expire Turn": 99999
                }
                nation.tags["Observer Status"] = new_tag
            
            elif decision == "Decline":
                valid_research = False
                while not valid_research:
                    research_name = input(f"Enter {nation.name} military technology decision: ")
                    valid_research = self._gain_free_research(research_name, nation)
        
        self.state = 0

    def has_conditions_met(self) -> bool:
        return True

class PeacetimeRewards(Event):
    
    def __init__(self, game_id: str, event_name: str, event_data: dict):
        Event.__init__(self, game_id, event_name, event_data)

    def activate(self):
        
        names = []
        for nation in Nations:
            if Wars.at_peace_for_x(nation.id) >= 12:
                self.targets.append(nation.id)
                names.append(nation.name)
        nations_receiving_award_str = ", ".join(names)
        
        Notifications.add(f"New Event: {self.name}!", 3)
        Notifications.add(f"Receiving reward: {nations_receiving_award_str}.", 3)
        
        self.state = 2

    def resolve(self):
        
        for nation_id in self.targets:
            nation = Nations.get(nation_id)
            valid_research = False
            while not valid_research:
                research_name = input(f"Enter {nation.name} technology decision: ")
                valid_research = self._gain_free_research(research_name, nation)

        self.state = 0

    def has_conditions_met(self) -> bool:

        if not _at_least_x_nations_at_peace_for_y_turns(self.game_id, 1, 12):
            return False
        
        return True

class PowerPlantMeltdown(Event):
    
    def __init__(self, game_id: str, event_name: str, event_data: dict):
        Event.__init__(self, game_id, event_name, event_data)

    def activate(self):
        
        for region in Regions:
            if region.improvement.name == "Nuclear Power Plant":
                self.targets.append(region.id)
        random.shuffle(self.targets)
        meltdown_region_id = self.targets.pop()

        nation = Nations.get(str(meltdown_region_id))
        region = Regions.load(meltdown_region_id)

        nation.improvement_counts["Nuclear Power Plant"] -= 1
        region.improvement.clear()
        if region.unit.name is not None:
            nation.unit_counts[region.unit.name] -= 1
            region.unit.clear()
        region.data.fallout = 99999
        
        nation.update_stockpile("Political Power", 0, overwrite=True)
        Notifications.add(f"The {nation.name} Nuclear Power Plant in {meltdown_region_id} has melted down!", 3)
        
        self.state = 0

    def has_conditions_met(self) -> bool:

        if not _global_count_of_x_improvement_at_least_y(self.game_id, "Nuclear Power Plant", 1):
            return False

        return True

class ShiftingAttitudes(Event):
    
    def __init__(self, game_id: str, event_name: str, event_data: dict):
        Event.__init__(self, game_id, event_name, event_data)

    def activate(self):
        
        Notifications.add(f"New Event: {self.name}!", 3)
        for nation in Nations:
            self.targets.append(nation.id)
        
        self.state = 2

    def resolve(self):

        self.choices = ["Change", "Keep"]
        print(f"Available Options: {" or ".join(self.choices)}")
        decision_dict = self._collect_basic_decisions()

        for nation_id, decision in decision_dict.items():
            
            nation = Nations.get(nation_id)
            
            if decision == "Change":
                new_fp = input(f"Enter new foreign policy: ")
                nation.fp = new_fp
            
            elif decision == "Keep":
                new_tag = {
                    "Political Power Rate": -20,
                    "Expire Turn": self.game.turn + self.duration + 1
                }
                nation.tags["Shifting Attitudes"] = new_tag
                valid_research = False
                while not valid_research:
                    research_name = input(f"Enter {nation.name} technology decision: ")
                    valid_research = self._gain_free_research(research_name, nation)
        
        self.state = 0

    def has_conditions_met(self) -> bool:

        if _is_first_event(self.game_id):
            return False
        
        return True

class UnitedNationsPeacekeepingMandate(Event):
    
    def __init__(self, game_id: str, event_name: str, event_data: dict):
        Event.__init__(self, game_id, event_name, event_data)

    def activate(self):

        for war in Wars:
            if war.outcome == "TBD":
                war.end_conflict("White Peace")
                Notifications.add(f"{war.name} has ended with a white peace due to United Nations Peacekeeping Mandate.", 3)

        self.state = 0

    def has_conditions_met(self) -> bool:

        if not _at_least_x_ongoing_wars(self.game_id, 3):
            return False
        
        return True

class WidespreadCivilDisorder(Event):
    
    def __init__(self, game_id: str, event_name: str, event_data: dict):
        Event.__init__(self, game_id, event_name, event_data)

    def activate(self):

        Notifications.add(f"New Event: {self.name}!", 3)

        for nation in Nations:
            new_tag = {
                "Expire Turn": self.game.turn + self.duration + 1
            }
            nation.tags["Civil Disorder"] = new_tag

        self.state = 1
        self.expire_turn = self.game.turn + self.duration + 1

    def has_conditions_met(self) -> bool:

        if _is_first_event(self.game_id):
            return False
        
        return True

class Embargo(Event):
    
    def __init__(self, game_id: str, event_name: str, event_data: dict):
        Event.__init__(self, game_id, event_name, event_data)

    def activate(self):
        
        Notifications.add(f"New Event: {self.name}!", 3)
        for nation in Nations:
            self.targets.append(nation.id)
        
        self.state = 2

    def resolve(self):

        print("""Available Options: "# Nation Name" or "Abstain" """)
        self.vote_tally = self._get_votes_nation()
        nation_name = self._determine_vote_winner()

        if nation_name is None:
            Notifications.add(f"Vote tied. No nation has been embargoed.", 3)
            self.state = 0
            return
        
        nation = Nations.get(nation_name)
        new_tag = {
            "Expire Turn": self.game.turn + self.duration + 1
        }
        nation.tags["Embargo"] = new_tag
        
        Notifications.add(f"Having received {self.vote_tally[nation_name]} votes, {nation_name} has been embargoed", 3)
        
        self.state = 1
        self.expire_turn = self.game.turn + self.duration + 1     

    def has_conditions_met(self) -> bool:
        return True

class Humiliation(Event):
    
    def __init__(self, game_id: str, event_name: str, event_data: dict):
        Event.__init__(self, game_id, event_name, event_data)

    def activate(self):
        
        Notifications.add(f"New Event: {self.name}!", 3)
        for nation in Nations:
            self.targets.append(nation.id)
        
        self.state = 2

    def resolve(self):

        print("""Available Options: "# Nation Name" or "Abstain" """)
        self.vote_tally = self._get_votes_nation()
        nation_name = self._determine_vote_winner()

        if nation_name is None:
            Notifications.add(f"Vote tied. No nation has been humiliated.", 3)
            self.state = 0
            return

        nation = Nations.get(nation_name)
        new_tag = {
            "No Agenda Research": True,
            "Expire Turn": self.game.turn + self.duration + 1
        }
        nation.tags["Humiliation"] = new_tag
        
        Notifications.add(f"Having received {self.vote_tally[nation_name]} votes, {nation_name} has been humiliated.", 3)

        self.state = 1
        self.expire_turn = self.game.turn + self.duration + 1 

    def has_conditions_met(self) -> bool:
        return True

class ForeignInvestment(Event):
    
    def __init__(self, game_id: str, event_name: str, event_data: dict):
        Event.__init__(self, game_id, event_name, event_data)

    def activate(self):
        
        Notifications.add(f"New Event: {self.name}!", 3)
        for nation in Nations:
            self.targets.append(nation.id)
        
        self.state = 2

    def resolve(self):

        print("""Available Options: "# Nation Name" or "Abstain" """)
        self.vote_tally = self._get_votes_nation()
        nation_name = self._determine_vote_winner()

        if nation_name is None:
            Notifications.add(f"Vote tied. No nation will recieve the foreign investment.", 3)
            self.state = 0
            return

        nation = Nations.get(nation_name)
        new_tag = {
            "Market Buy Modifier": 0.2,
            "Expire Turn": self.game.turn + self.duration + 1
        }
        nation.tags["Foreign Investment"] = new_tag
        
        Notifications.add(f"Having received {self.vote_tally[nation_name]} votes, {nation_name} has recieved the foreign investment.", 3)

        self.state = 1
        self.expire_turn = self.game.turn + self.duration + 1 

    def has_conditions_met(self) -> bool:
        return True

class NominateMediator(Event):
    
    def __init__(self, game_id: str, event_name: str, event_data: dict):
        Event.__init__(self, game_id, event_name, event_data)

    def activate(self):
        
        Notifications.add(f"New Event: {self.name}!", 3)
        for nation in Nations:
            self.targets.append(nation.id)
        
        self.state = 2

    def resolve(self):

        print("""Available Options: "# Nation Name" or "Abstain" """)
        self.vote_tally = self._get_votes_nation()
        nation_name = self._determine_vote_winner()

        if nation_name is None:
            Notifications.add(f"Vote tied. No nation has been elected Mediator.", 3)
            self.state = 0
            return

        nation = Nations.get(nation_name)
        new_tag = {
            "Alliance Political Power Bonus": 0.25,
            "Truces Extended": [],
            "Expire Turn": self.game.turn + self.duration + 1
        }
        nation.tags["Mediator"] = new_tag

        Notifications.add(f"Having received {self.vote_tally[nation_name]} votes, {nation_name} has been elected Mediator.", 3)

        self.state = 1
        self.expire_turn = self.game.turn + self.duration + 1 

    def has_conditions_met(self) -> bool:
        return True

class SharedFate(Event):
    
    def __init__(self, game_id: str, event_name: str, event_data: dict):
        Event.__init__(self, game_id, event_name, event_data)

    def activate(self):
        
        Notifications.add(f"New Event: {self.name}!", 3)
        for nation in Nations:
            self.targets.append(nation.id)
        
        self.state = 2

    def resolve(self):

        self.choices = ["Cooperation", "Conflict", "Abstain"]
        print(f"Available Options: {" or ".join(self.choices)}")
        self.vote_tally = self._get_votes_option()
        option_name = self._determine_vote_winner()

        if option_name is None:
            Notifications.add(f"Vote tied. No option was resolved.", 3)
            self.state = 0
            return

        if option_name == "Cooperation":
            for nation in Nations:
                new_tag = {
                    "Alliance Limit Modifier": 1,
                    "Expire Turn": 99999
                }
                nation.tags["Shared Fate"] = new_tag
            Notifications.add(f"Cooperation won in a {self.vote_tally.get("Cooperation")} - {self.vote_tally.get("Conflict")} decision.", 3)

        elif option_name == "Conflict":
            for nation in Nations:
                new_tag = {
                    "Improvement Income": {
                        "Boot Camp": {
                            "Military Capacity": 1
                        }
                    },
                    "Expire Turn": 99999
                }
                nation.tags["Shared Fate"] = new_tag
            Notifications.add(f"Conflict won in a {self.vote_tally.get("Conflict")} - {self.vote_tally.get("Cooperation")} decision.", 3)

        self.state = 1
        self.duration = 99999

    def has_conditions_met(self) -> bool:
        return True

class ThreatContainment(Event):
    
    def __init__(self, game_id: str, event_name: str, event_data: dict):
        Event.__init__(self, game_id, event_name, event_data)

    def activate(self):
        
        Notifications.add(f"New Event: {self.name}!", 3)
        for nation in Nations:
            self.targets.append(nation.id)
        
        self.state = 2

    def resolve(self):

        print("""Available Options: "# Nation Name" or "Abstain" """)
        self.vote_tally = self._get_votes_nation()
        nation_name = self._determine_vote_winner()

        if nation_name is None:
            Notifications.add(f"Vote tied. No nation has been sanctioned.", 3)
            self.state = 0
            return
        
        nation = Nations.get(nation_name)
        new_tag = {
            "Military Capacity Rate": -20,
            "Trade Fee Modifier": -1,
            "Expire Turn": self.game.turn + self.duration + 1
        }
        nation.tags["Threat Containment"] = new_tag

        Notifications.add(f"Having received {self.vote_tally[nation_name]} votes, {nation_name} has been sanctioned.", 3)

        self.state = 1
        self.expire_turn = self.game.turn + self.duration + 1

    def has_conditions_met(self) -> bool:
        return True

class ForeignInvasion(Event):
    
    def __init__(self, game_id: str, event_name: str, event_data: dict):
        Event.__init__(self, game_id, event_name, event_data)

    def activate(self):
        
        Notifications.add(f"New Event: {self.name}!", 3)

        region_id_list = Regions.ids()
        invasion_point_id = None

        while True:
            
            invasion_point_id = random.choice(region_id_list)
            region = Regions.load(invasion_point_id)
            is_near_capital = any(adj_region.improvement.name == "Capital" for adj_region in region.graph.iter_adjacent_regions())
            if region.graph.is_edge and region.improvement.name != "Capital" and not is_near_capital:
                break
        
        color_candidates = list(palette.normal_to_occupied.keys())
        for nation in Nations:
            color_candidates.remove(nation.color)

        Nations.create("99", "NULL")
        foreign_invasion_nation = Nations.get("99")
        foreign_invasion_nation.color = random.choice(color_candidates)
        foreign_invasion_nation.name = "Foreign Adversary"
        foreign_invasion_nation.gov = "Foreign Nation"
        foreign_invasion_nation.fp = "Hostile"

        # note - all war justifications are set to null because this is not a conventional war
        Wars.create("99", "1", "NULL", [])
        war = Wars.get("Foreign Invasion")
        for nation in Nations:
            if nation.id == "1":
                combatant = war.get_combatant(nation.id)
                combatant.justification = "NULL"
            else:
                war.add_combatant(nation, "Secondary Defender", "N/A")
                combatant = war.get_combatant(nation.id)
                combatant.justification = "NULL"

        unit_name = self._foreign_invasion_determine_unit()
        invasion_point = Regions.load(invasion_point_id)
        self._foreign_invasion_initial_spawn(invasion_point_id, unit_name)
        for adj_id in invasion_point.graph.adjacent_regions:
            self._foreign_invasion_initial_spawn(adj_id, unit_name)
        
        self.state = 1
        self.expire_turn = self.game.turn + self.duration + 1

    def run_before(self, actions_dict: dict[str, list]) -> None:
        
        # generate movement actions
        destination_dict = {}
        for region in Regions:
            if region.unit.name is None or region.unit.owner_id != "99":
                continue
            ending_region_id, priority = self._foreign_invasion_calculate_target_region(list(region.graph.adjacent_regions.keys()), destination_dict)
            destination_dict[ending_region_id] = priority
            if ending_region_id is None:
                continue
            # foreign invasion always moves each unit one region at a time
            movement_action_str = f"Move {region.id}-{ending_region_id}"
            actions_dict["UnitMoveAction"].append(actions.UnitMoveAction(self.game_id, "99", movement_action_str))
        
        # generate deployment actions
        if self.game.turn % 4 == 0:
            Notifications.add("The Foreign Invasion has received reinforcements.", 3)
            for region in Regions:
                if region.data.owner_id == "99" and region.data.occupier_id == "0":
                    unit_name = self._foreign_invasion_determine_unit()
                    deploy_action_str = f"Deploy {unit_name} {region.id}"
                    actions_dict["UnitDeployAction"].append(actions.UnitDeployAction(self.game_id, "99", deploy_action_str))

        self.state = 1

    def run_after(self) -> None:
        
        foreign_invasion_nation = Nations.get("99")
                    
        # Foreign Invasion ends if no remaining units
        invasion_unit_count = 0
        for unit_name, count in foreign_invasion_nation.unit_counts.items():
            invasion_unit_count += count
        if invasion_unit_count == 0:
            self._foreign_invasion_end()
            self.state = 0
            return
        
        # Foreign Invasion ends if no unoccupied reinforcement regions
        invasion_unoccupied_count = 0
        for region in Regions:
            if region.data.owner_id == "99" and region.data.occupier_id == "0":
                invasion_unoccupied_count += 1
        if invasion_unoccupied_count == 0:
            self._foreign_invasion_end()
            self.state = 0
            return

        self.state = 1

    def has_conditions_met(self) -> bool:

        if _is_first_event(self.game_id):
            return False
        
        if not _no_major_events(self.game_id):
            return False
        
        return True
    
    def _foreign_invasion_determine_unit(self) -> str:

        if self.game.turn >= 40:
            return "Main Battle Tank"
        elif self.game.turn >= 32:
            return "Special Forces"
        elif self.game.turn >= 24:
            return "Mechanized Infantry"
        
        return "Infantry"
    
    def _foreign_invasion_initial_spawn(self, region_id: str, unit_name: str) -> None:

        region = Regions.load(region_id)

        if region.unit.name is not None:
            # remove old unit
            if region.unit.owner_id != "0":
                temp = Nations.get(region.unit.owner_id)
                temp.unit_counts[region.unit.name] -= 1
            region.unit.clear()

        if region.improvement.name is not None:
            # remove old improvement
            if region.data.owner_id != "0":
                temp = Nations.get(region.data.owner_id)
                temp.improvement_counts[region.improvement.name] -= 1
            region.improvement.clear()

        region.data.owner_id = "99"
        region.data.occupier_id = "0"
        region.unit.set(unit_name, "99")

        foreign_nation = Nations.get("99")
        foreign_nation.unit_counts[unit_name] += 1

    def _foreign_invasion_calculate_target_region(self, adjacency_list: list, destination_dict: dict) -> tuple:
        """
        Function that contains Foreign Invasion attack logic.
        Designed to find path of least resistance but has no care for the health of its own units.
        """

        # TODO: make movement smarter as it currently can only "see" one region away so the invasion is stumbling around blind
        
        target_region_id = None
        target_region_health = 0
        target_region_priority = -1

        while adjacency_list != []:

            # get random adjacent region
            index = random.randrange(len(adjacency_list))
            adjacent_region_id = adjacency_list.pop(index)

            # get data from region
            region = Regions.load(adjacent_region_id)
            candidate_region_priority = 0
            candidate_region_health = 0
            
            # increase priority based on control data
            # occupied friendly is the highest priority
            if region.data.owner_id == "99" and region.data.occupier_id != "0":
                candidate_region_priority += 10
            # unoccupied unclaimed region
            elif region.data.owner_id == "0" and region.data.occupier_id != "99":
                candidate_region_priority += 4
            # occupied unclaimed region
            elif region.data.owner_id == "0":
                candidate_region_priority += 2
            # friendly unoccupied region
            elif region.data.owner_id == "99":
                candidate_region_priority += 0
            # unoccupied enemy region
            elif region.data.owner_id != "99" and region.data.occupier_id != "99":
                candidate_region_priority += 8
            # occupied enemy region
            elif region.data.owner_id != "99":
                candidate_region_priority += 6
            
            # increase priority by one if there is a hostile unit
            if region.unit.name != None and region.unit.owner_id != "0":
                candidate_region_priority += 1

            # try to prevent units from tripping over each other on unclaimed regions and friendly unoccupied regions
            if adjacent_region_id in destination_dict and (candidate_region_priority == 0 or candidate_region_priority == 2 or candidate_region_priority == 4):
                continue
            
            # calculate region health
            if region.improvement.name != None and region.improvement.health != "99" and region.data.owner_id != "99" and region.data.occupier_id != "99":
                candidate_region_health += region.improvement.health
            if region.unit.name != None and region.unit.owner_id != "0":
                candidate_region_health += region.unit.health
            
            #check if candidate region is an easier or higher priority target
            if candidate_region_priority > target_region_priority:
                target_region_id = adjacent_region_id
                target_region_health = candidate_region_health
                target_region_priority = candidate_region_priority
            elif candidate_region_priority == target_region_priority and candidate_region_health < target_region_health:
                target_region_id = adjacent_region_id
                target_region_health = candidate_region_health
                target_region_priority = candidate_region_priority
        
        return target_region_id, target_region_priority

    def _foreign_invasion_end(self):

        foreign_invasion_nation = Nations.get("99")
    
        for region in Regions:
            
            if region.data.owner_id == "99":
                region.data.owner_id = "0"
                region.data.occupier_id = "0"
            elif region.data.occupier_id == "99":
                region.data.occupier_id = "0"
            
            if region.unit.owner_id == "99":
                foreign_invasion_nation.unit_counts[region.unit.name] -= 1
                region.unit.clear()

            war = Wars.get("Foreign Invasion")
            war.end = self.game.turn
            war.outcome = "White Peace"

class Pandemic(Event):
    
    def __init__(self, game_id: str, event_name: str, event_data: dict):
        Event.__init__(self, game_id, event_name, event_data)
        self.intensify: int = event_data.get("Intensify Value", -1)
        self.spread: int = event_data.get("Spread Value", -1)
        self.cure_current: int = event_data.get("Completed Cure Research", -1)
        self.cure_threshold: int = event_data.get("Needed Cure Research", 99999)
        self.closed_borders: list = event_data.get("Closed Borders List", [])

    def activate(self):
        
        Notifications.add(f"New Event: {self.name}!", 3)
            
        self.intensify = random.randint(3, 9)
        self.spread = random.randint(3, 9)
        self.cure_current = 0
        self.cure_threshold = len(Nations) * 50
        self.closed_borders = []
        origin_region_id = random.choice(Regions.ids())
        
        region = Regions.load(origin_region_id)
        region.data.infection += 1
        
        self.state = 1
        self.expire_turn = 99999

    def run_after(self) -> None:
        
        if self.cure_current >= self.cure_threshold:
            
            # run pandemic decline procedure
            for region in Regions:
                region.data.infection -= 1

        else:

            # conduct intensify rolls
            for region in Regions:
                if region.data.infection > 0 and region.data.infection < 10:
                    # intensify check
                    intensify_roll = random.randint(1, 10)
                    if intensify_roll < self.intensify:
                        continue
                    # intensify more if near capital or city
                    if region.check_for_adjacent_improvement(improvement_names = {'Capital', 'City'}):
                        region.data.infection += 2
                    else:
                        region.data.infection += 1

            # get a list of regions infected before spreading starts
            infected_regions = []
            for region in Regions:
                if region.data.infection > 0:
                    infected_regions.append(region.id)

            # conduct spread roles
            for region_id in infected_regions:
                region = Regions.load(region_id)
                if region.data.infection == 0:
                    continue
                for adjacent_region in region.graph.iter_adjacent_regions():
                    adjacent_owner_id = adjacent_region.data.owner_id
                    # spread only to regions that are not yet infected
                    if adjacent_region.data.infection != 0:
                        continue
                    spread_roll = random.randint(1, 20)
                    # spread attempt
                    if not region.data.quarantine or (region.data.owner_id != adjacent_owner_id and adjacent_owner_id in self.closed_borders):
                        if spread_roll == 20:
                            adjacent_region.data.infection += 1
                    else:
                        if spread_roll >= self.spread:
                            adjacent_region.data.infection += 1

        # sum up total infection scores
        unowned_infection = 0
        infection_scores = [0] * len(Nations)
        for region in Regions:
            if region.data.owner_id != "0" and region.data.owner_id <= len(infection_scores):
                infection_scores[int(region.data.owner_id) - 1] += region.data.infection
            else:
                unowned_infection += region.data.infection
        # check if pandemic has been eradicated
        infection_total = sum(infection_scores) + unowned_infection
        if infection_total == 0:
            for region in Regions:
                region.data.quarantine = False
            Notifications.add("The pandemic has been eradicated!", 3)
            self.state = 0
            return
        
        # print diplomacy log messages
        cure_percentage = float(self.cure_current / self.cure_threshold)
        cure_percentage = round(cure_percentage, 2)
        if infection_total != 0:
            if cure_percentage >= 0.5:
                Notifications.add(f"Pandemic intensify value: {self.intensify}", 3)
                Notifications.add(f"Pandemic spread value: {self.spread}", 3)
            if cure_percentage >= 0.75:
                for nation in Nations:
                    score = infection_scores[int(nation.id) - 1]
                    Notifications.add(f"{nation.name} pandemic infection score: {score}", 3)
            if cure_percentage < 1:
                Notifications.add(f"Pandemic cure research progress: {self.cure_current}/{self.cure_threshold}", 3)
            else:
                Notifications.add(f"Pandemic cure research has been completed! The pandemic is now in decline.", 3)

        self.state = 1

    def export(self) -> dict:
        
        return {
            "Name": self.name,
            "Type": self.type,
            "Duration": self.duration,
            "Targets": self.targets,
            "Expiration": self.expire_turn,
            "Intensify Value": self.intensify,
            "Spread Value": self.spread,
            "Completed Cure Research": self.cure_current,
            "Needed Cure Research": self.cure_threshold,
            "Closed Borders List": self.closed_borders
        }

    def has_conditions_met(self) -> bool:

        if _is_first_event(self.game_id):
            return False
        
        if not _no_major_events(self.game_id):
            return False
        
        return True

class FaustianBargain(Event):
    
    def __init__(self, game_id: str, event_name: str, event_data: dict):
        Event.__init__(self, game_id, event_name, event_data)

    def activate(self):
        
        Notifications.add(f"New Event: {self.name}!", 3)
        for nation in Nations:
            self.targets.append(nation.id)
        
        self.state = 2

    def resolve(self):

        candidates_list = []
        
        self.choices = ["Accept", "Decline"]
        print(f"Available Options: {" or ".join(self.choices)}")
        decision_dict = self._collect_basic_decisions()

        for player_id, choice in decision_dict.items():
            nation = Nations.get(player_id)
            if choice == "Accept" and nation.improvement_counts["Capital"] > 0:
                candidates_list.append(player_id)
            else:
                nation.update_stockpile("Political Power", 5)

        if len(candidates_list) == 0:
            Notifications.add("No nation took the Faustian Bargain. collaborate with the foreign nation.", 3)
            self.state = 0
            return
        
        random.shuffle(candidates_list)
        nation_id = candidates_list.pop()
        nation = Nations.get(nation_id)

        new_tag = {
            "Expire Turn": 99999,
            "No Agenda Research": True
        }
        for resource_name in nation._resources:
            if resource_name not in ["Political Power", "Military Capacity"]:
                new_tag[f"{resource_name} Rate"] = 20
        nation.tags["Faustian Bargain"] = new_tag

        for alliance in Alliances:
            if nation.name in alliance.current_members:
                alliance.remove_member(nation.name)

        Notifications.add(f"{nation.name} took the Faustian Bargain and will collaborate with the foreign nation.", 3)

        self.state = 1
        self.duration = 99999

    def run_after(self) -> None:
        
        # identify collaborator
        for nation in Nations:
            if "Faustian Bargain" in nation.tags:
                break
        
        # check if collaborator has been defeated (no capital)
        if nation.improvement_counts["Capital"] == 0:
            del nation.tags["Faustian Bargain"]
            self.state = 0
            Notifications.add(f"{self.name} event has ended.", 3)
            return

        self.state = 1

    def has_conditions_met(self) -> bool:

        if _is_first_event(self.game_id):
            return False
        
        if not _no_major_events(self.game_id):
            return False
        
        return True

def load_event(game_id: str, event_name: str, event_data: dict | None) -> any:
    """
    Creates an event object based on the event name.

    Params:
        game_id (str): Game ID string.
        event_name (str): Event name string.
        event_data (dict | None): Event data.
        temp (bool): If set to True, the event object will not load any game data.

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

    if event_name not in events:
        raise Exception(f"Error: {event_name} event not recognized.")

    if event_data is None:
        sd_event = SD.events[event_name]
        event_data = {
            "Type": sd_event.type,
            "Duration": sd_event.duration
        }

    return events[event_name](game_id, event_name, event_data)
    
def _is_first_event(game_id: str) -> bool:

    game = Games.load(game_id)
    
    already_chosen_events = set(game.inactive_events) | set(key for key in game.active_events)

    if len(already_chosen_events) != 0:
        return False
    
    return True

def _no_major_events(game_id: str) -> bool:

    game = Games.load(game_id)
    
    already_chosen_events = set(game.inactive_events) | set(key for key in game.active_events)
   
    for event_name, event_data in SD.events:
        if event_name in already_chosen_events and event_data.type == "Major Event":
            return False
        
    return True

def _no_ranking_tie(game_id: str, ranking: str) -> bool:

    top_three = Nations.get_top_three(ranking)
    if top_three[0][1] == top_three[1][1]:
        return False
    
    return True

def _at_least_x_ongoing_wars(game_id: str, count: int) -> bool:

    ongoing_war_count = 0
    for war in Wars:
        if war.outcome == "TBD":
            ongoing_war_count += 1
    
    if ongoing_war_count < count:
        return False
    
    return True

def _at_least_x_nations_at_peace_for_y_turns(game_id: str, nation_count: int, turn_count: int) -> bool:

    at_peace_count = 0
    for nation in Nations:
        if Wars.at_peace_for_x(nation.id) >= turn_count:
            at_peace_count += 1
    
    if at_peace_count < nation_count:
        return False
    
    return True

def _global_count_of_x_improvement_at_least_y(game_id: str, improvement_name: str, count: int) -> bool:

    global_total = 0
    for nation in Nations:
        global_total += nation.improvement_counts[improvement_name]
    
    if global_total < count:
        return False
    
    return True
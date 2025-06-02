import ast
import csv
import json
import random

from app import core
from app import palette
from app.region import Region
from app.improvement import Improvement
from app.unit import Unit
from app.nationdata import Nation
from app.nationdata import NationTable
from app.alliance import AllianceTable
from app.war import WarTable
from app.notifications import Notifications
from app import actions


def trigger_event(game_id: str) -> None:
    """
    Activates and resolves a random event.
    """

    # load active_games.json
    with open('active_games.json', 'r') as json_file:
        active_games_dict = json.load(json_file)

    # get list of events already used
    already_chosen_events= set(active_games_dict[game_id]["Inactive Events"]) | set(key for key in active_games_dict[game_id]["Active Events"])

    # filter out inelligable events
    events = []
    for event_name, event_details in EVENT_DICT.items():
        if event_name in already_chosen_events:
            continue
        if not _is_valid(game_id, event_details["Conditions"], already_chosen_events):
            continue
        events.append(event_name)
    
    # select and initiate random event
    chosen_event = random.choice(events)
    print(f"Triggering {chosen_event} event...")
    initiate_event(game_id, chosen_event, active_games_dict)

    # save changes to active_games.json
    with open('active_games.json', 'w') as json_file:
        json.dump(active_games_dict, json_file, indent=4)

def initiate_event(game_id: str, chosen_event: str, active_games_dict: dict) -> None:
    """
    Initiates the chosen event. If it is an instant resolution event, it will be fully resolved.
    """

    # get game data
    nation_table = NationTable(game_id)
    war_table = WarTable(game_id)
    notifications = Notifications(game_id)
    current_turn_num = core.get_current_turn_num(game_id)
    with open(f'gamedata/{game_id}/regdata.json', 'r') as json_file:
        regdata_dict = json.load(json_file)

    match chosen_event:

        case "Assassination":
            # select victim
            victim_player_id = random.randint(1, len(nation_table)) 
            victim_nation = nation_table.get(str(victim_player_id))
            notifications.append(f"{victim_nation.name} has been randomly selected for the {chosen_event} event!", 2)
            # save to Current Event key to be activated later
            active_games_dict[game_id]["Current Event"][chosen_event] = [victim_player_id]

        case "Corruption Scandal":
            # select victim
            top_three_economy = nation_table.get_top_three("netIncome")
            victim_nation_name = top_three_economy[0][0]
            victim_nation = nation_table.get(victim_nation_name)
            notifications.append(f"{victim_nation.name} has been randomly selected for the {chosen_event} event!", 2)
            # resolve event now
            new_tag = {}
            new_tag["Dollars Rate"] = -20
            new_tag["Political Power Rate"] = -20
            new_tag["Expire Turn"] = current_turn_num + EVENT_DICT[chosen_event]["Duration"] + 1
            victim_nation.tags["Corruption Scandal"] = new_tag
            nation_table.save(victim_nation)
            # save to active events list
            active_games_dict[game_id]["Active Events"][chosen_event] = current_turn_num + EVENT_DICT[chosen_event]["Duration"] + 1
        
        case "Coup":
            # select victim
            lowest_economy = nation_table.get_lowest_in_record("netIncome")
            victim_nation_name = lowest_economy[0]
            victim_nation = nation_table.get(victim_nation_name)
            # resolve event now
            old_government = victim_nation.gov
            gov_list = ['Republic', 'Technocracy', 'Oligarchy', 'Totalitarian', 'Remnant', 'Protectorate', 'Military Junta', 'Crime Syndicate']
            gov_list.remove(old_government)
            random.shuffle(gov_list)
            new_government = gov_list.pop()
            victim_nation.gov = new_government
            victim_nation.update_stockpile("Political Power", 0, overwrite=True)
            nation_table.save(victim_nation)
            notifications.append(f"{victim_nation_name}'s {old_government} government has been defeated by a coup. A new {new_government} government has taken power.", 2)
            # save to inactive events list
            active_games_dict[game_id]["Inactive Events"].append(chosen_event)
        
        case "Decaying Infrastructure":
            # select victims
            top_three = nation_table.get_top_three("nationSize")
            top_three_ids = set()
            for nation_name, nation_size in top_three:
                temp = nation_table.get(nation_name)
                top_three_ids.add(temp.id)
            # resolve event now
            for region_id in regdata_dict:
                region_improvement = Improvement(region_id, game_id)
                if str(region_improvement.owner_id) in top_three_ids and region_improvement.name is not None and region_improvement.name != "Capital":
                    decay_roll = random.randint(1, 10)
                    if decay_roll >= 9:
                        nation = nation_table.get(str(region_improvement.owner_id))
                        nation.improvement_counts[region_improvement.name] -= 1
                        nation_table.save(nation)
                        notifications.append(f"{victim_nation_name} {region_improvement.name} in {region_id} has decayed.", 2)
                        region_improvement.clear()
            # save to inactive events list
            active_games_dict[game_id]["Inactive Events"].append(chosen_event)

        case "Desertion":
            # get data on all nations actively at war
            defection_victims_dict = {}
            for nation in nation_table:
                if war_table.is_at_peace(nation.id):
                    continue
                defection_victims_entry = {}
                defection_victims_entry["lowestScore"] = 99999
                for war in war_table:
                    if war.outcome != "TBD" or nation.id not in war.combatants:
                        continue
                    # check if this war is the lowest
                    nation_combatant_data = war.get_combatant(nation.id)
                    if 'Attacker' in nation_combatant_data.role:
                        score = war.attacker_total
                    else:
                        score = war.defender_total
                    if score < defection_victims_entry["lowestScore"]:
                        defection_victims_entry["lowestScore"] = score
                defection_victims_dict[nation.id] = defection_victims_entry
            # select victims
            min_value = min(entry["lowestScore"] for entry in defection_victims_dict.values())
            filtered_dict = {}
            for nation_id, defection_data in defection_victims_dict.items():
                if defection_data["lowestScore"] == min_value:
                    filtered_dict[nation_id] = defection_data
            defection_victims_dict = filtered_dict
            # resolve event now
            for region_id in regdata_dict:
                region_unit = Unit(region_id, game_id)
                if region_unit.owner_id in defection_victims_dict:
                    defection_roll = random.randint(1, 10)
                    if defection_roll >= 9:
                        nation = nation_table.get(str(region_unit.owner_id))
                        nation.unit_counts[region_unit.name] -= 1
                        nation_table.save(nation)
                        notifications.append(f"{nation.name} {unit_name} {region_id} has deserted.", 2)
                        region_unit.clear()
            # save to inactive events list
            active_games_dict[game_id]["Inactive Events"].append(chosen_event)

        case "Diplomatic Summit":
            notifications.append(f"New Event: {chosen_event}!", 2)
            _save_as_standard_delayed_event(game_id, chosen_event, active_games_dict, nation_table)

        case "Foreign Aid":
            # select nations that will benefit from this event
            affected_players = set()
            for record_name in ["militaryStrength", "nationSize", "netIncome", "researchCount", "transactionCount"]:
                top_three = nation_table.get_top_three(record_name)
                for nation_name, score in top_three:
                    if score != 0:
                        affected_players.add(nation_name) 
            # resolve event now
            for nation_name in affected_players:
                nation = nation_table.get(nation_name)
                count = nation.improvement_counts["City"]
                if count > 0:
                    nation.update_stockpile("Dollars", count * 5)
                    notifications.append(f"{nation_name} has received {count * 5} dollars worth of foreign aid.", 2)
            # save to inactive events list
            active_games_dict[game_id]["Inactive Events"].append(chosen_event)

        case "Foreign Interference":
            notifications.append(f"New Event: {chosen_event}!", 2)
            active_games_dict = _save_as_standard_delayed_event(game_id, chosen_event, active_games_dict, nation_table)

        case "Lost Nuclear Weapons":
            # select victim
            victim_player_id = random.randint(1, len(nation_table)) 
            victim_nation = nation_table.get(str(victim_player_id))
            notifications.append(f"{victim_nation.name} has been randomly selected for the {chosen_event} event!", 2)
            #save to Current Event key to be activated later
            active_games_dict[game_id]["Current Event"][chosen_event] = [victim_player_id]

        case "Security Breach":
            top_three = nation_table.get_top_three("researchCount")
            victim_nation_name = top_three[0][0]
            notifications.append(f"{victim_nation_name} has suffered a {chosen_event}!", 2)
            #save to Current Event key to be activated later
            active_games_dict[game_id]["Current Event"][chosen_event] = [victim_player_id]

        case "Market Inflation":
            # save as an active event
            active_event_dict = {}
            active_games_dict[game_id]["Active Events"][chosen_event] = current_turn_num + EVENT_DICT[chosen_event]["Duration"] + 1
        
        case "Market Recession":
            # save as an active event
            active_event_dict = {}
            active_games_dict[game_id]["Active Events"][chosen_event] = current_turn_num + EVENT_DICT[chosen_event]["Duration"] + 1

        case "Observer Status Invitation":
            notifications.append(f"New Event: {chosen_event}!", 2)
            active_games_dict = _save_as_standard_delayed_event(game_id, chosen_event, active_games_dict, nation_table)

        case "Peacetime Rewards":
            effected_player_ids = []
            names = []
            for nation in nation_table:
                if war_table.at_peace_for_x(nation.id) >= 12:
                    effected_player_ids.append(nation.id)
                    names.append(nation.name)
            nations_receiving_award_str = ", ".join(names)
            notifications.append(f"New Event: {chosen_event}!", 2)
            notifications.append(f"Receiving reward: {nations_receiving_award_str}.", 2)
            # save to Current Event key to be activated later
            active_games_dict[game_id]["Current Event"][chosen_event] = effected_player_ids

        case "Power Plant Meltdown":
            # select regions with a nuclear power plant
            meltdown_candidates = set()
            for region_id in regdata_dict:
                region_improvement = Improvement(region_id, game_id)
                if region_improvement.name == "Nuclear Power Plant":
                    meltdown_candidates.add(region_id)
            # resolve event now
            random.shuffle(meltdown_candidates)
            meltdown_region_id = meltdown_candidates.pop()
            nation = nation_table.get(str(meltdown_region_id))
            region = Region(meltdown_region_id, game_id)
            region_improvement = Improvement(meltdown_region_id, game_id)
            region_unit = Unit(meltdown_region_id, game_id)
            nation.improvement_counts["Nuclear Power Plant"] -= 1
            region_improvement.clear()
            if region_unit.name is not None:
                nation.unit_counts[region_unit.name] -= 1
                region_unit.clear()
            region.set_fallout(99999)
            nation.update_stockpile("Political Power", 0, overwrite=True)
            nation_table.save(nation)
            notifications.append(f'The {nation.name} Nuclear Power Plant in {meltdown_region_id} has melted down!', 2)
            # save to inactive events list
            active_games_dict[game_id]["Inactive Events"].append(chosen_event)

        case "Shifting Attitudes":
            notifications.append(f"New Event: {chosen_event}!", 2)
            active_games_dict = _save_as_standard_delayed_event(game_id, chosen_event, active_games_dict, nation_table)

        case "United Nations Peacekeeping Mandate":
            # resolve event now
            for war in war_table:
                if war.outcome == "TBD":
                    war.end_conflict("White Peace")
                    notifications.append(f"{war.name} has ended with a white peace due to United Nations Peacekeeping Mandate.", 2)
            # save to inactive events list
            active_games_dict[game_id]["Inactive Events"].append(chosen_event)
        
        case "Widespread Civil Disorder":
            # resolve event now
            notifications.append(f"New Event: {chosen_event}!", 2)
            for nation in nation_table:
                new_tag = {}
                new_tag["Expire Turn"] = current_turn_num + EVENT_DICT[chosen_event]["Duration"] + 1
                nation.tags["Civil Disorder"] = new_tag
                nation_table.save(nation)
            # save as an active event
            active_games_dict[game_id]["Active Events"][chosen_event] = current_turn_num + EVENT_DICT[chosen_event]["Duration"] + 1
        
        case "Embargo":
            notifications.append(f"New Event: {chosen_event}!", 2)
            active_games_dict = _save_as_standard_delayed_event(game_id, chosen_event, active_games_dict, nation_table)

        case "Humiliation":
            notifications.append(f"New Event: {chosen_event}!", 2)
            active_games_dict = _save_as_standard_delayed_event(game_id, chosen_event, active_games_dict, nation_table)

        case "Foreign Investment":
            notifications.append(f"New Event: {chosen_event}!", 2)
            active_games_dict = _save_as_standard_delayed_event(game_id, chosen_event, active_games_dict, nation_table)

        case "Nominate Mediator":
            notifications.append(f"New Event: {chosen_event}!", 2)
            active_games_dict = _save_as_standard_delayed_event(game_id, chosen_event, active_games_dict, nation_table)

        case "Shared Fate":
            notifications.append(f"New Event: {chosen_event}!", 2)
            active_games_dict = _save_as_standard_delayed_event(game_id, chosen_event, active_games_dict, nation_table)

        case "Threat Containment":
            notifications.append(f"New Event: {chosen_event}!", 2)
            active_games_dict = _save_as_standard_delayed_event(game_id, chosen_event, active_games_dict, nation_table)

        case "Foreign Invasion":
            
            notifications.append(f"New Event: {chosen_event}!", 2)

            # randomly determine starting location (must be on edge of map)
            region_id_list = list(regdata_dict.keys())
            while True:
                
                invasion_point_id = random.choice(region_id_list)
                region = Region(invasion_point_id, game_id)
                region_improvement = Improvement(invasion_point_id, game_id)
                
                # must be on map edge
                if not region.is_edge:
                    continue
                
                # cannot spawn on or near a capital improvement
                if region_improvement.name == "Capital":
                    continue
                is_near_capital = any(Improvement(adj_id, game_id).name == "Capital" for adj_id in region.adjacent_regions)
                if is_near_capital:
                    continue
                
                # terminate loop - valid starting location found
                break
            
            # create foreign adversary nation
            color_candidates = list(palette.normal_to_occupied.keys())
            for nation in nation_table:
                color_candidates.remove(nation.color)
            nation_table.create("99", "NULL")
            foreign_invasion_nation = nation_table.get("99")
            foreign_invasion_nation.color = random.choice(color_candidates)
            foreign_invasion_nation.name = "Foreign Adversary"
            foreign_invasion_nation.gov = "Foreign Nation"
            foreign_invasion_nation.fp = "Hostile"
            nation_table.save(foreign_invasion_nation)

            # create war
            # note - all war justifications are set to null because this is not a conventional war
            war = war_table.create("99", "1", "NULL", [])
            for nation in nation_table:
                if nation.id == "1":
                    combatant = war.get_combatant(nation.id)
                    combatant.justification = "NULL"
                    war.save_combatant(combatant)
                else:
                    combatant = war.add_combatant(nation, "Secondary Defender", "N/A")
                    combatant.justification = "NULL"
                    war.save_combatant(combatant)
            war_table.save(war)

            # summon initial invasion
            unit_name = _foreign_invasion_unit(current_turn_num)
            invasion_point = Region(invasion_point_id, game_id)
            _foreign_invasion_initial_spawn(game_id, invasion_point_id, unit_name, nation_table)
            for adj_id in invasion_point.adjacent_regions:
                _foreign_invasion_initial_spawn(game_id, adj_id, unit_name, nation_table)
            
            # save as an active event
            active_games_dict[game_id]["Active Events"][chosen_event] = current_turn_num + EVENT_DICT[chosen_event]["Duration"] + 1

        case "Pandemic":
            
            notifications.append(f"New Event: {chosen_event}!", 2)
            
            # randomly generate pandemic properties
            intensify_roll = random.randint(3, 9)
            spread_roll = random.randint(3, 9)
            origin_region_id = random.choice(list(regdata_dict.keys()))
            
            # resolve event now
            region = Region(origin_region_id, game_id)
            region.add_infection()
            
            # save as an active event
            active_event_dict = {
                "Intensify Value": intensify_roll,
                "Spread Value": spread_roll,
                "Completed Cure Research": 0,
                "Needed Cure Research": len(nation_table) * 50,
                "Closed Borders List": [],
                "Expiration": current_turn_num + EVENT_DICT[chosen_event]["Duration"] + 1
            }
            active_games_dict[game_id]["Active Events"][chosen_event] = active_event_dict

        case "Faustian Bargain":
            notifications.append(f"New Event: {chosen_event}!", 2)
            active_games_dict = _save_as_standard_delayed_event(game_id, chosen_event, active_games_dict, nation_table)

def handle_current_event(game_id: str) -> None:
    """
    Handles a current event when called by site code.
    """
    
    # get game data
    current_turn_num = core.get_current_turn_num(game_id)
    nation_table = NationTable(game_id)
    alliance_table = AllianceTable(game_id)
    notifications = Notifications(game_id)
    with open(f'gamedata/{game_id}/regdata.json', 'r') as json_file:
        regdata_dict = json.load(json_file)
    with open(f'active_games.json', 'r') as json_file:  
        active_games_dict = json.load(json_file)

    # get event data
    current_event_dict = active_games_dict[game_id]["Current Event"]
    event_name = None
    effected_player_ids_list = None
    for key, value in current_event_dict.items():
        event_name: str = key
        effected_player_ids_list: list[str] = value
    
    # resolve outcome
    print(f"{event_name} Event Resolution")
    match event_name:

        case "Assassination":
            choices = ["Find the Perpetrator", "Find a Scapegoat"]
            print(f"Available Options: {" or ".join(choices)}")
            # collect decisions
            decision_dict = {}
            for player_id in effected_player_ids_list:
                nation = nation_table.get(player_id)
                while True:
                    decision = input(f"Enter {nation.name} decision: ")
                    if decision in choices:
                        break
                decision_dict[player_id] = decision
            # execute decisions
            for nation_id, decision in decision_dict.items():
                nation = nation_table.get(nation_id)
                if decision == "Find the Perpetrator":
                    nation.update_stockpile("Polticial Power", 5)
                    active_games_dict[game_id]["Inactive Events"].append(event_name)
                elif decision == "Find a Scapegoat":
                    while True:
                        scapegoat_nation_name = input("Enter the nation name to scapegoat: ")
                        try:
                            scapegoat = nation_table.get(scapegoat_nation_name)
                            break
                        except:
                            print("Unrecognized nation name, try again.")
                    new_tag = {}
                    new_tag["Combat Roll Bonus"] = scapegoat.id
                    new_tag["Expire Turn"] = current_turn_num + EVENT_DICT[event_name]["Duration"] + 1
                    nation.tags["Assassination Scapegoat"] = new_tag
                    active_games_dict[game_id]["Active Events"][event_name] = current_turn_num + EVENT_DICT[event_name]["Duration"] + 1
                nation_table.save(nation)

        case "Diplomatic Summit":
            choices = ["Attend", "Decline"]
            print(f"Available Options: {" or ".join(choices)}")
            # collect decisions
            decision_dict = {}
            for player_id in effected_player_ids_list:
                nation = nation_table.get(player_id)
                while True:
                    decision = input(f"Enter {nation.name} decision: ")
                    if decision in choices:
                        break
                decision_dict[player_id] = decision
            summit_attendance_list = []
            # execute decisions
            for nation_id, decision in decision_dict.items():
                nation = nation_table.get(nation_id)
                if decision == "Attend":
                    nation.update_stockpile("Political Power", 5)
                    summit_attendance_list.append(nation.id)
                elif decision == "Decline":
                    valid_research = False
                    while not valid_research:
                        research_name = input(f"Enter {nation.name} military technology decision: ")
                        valid_research = _gain_free_research(game_id, research_name, nation)
                nation_table.save(nation)
            # execute summit
            if len(summit_attendance_list) < 2:
                # summit has no effect because not enough attendees
                active_games_dict[game_id]["Inactive Events"].append(event_name)
            else:
                # add tags
                for nation_id in summit_attendance_list:
                    nation = nation_table.get(nation_id)
                    new_tag = {}
                    for attendee_id in summit_attendance_list:
                        new_tag[f"Cannot Declare War On #{attendee_id}"] = True
                    new_tag["Expire Turn"] = current_turn_num + EVENT_DICT[event_name]["Duration"] + 1
                    nation.tags["Summit"] = new_tag
                    nation_table.save(nation)
                # save event
                active_games_dict[game_id]["Active Events"][event_name] = current_turn_num + EVENT_DICT[event_name]["Duration"] + 1

        case "Foreign Interference":
            choices = ["Accept", "Decline"]
            print(f"Available Options: {" or ".join(choices)}")
            # collect decisions
            decision_dict = {}
            for player_id in effected_player_ids_list:
                nation = nation_table.get(player_id)
                while True:
                    decision = input(f"Enter {nation.name} decision: ")
                    if decision in choices:
                        break
                decision_dict[player_id] = decision
            # execute decisions
            war_actions: list[actions.WarAction] = []
            for nation_id, decision in decision_dict.items():
                nation = nation_table.get(nation_id)
                if decision == "Accept":
                    # add war
                    action_valid = False
                    while not action_valid:
                        enemy_nation_name = input("Enter nation you wish to declare war on: ")
                        chosen_war_justification = input("Enter desired war justification: ")
                        action_str = f"War {enemy_nation_name} {chosen_war_justification}"
                        war_action = actions.WarAction(game_id, nation_id, action_str)
                        if war_action.is_valid():
                            action_valid = True
                    # add tag
                    new_tag = {}
                    new_tag["Foreign Interference Target"] = enemy_nation_name
                    for resource_name in nation._resources:
                        if resource_name in ["Political Power", "Military Capacity"]:
                            continue
                        new_tag[f"{resource_name} Rate"] = 10
                    new_tag["Expire Turn"] = 99999
                    nation.tags["Foreign Interference"] = new_tag
                elif decision == "Decline":
                    nation.update_stockpile("Political Power", 5)
                nation_table.save(nation)
            # declare wars
            actions.resolve_war_actions(game_id, war_actions)
            # save event
            active_games_dict[game_id]["Inactive Events"].append(event_name)

        case "Lost Nuclear Weapons":
            choices = ["Claim", "Scuttle"]
            print(f"Available Options: {" or ".join(choices)}")
            # collect decisions
            decision_dict = {}
            for player_id in effected_player_ids_list:
                nation = nation_table.get(player_id)
                while True:
                    decision = input(f"Enter {nation.name} decision: ")
                    if decision in choices:
                        break
                decision_dict[player_id] = decision
            # execute decisions
            for nation_id, decision in decision_dict.items():
                nation = nation_table.get(nation_id)
                if decision == "Claim":
                    valid_region_id = False
                    while not valid_region_id:
                        silo_location_id = input("Enter region id for Missile Silo: ")
                        silo_location_id = silo_location_id.upper()
                        if silo_location_id in regdata_dict:
                            valid_region_id = True
                    nation.improvement_counts["Missile Silo"] += 1
                    region_improvement = Improvement(valid_region_id, game_id)
                    region_improvement.set_improvement("Missile Silo")
                    nation.nuke_count += 3
                elif decision == "Scuttle":
                    nation.update_stockpile("Technology", 15)
                nation_table.save(nation)
                notifications.append(f"{nation.name} chose to {decision.lower()} the old military installation.", 2)
            # save event
            active_games_dict[game_id]["Inactive Events"].append(event_name)
        
        case "Security Breach":
            victim_id = effected_player_ids_list[0]
            victim_nation = nation_table.get(victim_id)
            # technology copying
            for nation in nation_table:
                if nation.id == victim_id:
                    continue
                valid_research = False
                while not valid_research:
                    research_name = input(f"Enter {nation.name} technology decision: ")
                    if research_name not in victim_nation.completed_research:
                        continue
                    valid_research = _gain_free_research(game_id, research_name, nation)
                nation_table.save(nation)
            # add tag
            new_tag = {}
            new_tag["Technology Rate"] = -20
            new_tag["Expire Turn"] = current_turn_num + EVENT_DICT[event_name]["Duration"] + 1
            victim_nation.tags["Security Breach"] = new_tag
            nation_table.save(victim_nation)
            active_games_dict[game_id]["Active Events"][event_name] = current_turn_num + EVENT_DICT[event_name]["Duration"] + 1

        case "Observer Status Invitation":
            choices = ["Accept", "Decline"]
            print(f"Available Options: {" or ".join(choices)}")
            # collect decisions
            decision_dict = {}
            for player_id in effected_player_ids_list:
                nation = nation_table.get(player_id)
                while True:
                    decision = input(f"Enter {nation.name} decision: ")
                    if decision in choices:
                        break
                decision_dict[player_id] = decision
            # execute decisions
            for nation_id, decision in decision_dict.items():
                nation = nation_table.get(nation_id)
                if decision == "Accept":
                    new_tag = {}
                    new_tag["Expire Turn"] = current_turn_num + EVENT_DICT[event_name]["Duration"] + 1
                    nation.tags["Observer Status"] = new_tag
                elif decision == "Decline":
                    valid_research = False
                    while not valid_research:
                        research_name = input(f"Enter {nation.name} military technology decision: ")
                        valid_research = _gain_free_research(game_id, research_name, nation)
                nation_table.save(nation)
            # save event
            active_games_dict[game_id]["Inactive Events"].append(event_name)

        case "Peacetime Rewards":
            # effect
            for nation_id in effected_player_ids_list:
                nation = nation_table.get(nation_id)
                valid_research = False
                while not valid_research:
                    research_name = input(f"Enter {nation.name} technology decision: ")
                    valid_research = _gain_free_research(game_id, research_name, nation)
                nation_table.save(nation)
            # save event
            active_games_dict[game_id]["Inactive Events"].append(event_name)

        case "Shifting Attitudes":
            choices = ["Change", "Keep"]
            print(f"Available Options: {" or ".join(choices)}")
            # collect decisions
            decision_dict = {}
            for player_id in effected_player_ids_list:
                nation = nation_table.get(player_id)
                while True:
                    decision = input(f"Enter {nation.name} decision: ")
                    if decision in choices:
                        break
                decision_dict[player_id] = decision
            # execute decisions
            for nation_id, decision in decision_dict.items():
                nation = nation_table.get(nation_id)
                if decision == "Change":
                    new_fp = input(f"Enter new foreign policy: ")
                    nation.fp = new_fp
                elif decision == "Keep":
                    # add tag
                    new_tag = {}
                    new_tag["Political Power Rate"] = -20
                    new_tag["Expire Turn"] = current_turn_num + EVENT_DICT[event_name]["Duration"] + 1
                    nation.tags["Shifting Attitudes"] = new_tag
                    # give research
                    valid_research = False
                    while not valid_research:
                        research_name = input(f"Enter {nation.name} technology decision: ")
                        valid_research = _gain_free_research(game_id, research_name, nation)
                nation_table.save(nation)
            # save event
            active_games_dict[game_id]["Inactive Events"].append(event_name)

        case "Embargo":
            
            # voting
            print("""Available Options: "# Nation Name" or "Abstain" """)
            vote_tally_dict = _get_votes_nation(effected_player_ids_list, nation_table)
            nation_name = _determine_vote_winner(vote_tally_dict)
            
            # event success
            if nation_name is not None:
                nation = nation_table.get(nation_name)
                new_tag = {}
                new_tag["Expire Turn"] = current_turn_num + EVENT_DICT[event_name]["Duration"] + 1
                nation.tags["Embargo"] = new_tag
                nation_table.save(nation)
                notifications.append(f"Having received {vote_tally_dict[nation_name]} votes, {nation_name} has been embargoed", 2)
                active_games_dict[game_id]["Active Events"][event_name] = current_turn_num + EVENT_DICT[event_name]["Duration"] + 1
            
            # vote tied
            else:
                notifications.append(f"Vote tied. No nation has been embargoed.", 2)
                active_games_dict[game_id]["Inactive Events"].append(event_name)

        case "Humiliation":
            
            # voting
            print("""Available Options: "# Nation Name" or "Abstain" """)
            vote_tally_dict = _get_votes_nation(effected_player_ids_list, nation_table)
            nation_name = _determine_vote_winner(vote_tally_dict)
            
            # event success
            if nation_name is not None:
                nation = nation_table.get(nation_name)
                new_tag = {}
                new_tag["No Agenda Research"] = True
                new_tag["Expire Turn"] = current_turn_num + EVENT_DICT[event_name]["Duration"] + 1
                nation.tags["Humiliation"] = new_tag
                nation_table.save(nation)
                notifications.append(f"Having received {vote_tally_dict[nation_name]} votes, {nation_name} has been humiliated.", 2)
                active_games_dict[game_id]["Active Events"][event_name] = current_turn_num + EVENT_DICT[event_name]["Duration"] + 1
            
            # vote tied
            else:
                notifications.append(f"Vote tied. No nation has been humiliated.", 2)
                active_games_dict[game_id]["Inactive Events"].append(event_name)

        case "Foreign Investment":
            
            # voting
            print("""Available Options: "# Nation Name" or "Abstain" """)
            vote_tally_dict = _get_votes_nation(effected_player_ids_list, nation_table)
            nation_name = _determine_vote_winner(vote_tally_dict)
            
            # event success
            if nation_name is not None:
                nation = nation_table.get(nation_name)
                new_tag = {}
                new_tag["Expire Turn"] = current_turn_num + EVENT_DICT[event_name]["Duration"] + 1
                nation.tags["Foreign Investment"] = new_tag
                nation_table.save(nation)
                notifications.append(f"Having received {vote_tally_dict[nation_name]} votes, {nation_name} has recieved the foreign investment.", 2)
                active_games_dict[game_id]["Active Events"][event_name] = current_turn_num + EVENT_DICT[event_name]["Duration"] + 1
            
            # vote tied
            else:
                notifications.append(f"Vote tied. No nation has recieved the foreign investment.", 2)
                active_games_dict[game_id]["Inactive Events"].append(event_name)

        case "Nominate Mediator":
            
            # voting
            print("""Available Options: "# Nation Name" or "Abstain" """)
            vote_tally_dict = _get_votes_nation(effected_player_ids_list, nation_table)
            nation_name = _determine_vote_winner(vote_tally_dict)
            
            # event success
            if nation_name is not None:
                nation = nation_table.get(nation_name)
                new_tag = {
                    "Alliance Political Power Bonus": 0.25,
                    "Truces Extended": [],
                    "Expire Turn": current_turn_num + EVENT_DICT[event_name]["Duration"] + 1
                }
                nation.tags["Mediator"] = new_tag
                nation_table.save(nation)
                notifications.append(f"Having received {vote_tally_dict[nation_name]} votes, {nation_name} has been elected Mediator.", 2)
                active_games_dict[game_id]["Active Events"][event_name] = current_turn_num + EVENT_DICT[event_name]["Duration"] + 1
            
            # vote tied
            else:
                notifications.append(f"Vote tied. No nation has been elected Mediator.", 2)
                active_games_dict[game_id]["Inactive Events"].append(event_name)

        case "Shared Fate":
            
            # voting
            print("""Available Options: "# Cooperation" or "# Conflict" or "Abstain" """)
            vote_tally_dict = _get_votes_option(effected_player_ids_list, nation_table)
            option_name = _determine_vote_winner(vote_tally_dict)
            
            # cooperation wins
            if option_name == "Cooperation":
                nation = nation_table.get(nation_name)
                new_tag = {}
                new_tag["Alliance Limit Modifier"] = 1
                new_tag["Expire Turn"] = 99999
                nation.tags["Shared Fate"] = new_tag
                nation_table.save(nation)
                notifications.append(f"Cooperation won in a {vote_tally_dict.get("Cooperation")} - {vote_tally_dict.get("Conflict")} decision.", 2)
                active_games_dict[game_id]["Active Events"][event_name] = current_turn_num + EVENT_DICT[event_name]["Duration"] + 1

            elif option_name == "Conflict":
                nation = nation_table.get(nation_name)
                new_tag = {
                    "Improvement Income": {
                        "Boot Camp": {
                            "Military Capacity": 1
                        }
                    },
                    "Expire Turn": 99999
                }
                nation.tags["Shared Fate"] = new_tag
                nation_table.save(nation)
                notifications.append(f"Conflict won in a {vote_tally_dict.get("Conflict")} - {vote_tally_dict.get("Cooperation")} decision.", 2)
                active_games_dict[game_id]["Active Events"][event_name] = current_turn_num + EVENT_DICT[event_name]["Duration"] + 1
            
            # vote tied
            else:
                notifications.append(f"Shared Fate vote tied. No option was resolved.", 2)
                active_games_dict[game_id]["Inactive Events"].append(event_name)

        case "Threat Containment":
            
            # voting
            print("""Available Options: "# Nation Name" or "Abstain" """)
            vote_tally_dict = _get_votes_nation(effected_player_ids_list, nation_table)
            nation_name = _determine_vote_winner(vote_tally_dict)
            
            # event success
            if nation_name is not None:
                nation = nation_table.get(nation_name)
                new_tag = {}
                new_tag["Military Capacity Rate"] = -20
                new_tag["Trade Fee Modifier"] = -1
                new_tag["Expire Turn"] = current_turn_num + EVENT_DICT[event_name]["Duration"] + 1
                nation.tags["Threat Containment"] = new_tag
                nation_table.save(nation)
                notifications.append(f"Having received {vote_tally_dict[nation_name]} votes, {nation_name} has been sanctioned.", 2)
                active_games_dict[game_id]["Active Events"][event_name] = current_turn_num + EVENT_DICT[event_name]["Duration"] + 1
            
            # vote tied
            else:
                notifications.append(f"Vote tied. No nation has been sanctioned.", 2)
                active_games_dict[game_id]["Inactive Events"].append(event_name)

        case "Faustian Bargain":
            
            # recieve decisions
            print("""Available Options: "Accept" or "Decline" """)
            candidates_list = []
            for player_id in effected_player_ids_list:
                nation = nation_table.get(player_id)
                while True:
                    decision = input(f"Enter {nation.name} decision: ")
                    if decision == "Accept":
                        if nation.improvement_counts["Capital"] > 0:
                            candidates_list.append(nation.id)
                            break
                    elif decision == "Decline":
                        nation.update_stockpile("Political Power", 5)
                        break
                nation_table.save(nation)
            
            # execute event
            if candidates_list != []:
                # determine collaborator
                random.shuffle(candidates_list)
                nation_id = candidates_list.pop()
                nation = nation_table.get(nation_id)
                notifications.append(f"{nation.name} took the Faustian Bargain and will collaborate with the foreign nation.", 2)
                # remove collaborator from alliances
                for alliance in alliance_table:
                    if nation_name in alliance.current_members:
                        alliance.remove_member(nation_name)
                # add tag
                new_tag = {
                    "Expire Turn": current_turn_num + EVENT_DICT[event_name]["Duration"] + 1,
                    "No Agenda Research": True
                }
                for resource_name in nation._resources:
                    if resource_name not in ["Political Power", "Military Capacity"]:
                        new_tag[f"{resource_name} Rate"] = 20
                nation.tags["Faustian Bargain"] = new_tag
                nation_table.save(nation)
                # save event
                active_games_dict[game_id]["Active Events"][event_name] = current_turn_num + EVENT_DICT[event_name]["Duration"] + 1
            
            # nobody wanted to be a dirty filthy traitor
            else:
                notifications.append("No nation took the Faustian Bargain. collaborate with the foreign nation.", 2)
                active_games_dict[game_id]["Inactive Events"].append(event_name)

    # save files
    active_games_dict[game_id]["Current Event"] = {}
    with open('active_games.json', 'w') as json_file:
        json.dump(active_games_dict, json_file, indent=4)

def resolve_active_events(game_id: str, turn_status: str, actions_dict: dict[str, list]) -> None:
    """
    Function that handles active events depending on turn status.
    """

    # get game data
    nation_table = NationTable(game_id)
    notifications = Notifications(game_id)
    current_turn_num = core.get_current_turn_num(game_id)
    with open(f'gamedata/{game_id}/regdata.json', 'r') as json_file:
        regdata_dict = json.load(json_file)
    with open('active_games.json', 'r') as json_file:
        active_games_dict = json.load(json_file)

    active_events_list = list(active_games_dict[game_id]["Active Events"].keys())
    for event_name in active_events_list:
        match event_name:

            case "Foreign Invasion":
                
                if turn_status == "Before Actions":
                    
                    # generate movement actions
                    # tba - make movement smarter as it currently can only "see" one region away so the invasion is stumbling around blind
                    for region_id in regdata_dict:
                        region = Region(region_id, game_id)
                        region_unit = Unit(region_id, game_id)
                        if region_unit.name is not None and region_unit.owner_id == 99:
                            destination_dict = {}
                            ending_region_id, priority = _foreign_invasion_calculate_target_region(game_id, list(region.adjacent_regions.keys()), destination_dict)
                            destination_dict[ending_region_id] = priority
                            if ending_region_id is not None:
                                # foreign invasion always moves each unit one region at a time
                                movement_action_str = f"Move {region_id}-{ending_region_id}"
                                actions_dict["UnitMoveAction"].append(actions.UnitMoveAction(game_id, "99", movement_action_str))
                    
                    # generate deployment actions
                    if current_turn_num % 4 == 0:
                        notifications.append("The Foreign Invasion has received reinforcements.", 2)
                        for region_id in regdata_dict:
                            region = Region(region_id, game_id)
                            if region.owner_id == 99 and region.occupier_id == 0:
                                unit_name = _foreign_invasion_unit(current_turn_num)
                                deploy_action_str = f"Deploy {unit_name} {region_id}"
                                actions_dict["UnitDeployAction"].append(actions.UnitDeployAction(game_id, "99", deploy_action_str))

                elif turn_status == "After Actions":

                    foreign_invasion_nation = nation_table.get("99")
                    
                    # check if Foreign Invasion has no remaining units
                    invasion_unit_count = 0
                    for unit_name, count in foreign_invasion_nation.unit_counts.items():
                        invasion_unit_count += count
                    if invasion_unit_count == 0:
                        _foreign_invasion_end(game_id, foreign_invasion_nation)
                        nation_table.save(foreign_invasion_nation)
                    
                    # check if Foreign Invasion has no unoccupied reinforcement regions
                    invasion_unoccupied_count = 0
                    for region_id in regdata_dict:
                        region = Region(region_id, game_id)
                        if region.owner_id == 99 and region.occupier_id == 0:
                            invasion_unoccupied_count += 1
                    if invasion_unoccupied_count == 0:
                        _foreign_invasion_end(game_id, foreign_invasion_nation)
                        nation_table.save(foreign_invasion_nation)

            case "Pandemic":
                
                if turn_status == "After Actions":
                    
                    # load event data
                    intensify_value = active_games_dict[game_id]['Active Events'][event_name]["Intensify Value"]
                    spread_value = active_games_dict[game_id]['Active Events'][event_name]["Spread Value"]
                    completed_cure_research = active_games_dict[game_id]['Active Events'][event_name]["Completed Cure Research"]
                    needed_cure_research = active_games_dict[game_id]['Active Events'][event_name]["Needed Cure Research"]
                    closed_borders_player_ids_list = active_games_dict[game_id]['Active Events'][event_name]["Closed Borders List"]
                    cure_percentage = float(completed_cure_research) / float(needed_cure_research)
                    cure_percentage = round(cure_percentage, 2)
                    
                    if completed_cure_research >= needed_cure_research:
                        # run pandemic decline procedure
                        for region_id in regdata_dict:
                            region = Region(region_id, game_id)
                            region.add_infection(-1)
                    else:
                        
                        # conduct intensify rolls
                        for region_id in regdata_dict:
                            region = Region(region_id, game_id)
                            if region.infection() > 0 and region.infection() < 10:
                                # intensify check
                                intensify_roll = random.randint(1, 10)
                                if intensify_roll < intensify_value:
                                    continue
                                # intensify more if near capital or city
                                if region.check_for_adjacent_improvement(improvement_names = {'Capital', 'City'}):
                                    region.add_infection(2)
                                else:
                                    region.add_infection(1)

                        # get a list of regions infected before spreading starts
                        infected_regions = []
                        for region_id in regdata_dict:
                            region = Region(region_id, game_id)
                            if region.infection() > 0:
                                infected_regions.append(region_id)
                        
                        # conduct spread roles
                        for region_id in infected_regions:
                            region = Region(region_id, game_id)
                            if region.infection() > 0:
                                for adjacent_region_id in region.adjacent_regions:
                                    adjacent_region = Region(adjacent_region_id, game_id)
                                    adjacent_owner_id = adjacent_region.owner_id
                                    # spread only to regions that are not yet infected
                                    if adjacent_region.infection() != 0:
                                        continue
                                    spread_roll = random.randint(1, 20)
                                    # spread attempt
                                    if region.is_quarantined() or region.owner_id != adjacent_owner_id and adjacent_owner_id in closed_borders_player_ids_list:
                                        if spread_roll == 20:
                                            adjacent_region.add_infection(1)
                                    else:
                                        if spread_roll >= spread_value:
                                            adjacent_region.add_infection(1)
                    
                    # sum up total infection scores
                    infection_scores = [0] * len(nation_table)
                    for region_id in regdata_dict:
                        region = Region(region_id, game_id)
                        owner_id = region.owner_id
                        if owner_id != 0 and owner_id <= len(infection_scores):
                            infection_scores[owner_id - 1] += region.infection()
                    
                    # check if pandemic has been eradicated
                    infection_total = sum(infection_scores)
                    if infection_total == 0:
                        for region_id in regdata_dict:
                            region = Region(region_id, game_id)
                            if region.is_quarantined():
                                region.set_quarantine(False)
                        del active_games_dict[game_id]['Active Events'][event_name]
                        active_games_dict[game_id]["Inactive Events"].append(event_name)
                        notifications.append("The pandemic has been eradicated!", 2)
                    
                    # print diplomacy log messages
                    if infection_total != 0:
                        if cure_percentage >= 0.5:
                            notifications.append(f"Pandemic intensify value: {intensify_value}", 2)
                            notifications.append(f"Pandemic spread value: {spread_value}", 2)
                        if cure_percentage >= 0.75:
                            for nation in nation_table:
                                score = infection_scores[int(nation.id) - 1]
                                notifications.append(f"{nation.name} pandemic infection score: {score}", 2)
                        if cure_percentage < 1:
                            notifications.append(f"Pandemic cure research progress: {completed_cure_research}/{needed_cure_research}", 2)
                        else:
                            notifications.append(f"Pandemic cure research has been completed! The pandemic is now in decline.", 2)
                    
            case "Faustian Bargain":

                if turn_status == "After Actions":
                    
                    # identify collaborator
                    for nation in nation_table:
                        if "Faustian Bargain" in nation.tags:
                            break
                    
                    # check if collaborator has been defeated (no capital)
                    if nation.improvement_counts["Capital"] == 0:
                        # delete tag
                        del nation.tags["Faustian Bargain"]
                        nation_table.save(nation)
                        # delete event
                        del active_games_dict[game_id]['Active Events'][event_name]
                        active_games_dict[game_id]["Inactive Events"].append(event_name)
                        notifications.append(f"{event_name} event has ended.", 2)

    # filter out events that have expired
    active_events_filtered = {}
    if turn_status == "After Actions":
        for event_name, event_data in active_games_dict[game_id]["Active Events"].items():
            
            # event has expired - end it
            if isinstance(event_data, int):
                expire_turn = event_data
                if current_turn_num >= expire_turn:
                    notifications.append(f"{event_name} event has ended.", 2)
                    if event_name == "Foreign Invasion":
                        foreign_invasion_nation = nation_table.get("99")
                        _foreign_invasion_end(game_id, foreign_invasion_nation)
                        nation_table.save(foreign_invasion_nation)
                    continue
            else:
                expire_turn = event_data["Expiration"]
                if current_turn_num >= expire_turn:
                    notifications.append(f"{event_name} event has ended.", 2)
                    continue
            
            # event still active - make notification
            active_events_filtered[event_name] = event_data
            if EVENT_DICT[event_name]["Duration"] != 99999 and isinstance(event_data, int):
                notifications.append(f"{event_name} will end on turn {event_data}.", 2)
            else:
                notifications.append(f"{event_name} event is active.", 2)
    
        active_games_dict[game_id]["Active Events"] = active_events_filtered
    
    # save active games
    with open('active_games.json', 'w') as json_file:
        json.dump(active_games_dict, json_file, indent=4)
   
def _is_valid(game_id: str, event_conditions: dict, already_chosen_events: set) -> bool:
    """
    Checks if an event is elligable to be selected this turn.
    """

    nation_table = NationTable(game_id)
    war_table = WarTable(game_id)

    for condition_name, var in event_conditions.items():
        
        match condition_name:

            case "First Event":
                if var == False and len(already_chosen_events) == 0:
                    return False
                elif var == True and len(already_chosen_events) != 0:
                    return False
            
            case "No Major Event":
                for event_name, event_data in EVENT_DICT.items():
                    if event_name in already_chosen_events and event_data["Type"] == "Major Event":
                        return False

            case "No Record Tie":
                top_three = nation_table.get_top_three(var)
                if top_three[0][1] == top_three[1][1]:
                    return False

            case "Ongoing War Minimum":
                ongoing_war_count = 0
                for war in war_table:
                    if war.outcome == "TBD":
                        ongoing_war_count += 1
                if ongoing_war_count < var:
                    return False

            case "At Peace For 12 Turns Minimum":
                at_peace_for_12_count = 0
                for nation in nation_table:
                    if war_table.at_peace_for_x(nation.id) >= 12:
                        at_peace_for_12_count += 1
                if at_peace_for_12_count < var:
                    return False

            case "Global Count Minimum":
                for improvement_name, minimum in var.items():
                    global_total = 0
                    for nation in nation_table:
                        global_total += nation.improvement_counts[improvement_name]
                    if global_total < minimum:
                        return False
                    
    return True

def _save_as_standard_delayed_event(game_id: str, chosen_event: str, active_games_dict: dict, nation_table: NationTable) -> None:
    """
    Updates active_games_dict with a new current event. Used for all events in which there is a pending option / vote effecting all players.
    """

    effected_player_ids = []
    for i in range(1, len(nation_table) + 1):
        effected_player_ids.append(str(i))
    # save to Current Event key to be activated later
    active_games_dict[game_id]["Current Event"][chosen_event] = effected_player_ids

def _gain_free_research(game_id: str, research_name: str, nation: Nation) -> bool:
    """
    Returns updated playerdata_List and a bool that is True if the research was valid, False otherwise.
    """

    tech_scenario_dict = core.get_scenario_dict(game_id, "Technologies")
    try:
        prereq = tech_scenario_dict[research_name]['Prerequisite']
    except:
        return False

    # prereq check
    if prereq != None and prereq not in nation.completed_research:
        return False
    
    # gain technology
    nation.add_tech(research_name)
    nation.award_research_bonus(research_name)

    return True

def _get_votes_nation(voting_nation_ids: list, nation_table: NationTable) -> dict[str, int]:
    
    vote_tally_dict = {}
    
    for nation_id in voting_nation_ids:
        
        nation = nation_table.get(nation_id)
        
        while True:
            
            # get vote
            decision = input(f"Enter {nation.name} vote: ")
            decision = decision.strip()
            if decision == "Abstain":
                break

            # parse vote
            decision_data = decision.split()
            vote_count = int(decision_data[0])
            target_name = " ".join(decision_data[1:])

            # validate vote
            if vote_count > float(nation.get_stockpile("Political Power")):
                continue
            if target_name not in nation_table._name_to_id:
                continue
            
            # add votes
            if target_name in vote_tally_dict:
                vote_tally_dict[target_name] += vote_count
            else:
                vote_tally_dict[target_name] = vote_count
            
            # pay for votes
            nation.update_stockpile("Political Power", -1 * vote_count)
            nation_table.save(nation)
            break
    
    return vote_tally_dict

def _get_votes_option(voting_nation_ids: list, nation_table: NationTable, options: list) -> dict[str, int]:

    vote_tally_dict = {}
    
    for nation_id in voting_nation_ids:
        
        nation = nation_table.get(nation_id)
        
        while True:
            
            # get vote
            decision = input(f"Enter {nation.name} vote: ")
            decision = decision.strip()
            if decision == "Abstain":
                break

            # parse vote
            decision_data = decision.split()
            vote_count = int(decision_data[0])
            option_name = " ".join(decision_data[1:])

            # validate vote
            if vote_count > float(nation.get_stockpile("Political Power")):
                continue
            if option_name not in options:
                continue
            
            # add votes
            if option_name in vote_tally_dict:
                vote_tally_dict[option_name] += vote_count
            else:
                vote_tally_dict[option_name] = vote_count
            
            # pay for votes
            nation.update_stockpile("Political Power", -1 * vote_count)
            nation_table.save(nation)
            break
    
    return vote_tally_dict

def _determine_vote_winner(vote_tally_dict: dict[str, int]) -> str | None:

    # no winner if no votes
    if len(vote_tally_dict) == 0:
        return None

    # sort the vote
    sorted_vote_tally_dict = dict(sorted(vote_tally_dict.items(), key=lambda item: item[1], reverse=True))

    # if only one outcome recieved votes, that one wins
    if len(sorted_vote_tally_dict) == 1:
        winning_outcome_data = list(sorted_vote_tally_dict.items())[:1]
        return winning_outcome_data[0][0]

    # return outcome with most votes provided there is no tie
    top_two = list(sorted_vote_tally_dict.items())[:2]
    if top_two[0][1] == top_two[1][1]:
        return None
    return top_two[0][0]
    
def _foreign_invasion_unit(current_turn_num: int):
    if current_turn_num >= 40:
        return "Main Battle Tank"
    elif current_turn_num >= 32:
        return "Special Forces"
    elif current_turn_num >= 24:
        return "Mechanized Infantry"
    else:
        return "Infantry"

def _foreign_invasion_initial_spawn(game_id: str, region_id: str, unit_name: str, nation_table: NationTable):
    
    region = Region(region_id, game_id)
    region_improvement = Improvement(region_id, game_id)
    region_unit = Unit(region_id, game_id)

    if region_unit.name is not None:
        # remove old unit
        temp = nation_table.get(str(region_unit.owner_id))
        temp.unit_counts[region_unit.name] -= 1
        region_unit.clear()
        nation_table.save(temp)

    if region_improvement.name is not None:
        # remove old improvement
        temp = nation_table.get(str(region_improvement.owner_id))
        temp.improvement_counts[region_improvement.name] -= 1
        region_improvement.clear()
        nation_table.save(temp)

    region.set_owner_id(99)
    region.set_occupier_id(0)
    region_unit.set_unit(unit_name, 99)

    foreign_nation = nation_table.get("99")
    foreign_nation.unit_counts[unit_name] += 1
    nation_table.save(foreign_nation)

def _foreign_invasion_calculate_target_region(game_id: str, adjacency_list: list, destination_dict: dict) -> tuple:
    """
    Function that contains Foreign Invasion attack logic.
    Designed to find path of least resistance but has no care for the health of its own units.
    """
    
    target_region_id = None
    target_region_health = 0
    target_region_priority = -1

    while adjacency_list != []:

        # get random adjacent region
        index = random.randrange(len(adjacency_list))
        adjacent_region_id = adjacency_list.pop(index)

        # get data from region
        region = Region(adjacent_region_id, game_id)
        region_improvement = Improvement(adjacent_region_id, game_id)
        region_unit = Unit(adjacent_region_id, game_id)
        candidate_region_priority = 0
        candidate_region_health = 0
        
        # increase priority based on control data
        # occupied friendly is the highest priority
        if region.owner_id == 99 and region.occupier_id != 0:
            candidate_region_priority += 10
        # unoccupied unclaimed region
        elif region.owner_id == 0 and region.occupier_id != 99:
            candidate_region_priority += 4
        # occupied unclaimed region
        elif region.owner_id == 0:
            candidate_region_priority += 2
        # friendly unoccupied region
        elif region.owner_id == 99:
            candidate_region_priority += 0
        # unoccupied enemy region
        elif region.owner_id != 99 and region.occupier_id != 99:
            candidate_region_priority += 8
        # occupied enemy region
        elif region.owner_id != 99:
            candidate_region_priority += 6
        
        # increase priority by one if there is a hostile unit
        if region_unit.name != None and region_unit.owner_id != 0:
            candidate_region_priority += 1

        # try to prevent units from tripping over each other on unclaimed regions and friendly unoccupied regions
        if adjacent_region_id in destination_dict and (candidate_region_priority == 0 or candidate_region_priority == 2 or candidate_region_priority == 4):
            continue
        
        # calculate region health
        if region_improvement.name != None and region_improvement.health != 99 and region.owner_id != 99 and region.occupier_id != 99:
            candidate_region_health += region_improvement.health
        if region_unit.name != None and region_unit.owner_id != 0:
            candidate_region_health += region_unit.health
        
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

def _foreign_invasion_end(game_id: str, foreign_invasion_nation: Nation):
    
    war_table = WarTable(game_id)
    current_turn_num = core.get_current_turn_num(game_id)
    with open(f'gamedata/{game_id}/regdata.json', 'r') as json_file:
        regdata_dict = json.load(json_file)
    
    for region_id in regdata_dict:
        
        region = Region(region_id, game_id)
        region_unit = Unit(region_id, game_id)
        
        # reinforcement regions are abandoned
        if region.owner_id == 99:
            region.set_owner_id(0)
            region.set_occupier_id(0)
        
        # occupied regions are unoccupied
        elif region.occupier_id == 99:
            region.set_occupier_id(0)
        
        # foreign invasion units are deleted
        if region_unit.owner_id == 99:
            foreign_invasion_nation.unit_counts[region_unit.name] -= 1
            region_unit.clear()

        # foreign invasion war ends
        war = war_table.get("Foreign Invasion")
        war.end = current_turn_num
        war.outcome = "White Peace"
        war_table.save(war)

EVENT_DICT = {
    "Assassination": {
        "Type": "Standard Event",
        "Resolution": "Delayed Option",
        "Duration": 8,
        "Conditions": {}
    },
    "Corruption Scandal": {
        "Type": "Standard Event",
        "Resolution": "Instant",
        "Duration": 8,
        "Conditions": {
            "No Record Tie": "netIncome"
        }
    },
    "Coup": {
        "Type": "Standard Event",
        "Resolution": "Instant",
        "Duration": 0,
        "Conditions": {
            "First Event": False
        }
    },
    "Decaying Infrastructure": {
        "Type": "Standard Event",
        "Resolution": "Instant",
        "Duration": 0,
        "Conditions": {
            "First Event": False
        }
    },
    "Desertion": {
        "Type": "Standard Event",
        "Resolution": "Instant",
        "Duration": 0,
        "Conditions": {
            "Ongoing War Minimum": 1
        }
    },
    "Diplomatic Summit": {
        "Type": "Standard Event",
        "Resolution": "Delayed Option",
        "Duration": 8,
        "Conditions": {}
    },
    "Foreign Aid": {
        "Type": "Standard Event",
        "Resolution": "Instant",
        "Duration": 0,
        "Conditions": {}
    },
    "Foreign Interference": {
        "Type": "Standard Event",
        "Resolution": "Delayed Option",
        "Duration": 0,
        "Conditions": {
            "First Event": False
        }
    },
    "Lost Nuclear Weapons": {
        "Type": "Standard Event",
        "Resolution": "Delayed Option",
        "Duration": 0,
        "Conditions": {}
    },
    "Security Breach": {
        "Type": "Standard Event",
        "Resolution": "Delayed Option",
        "Duration": 4,
        "Conditions": {
            "No Record Tie": "researchCount"
        }
    },
    "Market Inflation": {
        "Type": "Standard Event",
        "Resolution": "Instant",
        "Duration": 8,
        "Conditions": {}
    },
    "Market Recession": {
        "Type": "Standard Event",
        "Resolution": "Instant",
        "Duration": 8,
        "Conditions": {}
    },
    "Observer Status Invitation": {
        "Type": "Standard Event",
        "Resolution": "Delayed Option",
        "Duration": 8,
        "Conditions": {}
    },
    "Peacetime Rewards": {
        "Type": "Standard Event",
        "Resolution": "Instant",
        "Duration": 0,
        "Conditions": {
            "At Peace For 12 Turns Minimum": 1
        }
    },
    "Power Plant Meltdown": {
        "Type": "Standard Event",
        "Resolution": "Instant",
        "Duration": 0,
        "Conditions": {
            "Global Count Minimum": {
                "Nuclear Power Plant": 1
            }
        }
    },
    "Shifting Attitudes": {
        "Type": "Standard Event",
        "Resolution": "Delayed Option",
        "Duration": 4,
        "Conditions": {
            "First Event": False
        }
    },
    "United Nations Peacekeeping Mandate": {
        "Type": "Standard Event",
        "Resolution": "Instant",
        "Duration": 0,
        "Conditions": {
            "Ongoing War Minimum": 3
        }
    },
    "Widespread Civil Disorder": {
        "Type": "Standard Event",
        "Resolution": "Instant",
        "Duration": 8,
        "Conditions": {
            "First Event": False
        }
    },
    "Embargo": {
        "Type": "Voting Events",
        "Resolution": "Delayed Vote",
        "Duration": 8,
        "Conditions": {}
    },
    "Humiliation": {
        "Type": "Voting Events",
        "Resolution": "Delayed Vote",
        "Duration": 8,
        "Conditions": {}
    },
    "Foreign Investment": {
        "Type": "Voting Events",
        "Resolution": "Delayed Vote",
        "Duration": 16,
        "Conditions": {}
    },
    "Nominate Mediator": {
        "Type": "Voting Events",
        "Resolution": "Delayed Vote",
        "Duration": 16,
        "Conditions": {}
    },
    "Shared Fate": {
        "Type": "Voting Events",
        "Resolution": "Delayed Vote",
        "Duration": 99999,
        "Conditions": {}
    },
    "Threat Containment": {
        "Type": "Voting Events",
        "Resolution": "Delayed Vote",
        "Duration": 8,
        "Conditions": {}
    },
    "Foreign Invasion": {
        "Type": "Major Event",
        "Resolution": "Instant",
        "Duration": 20,
        "Conditions": {
            "First Event": False,
            "No Major Event": True
        }
    },
    "Pandemic": {
        "Type": "Major Event",
        "Resolution": "Instant",
        "Duration": 99999,
        "Conditions": {
            "First Event": False,
            "No Major Event": True
        }
    },
    "Faustian Bargain": {
        "Type": "Major Event",
        "Resolution": "Instant",
        "Duration": 99999,
        "Conditions": {
            "First Event": False,
            "No Major Event": True
        }
    },
}
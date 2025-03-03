import ast
import csv
import json
import random

from app import core
from app import private_actions
from app import checks
from app.region import Region
from app.improvement import Improvement
from app.unit import Unit
from app.wardata import WarData
from app.notifications import Notifications

#EVENT INITIATION CODE
################################################################################

def trigger_event(full_game_id: str, current_turn_num: int) -> None:
    """
    Activates and resolves a random event.

    Params:
        full_game_id (str): The full game_id of the active game.
        current_turn_num (int): An integer representing the current turn number.
    """

    # get game data
    playerdata_filepath = f'gamedata/{full_game_id}/playerdata.csv'
    playerdata_list = core.read_file(playerdata_filepath, 1)
    with open('active_games.json', 'r') as json_file:
        active_games_dict = json.load(json_file)

    # get list of events already used and build event conditions dict
    events_list = list(EVENT_DICT.keys())
    random.shuffle(events_list)
    event_conditions_dict = build_event_conditions_dict(full_game_id, current_turn_num, playerdata_list, active_games_dict)
    already_chosen_events_list = []
    already_chosen_events_list += active_games_dict[full_game_id]["Inactive Events"]
    already_chosen_events_list += [key for key in active_games_dict[full_game_id]["Active Events"]]
    event_override = None

    chosen_event = None
    while True:
        # randomly draw an event or use preselected one
        chosen_event = events_list.pop()
        if event_override is not None:
            chosen_event = event_override
        # check if event conditions have been met
        if chosen_event not in already_chosen_events_list and event_conditions_met(chosen_event, event_conditions_dict, full_game_id, active_games_dict):
            print(chosen_event)
            active_games_dict, playerdata_list= initiate_event(chosen_event, event_conditions_dict, full_game_id, current_turn_num, active_games_dict, playerdata_list)
            break

    # save changes to playerdata
    with open(playerdata_filepath, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(core.player_data_header)
        writer.writerows(playerdata_list)

    # save changes to active_games.json
    with open('active_games.json', 'w') as json_file:
        json.dump(active_games_dict, json_file, indent=4)

def build_event_conditions_dict(game_id: str, current_turn_num: int, playerdata_list, active_games_dict: dict) -> dict:
    """
    Returns a dictionary of event condition data generated from game data.

    Params:
        game_id (str): The full game_id of the active game.
        current_turn_num (int): An integer representing the current turn number.
        playerdata_list (list of lists): A list of lists containing all playerdata derived from playerdata.csv
        active_games_dict (dict): A dictionary derived from the active_games.json file.
    
    Returns:
        event_conditions_dict (dict): A dictionary containing all event condition data.
    """

    improvement_data_dict = core.get_scenario_dict(game_id, "Improvements")

    event_conditions_dict = {
        "At Peace For At Least 8 Turns": [],
        "Event Count": len(active_games_dict[game_id]["Active Events"]) + len(active_games_dict[game_id]["Inactive Events"]),
        "Global Improvement Count List": [0] * len(improvement_data_dict.keys()),
        "Most Research": "N/A",
        "Ongoing Wars": [],
        "Players at War": [],
    }

    nation_name_list = []
    for index, playerdata in enumerate(playerdata_list):
        player_id = index + 1
        player_improvement_count_list = ast.literal_eval(playerdata[27])
        event_conditions_dict["Global Improvement Count List"] = [x + y for x, y in zip(player_improvement_count_list, event_conditions_dict["Global Improvement Count List"])]
        nation_name_list.append(playerdata[1])
    
    research_1st, research_2nd, research_3rd = checks.get_top_three(game_id, 'most_research', True)
    research_1st_data = research_1st.split()
    research_2nd_data = research_2nd.split()
    if research_1st_data[-1] != research_2nd_data[-1]:
        for nation_name in nation_name_list:
            if nation_name in research_1st:
                event_conditions_dict["Most Research"] = nation_name
                break
    
    wardata = WarData(game_id)
    for index, playerdata in enumerate(playerdata_list):
        player_id = index + 1
        at_peace_since = wardata.is_at_peace(player_id, True)
        if at_peace_since and current_turn_num - at_peace_since >= 8:
            event_conditions_dict["At Peace For At Least 8 Turns"].append(player_id)
        if not at_peace_since:
            event_conditions_dict["Players at War"].append(player_id)
    for war, war_data in wardata.wardata_dict.items():
        if war_data["outcome"] == "TBD":
            event_conditions_dict["Ongoing Wars"].append(war)

    return event_conditions_dict

def event_conditions_met(chosen_event: str, event_conditions_dict: dict, game_id: str, active_games_dict: dict) -> bool:
    """
    Returns True if the conditions of an event are met, otherwise returns False.
    Note - it is probably possible to merge build_event_conditions_dict and this function together.

    Params:
        chosen_event (str): A string that is the name of an event.
        event_conditions_dict (dict): A dictionary of event conditions data generated from build_event_conditions_dict().
        full_game_id (str): The full game_id of the active game.
        active_games_dict (str): A dictionary derived from the active_games.json file.
    """

    # get data from game
    improvement_data_dict = core.get_scenario_dict(game_id, "Improvements")
    
    # check all conditions
    for condition in EVENT_DICT[chosen_event]["Conditions List"]:
        match condition:
            
            case "Cannot be First Event":
                if event_conditions_dict["Event Count"] == 0:
                    return False
            
            case "At Peace For At Least 8 Turns >= 1":
                if len(event_conditions_dict["At Peace For At Least 8 Turns"]) == 0:
                    return False
            
            case "Ongoing Wars >= 3":
                if len(event_conditions_dict["Ongoing Wars"]) < 3:
                    return False
            
            case "Ongoing Wars >= 1":
                if len(event_conditions_dict["Ongoing Wars"]) == 0:
                    return False
            
            case "No Most Research Tie":
                if event_conditions_dict["Most Research"] == "N/A":
                    return False
            
            case "No Major Event":
                major_event_list = [event_name for event_name, data in EVENT_DICT.items() if data.get('Type') == 'Major Event']
                for event in active_games_dict[game_id]["Active Events"]:
                    if event in major_event_list:
                        return False
                for event in active_games_dict[game_id]["Inactive Events"]:
                    if event in major_event_list:
                        return False
            
            case _:
                # default case - global improvement count of some improvement is >= 1
                improvement_name_list = sorted(improvement_data_dict.keys())
                for improvement in improvement_name_list:
                    if improvement in condition:
                        improvement_index = improvement_name_list.index(improvement)
                        improvement_count = event_conditions_dict["Global Improvement Count List"][improvement_index]
                        if improvement_count == 0:
                            return False
    
    return True

def initiate_event(chosen_event: str, event_conditions_dict: dict, game_id: str, current_turn_num: int, active_games_dict: dict, playerdata_list):
    """
    Initiates the chosen event. If it is an instant resolution event, it will be resolved.
    This function is a fucking mess and should probably be burned down and totally replaced at some point.
    """

    notifications = Notifications(game_id)
    improvement_data_dict = core.get_scenario_dict(game_id, "Improvements")
    with open(f'gamedata/{game_id}/regdata.json', 'r') as json_file:
        regdata_dict = json.load(json_file)
    nation_name_list = []
    for playerdata in playerdata_list:
        nation_name_list.append(playerdata[1])

    match chosen_event:

        case "Assassination":
            victim_player_id = random.randint(1, len(playerdata_list)) 
            victim_nation_name = playerdata_list[victim_player_id - 1][1]
            notifications.append(f'{victim_nation_name} has been randomly selected for the {chosen_event} event!', 2)
            #save to Current Event key to be activated later
            active_games_dict[game_id]["Current Event"][chosen_event] = [victim_player_id]
        
        case "Coup D'état":
            victim_nation_name = core.get_lowest_in_record(game_id, "strongest_economy")
            victim_player_id = nation_name_list.index(victim_nation_name) + 1
            #resolve event now
            old_government = playerdata_list[victim_player_id - 1][3]
            gov_list = ['Republic', 'Technocracy', 'Oligarchy', 'Totalitarian', 'Remnant', 'Protectorate', 'Military Junta', 'Crime Syndicate']
            gov_list.remove(playerdata_list[victim_player_id - 1][3])
            random.shuffle(gov_list)
            new_government = gov_list.pop()
            playerdata_list[victim_player_id - 1][3] = new_government
            notifications.append(f"{victim_nation_name}'s {old_government} government has been defeated by a coup. A new {new_government} government has taken power.", 2)
            #save to inactive events list
            active_games_dict[game_id]["Inactive Events"].append(chosen_event)
        
        case "Decaying Infrastructure":
            top_three_economy = checks.get_top_three(game_id, "strongest_economy", False)
            #resolve event now
            for region_id in regdata_dict:
                region = Region(region_id, game_id)
                region_improvement = Improvement(region_id, game_id)
                victim_player_id = region.owner_id
                improvement_name = region_improvement.name
                victim_nation_name = nation_name_list[victim_player_id - 1]
                if victim_nation_name not in top_three_economy and improvement_name in ['Coal Mine', 'Strip Mine', 'Oil Well', 'Oil Refinery', 'Solar Farm', 'Wind Farm']:
                    decay_roll = random.randint(1, 10)
                    if decay_roll >= 6:
                        region_improvement.clear()
                        notifications.append(f'{victim_nation_name} {improvement_name} in {region_id} has decayed.', 2)
            #save to inactive events list
            active_games_dict[game_id]["Inactive Events"].append(chosen_event)

        case "Defection":
            wardata = WarData(game_id)
            defection_victims_dict = {}
            for player_id in event_conditions_dict["Players at War"]:
                nation_name = playerdata_list[player_id - 1][1]
                defection_victims_entry = {}
                defection_victims_entry["lowestScore"] = None
                defection_victims_entry["enemyIDs"] = []
                for war, war_data in wardata.wardata_dict.items():
                    if nation_name in war_data["combatants"] and war_data["outcome"] == "TBD":
                        war_role = war_data["combatants"][nation_name]["role"]
                        if 'Attacker' in war_role:
                            score = war_data["attackerWarScore"]["total"]
                        else:
                            score = war_data["defenderWarScore"]["total"]
                        if score < defection_victims_entry["lowestScore"]:
                            defection_victims_entry["lowestScore"] = score
                for i in range(len(playerdata_list)):
                    if player_id == i + 1:
                        continue
                    if wardata.are_at_war(player_id, i + 1):
                        defection_victims_entry["enemyIDs"].append(i + 1)
                defection_victims_dict[nation_name] = defection_victims_entry
            min_value = min(entry["lowestScore"] for entry in defection_victims_dict.values() if "lowestScore" in entry)
            filtered_dict = {}
            for nation_name, defection_data in defection_victims_dict.items():
                if defection_data["lowestScore"] == min_value:
                    filtered_dict[nation_name] = defection_data
            defection_victims_dict = filtered_dict
            #resolve event now
            for region_id in regdata_dict:
                region = Region(region_id, game_id)
                region_unit = Unit(region_id, game_id)
                victim_nation_name = nation_name_list[region_unit.owner_id - 1]
                if victim_nation_name in defection_victims_dict and region.owner_id in defection_victims_dict["enemyIDs"]:
                    defection_roll = random.randint(1, 10)
                    if defection_roll == 10:
                        opponent_player_id = region.owner_id
                        region_unit.set_owner_id(opponent_player_id)
                        opponent_nation_name = playerdata_list[opponent_player_id - 1][1]
                        notifications.append(f'{victim_nation_name} {unit_name} {region_id} has defected to {opponent_nation_name}.', 2)
                    elif defection_roll >= 8:
                        region_unit.clear()
                        notifications.append(f'{victim_nation_name} {unit_name} {region_id} has disbanded.', 2)
            #save to inactive events list
            active_games_dict[game_id]["Inactive Events"].append(chosen_event)

        case "Diplomatic Summit":
            notifications.append(f'New Event: {chosen_event}!', 2)
            active_games_dict = save_as_standard_delayed_event(chosen_event, active_games_dict, game_id, playerdata_list)

        case "Foreign Aid":
            #tba: add calculation for All nations who are in the top three of at least one category
            effected_player_ids = []
            #resolve event now
            for victim_player_id in effected_player_ids:
                victim_nation_name = playerdata_list[victim_player_id - 1][1]
                dollars_economy_data = ast.literal_eval(playerdata_list[victim_player_id - 1][9])
                dollars_stored = float(dollars_economy_data[0])
                dollars_capacity = float(dollars_economy_data[1])
                improvement_name_list = sorted(improvement_data_dict.keys())
                improvement_count_list = ast.literal_eval(playerdata_list[victim_player_id - 1][27])
                city_index = improvement_name_list.index("City")
                city_count = improvement_count_list[city_index]
                if city_count >= 0:
                    dollars_stored += city_count * 5
                    if dollars_stored > dollars_capacity:
                        dollars_stored = dollars_capacity
                    dollars_economy_data[0] = str(dollars_stored)
                    playerdata_list[victim_player_id - 1][9] = str(dollars_economy_data)
                    notifications.append(f'{victim_nation_name} has received {city_count * 5} dollars worth of foreign aid.', 2)
            #save to inactive events list
            active_games_dict[game_id]["Inactive Events"].append(chosen_event)

        case "Foreign Interference":
            notifications.append(f'New Event: {chosen_event}!', 2)
            active_games_dict = save_as_standard_delayed_event(chosen_event, active_games_dict, game_id, playerdata_list)

        case "Lost Nuclear Weapons":
            chosen_player_id = random.randint(1, len(playerdata_list))
            chosen_nation_name = playerdata_list[chosen_player_id - 1][1]
            notifications.append(f'{chosen_nation_name} has been randomly selected for the {chosen_event} event!', 2)
            #save to Current Event key to be activated later
            active_games_dict[game_id]["Current Event"][chosen_event] = [chosen_player_id]

        case "Major Security Breach":
            victim_player_id = event_conditions_dict["Most Research"]
            notifications.append(f'New Event: {chosen_event}!', 2)
            #save to Current Event key to be activated later
            active_games_dict[game_id]["Current Event"][chosen_event] = [victim_player_id]

        case "Market Inflation":
            #resolve event now
            market_resource_list = ['Technology', 'Coal', 'Oil', 'Basic Materials', 'Common Metals', 'Advanced Metals', 'Uranium', 'Rare Earth Elements']
            affected_resources_list = random.sample(market_resource_list, 3)
            #save as an active event
            active_event_dict = {}
            active_event_dict["Affected Resources"] = affected_resources_list
            active_event_dict["Expiration"] = current_turn_num + 8
            active_games_dict[game_id]["Active Events"][chosen_event] = active_event_dict
        
        case "Market Recession":
            #resolve event now
            market_resource_list = ['Technology', 'Coal', 'Oil', 'Basic Materials', 'Common Metals', 'Advanced Metals', 'Uranium', 'Rare Earth Elements']
            affected_resources_list = random.sample(market_resource_list, 3)
            #save as an active event
            active_event_dict = {}
            active_event_dict["Affected Resources"] = affected_resources_list
            active_event_dict["Expiration"] = current_turn_num + 8
            active_games_dict[game_id]["Active Events"][chosen_event] = active_event_dict

        case "Observer Status Invitation":
            notifications.append(f'New Event: {chosen_event}!', 2)
            active_games_dict = save_as_standard_delayed_event(chosen_event, active_games_dict, game_id, playerdata_list)

        case "Peacetime Rewards":
            effected_player_ids = event_conditions_dict["At Peace For At Least 8 Turns"]
            nations_receiving_award_list = []
            for player_id in effected_player_ids:
                nations_receiving_award_list.append(playerdata_list[player_id - 1][1])
            nations_receiving_award_str = ", ".join(nations_receiving_award_list)
            notifications.append(f'New Event: {chosen_event}!', 2)
            notifications.append(f'Nations receiving event reward: {nations_receiving_award_str}.', 2)
            #save to Current Event key to be activated later
            active_games_dict[game_id]["Current Event"][chosen_event] = effected_player_ids

        case "Power Plant Meltdown":
            meltdown_candidates = []
            for region_id in regdata_dict:
                region_improvement = Improvement(region_id, game_id)
                if region_improvement.name == "Nuclear Power Plant":
                    meltdown_candidates.append(region_id)
            random.shuffle(meltdown_candidates)
            meltdown_region_id = meltdown_candidates.pop()
            #resolve event now
            region = Region(meltdown_region_id, game_id)
            region_improvement = Improvement(meltdown_region_id, game_id)
            region_unit = Unit(meltdown_region_id, game_id)
            victim_player_id = region.owner_id
            victim_nation_name = playerdata_list[victim_player_id - 1][1]
            region_improvement.clear()
            region_unit.clear()
            region.set_fallout(1000)
            political_power_economy_data = ast.literal_eval(playerdata_list[victim_player_id - 1][10])
            political_power_economy_data[0] = '0.00'
            playerdata_list[victim_player_id - 1][10] = str(political_power_economy_data)
            notifications.append(f'The {victim_nation_name} Nuclear Power Plant in {meltdown_region_id} has melted down!', 2)
            #save to inactive events list
            active_games_dict[game_id]["Inactive Events"].append(chosen_event)

        case "Shifting Attitudes":
            notifications.append(f'New Event: {chosen_event}!', 2)
            active_games_dict = save_as_standard_delayed_event(chosen_event, active_games_dict, game_id, playerdata_list)

        case "United Nations Peacekeeping Mandate":
            #resolve event now
            wardata = WarData(game_id)
            for war_name, war_data in wardata.wardata_dict.items():
                if war_data["outcome"] == "TBD":
                    wardata.end_war(war_name, "White Peace")
                    notifications.append(f'{war_name} has ended with a white peace due to United Nations Peacekeeping Mandate.', 2)
            #save to inactive events list
            active_games_dict[game_id]["Inactive Events"].append(chosen_event)
        
        case "Widespread Civil Disorder":
            #resolve event now
            notifications.append(f'New Event: {chosen_event}!', 2)
            #save as an active event
            active_event_dict = {}
            active_event_dict["Expiration"] = current_turn_num + 8
            active_games_dict[game_id]["Active Events"][chosen_event] = active_event_dict
        
        case "Embargo":
            notifications.append(f'New Event: {chosen_event}!', 2)
            active_games_dict = save_as_standard_delayed_event(chosen_event, active_games_dict, game_id, playerdata_list)

        case "Humiliation":
            notifications.append(f'New Event: {chosen_event}!', 2)
            active_games_dict = save_as_standard_delayed_event(chosen_event, active_games_dict, game_id, playerdata_list)

        case "Foreign Investment":
            notifications.append(f'New Event: {chosen_event}!', 2)
            active_games_dict = save_as_standard_delayed_event(chosen_event, active_games_dict, game_id, playerdata_list)

        case "Nominate Mediator":
            notifications.append(f'New Event: {chosen_event}!', 2)
            active_games_dict = save_as_standard_delayed_event(chosen_event, active_games_dict, game_id, playerdata_list)

        case "Shared Fate":
            notifications.append(f'New Event: {chosen_event}!', 2)
            active_games_dict = save_as_standard_delayed_event(chosen_event, active_games_dict, game_id, playerdata_list)

        case "Threat Containment":
            notifications.append(f'New Event: {chosen_event}!', 2)
            active_games_dict = save_as_standard_delayed_event(chosen_event, active_games_dict, game_id, playerdata_list)

        case "Foreign Invasion":
            notifications.append(f'New Event: {chosen_event}!', 2)
            with open(f'gamedata/{game_id}/regdata.json', 'r') as json_file:
                regdata_dict = json.load(json_file)
            region_id_list = list(regdata_dict.keys())
            while True:
                invasion_candidate_id = random.choice(region_id_list)
                invasion_candidate = Region(invasion_candidate_id, game_id)
                if invasion_candidate.is_edge:
                    invasion_point_id = invasion_candidate_id
                    break
            reinforcements_regions_list = []
            reinforcements_regions_list.append(invasion_point_id)
            invasion_point = Region(invasion_point_id, game_id)
            reinforcements_regions_list += invasion_point.adjacent_regions
            hex_colors_list = list(core.player_colors_conversions.keys())
            for playerdata in playerdata_list:
                if playerdata[2] in hex_colors_list:
                    hex_colors_list.remove(playerdata[2])
            random.shuffle(hex_colors_list)
            invasion_color = hex_colors_list.pop()
            #resolve event now
            if current_turn_num >= 24:
                unit_name = 'Main Battle Tank'
            elif current_turn_num >= 16:
                unit_name = 'Special Forces'
            else:
                unit_name = 'Mechanized Infantry'
            for region_id in reinforcements_regions_list:
                region = Region(region_id, game_id)
                region_improvement = Improvement(region_id, game_id)
                region_unit = Unit(region_id, game_id)
                region.set_owner_id(99)
                region.set_occupier_id(0)
                region_improvement.clear()
                region_unit.set_unit(unit_name, 0)
            #save as an active event
            active_event_dict = {}
            active_event_dict["Reinforcements Regions"] = reinforcements_regions_list
            active_event_dict["Invasion Color"] = invasion_color
            active_event_dict["Expiration"] = current_turn_num + 20
            active_games_dict[game_id]["Active Events"][chosen_event] = active_event_dict

        case "Pandemic":
            notifications.append(f'New Event: {chosen_event}!', 2)
            intensify_roll = random.randint(3, 9)
            spread_roll = random.randint(3, 9)
            with open(f'gamedata/{game_id}/regdata.json', 'r') as json_file:
                regdata_dict = json.load(json_file)
            region_id_list = list(regdata_dict.keys())
            origin_region_id = random.choice(region_id_list)
            #resolve event now
            region = Region(origin_region_id, game_id)
            region.add_infection()
            #save as an active event
            active_event_dict = {}
            active_event_dict["Intensify Value"] = intensify_roll
            active_event_dict["Spread Value"] = spread_roll
            active_event_dict["Completed Cure Research"] = 0
            active_event_dict["Needed Cure Research"] = len(playerdata_list) * 50
            active_event_dict["Closed Borders List"] = []
            active_games_dict[game_id]["Active Events"][chosen_event] = active_event_dict

        case "Faustian Bargain":
            notifications.append(f'New Event: {chosen_event}!', 2)
            effected_player_ids = []
            for index, playerdata in enumerate(playerdata_list):
                player_id = index + 1
                effected_player_ids.append(player_id)
            #save to Current Event key to be activated later
            active_games_dict[game_id]["Current Event"][chosen_event] = effected_player_ids

    #correct political power if outside capacity
    for playerdata in playerdata_list:
        political_power_economy_data = ast.literal_eval(playerdata[10])
        stored_political_power = float(political_power_economy_data[0])
        political_power_storage_limit = float(political_power_economy_data[1])
        if stored_political_power > political_power_storage_limit:
            political_power_economy_data[0] = political_power_economy_data[1]
            playerdata[10] = str(political_power_economy_data)
        elif stored_political_power < 0:
            political_power_economy_data[0] = '0.00'
            playerdata[10] = str(political_power_economy_data)
    
    return active_games_dict, playerdata_list

def save_as_standard_delayed_event(chosen_event: str, active_games_dict: dict, full_game_id: str, playerdata_list) -> dict:
    """
    Updates active_games_dict with a new current event.
    Used for all events in which there is a pending option / vote effecting all players.

    Params:
        chosen_event (str): A string that is the name of an event.
        active_games_dict (dict): A dictionary derived from the active_games.json file.
        full_game_id (str): The full game_id of the active game.
        playerdata_list (list of lists): A list of lists containing all playerdata derived from playerdata.csv

    Returns:
        active_games_dict (dict): A dictionary derived from the active_games.json file.
    """

    effected_player_ids = []
    for i in range(len(playerdata_list)):
        player_id = i + 1
        effected_player_ids.append(player_id)
    #save to Current Event key to be activated later
    active_games_dict[full_game_id]["Current Event"][chosen_event] = effected_player_ids

    return active_games_dict


#HANDLE CURRENT EVENTS
################################################################################

def handle_current_event(active_games_dict: dict, game_id: str) -> None:
    """
    Handles a current event when called by site code.

    Params:
        active_games_dict (dict): A dictionary derived from the active_games.json file.
        game_id (str): The full game_id of the active game.

    Returns:
        active_games_dict (dict): A dictionary derived from the active_games.json file.
    """
    
    #get game information
    playerdata_filepath = f'gamedata/{game_id}/playerdata.csv'
    playerdata_list = core.read_file(playerdata_filepath, 1)
    nation_name_list = []
    for playerdata in playerdata_list:
        nation_name_list.append(playerdata[1])
    with open(f'gamedata/{game_id}/regdata.json', 'r') as json_file:
        regdata_dict = json.load(json_file)
    player_action_logs = list([]*len(playerdata_list))
    current_turn_num = core.get_current_turn_num(int(game_id[-1]))
    notifications = Notifications(game_id)

    #get event data
    current_event_dict = active_games_dict[game_id]["Current Event"]
    event_name = None
    effected_player_ids_list = None
    for key, value in current_event_dict.items():
        event_name = key
        effected_player_ids_list = value
    
    #resolve outcome
    print(f'{event_name} Event Resolution')
    match event_name:

        case "Assassination":
            print("""Available Options: "Find the Perpetrator" or "Find a Scapegoat" """)
            decision_list = []
            for player_id in effected_player_ids_list:
                nation_name = nation_name_list[player_id - 1]
                while True:
                    decision = input(f"Enter {nation_name} decision: ")
                    if decision == "Find the Perpetrator" or decision == "Find a Scapegoat":
                        break
                decision_list.append(decision)
            for index, decision in enumerate(decision_list):
                player_id = effected_player_ids_list[index]
                if decision == "Find the Perpetrator":
                    political_power_economy_data = ast.literal_eval(playerdata_list[player_id - 1][10])
                    political_power_stored = float(political_power_economy_data[0])
                    political_power_stored -= 5
                    political_power_economy_data[0] = core.round_total_income(political_power_stored)
                    playerdata_list[player_id - 1][10] = str(political_power_economy_data)
                    scapegoat_nation_name = None
                elif decision == "Find a Scapegoat":
                    political_power_economy_data = ast.literal_eval(playerdata_list[player_id - 1][10])
                    political_power_stored = float(political_power_economy_data[0])
                    political_power_stored -= 10
                    political_power_economy_data[0] = core.round_total_income(political_power_stored)
                    playerdata_list[player_id - 1][10] = str(political_power_economy_data)
                    scapegoat_nation_name = input("Enter the nation name to scapegoat: ")
            active_event_dict = {}
            active_event_dict["Expiration"] = current_turn_num + 8
            active_event_dict["Scapegoat"] = scapegoat_nation_name
            active_games_dict[game_id]["Active Events"][event_name] = active_event_dict

        case "Diplomatic Summit":
            print("""Available Options: "Attend" or "Decline" """)
            summit_attendance_list = []
            for player_id in effected_player_ids_list:
                nation_name = nation_name_list[player_id - 1]
                while True:
                    decision = input(f"Enter {nation_name} decision: ")
                    if decision == "Attend":
                        summit_attendance_list.append(nation_name)
                        political_power_economy_data = ast.literal_eval(playerdata_list[player_id - 1][10])
                        political_power_stored = float(political_power_economy_data[0])
                        political_power_stored += 10
                        political_power_economy_data[0] = core.round_total_income(political_power_stored)
                        break
                    elif decision == "Decline":
                        valid_research = False
                        while not valid_research:
                            research_name = input(f"Enter military research: ")
                            playerdata_list, valid_research = gain_free_research(game_id, research_name, player_id, playerdata_list)
                        break
            active_event_dict = {}
            active_event_dict["Expiration"] = current_turn_num + 8
            active_event_dict["Attendance"] = summit_attendance_list
            active_games_dict[game_id]["Active Events"][event_name] = active_event_dict

        case "Foreign Interference":
            print("""Available Options: "Accept" or "Decline" """)
            bribe_takers_list = []
            war_declaration_list = []
            for player_id in effected_player_ids_list:
                nation_name = nation_name_list[player_id - 1]
                #there are currently no guiderails for this
                while True:
                    decision = input(f"Enter {nation_name} decision: ")
                    if decision == "Accept":
                        enemy_nation_name = input("Enter nation you wish to declare war on: ")
                        chosen_war_justification = input("Enter desired war justification: ")
                        war_declaration_list.append([player_id, f'War {enemy_nation_name} {chosen_war_justification}'])
                        bribe_takers_list.append(nation_name)
                        break
                    elif decision == "Decline":
                        political_power_economy_data = ast.literal_eval(playerdata_list[player_id - 1][10])
                        political_power_stored = float(political_power_economy_data[0])
                        political_power_stored += 5
                        political_power_economy_data[0] = core.round_total_income(political_power_stored)
                        break
            player_action_logs = private_actions.resolve_war_declarations(war_declaration_list, game_id, current_turn_num, player_action_logs)
            if bribe_takers_list != []:
                active_event_dict = {}
                active_event_dict["Bribe List"] = bribe_takers_list
                active_games_dict[game_id]["Active Events"][event_name] = active_event_dict
            else:
                active_games_dict[game_id]["Inactive Events"].append(event_name)

        case "Lost Nuclear Weapons":
            print("""Available Options: "Claim" or "Scuttle" """)
            for player_id in effected_player_ids_list:
                nation_name = nation_name_list[player_id - 1]
                while True:
                    decision = input(f"Enter {nation_name} decision: ")
                    if decision == "Claim":
                        valid_region_id = False
                        while not valid_region_id:
                            silo_location_id = input("Enter region id for Missile Silo: ")
                            silo_location_id = silo_location_id.upper()
                            if silo_location_id in regdata_dict:
                                valid_region_id = True
                        region_improvement = Improvement(valid_region_id, game_id)
                        region_improvement.set_improvement('Missile Silo')
                        missile_data = ast.literal_eval(playerdata_list[player_id - 1][21])
                        missile_data[1] += 3
                        playerdata_list[player_id - 1][21] = str(missile_data)
                        break
                    elif decision == "Scuttle":
                        technology_economy_data = ast.literal_eval(playerdata_list[player_id - 1][11])
                        technology_stored = float(technology_economy_data[0])
                        technology_limit = float(technology_economy_data[1])
                        technology_stored += 20
                        if technology_stored > technology_limit:
                            technology_stored = technology_limit
                        technology_economy_data[0] = core.round_total_income(technology_stored)
                        playerdata_list[player_id - 1][11] = str(technology_economy_data)
                        break
                notifications.append(f'{nation_name} chose to {decision.lower()} the old military installation.', 2)
            active_games_dict[game_id]["Inactive Events"].append(event_name)
        
        case "Major Security Breach":
            for player_id in effected_player_ids_list:
                breach_research_list = ast.literal_eval(playerdata_list[player_id - 1][26])
            for index, playerdata in enumerate(playerdata_list):
                player_id = index + 1
                nation_name = nation_name_list[player_id - 1]
                valid_research = False
                while not valid_research:
                    chosen_research = input(f"Enter {nation_name} chosen research: ")
                    if chosen_research in breach_research_list:
                        playerdata_list, valid_research = gain_free_research(game_id, chosen_research, player_id, playerdata_list)
            active_games_dict[game_id]["Inactive Events"].append(event_name)
            
        case "Peacetime Rewards":
            for player_id in effected_player_ids_list:
                valid_research = False
                while not valid_research:
                    research_name = input(f"Enter energy or infrastructure research: ")
                    playerdata_list, valid_research = gain_free_research(game_id, research_name, player_id, playerdata_list)
            active_games_dict[game_id]["Inactive Events"].append(event_name)

        case "Shifting Attitudes":
            print("""Available Options: "Keep" or "Change" """)
            for player_id in effected_player_ids_list:
                nation_name = nation_name_list[player_id - 1]
                while True:
                    decision = input(f"Enter {nation_name} decision: ")
                    if decision == "Change":
                        new_foreign_policy = input(f"Enter new foreign policy: ")
                        playerdata_list[player_id - 1][7][4] = new_foreign_policy
                        break
                    elif decision == "Keep":
                        political_power_economy_data = ast.literal_eval(playerdata_list[player_id - 1][10])
                        political_power_stored = float(political_power_economy_data[0])
                        political_power_stored += 10
                        political_power_economy_data[0] = core.round_total_income(political_power_stored)
                        playerdata_list[player_id - 1][10] = str(political_power_economy_data)
                        break
            active_games_dict[game_id]["Inactive Events"].append(event_name)

        case "Embargo":
            print("""Available Options: "# Nation Name" or "Abstain" """)
            vote_tally_dict = {}
            for player_id in effected_player_ids_list:
                nation_name = nation_name_list[player_id - 1]
                decision = input(f"Enter {nation_name} vote: ")
                decision = decision.strip().title()
                for select_nation_name in nation_name_list:
                    if select_nation_name in decision:
                        decision_data = decision.split()
                        vote_count = int(decision_data[0].strip())
                        if select_nation_name in vote_tally_dict:
                            vote_tally_dict[select_nation_name] += vote_count
                        else:
                            vote_tally_dict[select_nation_name] = vote_count
                        political_power_economy_data = ast.literal_eval(playerdata_list[player_id - 1][10])
                        political_power_stored = float(political_power_economy_data[0])
                        political_power_stored -= vote_count
                        political_power_economy_data[0] = core.round_total_income(political_power_stored)
                        playerdata_list[player_id - 1][10] = str(political_power_economy_data)
                        break
            sorted_vote_tally_dict = dict(sorted(vote_tally_dict.items(), key=lambda item: item[1], reverse=True))
            top_two = list(sorted_vote_tally_dict.items())[:2]
            (nation_name_1, count_1), (nation_name_2, count_2) = top_two
            if count_1 != count_2:
                notifications.append(f'With {count_1} votes, {nation_name_1} has been embargoed.', 2)
                active_event_dict = {}
                active_event_dict["Chosen Nation Name"] = nation_name_1
                active_event_dict["Expiration"] = current_turn_num + 8
                active_games_dict[game_id]["Active Events"][event_name] = active_event_dict
            else:
                notifications.append(f'Vote tied between {nation_name_1} and {nation_name_2}. No embargo will be placed.', 2)
                active_games_dict[game_id]["Inactive Events"].append(event_name)

        case "Humiliation":
            print("""Available Options: "# Nation Name" or "Abstain" """)
            vote_tally_dict = {}
            for player_id in effected_player_ids_list:
                nation_name = nation_name_list[player_id - 1]
                decision = input(f"Enter {nation_name} vote: ")
                decision = decision.strip().title()
                for select_nation_name in nation_name_list:
                    if select_nation_name in decision:
                        decision_data = decision.split()
                        vote_count = int(decision_data[0].strip())
                        if select_nation_name in vote_tally_dict:
                            vote_tally_dict[select_nation_name] += vote_count
                        else:
                            vote_tally_dict[select_nation_name] = vote_count
                        political_power_economy_data = ast.literal_eval(playerdata_list[player_id - 1][10])
                        political_power_stored = float(political_power_economy_data[0])
                        political_power_stored -= vote_count
                        political_power_economy_data[0] = core.round_total_income(political_power_stored)
                        playerdata_list[player_id - 1][10] = str(political_power_economy_data)
                        break
            sorted_vote_tally_dict = dict(sorted(vote_tally_dict.items(), key=lambda item: item[1], reverse=True))
            top_two = list(sorted_vote_tally_dict.items())[:2]
            (nation_name_1, count_1), (nation_name_2, count_2) = top_two
            if count_1 != count_2:
                notifications.append(f'With {count_1} votes, {nation_name_1} has been humiliated.', 2)
                active_event_dict = {}
                active_event_dict["Chosen Nation Name"] = nation_name_1
                active_event_dict["Expiration"] = current_turn_num + 8
                active_games_dict[game_id]["Active Events"][event_name] = active_event_dict
            else:
                notifications.append(f'Vote tied between {nation_name_1} and {nation_name_2}. No humiliation will occur.', 2)
                active_games_dict[game_id]["Inactive Events"].append(event_name)

        case "Foreign Investment":
            print("""Available Options: "# Nation Name" or "Abstain" """)
            vote_tally_dict = {}
            for player_id in effected_player_ids_list:
                nation_name = nation_name_list[player_id - 1]
                decision = input(f"Enter {nation_name} vote: ")
                decision = decision.strip().title()
                for select_nation_name in nation_name_list:
                    if select_nation_name in decision:
                        decision_data = decision.split()
                        vote_count = int(decision_data[0].strip())
                        if select_nation_name in vote_tally_dict:
                            vote_tally_dict[select_nation_name] += vote_count
                        else:
                            vote_tally_dict[select_nation_name] = vote_count
                        political_power_economy_data = ast.literal_eval(playerdata_list[player_id - 1][10])
                        political_power_stored = float(political_power_economy_data[0])
                        political_power_stored -= vote_count
                        political_power_economy_data[0] = core.round_total_income(political_power_stored)
                        playerdata_list[player_id - 1][10] = str(political_power_economy_data)
                        break
            sorted_vote_tally_dict = dict(sorted(vote_tally_dict.items(), key=lambda item: item[1], reverse=True))
            top_two = list(sorted_vote_tally_dict.items())[:2]
            (nation_name_1, count_1), (nation_name_2, count_2) = top_two
            if count_1 != count_2:
                notifications.append(f'With {count_1} votes, {nation_name_1} will receive the foreign investment.', 2)
                active_event_dict = {}
                active_event_dict["Chosen Nation Name"] = nation_name_1
                active_event_dict["Expiration"] = current_turn_num + 8
                active_games_dict[game_id]["Active Events"][event_name] = active_event_dict
            else:
                notifications.append(f'Vote tied between {nation_name_1} and {nation_name_2}. No foreign investment will occur.', 2)
                active_games_dict[game_id]["Inactive Events"].append(event_name)

        case "Nominate Mediator":
            print("""Available Options: "# Nation Name" or "Abstain" """)
            vote_tally_dict = {}
            for player_id in effected_player_ids_list:
                nation_name = nation_name_list[player_id - 1]
                decision = input(f"Enter {nation_name} vote: ")
                decision = decision.strip().title()
                for select_nation_name in nation_name_list:
                    if select_nation_name in decision:
                        decision_data = decision.split()
                        vote_count = int(decision_data[0].strip())
                        if select_nation_name in vote_tally_dict:
                            vote_tally_dict[select_nation_name] += vote_count
                        else:
                            vote_tally_dict[select_nation_name] = vote_count
                        political_power_economy_data = ast.literal_eval(playerdata_list[player_id - 1][10])
                        political_power_stored = float(political_power_economy_data[0])
                        political_power_stored -= vote_count
                        political_power_economy_data[0] = core.round_total_income(political_power_stored)
                        playerdata_list[player_id - 1][10] = str(political_power_economy_data)
                        break
            sorted_vote_tally_dict = dict(sorted(vote_tally_dict.items(), key=lambda item: item[1], reverse=True))
            print(sorted_vote_tally_dict)
            top_two = list(sorted_vote_tally_dict.items())[:2]
            (nation_name_1, count_1), (nation_name_2, count_2) = top_two
            if count_1 != count_2:
                notifications.append(f'With {count_1} votes, {nation_name_1} has been elected Mediator.', 2)
                active_event_dict = {}
                active_event_dict["Chosen Nation Name"] = nation_name_1
                active_event_dict["Expiration"] = current_turn_num + 8
                active_event_dict["Extended Truces List"] = []
                active_games_dict[game_id]["Active Events"][event_name] = active_event_dict
            else:
                notifications.append(f'Vote tied between {nation_name_1} and {nation_name_2}. No nation will be elected Mediator.', 2)
                active_games_dict[game_id]["Inactive Events"].append(event_name)

        case "Shared Fate":
            print("""Available Options: "# Effect" or "Abstain" """)
            vote_tally_dict = {
                "Cooperation": 0,
                "Conflict": 0,
            }
            for player_id in effected_player_ids_list:
                nation_name = nation_name_list[player_id - 1]
                decision = input(f"Enter {nation_name} vote: ")
                decision = decision.strip().title()
                if "Cooperation" in decision:
                    decision_data = decision.split()
                    vote_count = int(decision_data[0].strip())
                    vote_tally_dict["Cooperation"] += vote_count
                    political_power_economy_data = ast.literal_eval(playerdata_list[player_id - 1][10])
                    political_power_stored = float(political_power_economy_data[0])
                    political_power_stored -= vote_count
                    political_power_economy_data[0] = core.round_total_income(political_power_stored)
                    playerdata_list[player_id - 1][10] = str(political_power_economy_data)
                elif "Conflict" in decision:
                    decision_data = decision.split()
                    vote_count = int(decision_data[0].strip())
                    vote_tally_dict["Conflict"] += vote_count
                    political_power_economy_data = ast.literal_eval(playerdata_list[player_id - 1][10])
                    political_power_stored = float(political_power_economy_data[0])
                    political_power_stored -= vote_count
                    political_power_economy_data[0] = core.round_total_income(political_power_stored)
                    playerdata_list[player_id - 1][10] = str(political_power_economy_data)
            cooperation_count = vote_tally_dict["Cooperation"]
            conflict_count = vote_tally_dict["Conflict"]
            if cooperation_count != conflict_count:
                if cooperation_count > conflict_count:
                    chosen_effect = "Cooperation"
                    notifications.append(f"By a vote of {cooperation_count} to {conflict_count}, {chosen_effect} wins.", 2)
                elif cooperation_count < conflict_count:
                    chosen_effect = "Conflict"
                    notifications.append(f"By a vote of {conflict_count} to {cooperation_count}, {chosen_effect} wins.", 2)
                active_event_dict = {}
                active_event_dict["Effect"] = chosen_effect
                active_games_dict[game_id]["Active Events"][event_name] = active_event_dict
            else:
                notifications.append(f'Vote tied between Cooperation and Conflict. No effect will be resolved.', 2)
                active_games_dict[game_id]["Inactive Events"].append(event_name)

        case "Threat Containment":
            print("""Available Options: "# Nation Name" or "Abstain" """)
            vote_tally_dict = {}
            for player_id in effected_player_ids_list:
                nation_name = nation_name_list[player_id - 1]
                decision = input(f"Enter {nation_name} vote: ")
                decision = decision.strip().title()
                for select_nation_name in nation_name_list:
                    if select_nation_name in decision:
                        decision_data = decision.split()
                        vote_count = int(decision_data[0].strip())
                        if select_nation_name in vote_tally_dict:
                            vote_tally_dict[select_nation_name] += vote_count
                        else:
                            vote_tally_dict[select_nation_name] = vote_count
                        political_power_economy_data = ast.literal_eval(playerdata_list[player_id - 1][10])
                        political_power_stored = float(political_power_economy_data[0])
                        political_power_stored -= vote_count
                        political_power_economy_data[0] = core.round_total_income(political_power_stored)
                        playerdata_list[player_id - 1][10] = str(political_power_economy_data)
                        break
            if vote_tally_dict != {}:
                sorted_vote_tally_dict = dict(sorted(vote_tally_dict.items(), key=lambda item: item[1], reverse=True))
                top_two = list(sorted_vote_tally_dict.items())[:2]
                (nation_name_1, count_1), (nation_name_2, count_2) = top_two
            else:
                count_1 = 0
                count_2 = 0
            if count_1 != count_2:
                notifications.append(f'With {count_1} votes, {nation_name_1} will be sanctioned.', 2)
                active_event_dict = {}
                active_event_dict["Chosen Nation Name"] = nation_name_1
                active_event_dict["Expiration"] = current_turn_num + 8
                active_games_dict[game_id]["Active Events"][event_name] = active_event_dict
            elif count_1 == 0 and count_2 == 0:
                notifications.append(f'All nations abstained. No nation will be sanctioned.', 2)
                active_games_dict[game_id]["Inactive Events"].append(event_name)
            else:
                notifications.append(f'Vote tied between {nation_name_1} and {nation_name_2}. No nation will be sanctioned.', 2)
                active_games_dict[game_id]["Inactive Events"].append(event_name)

        case "Faustian Bargain":
            print("""Available Options: "Accept" or "Decline" """)
            candidates_list = []
            for player_id in effected_player_ids_list:
                nation_name = nation_name_list[player_id - 1]
                while True:
                    decision = input(f"Enter {nation_name} decision: ")
                    if decision == "Accept":
                        if core.has_capital(player_id, game_id):
                            candidates_list.append(nation_name)
                            break
                    elif decision == "Decline":
                        political_power_economy_data = ast.literal_eval(playerdata_list[player_id - 1][10])
                        political_power_stored = float(political_power_economy_data[0])
                        political_power_stored += 5
                        political_power_economy_data[0] = core.round_total_income(political_power_stored)
                        break
            if candidates_list != []:
                random.shuffle(candidates_list)
                chosen_nation_name = candidates_list.pop()
                notifications.append(f'{chosen_nation_name} took the Faustian Bargain and will collaborate with the foreign nation.', 2)
                active_event_dict = {}
                active_event_dict["Chosen Nation Name"] = chosen_nation_name
                active_event_dict["Leased Regions List"] = []
                active_games_dict[game_id]["Active Events"][event_name] = active_event_dict
            else:
                notifications.append("No nation took the Faustian Bargain. collaborate with the foreign nation.", 2)
                active_games_dict[game_id]["Inactive Events"].append(event_name)

    #correct political power if outside capacity
    for playerdata in playerdata_list:
        political_power_economy_data = ast.literal_eval(playerdata[10])
        stored_political_power = float(political_power_economy_data[0])
        political_power_storage_limit = float(political_power_economy_data[1])
        if stored_political_power > political_power_storage_limit:
            political_power_economy_data[0] = political_power_economy_data[1]
            playerdata[10] = str(political_power_economy_data)
        elif stored_political_power < 0:
            political_power_economy_data[0] = '0.00'
            playerdata[10] = str(political_power_economy_data)

    #save files
    active_games_dict[game_id]["Current Event"] = {}
    with open('active_games.json', 'w') as json_file:
        json.dump(active_games_dict, json_file, indent=4)

    with open(playerdata_filepath, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(core.player_data_header)
        writer.writerows(playerdata_list)

def gain_free_research(game_id, research_name, player_id, playerdata_list):
    """
    Returns updated playerdata_List and a bool that is True if the research was valid, False otherwise.
    """

    player_government = playerdata_list[player_id - 1][3]
    player_political_power_data = ast.literal_eval(playerdata_list[player_id - 1][10])
    player_stored_political_power = float(player_political_power_data[0])
    player_research_list = ast.literal_eval(playerdata_list[player_id - 1][26])
    research_data_dict = core.get_scenario_dict(game_id, "Technologies")
    research_prereq = research_data_dict[research_name]['Prerequisite']

    valid_research = True
    if research_name in player_research_list:
        valid_research = False
    if research_prereq != None and research_prereq not in player_research_list:
        valid_research = False
    if valid_research:
        player_research_list.append(research_name)
        if player_government == 'Totalitarian':
            totalitarian_bonus_list = []
            for key, value in research_data_dict.items():
                if value.get("Research Type") in ['Energy', 'Infrastructure']:
                    totalitarian_bonus_list.append(key)
            if research_name in totalitarian_bonus_list:
                player_stored_political_power += 2

    player_political_power_data[0] = core.round_total_income(player_stored_political_power)
    playerdata_list[player_id - 1][10] = str(player_political_power_data)
    playerdata_list[player_id - 1][26] = str(player_research_list)

    return playerdata_list, valid_research
    

#HANDLE ACTIVE EVENTS
################################################################################

def resolve_active_events(turn_status, public_actions_dict, private_actions_dict, full_game_id):
    """
    Function that handles active events depending on turn status.

    Paramteters:
    - turn_status: A string that is either "Before Actions" or "After Actions".
    - full_game_id: The full game_id of the active game.
    """

    with open('active_games.json', 'r') as json_file:
        active_games_dict = json.load(json_file)

    active_events_list = list(active_games_dict[full_game_id]["Active Events"].keys())
    for event_name in active_events_list:
        public_actions_dict, private_actions_dict, active_games_dict = handle_active_event(event_name, public_actions_dict, private_actions_dict, active_games_dict, full_game_id, turn_status)
    
    with open('active_games.json', 'w') as json_file:
        json.dump(active_games_dict, json_file, indent=4)

    return public_actions_dict, private_actions_dict

def handle_active_event(event_name, public_actions_dict, private_actions_dict, active_games_dict, game_id, turn_status):
    """
    For active events that require special handling which cannot be integrated cleanly in other game code.
    Also retires any active events that expire at end of turn
    """

    #get game information
    playerdata_filepath = f'gamedata/{game_id}/playerdata.csv'
    playerdata_list = core.read_file(playerdata_filepath, 1)
    current_turn_num = core.get_current_turn_num(int(game_id[-1]))
    with open(f'gamedata/{game_id}/regdata.json', 'r') as json_file:
        regdata_dict = json.load(json_file)
    notifications = Notifications(game_id)
    
    #resolve active event
    match event_name:
        

        case "Foreign Invasion":
            
            if turn_status == "Before Actions":
                #add move orders to action dictionary
                for region_id in regdata_dict:
                    region = Region(region_id, game_id)
                    region_unit = Unit(region_id, game_id)
                    if region_unit.name != None and region_unit.owner_id == 0:
                        destination_dict = {}
                        ending_region_id, priority = determine_target_region(region.adjacent_regions, destination_dict, game_id)
                        destination_dict[ending_region_id] = priority
                        if ending_region_id is not None:
                            movement_action_str = f'Move {region_id}-{ending_region_id}'
                            private_actions_dict['Move'].append([99, movement_action_str])
                #add deploy orders to action dictionary
                if current_turn_num % 4 == 0:
                    notifications.append("The Foreign Invasion has received reinforcements.", 2)
                    for region_id in regdata_dict:
                        region = Region(region_id, game_id)
                        if region.owner_id == 99 and region.occupier_id == 0:
                            if current_turn_num >= 32:
                                unit_name = 'Heavy Tank'
                            elif current_turn_num >= 24:
                                unit_name = 'Special Forces'
                            else:
                                unit_name = 'Mechanized Infantry'
                            deploy_action_str = f'Deploy {unit_name} {region_id}'
                            private_actions_dict['Deploy'].append([99, deploy_action_str])

            if turn_status == "After Actions":
                #check if Foreign Invasion has no remaining units
                invasion_unit_count = 0
                for region_id in regdata_dict:
                    region_unit = Unit(region_id, game_id)
                    if region_unit.name != None and region_unit.owner_id == 0:
                        invasion_unit_count += 1
                if invasion_unit_count == 0:
                    end_foreign_invasion(game_id)
                #check if Foreign Invasion has no unoccupied reinforcement regions
                invasion_unoccupied_count = 0
                for region_id in active_games_dict[game_id]['Active Events'][event_name]["Reinforcements Regions"]:
                    region = Region(region_id, game_id)
                    if region.occupier_id == 0:
                        invasion_unoccupied_count += 1
                if invasion_unoccupied_count == 0:
                    end_foreign_invasion(game_id)


        case "Pandemic":
            
            if turn_status == "After Actions":
                intensify_value = active_games_dict[game_id]['Active Events'][event_name]["Intensify Value"]
                spread_value = active_games_dict[game_id]['Active Events'][event_name]["Spread Value"]
                completed_cure_research = active_games_dict[game_id]['Active Events'][event_name]["Completed Cure Research"]
                needed_cure_research = active_games_dict[game_id]['Active Events'][event_name]["Needed Cure Research"]
                closed_borders_player_ids_list = active_games_dict[game_id]['Active Events'][event_name]["Closed Borders List"]
                cure_percentage = float(completed_cure_research) / float(needed_cure_research)
                cure_percentage = round(cure_percentage, 2)
                if completed_cure_research >= needed_cure_research:
                    #run pandemic decline procedure
                    for region_id in regdata_dict:
                        region = Region(region_id, game_id)
                        region.add_infection(-2)
                else:
                    #conduct intensify rolls
                    for region_id in regdata_dict:
                        region = Region(region_id, game_id)
                        if region.infection() > 0 and region.infection() < 10:
                            intensify_roll = random.randint(1, 10)
                            if intensify_roll >= intensify_value:
                                if region.check_for_adjacent_improvement(improvement_names = {'Capital', 'City'}):
                                    region.add_infection(2)
                                else:
                                    region.add_infection(1)
                    #conduct spread roles
                    # to do - make closed_borders_player_ids_list a dictionary instead of a list to improve runtime
                    for region_id in regdata_dict:
                        region = Region(region_id, game_id)
                        if region.infection() > 0:
                            for adjacent_region_id in region.adjacent_regions:
                                adjacent_region = Region(adjacent_region_id, game_id)
                                adjacent_owner_id = adjacent_region.owner_id
                                if adjacent_region.infection() == 0:
                                    if region.is_quarantined() or region.owner_id != adjacent_owner_id and adjacent_owner_id in closed_borders_player_ids_list:
                                        spread_roll = random.randint(1, 20)
                                        if spread_roll == 20:
                                            adjacent_region.add_infection(1)
                                    else:
                                        spread_roll = random.randint(1, 10)
                                        if spread_roll >= spread_value:
                                            adjacent_region.add_infection(1)
                #get total infection scores
                infection_scores = [0] * len(playerdata_list)
                for region_id in regdata_dict:
                    region = Region(region_id, game_id)
                    owner_id = region.owner_id
                    if owner_id != 0 and owner_id <= len(infection_scores):
                        infection_scores[owner_id - 1] += region.infection()
                #check if pandemic has been eradicated
                infection_total = sum(infection_scores)
                if infection_total == 0:
                    for region_id in regdata_dict:
                        region = Region(region_id, game_id)
                        if region.is_quarantined():
                            region.set_quarantine(False)
                    del active_games_dict[game_id]['Active Events'][event_name]
                    active_games_dict[game_id]["Inactive Events"].append(event_name)
                    notifications.append("The pandemic has been eradicated!", 2)
                #print diplomacy log messages
                if infection_total != 0:
                    if cure_percentage >= 0.5:
                        notifications.append(f"Pandemic intensify value: {intensify_value}", 2)
                        notifications.append(f"Pandemic spread value: {spread_value}", 2)
                    if cure_percentage >= 0.75:
                        for index, score in enumerate(infection_scores):
                            nation_name = playerdata_list[index][1]
                            notifications.append(f"{nation_name} pandemic infection score: {score}", 2)
                    if cure_percentage < 1:
                        notifications.append(f"Pandemic cure research progress: {completed_cure_research}/{needed_cure_research}", 2)
                    else:
                        notifications.append(f"Pandemic cure research has been completed! The pandemic is now in decline.", 2)
                
        case "Faustian Bargain":

            if turn_status == "After Actions":
                nation_name_list = []
                for playerdata in playerdata_list:
                    nation_name_list.append(playerdata[1])
                chosen_nation_name = active_games_dict[game_id]["Active Events"][event_name]["Chosen Nation Name"]
                player_id = nation_name_list.index(chosen_nation_name) + 1
                #check if leased regions have changed hands
                for region_id in active_games_dict[game_id]["Active Events"]["Faustian Bargain"]["Leased Regions List"]:
                    region = Region(region_id, game_id)
                    if region.owner_id != player_id:
                        active_games_dict[game_id]["Active Events"]["Faustian Bargain"]["Leased Regions List"].remove(region_id)
                        notifications.append(f"{region_id} is no longer being leased to the foreign nation.", 2)
                #check if bargain has been defeated (no capital)
                if not core.has_capital(player_id, game_id):
                    del active_games_dict[game_id]['Active Events'][event_name]
                    active_games_dict[game_id]["Inactive Events"].append(event_name)
                    notifications.append(f"{event_name} event has ended.", 2)

    #retire active events if expired at end of turn
    current_turn_num = int(active_games_dict[game_id]["Statistics"]["Current Turn"])
    if turn_status == "After Actions" and event_name in active_games_dict[game_id]['Active Events']:
        if "Expiration" in active_games_dict[game_id]['Active Events'][event_name]:
            if active_games_dict[game_id]['Active Events'][event_name]["Expiration"] == current_turn_num:
                #handle special cases
                if event_name == "Foreign Invasion":
                    end_foreign_invasion(game_id)
                del active_games_dict[game_id]['Active Events'][event_name]
                active_games_dict[game_id]["Inactive Events"].append(event_name)
                notifications.append(f"{event_name} event has ended.", 2)
            else:
                #add active event to diplomacy log
                notifications.append(f"{event_name} event is ongoing.", 2)

    #save files
    with open(playerdata_filepath, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(core.player_data_header)
        writer.writerows(playerdata_list)

    return public_actions_dict, private_actions_dict, active_games_dict
    
def determine_target_region(adjacency_list, destination_dict, game_id):
    """
    Function that contains Foreign Invasion attack logic.
    Designed to find path of least resistance but has no care for the health of its own units.
    """
    
    random.shuffle(adjacency_list)
    target_region_id = None
    target_region_health = 0
    target_region_priority = -1

    for adjacent_region_id in adjacency_list:
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

def end_foreign_invasion(game_id):
    
    with open(f'gamedata/{game_id}/regdata.json', 'r') as json_file:
        regdata_dict = json.load(json_file)
    
    for region_id in regdata_dict:
        region = Region(game_id, region_id)
        region_unit = Unit(game_id, region_id)
        if region.owner_id == 99:
            region.set_owner_id(0)
            region.set_occupier_id(0)
        if region.occupier_id == 99:
            region.set_occupier_id(0)
        if region_unit.name != None and region_unit.owner_id != 0:
            region_unit.clear()


#EVENT DICTIONARY
################################################################################

EVENT_DICT = {
    "Assassination": {
        "Type": "Standard Event",
        "Resolution": "Delayed Option",
        "Conditions List": []
    },
    "Coup D'état": {
        "Type": "Standard Event",
        "Resolution": "Instant",
        "Conditions List": ["Cannot be First Event"]
    },
    "Decaying Infrastructure": {
        "Type": "Standard Event",
        "Resolution": "Instant",
        "Conditions List": ["Cannot be First Event"]
    },
    "Defection": {
        "Type": "Standard Event",
        "Resolution": "Instant",
        "Conditions List": ["Ongoing Wars >= 1"]
    },
    "Diplomatic Summit": {
        "Type": "Standard Event",
        "Resolution": "Delayed Option",
        "Conditions List": []
    },
    "Foreign Aid": {
        "Type": "Standard Event",
        "Resolution": "Instant",
        "Conditions List": []
    },
    "Foreign Interference": {
        "Type": "Standard Event",
        "Resolution": "Delayed Option",
        "Conditions List": ["Cannot be First Event"]
    },
    "Lost Nuclear Weapons": {
        "Type": "Standard Event",
        "Resolution": "Delayed Option",
        "Conditions List": []
    },
    "Major Security Breach": {
        "Type": "Standard Event",
        "Resolution": "Delayed Option",
        "Conditions List": ["No Most Research Tie"]
    },
    "Market Inflation": {
        "Type": "Standard Event",
        "Resolution": "Instant",
        "Conditions List": []
    },
    "Market Recession": {
        "Type": "Standard Event",
        "Resolution": "Instant",
        "Conditions List": []
    },
    "Observer Status Invitation": {
        "Type": "Standard Event",
        "Resolution": "Delayed Option",
        "Conditions List": []
    },
    "Peacetime Rewards": {
        "Type": "Standard Event",
        "Resolution": "Instant",
        "Conditions List": ["Cannot be First Event", "At Peace For At Least 8 Turns >= 1"]
    },
    "Power Plant Meltdown": {
        "Type": "Standard Event",
        "Resolution": "Instant",
        "Conditions List": ["Global Nuclear Power Plant Count >= 1"]
    },
    "Shifting Attitudes": {
        "Type": "Standard Event",
        "Resolution": "Delayed Option",
        "Conditions List": ["Cannot be First Event"]
    },
    "United Nations Peacekeeping Mandate": {
        "Type": "Standard Event",
        "Resolution": "Instant",
        "Conditions List": ["Ongoing Wars >= 3"]
    },
    "Widespread Civil Disorder": {
        "Type": "Standard Event",
        "Resolution": "Instant",
        "Conditions List": ["Cannot be First Event"]
    },
    "Embargo": {
        "Type": "Voting Events",
        "Resolution": "Delayed Vote",
        "Conditions List": []
    },
    "Humiliation": {
        "Type": "Voting Events",
        "Resolution": "Delayed Vote",
        "Conditions List": []
    },
    "Foreign Investment": {
        "Type": "Voting Events",
        "Resolution": "Delayed Vote",
        "Conditions List": []
    },
    "Nominate Mediator": {
        "Type": "Voting Events",
        "Resolution": "Delayed Vote",
        "Conditions List": []
    },
    "Shared Fate": {
        "Type": "Voting Events",
        "Resolution": "Delayed Vote",
        "Conditions List": []
    },
    "Threat Containment": {
        "Type": "Voting Events",
        "Resolution": "Delayed Vote",
        "Conditions List": []
    },
    "Foreign Invasion": {
        "Type": "Major Event",
        "Resolution": "Instant",
        "Conditions List": ["Cannot be First Event", "No Major Event"]
    },
    "Pandemic": {
        "Type": "Major Event",
        "Resolution": "Instant",
        "Conditions List": ["Cannot be First Event", "No Major Event"]
    },
    "Faustian Bargain": {
        "Type": "Major Event",
        "Resolution": "Instant",
        "Conditions List": ["Cannot be First Event", "No Major Event"]
    },
}
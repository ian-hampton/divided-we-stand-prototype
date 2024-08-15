import ast
import csv
import json
import random

from app import core
from app import private_actions
from app import checks

#EVENT INITIATION CODE
################################################################################

def trigger_event(full_game_id, current_turn_num, diplomacy_log):
    '''
    Activates and resolves a random event. Returns an updated diplomacy_log.

    Parameters:
    - full_game_id: The full game_id of the active game.
    - current_turn_num: An integer representing the current turn number.
    - diplomacy_log: A list of pre-generated diplomatic interaction logs.
    '''

    with open('active_games.json', 'r') as json_file:
        active_games_dict = json.load(json_file)

    playerdata_filepath = f'gamedata/{full_game_id}/playerdata.csv'
    playerdata_list = core.read_file(playerdata_filepath, 1)

    regdata_filepath = f'gamedata/{full_game_id}/regdata.csv'
    regdata_list = core.read_file(regdata_filepath, 2)

    wardata_filepath = f'gamedata/{full_game_id}/wardata.csv'
    wardata_list = core.read_file(wardata_filepath, 2)

    events_list = list(EVENT_DICT.keys())
    random.shuffle(events_list)
    event_conditions_dict = build_event_conditions_dict(full_game_id, current_turn_num, playerdata_list, active_games_dict)
    already_chosen_events_list = []
    already_chosen_events_list += active_games_dict[full_game_id]["Inactive Events"]
    already_chosen_events_list += [key for key in active_games_dict[full_game_id]["Active Events"]]
    event_override = None

    chosen_event = None
    while True:
        chosen_event = events_list.pop()
        if event_override is not None:
            chosen_event = event_override
        if event_conditions_met(chosen_event, event_conditions_dict, full_game_id, active_games_dict) and chosen_event not in already_chosen_events_list:
            print(chosen_event)
            active_games_dict, playerdata_list, regdata_list, wardata_list, diplomacy_log = initiate_event(chosen_event, event_conditions_dict, full_game_id, current_turn_num, active_games_dict, playerdata_list, regdata_list, wardata_list, diplomacy_log)
            break

    with open('active_games.json', 'w') as json_file:
        json.dump(active_games_dict, json_file, indent=4)

    with open(playerdata_filepath, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(core.player_data_header)
        writer.writerows(playerdata_list)

    with open(regdata_filepath, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(core.regdata_header_a)
        writer.writerow(core.regdata_header_b)
        writer.writerows(regdata_list)

    with open(wardata_filepath, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(core.wardata_header_a)
        writer.writerow(core.wardata_header_b)
        writer.writerows(wardata_list)

    return diplomacy_log

def build_event_conditions_dict(full_game_id, current_turn_num, playerdata_list, active_games_dict):
    '''
    Returns a dictionary of event condition data generated from game data.

    Parameters:
    - full_game_id: The full game_id of the active game.
    - current_turn_num: An integer representing the current turn number.
    - playerdata_list: A list of lists containing all playerdata derived from playerdata.csv
    - active_games_dict: A dictionary derived from the active_games.json file.
    '''

    wardata_filepath = f'gamedata/{full_game_id}/wardata.csv'
    wardata_list = core.read_file(wardata_filepath, 2)

    event_conditions_dict = {
        "At Peace For At Least 8 Turns": [],
        "Event Count": len(active_games_dict[full_game_id]["Active Events"]) + len(active_games_dict[full_game_id]["Inactive Events"]),
        "Global Improvement Count List": [0 * len(core.improvement_data_dict)],
        "Greater Than 5 Stability": [],
        "Less Than 8 Stability": [],
        "Lass Than 4 Stability": [],
        "Most Research": "N/A",
        "Ongoing Wars": [],
        "Players at War": [],
        "Defeat Penalty": [],
    }

    nation_name_list = []
    for index, playerdata in enumerate(playerdata_list):
        player_id = index + 1
        player_improvement_count_list = ast.literal_eval(playerdata[27])
        event_conditions_dict["Global Improvement Count List"] = [x + y for x, y in zip(player_improvement_count_list, event_conditions_dict["Global Improvement Count List"])]
        stability_data = ast.literal_eval(playerdata[7])
        stability_header_list = stability_data[0].split(" ")
        stability_header_list = stability_header_list[1].split("/")
        stability_value = int(stability_header_list[0])
        if stability_value < 8 and stability_value > 5:
            event_conditions_dict["Less Than 8 Stability"].append(player_id)
            event_conditions_dict["Greater Than 5 Stability"].append(player_id)
        elif stability_value > 5:
            event_conditions_dict["Greater Than 5 Stability"].append(player_id)
        elif stability_value < 4:
            event_conditions_dict["Lass Than 4 Stability"].append(player_id)
        for stability_data_entry in stability_data:
            if "from Defeat" in stability_data_entry:
                event_conditions_dict["Defeat Penalty"].append(player_id)
                break
        nation_name_list.append(playerdata[1])
    
    research_1st, research_2nd, research_3rd = checks.get_top_three(full_game_id, 'most_research', True)
    research_1st_data = research_1st.split()
    research_2nd_data = research_2nd.split()
    if research_1st_data[-1] != research_2nd_data[-1]:
        for nation_name in nation_name_list:
            if nation_name in research_1st:
                event_conditions_dict["Most Research"] = nation_name
                break
    
    wardata_list = wardata_list.reverse()
    try:
        for war in wardata_list:
            event_conditions_dict["Ongoing Wars"].append(war[11])
            war_start = int(war[12])
            players_at_war = []
            for player_id in range(1, len(playerdata_list) + 1):
                if war[player_id] != '-' and current_turn_num - war_start <= 8:
                    players_at_war.append(players_at_war)
            players_at_war = set(players_at_war)
            for player_id in range(1, len(playerdata_list) + 1):
                if player_id not in players_at_war:
                    event_conditions_dict["At Peace For At Least 8 Turns"].append(player_id)
            for player_id in players_at_war:
                if players_at_war not in event_conditions_dict["Players at War"]:
                    event_conditions_dict["Players at War"].append(player_id)
    except(TypeError):
        for player_id in range(1, len(playerdata_list) + 1):
            event_conditions_dict["At Peace For At Least 8 Turns"].append(player_id)

    return event_conditions_dict

def event_conditions_met(chosen_event, event_conditions_dict, full_game_id, active_games_dict):
    '''
    Returns True if the conditions of an event are met, otherwise returns False.

    Parameters:
    - chosen_event: A string that is the name of an event.
    - event_conditions_dict: A dictionary of event conditions data generated from build_event_conditions_dict().
    - active_games_dict: A dictionary derived from the active_games.json file.
    '''

    if chosen_event in active_games_dict[full_game_id]["Inactive Events"]:
        return False
    
    for condition in EVENT_DICT[chosen_event]["Conditions List"]:
        match condition:
            case "Cannot be First Event":
                if event_conditions_dict["Event Count"] == 0:
                    return False
            case "At Peace For At Least 8 Turns >= 1":
                if len(event_conditions_dict["At Peace For At Least 8 Turns"]) == 0:
                    return False
            case "Greater Than 5 Stability":
                if len(event_conditions_dict["Greater Than 5 Stability"]) == 0:
                    return False
            case "Less Than 8 Stability >= 1":
                if len(event_conditions_dict["Less Than 8 Stability >= 1"]) == 0:
                    return False
            case "Less Than 4 Stability >= 1":
                if len(event_conditions_dict["Less Than 4 Stability >= 1"]) == 0:
                    return False
            case "Ongoing Wars >= 3":
                if len(event_conditions_dict["Ongoing Wars"]) < 3:
                    return False
            case "Ongoing Wars >= 1":
                if len(event_conditions_dict["Ongoing Wars"]) == 0:
                    return False
            case "Defeat Penalty >= 1":
                if len(event_conditions_dict["Defeat Penalty"]) == 0:
                    return False
            case "No Most Research Tie":
                if event_conditions_dict["Most Research"] == "N/A":
                    return False
            case "No Major Event":
                major_event_list = [event_name for event_name, data in EVENT_DICT.items() if data.get('Type') == 'Major Event']
                for event in active_games_dict[full_game_id]["Active Events"]:
                    if event in major_event_list:
                        return False
                for event in active_games_dict[full_game_id]["Inactive Events"]:
                    if event in major_event_list:
                        return False
            case _:
                improvement_name_list = sorted(core.improvement_data_dict.keys())
                for improvement in improvement_name_list:
                    if improvement in condition:
                        improvement_index = improvement_name_list.index(improvement)
                        improvement_count = event_conditions_dict["Global Improvement Count List"][improvement_index]
                        if improvement_count == 0:
                            return False
        return False
    
    return True

def initiate_event(chosen_event, event_conditions_dict, full_game_id, current_turn_num, active_games_dict, playerdata_list, regdata_list, wardata_list, diplomacy_log):
    '''
    Initiates the chosen event. If it is an instant resolution event, it will be resolved.

    Parameters:
    - Too many to count, this function is insane.
    '''

    nation_name_list = []
    for playerdata in playerdata_list:
        nation_name_list.append(playerdata[1])

    match chosen_event:

        case "Assassination":
            less_then_8_stability_list = event_conditions_dict["Less Than 8 Stability"]
            random.shuffle(less_then_8_stability_list)
            victim_player_id = less_then_8_stability_list.pop()
            victim_nation_name = playerdata_list[victim_player_id - 1][1]
            diplomacy_log.append(f'{victim_nation_name} has been randomly selected for the {chosen_event} event!')
            #save to Current Event key to be activated later
            active_games_dict[full_game_id]["Current Event"][chosen_event] = [victim_player_id]
        
        case "Coup D'état":
            less_then_4_stability_list = event_conditions_dict["Less Than 4 Stability"]
            random.shuffle(less_then_4_stability_list)
            victim_player_id = less_then_4_stability_list.pop()
            victim_nation_name = playerdata_list[victim_player_id - 1][1]
            #resolve event now
            old_government = playerdata_list[victim_player_id - 1][3]
            gov_list = ['Republic', 'Technocracy', 'Oligarchy', 'Totalitarian', 'Remnant', 'Protectorate', 'Military Junta', 'Crime Syndicate']
            gov_list.remove(playerdata_list[victim_player_id - 1][3])
            random.shuffle(gov_list)
            new_government = gov_list.pop()
            playerdata_list[victim_player_id - 1][3] = new_government
            diplomacy_log.append(f"{victim_nation_name}'s {old_government} has been defeated by a coup. Government changed to {new_government}.")
            #save to inactive events list
            active_games_dict[full_game_id]["Inactive Events"].append(chosen_event)
        
        case "Decaying Infrastructure":
            less_then_6_stability_list = []
            for player_id in range(len(playerdata_list)):
                if player_id not in event_conditions_dict["Greater Than 5 Stability"]:
                    less_then_6_stability_list.append(player_id)
            #resolve event now
            for region in regdata_list:
                region_id = region[0]
                ownership_data = ast.literal_eval(region[2])
                improvement_data = ast.literal_eval(region[4])
                victim_player_id = ownership_data[0]
                improvement_name = improvement_data[0]
                if victim_player_id in less_then_6_stability_list and improvement_name in ['Coal Mine', 'Strip Mine', 'Oil Well', 'Oil Refinery', 'Solar Farm', 'Wind Farm']:
                    decay_roll = random.randint(1, 10)
                    if decay_roll >= 6:
                        victim_nation_name = playerdata_list[victim_player_id - 1][1]
                        region[4] = str([None, 99])
                        diplomacy_log.append(f'{victim_nation_name} {improvement_name} in {region_id} has decayed.')
            #save to inactive events list
            active_games_dict[full_game_id]["Inactive Events"].append(chosen_event)

        case "Defection":
            defection_victims_dict = {}
            lowest_stability_value = 10
            for player_id in event_conditions_dict["Players at War"]:
                playerdata = playerdata_list[player_id - 1]
                stability_data = ast.literal_eval(playerdata[7])
                stability_header_list = stability_data[0].split(" ")
                stability_header_list = stability_header_list[1].split("/")
                stability_value = int(stability_header_list[0])
                if stability_value < lowest_stability_value:
                    nation_name = playerdata_list[player_id - 1][1]
                    defection_victims_dict = {}
                    victim_data = {}
                    victim_data["Victim Player ID"] = player_id
                    victim_data["Main Opponent Player ID"] = 0
                    defection_victims_dict[nation_name] = victim_data
                    lowest_stability_value = stability_value
                elif stability_value == lowest_stability_value:
                    victim_data = {}
                    victim_data["Victim Player ID"] = player_id
                    victim_data["Main Opponent Player ID"] = 0
                    defection_victims_dict[nation_name] = victim_data
            for nation_name in defection_victims_dict:
                victim_player_id = defection_victims_dict[nation_name]["Victim Player ID"]
                for war in wardata_list:
                    if war[victim_player_id] != '-' and war[13] == 'Ongoing':
                        for index, player_war_data in enumerate(war):
                            if player_war_data != '-' and index != victim_player_id:
                                player_war_data = ast.literal_eval(player_war_data)
                                if 'Main' in player_war_data[0]:
                                    opponent_player_id = index
                                    break
                        defection_victims_dict[nation_name]["Main Opponent Player ID"] = opponent_player_id
                        break
            #resolve event now
            for region in regdata_list:
                region_id = region[0]
                unit_data = ast.literal_eval(region[5])
                player_id = ownership_data[0]
                nation_name = playerdata_list[player_id - 1][1]
                unit_name = unit_data[0]
                unit_health = unit_data[1]
                unit_owner_id = None
                if unit_name != None:
                    unit_owner_id = unit_data[2]
                if nation_name in defection_victims_dict and unit_owner_id != None:
                    if unit_owner_id == defection_victims_dict[nation_name]["Victim Player ID"]:
                        victim_nation_name = nation_name
                        defection_roll = random.randint(1, 10)
                        if defection_roll == 10:
                            opponent_player_id = defection_victims_dict[nation_name]["Main Opponent Player ID"]
                            unit_data = str([unit_name, unit_health, opponent_player_id])
                            opponent_nation_name = playerdata_list[opponent_player_id - 1][1]
                            diplomacy_log.append(f'{victim_nation_name} {unit_name} {region_id} has defected to {opponent_nation_name}.')
                        elif defection_roll >= 8:
                            unit_data = str([None, 99])
                            diplomacy_log.append(f'{victim_nation_name} {unit_name} {region_id} has disbanded.')
            #save to inactive events list
            active_games_dict[full_game_id]["Inactive Events"].append(chosen_event)

        case "Diplomatic Summit":
            diplomacy_log.append(f'New Event: {chosen_event}!')
            active_games_dict = save_as_standard_delayed_event(chosen_event, active_games_dict, full_game_id, playerdata_list)

        case "Downward Spiral":
            effected_player_ids = event_conditions_dict["Defeat Penalty"]
            #resolve event now
            for victim_player_id in effected_player_ids:
                victim_nation_name = playerdata_list[victim_player_id - 1][1]
                victim_stability_data = ast.literal_eval(playerdata_list[victim_player_id - 1][7])
                for entry in victim_stability_data:
                    if "from Defeat" in entry:
                        entry = entry.replace('-2 from Defeat', '-3 from Defeat')
                        entry = entry.replace('-1 from Defeat', '-2 from Defeat')
                        diplomacy_log.append(f'{victim_nation_name} was effected by the Downward Spiral event.')
                playerdata_list[victim_player_id - 1][7] = str(victim_stability_data)
            #save to inactive events list
            active_games_dict[full_game_id]["Inactive Events"].append(chosen_event)

        case "Foreign Aid":
            effected_player_ids = event_conditions_dict["Greater Than 5 Stability"]
            #resolve event now
            for victim_player_id in effected_player_ids:
                victim_nation_name = playerdata_list[victim_player_id - 1][1]
                dollars_economy_data = ast.literal_eval(playerdata_list[victim_player_id - 1][9])
                dollars_stored = float(dollars_economy_data[0])
                dollars_capacity = float(dollars_economy_data[1])
                improvement_name_list = sorted(core.improvement_data_dict.keys())
                improvement_count_list = ast.literal_eval(playerdata_list[victim_player_id - 1][27])
                city_index = improvement_name_list.index("City")
                city_count = improvement_count_list[city_index]
                if city_count >= 0:
                    dollars_stored += city_count * 5
                    if dollars_stored > dollars_capacity:
                        dollars_stored = dollars_capacity
                    dollars_economy_data[0] = str(dollars_stored)
                    playerdata_list[victim_player_id - 1][9] = str(dollars_economy_data)
                    diplomacy_log.append(f'{victim_nation_name} has received {city_count * 5} dollars worth of foreign aid.')
            #save to inactive events list
            active_games_dict[full_game_id]["Inactive Events"].append(chosen_event)

        case "Foreign Interference":
            diplomacy_log.append(f'New Event: {chosen_event}!')
            active_games_dict = save_as_standard_delayed_event(chosen_event, active_games_dict, full_game_id, playerdata_list)

        case "Influence Through Trade":
            with open(f'gamedata/{full_game_id}/statistics.json', 'r') as json_file:
                statistics_dict = json.load(json_file)
            trade_count_dict = statistics_dict['Trade Count']
            sorted_trade_count_dict = dict(sorted(trade_count_dict.items(), key=lambda item: item[1], reverse=True))
            top_four = sorted_trade_count_dict[:4]
            (nation_name_1, count_1), (nation_name_2, count_2), (nation_name_3, count_3), (nation_name_4, count_4) = top_four
            #resolve event now
            if count_1 != count_2:
                index = nation_name_list.index(nation_name_1)
                player_id = index + 1
                political_power_economy_data = ast.literal_eval(playerdata_list[player_id - 1][10])
                political_power_count = float(political_power_economy_data[0])
                political_power_count += 15
                political_power_economy_data[0] = core.round_total_income(political_power_count)
                playerdata_list[victim_player_id - 1][10] = str(political_power_economy_data)
            if count_2 != count_3:
                index = nation_name_list.index(nation_name_2)
                player_id = index + 1
                political_power_economy_data = ast.literal_eval(playerdata_list[player_id - 1][10])
                political_power_count = float(political_power_economy_data[0])
                political_power_count += 10
                political_power_economy_data[0] = core.round_total_income(political_power_count)
                playerdata_list[victim_player_id - 1][10] = str(political_power_economy_data)
            if count_3 != count_4:
                index = nation_name_list.index(nation_name_3)
                player_id = index + 1
                political_power_economy_data = ast.literal_eval(playerdata_list[player_id - 1][10])
                political_power_count = float(political_power_economy_data[0])
                political_power_count += 5
                political_power_economy_data[0] = core.round_total_income(political_power_count)
                playerdata_list[victim_player_id - 1][10] = str(political_power_economy_data)
            with open(f'gamedata/{full_game_id}/statistics.json', 'w') as json_file:
                json.dump(statistics_dict, json_file, indent=4)
            #if a reward for first place was given save to active otherwise can
            if count_1 != count_2:
                active_event_dict = {}
                active_event_dict['Income Bonus Winner'] = nation_name_1
                active_games_dict[full_game_id]["Active Events"][chosen_event] = active_event_dict
            else:
                #save to inactive events list
                active_games_dict[full_game_id]["Inactive Events"].append(chosen_event)
        case "Lost Nuclear Weapons":
            chosen_player_id = random.randint(1, len(playerdata_list))
            chosen_nation_name = playerdata_list[chosen_player_id - 1][1]
            diplomacy_log.append(f'{chosen_nation_name} has been randomly selected for the {chosen_event} event!')
            #save to Current Event key to be activated later
            active_games_dict[full_game_id]["Current Event"][chosen_event] = [chosen_player_id]

        case "Major Security Breach":
            victim_player_id = event_conditions_dict["Most Research"]
            diplomacy_log.append(f'New Event: {chosen_event}!')
            #save to Current Event key to be activated later
            active_games_dict[full_game_id]["Current Event"][chosen_event] = [victim_player_id]

        case "Observer Status Invitation":
            diplomacy_log.append(f'New Event: {chosen_event}!')
            active_games_dict = save_as_standard_delayed_event(chosen_event, active_games_dict, full_game_id, playerdata_list)

        case "Peacetime Rewards":
            effected_player_ids = event_conditions_dict["At Peace For At Least 8 Turns"]
            nations_receiving_award_list = []
            for player_id in effected_player_ids:
                nations_receiving_award_list.append(playerdata_list[player_id - 1][1])
            nations_receiving_award_str = ", ".join(nations_receiving_award_list)
            diplomacy_log.append(f'New Event: {chosen_event}!')
            diplomacy_log.append(f'Nations receiving event reward: {nations_receiving_award_str}.')
            #save to Current Event key to be activated later
            active_games_dict[full_game_id]["Current Event"][chosen_event] = effected_player_ids

        case "Power Plant Meltdown":
            meltdown_candidates = []
            for region in regdata_list:
                region_id = region[0]
                ownership_data = ast.literal_eval(region[2])
                improvement_data = ast.literal_eval(region[4])
                if improvement_data[0] == "Nuclear Power Plant":
                    meltdown_candidates.append(region_id)
            random.shuffle(meltdown_candidates)
            meltdown_region_id = meltdown_candidates.pop()
            #resolve event now
            meltdown_region_data = core.get_region_data(regdata_list, meltdown_region_id)
            control_data = ast.literal_eval(meltdown_region_data[2])
            victim_player_id = control_data[2]
            victim_nation_name = playerdata_list[victim_player_id - 1][1]
            meltdown_region_data[4] = str([None, 99])
            meltdown_region_data[5] = str([None, 99])
            meltdown_region_data[6] = str([True, 99])
            political_power_economy_data = ast.literal_eval(playerdata_list[victim_player_id - 1][10])
            political_power_economy_data[0] = '0.00'
            playerdata_list[victim_player_id - 1][10] = str(political_power_economy_data)
            victim_stability_data = ast.literal_eval(playerdata_list[victim_player_id - 1][7])
            victim_stability_data.append('-1 from Events')
            playerdata_list[victim_player_id - 1][7] = str(victim_stability_data)
            diplomacy_log.append(f'The {victim_nation_name} Nuclear Power Plant in {meltdown_region_id} has melted down!')
            #save to inactive events list
            active_games_dict[full_game_id]["Inactive Events"].append(chosen_event)

        case "Shifting Attitudes":
            diplomacy_log.append(f'New Event: {chosen_event}!')
            active_games_dict = save_as_standard_delayed_event(chosen_event, active_games_dict, full_game_id, playerdata_list)

        case "United Nations Peacekeeping Mandate":
            #resolve event now
            for war in wardata_list:
                if war[13] == 'Ongoing':
                    signatories_list = [False, False, False, False, False, False, False, False, False, False]
                    for i in range(1, 11):
                        if war[i] != '-':
                            signatories_list[i - 1] = True
                    for region in regdata_list:
                        if len(region[0]) == 5:
                            control_data = ast.literal_eval(region[2])
                            owner_id = control_data[0]
                            occupier_id = control_data[1]
                            if signatories_list[owner_id - 1] and signatories_list[occupier_id - 1]:
                                new_data = [owner_id, 0]
                                region[2] = str(new_data)
                    core.add_truce_period(full_game_id, signatories_list, 'White Peace', current_turn_num)
                    war_name = war[11]
                    war[13] = 'White Peace'
                    war[15] = current_turn_num
                    diplomacy_log.append(f'{war_name} has ended with a white peace.')
                    break
            #update playerdata
            diplomatic_relations_masterlist = []
            for playerdata in playerdata_list:
                diplomatic_relations_masterlist.append(ast.literal_eval(playerdata[22]))
            diplomatic_relations_masterlist = core.repair_relations(diplomatic_relations_masterlist, wardata_list)
            for index, playerdata in enumerate(playerdata_list):
                victim_stability_data = ast.literal_eval(playerdata[7])
                victim_stability_data.append('1 from Events')
                playerdata[7] = str(victim_stability_data)
                playerdata[22] = str(diplomatic_relations_masterlist[index])
            #save to inactive events list
            active_games_dict[full_game_id]["Inactive Events"].append(chosen_event)
        
        case "Widespread Civil Disorder":
            record_filepath = f'gamedata/{full_game_id}/largest_nation.csv'
            record_list = core.read_file(record_filepath, 0)
            candidates = []
            for index, record in enumerate(record_list):
                if index == 0:
                    continue
                value = int(record[-1])
                nation_name = nation_name_list[index - 1]
                candidates.append([nation_name, value])
            sorted_candidates = sorted(candidates, key = lambda x: x[-1], reverse = True)
            first_place = [sorted_candidates[0][0], sorted_candidates[0][1]]
            second_place = [sorted_candidates[1][0], sorted_candidates[1][1]]
            second_to_last_place = [sorted_candidates[-2][0], sorted_candidates[-2][1]]
            last_place = [sorted_candidates[-1][0], sorted_candidates[-1][1]]
            #resolve event now
            first_player_id = None
            last_player_id = None
            if first_place[1] != second_place[1]:
                first_nation_name = first_place[0]
                first_player_id = nation_name_list.index(first_nation_name) + 1
            if last_place[1] != second_to_last_place[1]:
                last_nation_name = last_place[0]
                last_player_id = nation_name_list.index(last_nation_name) + 1
            for index, playerdata in enumerate(playerdata_list):
                player_id = index + 1
                if player_id == first_player_id:
                    first_stability_data = ast.literal_eval(playerdata[7])
                    first_stability_data.append('-1 from Events')
                    playerdata[7] = str(first_stability_data)
                    diplomacy_log.append(f'{first_nation_name} lost -1 stability due to Widespread Civil Disorder.')
                elif player_id == last_player_id:
                    last_stability_data = ast.literal_eval(playerdata[7])
                    last_stability_data.append('1 from Events')
                    playerdata[7] = str(last_stability_data)
                    diplomacy_log.append(f'{last_nation_name} gained 1 stability due to Widespread Civil Disorder.')
            #save as an active event
            active_event_dict = {}
            active_event_dict["Expiration"] = current_turn_num + 8
            active_games_dict[full_game_id]["Active Events"][chosen_event] = active_event_dict
        
        case "Embargo":
            diplomacy_log.append(f'New Event: {chosen_event}!')
            active_games_dict = save_as_standard_delayed_event(chosen_event, active_games_dict, full_game_id, playerdata_list)

        case "Humiliation":
            diplomacy_log.append(f'New Event: {chosen_event}!')
            active_games_dict = save_as_standard_delayed_event(chosen_event, active_games_dict, full_game_id, playerdata_list)

        case "Foreign Investment":
            diplomacy_log.append(f'New Event: {chosen_event}!')
            active_games_dict = save_as_standard_delayed_event(chosen_event, active_games_dict, full_game_id, playerdata_list)

        case "Nominate Mediator":
            diplomacy_log.append(f'New Event: {chosen_event}!')
            active_games_dict = save_as_standard_delayed_event(chosen_event, active_games_dict, full_game_id, playerdata_list)

        case "Shared Fate":
            diplomacy_log.append(f'New Event: {chosen_event}!')
            active_games_dict = save_as_standard_delayed_event(chosen_event, active_games_dict, full_game_id, playerdata_list)

        case "Threat Containment":
            diplomacy_log.append(f'New Event: {chosen_event}!')
            active_games_dict = save_as_standard_delayed_event(chosen_event, active_games_dict, full_game_id, playerdata_list)

        case "Foreign Invasion":
            invasion_candidates_list = []
            for region in regdata_list:
                if ast.literal_eval(region[9]):
                    invasion_candidates_list.append(region[0])
            random.shuffle(invasion_candidates_list)
            invasion_point = invasion_candidates_list.pop()
            reinforcements_regions_list = []
            reinforcements_regions_list.append(invasion_point)
            invasion_point_region_data = core.get_region_data(regdata_list, invasion_point)
            reinforcements_regions_list = reinforcements_regions_list + ast.literal_eval(invasion_point_region_data[8])
            hex_colors_list = list(core.player_colors_conversions.keys())
            for playerdata in playerdata_list:
                if playerdata[2] in hex_colors_list:
                    hex_colors_list.remove(playerdata[2])
            random.shuffle(hex_colors_list)
            invasion_color = hex_colors_list.pop()
            #resolve event now
            if current_turn_num >= 24:
                unit_abbrev = 'HT'
                unit_health = 10
            elif current_turn_num >= 16:
                unit_abbrev = 'ME'
                unit_health = 8
            else:
                unit_abbrev = 'IN'
                unit_health = 6
            for region_id in reinforcements_regions_list:
                for region in regdata_list:
                    if region[0] == region_id:
                        region[2] = str([99, 0])
                        region[5] = str([unit_abbrev, unit_health])
            #save as an active event
            active_event_dict = {}
            active_event_dict["Reinforcements Regions"] = reinforcements_regions_list
            active_event_dict["Invasion Color"] = invasion_color
            active_event_dict["Expiration"] = current_turn_num + 20
            active_games_dict[full_game_id]["Active Events"][chosen_event] = active_event_dict

        case "Pandemic":
            diplomacy_log.append(f'New Event: {chosen_event}!')
            intensify_roll = random.randint(3, 9)
            spread_roll = random.randint(3, 9)
            region_list = []
            for region in regdata_list:
                region_list.append(region[0])
            random.shuffle(region_list)
            origin_region_id = region_list.pop()
            #resolve event now
            for region in regdata_list:
                if region[0] == origin_region_id:
                    region[12] = 1
            #save as an active event
            active_event_dict = {}
            active_event_dict["Intensify Value"] = intensify_roll
            active_event_dict["Spread Value"] = spread_roll
            active_event_dict["Completed Cure Research"] = 0
            active_event_dict["Needed Cure Research"] = len(playerdata_list) * 50
            active_event_dict["Closed Borders List"] = []
            active_games_dict[full_game_id]["Active Events"][chosen_event] = active_event_dict

        case "Faustian Bargain":
            diplomacy_log.append(f'New Event: {chosen_event}!')
            effected_player_ids = []
            for index, playerdata in enumerate(playerdata_list):
                player_id = index + 1
                effected_player_ids.append(player_id)
            #save to Current Event key to be activated later
            active_games_dict[full_game_id]["Current Event"][chosen_event] = effected_player_ids

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
    
    return active_games_dict, playerdata_list, regdata_list, wardata_list, diplomacy_log

def save_as_standard_delayed_event(chosen_event, active_games_dict, full_game_id, playerdata_list):
    '''
    Updates active_games_dict with a new current event.
    Used for all events in which there is a pending option / vote effecting all players.

    Parameters:
    - chosen_event: A string that is the name of an event.
    - active_games_dict: A dictionary derived from the active_games.json file.
    - full_game_id: The full game_id of the active game.
    - playerdata_list: A list of lists containing all playerdata derived from playerdata.csv
    '''

    effected_player_ids = []
    for i in range(len(playerdata_list)):
        player_id = i + 1
        effected_player_ids.append(player_id)
    #save to Current Event key to be activated later
    active_games_dict[full_game_id]["Current Event"][chosen_event] = effected_player_ids

    return active_games_dict


#HANDLE CURRENT EVENTS
################################################################################

def handle_current_event(active_games_dict, full_game_id, diplomacy_log):
    '''
    Handles a current event when called by site code. Returns updated diplomacy_log.

    Parameters:
    - active_games_dict: A dictionary derived from the active_games.json file.
    - full_game_id: The full game_id of the active game.
    - diplomacy_log: A list of pre-generated diplomatic interaction logs.
    '''
    
    #get game information
    playerdata_filepath = f'gamedata/{full_game_id}/playerdata.csv'
    playerdata_list = core.read_file(playerdata_filepath, 1)
    regdata_filepath = f'gamedata/{full_game_id}/regdata.csv'
    regdata_list = core.read_file(regdata_filepath, 2)
    nation_name_list = []
    for playerdata in playerdata_list:
        nation_name_list.append(playerdata[1])
    region_list = []
    for region in regdata_list:
        region_list.append(region[0])
    player_action_logs = list([]*len(playerdata_list))
    game_id = int(full_game_id[-1])
    current_turn_num = core.get_current_turn_num(game_id)

    #get event data
    current_event_dict = active_games_dict[full_game_id]["Current Event"]
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
                decision.append(decision)
            for index, decision in enumerate(decision_list):
                player_id = index + 1
                if decision == "Find the Perpetrator":
                    political_power_economy_data = ast.literal_eval(playerdata_list[player_id - 1][10])
                    political_power_stored = float(political_power_economy_data[0])
                    political_power_stored -= 5
                    political_power_economy_data[0] = core.round_total_income(political_power_stored)
                    playerdata_list[player_id - 1][10] = str(political_power_economy_data)
                    stability_data = ast.literal_eval(playerdata_list[player_id - 1][7])
                    stability_data.append('-1 from Events')
                    playerdata_list[player_id - 1][7] = str(stability_data)
                elif decision == "Find a Scapegoat":
                    political_power_economy_data = ast.literal_eval(playerdata_list[player_id - 1][10])
                    political_power_stored = float(political_power_economy_data[0])
                    political_power_stored += 10
                    political_power_economy_data[0] = core.round_total_income(political_power_stored)
                    playerdata_list[player_id - 1][10] = str(political_power_economy_data)
                    stability_data = ast.literal_eval(playerdata_list[player_id - 1][7])
                    stability_data.append('-2 from Events')
                    playerdata_list[player_id - 1][7] = str(stability_data)

        case "Diplomatic Summit":
            print("""Available Options: "Attend" or "Decline" """)
            summit_attendance_list = []
            for player_id in effected_player_ids_list:
                nation_name = nation_name_list[player_id - 1]
                while True:
                    decision = input(f"Enter {nation_name} decision: ")
                    if decision == "Attend":
                        stability_data = ast.literal_eval(playerdata_list[player_id - 1][7])
                        stability_data.append('1 from Events')
                        playerdata_list[player_id - 1][7] = str(stability_data)
                        summit_attendance_list.append(nation_name)
                        break
                    elif decision == "Decline":
                        valid_research = False
                        while not valid_research:
                            research_name = input(f"Enter military research: ")
                            playerdata_list, valid_research = gain_free_research(research_name, player_id, playerdata_list)
            active_event_dict = {}
            active_event_dict["Expiration"] = current_turn_num + 8
            active_event_dict["Attendance"] = summit_attendance_list
            active_games_dict[full_game_id]["Active Events"][event_name] = active_event_dict

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
                        stability_data = ast.literal_eval(playerdata_list[player_id - 1][7])
                        stability_data.append('1 from Events')
                        playerdata_list[player_id - 1][7] = str(stability_data)
                        break
            diplomacy_log, player_action_logs = private_actions.resolve_war_declarations(war_declaration_list, full_game_id, current_turn_num, diplomacy_log, player_action_logs)
            if bribe_takers_list != []:
                active_event_dict = {}
                active_event_dict["Bribe List"] = bribe_takers_list
                active_games_dict[full_game_id]["Active Events"][event_name] = active_event_dict
            else:
                active_games_dict[full_game_id]["Inactive Events"].append(event_name)

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
                            if silo_location_id in region_list:
                                valid_region_id = True
                        improvement_data = ['Missile Silo', 5]
                        regdata_list = core.update_improvement_data(regdata_list, silo_location_id, improvement_data)
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
                diplomacy_log.append(f'{nation_name} chose to {decision.lower()} the old military installation.')
            active_games_dict[full_game_id]["Inactive Events"].append(event_name)
        
        case "Major Security Breach":
            for player_id in effected_player_ids_list:
                breach_research_list = ast.literal_eval(playerdata_list[player_id - 1][26])
                stability_data = ast.literal_eval(playerdata_list[player_id - 1][7])
                stability_data.append('-1 from Events')
                playerdata_list[player_id - 1][7] = str(stability_data)
            for index, playerdata in enumerate(playerdata_list):
                player_id = index + 1
                nation_name = nation_name_list[player_id - 1]
                valid_research = False
                while not valid_research:
                    chosen_research = input(f"Enter {nation_name} chosen research: ")
                    if chosen_research in breach_research_list:
                        playerdata_list, valid_research = gain_free_research(chosen_research, player_id, playerdata_list)
            active_games_dict[full_game_id]["Inactive Events"].append(event_name)
            
        case "Peacetime Rewards":
            for player_id in effected_player_ids_list:
                stability_data = ast.literal_eval(playerdata_list[player_id - 1][7])
                stability_data.append('1 from Events')
                playerdata_list[player_id - 1][7] = str(stability_data)
                valid_research = False
                while not valid_research:
                    research_name = input(f"Enter energy or infrastructure research: ")
                    playerdata_list, valid_research = gain_free_research(research_name, player_id, playerdata_list)
            active_games_dict[full_game_id]["Inactive Events"].append(event_name)

        case "Shifting Attitudes":
            print("""Available Options: "Keep" or "Change" """)
            for player_id in effected_player_ids_list:
                nation_name = nation_name_list[player_id - 1]
                while True:
                    decision = input(f"Enter {nation_name} decision: ")
                    if decision == "Keep":
                        new_foreign_policy = input(f"Enter new foreign policy: ")
                        playerdata_list[player_id - 1][7][4] = new_foreign_policy
                        stability_data = ast.literal_eval(playerdata_list[player_id - 1][7])
                        stability_data.append('1 from Events')
                        playerdata_list[player_id - 1][7] = str(stability_data)
                        break
                    elif decision == "Change":
                        political_power_economy_data = ast.literal_eval(playerdata_list[player_id - 1][10])
                        political_power_stored = float(political_power_economy_data[0])
                        political_power_stored += 10
                        political_power_economy_data[0] = core.round_total_income(political_power_stored)
                        playerdata_list[player_id - 1][10] = str(political_power_economy_data)
                        break
            active_games_dict[full_game_id]["Inactive Events"].append(event_name)

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
            top_two = sorted_vote_tally_dict[:2]
            (nation_name_1, count_1), (nation_name_2, count_2) = top_two
            if count_1 != count_2:
                diplomacy_log.append(f'With {count_1} votes, {nation_name_1} has been embargoed.')
                active_event_dict = {}
                active_event_dict["Chosen Nation Name"] = nation_name_1
                active_event_dict["Expiration"] = current_turn_num + 8
                active_games_dict[full_game_id]["Active Events"][event_name] = active_event_dict
            else:
                diplomacy_log.append(f'Vote tied between {nation_name_1} and {nation_name_2}. No embargo will be placed.')
                active_games_dict[full_game_id]["Inactive Events"].append(event_name)

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
            top_two = sorted_vote_tally_dict[:2]
            (nation_name_1, count_1), (nation_name_2, count_2) = top_two
            if count_1 != count_2:
                diplomacy_log.append(f'With {count_1} votes, {nation_name_1} has been humiliated.')
                active_event_dict = {}
                active_event_dict["Chosen Nation Name"] = nation_name_1
                active_event_dict["Expiration"] = current_turn_num + 8
                active_games_dict[full_game_id]["Active Events"][event_name] = active_event_dict
            else:
                diplomacy_log.append(f'Vote tied between {nation_name_1} and {nation_name_2}. No humiliation will occur.')
                active_games_dict[full_game_id]["Inactive Events"].append(event_name)

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
            top_two = sorted_vote_tally_dict[:2]
            (nation_name_1, count_1), (nation_name_2, count_2) = top_two
            if count_1 != count_2:
                diplomacy_log.append(f'With {count_1} votes, {nation_name_1} will receive the foreign investment.')
                active_event_dict = {}
                active_event_dict["Chosen Nation Name"] = nation_name_1
                active_event_dict["Expiration"] = current_turn_num + 8
                active_games_dict[full_game_id]["Active Events"][event_name] = active_event_dict
            else:
                diplomacy_log.append(f'Vote tied between {nation_name_1} and {nation_name_2}. No foreign investment will occur.')
                active_games_dict[full_game_id]["Inactive Events"].append(event_name)

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
            top_two = sorted_vote_tally_dict[:2]
            (nation_name_1, count_1), (nation_name_2, count_2) = top_two
            if count_1 != count_2:
                diplomacy_log.append(f'With {count_1} votes, {nation_name_1} has been elected Mediator.')
                active_event_dict = {}
                active_event_dict["Chosen Nation Name"] = nation_name_1
                active_event_dict["Expiration"] = current_turn_num + 8
                active_event_dict["Extended Truces List"] = []
                active_games_dict[full_game_id]["Active Events"][event_name] = active_event_dict
            else:
                diplomacy_log.append(f'Vote tied between {nation_name_1} and {nation_name_2}. No nation will be elected Mediator.')
                active_games_dict[full_game_id]["Inactive Events"].append(event_name)

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
                    diplomacy_log.append(f"By a vote of {cooperation_count} to {conflict_count}, {chosen_effect} wins.")
                elif cooperation_count < conflict_count:
                    chosen_effect = "Conflict"
                    diplomacy_log.append(f"By a vote of {conflict_count} to {cooperation_count}, {chosen_effect} wins.")
                active_event_dict = {}
                active_event_dict["Effect"] = chosen_effect
                active_games_dict[full_game_id]["Active Events"][event_name] = active_event_dict
            else:
                diplomacy_log.append(f'Vote tied between Cooperation and Conflict. No effect will be resolved.')
                active_games_dict[full_game_id]["Inactive Events"].append(event_name)

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
                top_two = sorted_vote_tally_dict[:2]
                (nation_name_1, count_1), (nation_name_2, count_2) = top_two
            else:
                count_1 = 0
                count_2 = 0
            if count_1 != count_2:
                diplomacy_log.append(f'With {count_1} votes, {nation_name_1} will be sanctioned.')
                active_event_dict = {}
                active_event_dict["Chosen Nation Name"] = nation_name_1
                active_event_dict["Expiration"] = current_turn_num + 8
                active_games_dict[full_game_id]["Active Events"][event_name] = active_event_dict
            elif count_1 == 0 and count_2 == 0:
                diplomacy_log.append(f'All nations abstained. No nation will be sanctioned.')
                active_games_dict[full_game_id]["Inactive Events"].append(event_name)
            else:
                diplomacy_log.append(f'Vote tied between {nation_name_1} and {nation_name_2}. No nation will be sanctioned.')
                active_games_dict[full_game_id]["Inactive Events"].append(event_name)

        case "Faustian Bargain":
            print("""Available Options: "Accept" or "Decline" """)
            candidates_list = []
            for player_id in effected_player_ids_list:
                nation_name = nation_name_list[player_id - 1]
                while True:
                    decision = input(f"Enter {nation_name} decision: ")
                    if decision == "Accept":
                        candidates_list.append(nation_name)
                    elif decision == "Decline":
                        stability_data = ast.literal_eval(playerdata_list[player_id - 1][7])
                        stability_data.append('1 from Events')
                        playerdata_list[player_id - 1][7] = str(stability_data)
                        break
            if candidates_list != []:
                random.shuffle(candidates_list)
                chosen_nation_name = candidates_list.pop()
                diplomacy_log.append(f'{chosen_nation_name} took the Faustian Bargain and will collaborate with the foreign nation.')
                active_event_dict = {}
                active_event_dict["Chosen Nation Name"] = chosen_nation_name
                active_event_dict["Leased Regions List"] = []
                active_games_dict[full_game_id]["Active Events"][event_name] = active_event_dict
            else:
                diplomacy_log.append("No nation took the Faustian Bargain. collaborate with the foreign nation.")
                active_games_dict[full_game_id]["Inactive Events"].append(event_name)

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
    active_games_dict[full_game_id]["Current Event"] = {}
    with open('active_games.json', 'w') as json_file:
        json.dump(active_games_dict, json_file, indent=4)

    with open(playerdata_filepath, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(core.player_data_header)
        writer.writerows(playerdata_list)

    with open(regdata_filepath, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(core.regdata_header_a)
        writer.writerow(core.regdata_header_b)
        writer.writerows(regdata_list)

    return diplomacy_log

def gain_free_research(research_name, player_id, playerdata_list):
    '''
    Returns updated playerdata_List and a bool that is True if the research was valid, False otherwise.
    '''

    player_government = playerdata_list[player_id - 1][3]
    player_political_power_data = ast.literal_eval(playerdata_list[player_id - 1][10])
    player_stored_political_power = float(player_political_power_data[0])
    player_research_list = ast.literal_eval(playerdata_list[player_id - 1][26])
    research_prereq = core.research_data_dict[research_name]['Prerequisite']

    valid_research = True
    if research_name in player_research_list:
        valid_research = False
    if research_prereq not in player_research_list and research_prereq != None:
        valid_research = False
    if valid_research:
        player_research_list.append(research_name)
        if player_government == 'Totalitarian':
            totalitarian_bonus_list = []
            for key, value in core.research_data_dict.items():
                if value.get("Research Type") in ['Energy', 'Infrastructure']:
                    totalitarian_bonus_list.append(key)
            if research_name in totalitarian_bonus_list:
                player_stored_political_power += 1

    player_political_power_data[0] = core.round_total_income(player_stored_political_power)
    playerdata_list[player_id - 1][10] = str(player_political_power_data)
    playerdata_list[player_id - 1][26] = str(player_research_list)

    return playerdata_list, valid_research
    

#HANDLE ACTIVE EVENTS
################################################################################

def resolve_active_events(turn_status, public_actions_dict, private_actions_dict, full_game_id, diplomacy_log):
    '''
    Function that handles active events depending on turn status. Returns updated diplomacy_log.

    Paramteters:
    - turn_status: A string that is either "Before Actions" or "After Actions".
    - full_game_id: The full game_id of the active game.
    - diplomacy_log: A list of pre-generated diplomatic interaction logs.
    '''

    with open('active_games.json', 'r') as json_file:
        active_games_dict = json.load(json_file)

    for event_name in active_games_dict[full_game_id]["Active Events"]:
        public_actions_dict, private_actions_dict, active_games_dict, diplomacy_log = handle_active_event(event_name, public_actions_dict, private_actions_dict, active_games_dict, full_game_id, turn_status, diplomacy_log)
    
    with open('active_games.json', 'w') as json_file:
        json.dump(active_games_dict, json_file, indent=4)

    return public_actions_dict, private_actions_dict, diplomacy_log 

def handle_active_event(event_name, public_actions_dict, private_actions_dict, active_games_dict, full_game_id, turn_status, diplomacy_log):
    '''
    For active events that require special handling which cannot be integrated cleanly in other game code.
    '''

    #get game information
    playerdata_filepath = f'gamedata/{full_game_id}/playerdata.csv'
    playerdata_list = core.read_file(playerdata_filepath, 1)
    regdata_filepath = f'gamedata/{full_game_id}/regdata.csv'
    regdata_list = core.read_file(regdata_filepath, 2)
    game_id = int(full_game_id[-1])
    current_turn_num = core.get_current_turn_num(game_id)
    
    #resolve active event
    match event_name:
        

        case "Foreign Invasion":
            
            if turn_status == "Before Actions":
                #add move orders to action dictionary
                for region in regdata_list:
                    starting_region_id = region[0]
                    control_data = ast.literal_eval(region[2])
                    unit_data = ast.literal_eval(region[5])
                    adjacency_list = ast.literal_eval(region[8])
                    if unit_data[0] != None:
                        if unit_data[2] == 99:
                            ending_region_id = determine_target_region(regdata_list, adjacency_list)
                            if ending_region_id is not None:
                                movement_action_str = f'Move {starting_region_id}-{ending_region_id}'
                                private_actions_dict['Move'].append([99, movement_action_str])
                #add deploy orders to action dictionary
                for region in regdata_list:
                    region_id = region[0]
                    control_data = ast.literal_eval(region[2])
                    unit_data = ast.literal_eval(region[5])
                    if control_data[0] == 99 and control_data[1] == 0:
                        if unit_data[0] != None:
                            if unit_data[2] != 99:
                                continue
                        if current_turn_num >= 24:
                            unit_abbrev = 'HT'
                        elif current_turn_num >= 16:
                            unit_abbrev = 'ME'
                        else:
                            unit_abbrev = 'IN'
                        deploy_action_str = f'Deploy {unit_abbrev} {region_id}'
                        private_actions_dict['Deploy'].append([99, deploy_action_str])

            if turn_status == "After Actions":
                #check if Foreign Invasion has no remaining units
                invasion_unit_count = 0
                for region in regdata_list:
                    unit_data = ast.literal_eval(region[5])
                    if unit_data[0] != None:
                        if unit_data[2] == 99:
                            invasion_unit_count += 1
                if invasion_unit_count == 0:
                    regdata_list = end_foreign_invasion(regdata_list)
                #check if Foreign Invasion has no unoccupied reinforcement regions
                invasion_unoccupied_count = 0
                for region_id in active_games_dict[full_game_id]['Active Events'][event_name]["Reinforcements Regions"]:
                    region_data = core.get_region_data(regdata_list, region_id)
                    control_data = ast.literal_eval(region_data[2])
                    if control_data[1] == 0:
                        invasion_unoccupied_count += 1
                if invasion_unoccupied_count == 0:
                    regdata_list = end_foreign_invasion(regdata_list)


        case "Pandemic":
            
            if turn_status == "After Actions":
                intensify_value = active_games_dict[full_game_id]['Active Events'][event_name]["Intensify Value"]
                spread_value = active_games_dict[full_game_id]['Active Events'][event_name]["Spread Value"]
                completed_cure_research = active_games_dict[full_game_id]['Active Events'][event_name]["Completed Cure Research"]
                needed_cure_research = active_games_dict[full_game_id]['Active Events'][event_name]["Needed Cure Research"]
                closed_borders_player_ids_list = active_games_dict[full_game_id]['Active Events'][event_name]["Closed Borders List"]
                cure_percentage = float(completed_cure_research) / float(needed_cure_research)
                cure_percentage = round(cure_percentage, 2)
                if completed_cure_research >= needed_cure_research:
                    #run pandemic decline procedure
                    for region in regdata_list:
                        infection_score = region[12]
                        if infection_score > 0:
                            infection_score -= 2
                        if infection_score < 0:
                            infection_score = 0
                        region[12] = infection_score
                else:
                    #conduct intensify rolls
                    for region in regdata_list:
                        infection_score = region[12]
                        if infection_score > 0 and infection_score < 10:
                            control_data = ast.literal_eval(region[2])
                            intensify_roll = random.randint(1, 10)
                            if intensify_roll >= intensify_value:
                                if core.check_for_adjacent_improvement(control_data[0], region[0], ['Capital', 'City'], regdata_list):
                                    infection_score += 2
                                else:
                                    infection_score += 1
                    #conduct spread roles
                    for region in regdata_list:
                        control_data = ast.literal_eval(region[2])
                        adjacency_list = ast.literal_eval(region[8])
                        quarantined = region[11]
                        infection_score = region[12]
                        if infection_score > 0:
                            for region_id in adjacency_list:
                                adjacent_region_data = core.get_region_data(regdata_list, region_id)
                                adjacent_control_data = ast.literal_eval(adjacent_region_data[2])
                                adjacent_infection_score = adjacent_region_data[12]
                                if adjacent_infection_score == 0:
                                    if not quarantined and (control_data[0] != adjacent_control_data[0] and adjacent_control_data[0] not in closed_borders_player_ids_list):
                                        spread_roll = random.randint(1, 10)
                                        if spread_roll < spread_value:
                                            continue
                                    else:
                                        spread_roll = random.randint(1, 20)
                                        if spread_roll > 1:
                                            continue
                                adjacent_region_data[12] = 1
                #get total infection scores
                infection_scores = [0 * len(playerdata_list)]
                for region in regdata_list:
                    control_data = ast.literal_eval(region[2])
                    owner_id = control_data[0]
                    infection_score = region[12]
                    if owner_id in range(1, len(infection_scores) + 1):
                        infection_scores[owner_id - 1] += infection_score
                #check if pandemic has been eradicated
                infection_total = sum(infection_scores)
                if infection_total == 0:
                    for region in regdata_list:
                        quarantined = region[11]
                        if quarantined:
                            region[11] = False
                    del active_games_dict[full_game_id]['Active Events'][event_name]
                    active_games_dict[full_game_id]["Inactive Events"].append(event_name)
                    diplomacy_log.append("The pandemic has been eradicated!")
                #print diplomacy log messages
                if infection_total != 0:
                    if cure_percentage >= 0.5:
                        for index, score in enumerate(infection_scores):
                            nation_name = playerdata_list[index][1]
                            diplomacy_log.append(f"{nation_name} pandemic infection score: {score}")
                    if cure_percentage >= 0.75:
                        diplomacy_log.append(f"Pandemic intensify value: {intensify_value}")
                        diplomacy_log.append(f"Pandemic spread value: {spread_value}")
                    if cure_percentage < 1:
                        diplomacy_log.append(f"Pandemic cure research progress: {completed_cure_research}/{needed_cure_research}")
                    else:
                        diplomacy_log.append(f"Pandemic cure research has been completed! The pandemic is now in decline.")
                
        case "Faustian Bargain":

            if turn_status == "After Actions":
                #check if leased regions have changed hands
                for region_id in active_games_dict[full_game_id]["Active Events"]["Faustian Bargain"]["Leased Regions List"]:
                    region_data = core.get_region_data(regdata_list, region_id)
                    control_data = ast.literal_eval(region_data[2])
                    if control_data[0] != player_id:
                        active_games_dict[full_game_id]["Active Events"]["Faustian Bargain"]["Leased Regions List"].remove(region_id)
                        diplomacy_log.append(f"{region_id} is no longer being leased to the foreign nation.")
                #check if chosen nation has hit zero stability
                nation_name_list = []
                for playerdata in playerdata_list:
                    nation_name_list.append(playerdata[1])
                chosen_nation_name = active_games_dict[full_game_id]["Active Events"][event_name]["Chosen Nation Name"]
                player_id = nation_name_list.index(chosen_nation_name)
                player_stability_list = ast.literal_eval(playerdata_list[player_id - 1][7])
                zero_stability_consequences_list = ['Compromised Military Secrets', 'Material Shortage', 'Embezzlement', 'Secession', 'Low Morale', 'Widespread Instability']
                chosen_nation_hit_zero = False
                for entry in player_stability_list:
                    if entry in zero_stability_consequences_list:
                        chosen_nation_hit_zero = True
                if chosen_nation_hit_zero:
                    del active_games_dict[full_game_id]['Active Events'][event_name]
                    active_games_dict[full_game_id]["Inactive Events"].append(event_name)
                    diplomacy_log.append(f"{event_name} event has ended.")


    #retire active events if expired at end of turn
    current_turn_num = int(active_games_dict[full_game_id]["Current Turn"])
    if turn_status == "After Actions":
        if "Expiration" in active_games_dict[full_game_id]['Active Events'][event_name]:
            if active_games_dict[full_game_id]['Active Events'][event_name]["Expiration"] == current_turn_num:
                #handle special cases
                print("YOU SHOULD NOT BE READING THIS")
                if event_name == "Foreign Invasion":
                    regdata_list = end_foreign_invasion(regdata_list)
                del active_games_dict[full_game_id]['Active Events'][event_name]
                active_games_dict[full_game_id]["Inactive Events"].append(event_name)
                diplomacy_log.append(f"{event_name} event has ended.")
            else:
                #add active event to diplomacy log
                diplomacy_log.append(f"{event_name} event is ongoing.")

    #save files
    with open(playerdata_filepath, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(core.player_data_header)
        writer.writerows(playerdata_list)
    with open(regdata_filepath, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(core.regdata_header_a)
        writer.writerow(core.regdata_header_b)
        writer.writerows(regdata_list)

    return public_actions_dict, private_actions_dict, active_games_dict, diplomacy_log
    
def determine_target_region(regdata_list, adjacency_list):
    '''
    Function that contains Foreign Invasion attack logic.
    Designed to find path of least resistance but has no care for the health of its own units.
    '''
    
    random.shuffle(adjacency_list)
    target_region_id = None
    target_region_health = 0
    target_region_priority = 0

    for adjacent_region_id in adjacency_list:
        candidate_region_data = core.get_region_data(regdata_list, adjacent_region_id)
        candidate_region_id = candidate_region_data[0]
        control_data = ast.literal_eval(candidate_region_data[2])
        improvement_data = ast.literal_eval(candidate_region_data[4])
        unit_data = ast.literal_eval(candidate_region_data[5])
        candidate_region_priority = 0
        candidate_region_health = 0
        #evaluate candidate region priority
        if control_data[0] == 99 and control_data[1] != 0:
            candidate_region_priority += 6
        if control_data[0] != 99 and control_data[1] != 99:
            candidate_region_priority += 4
        elif control_data[0] != 99:
            candidate_region_priority += 2
        elif control_data[0] == 0:
            continue
        if unit_data[0] != None:
            if unit_data[2] != 99:
                candidate_region_priority += 1
        #evaluate candidate region health
        if improvement_data[0] != None and improvement_data[1] != 99 and control_data[0] != 99:
            candidate_region_health += improvement_data[1]
        if unit_data[0] != None:
            if unit_data[2] != 99:
                candidate_region_health += unit_data[1]
        #check if candidate region is an easier or higher priority target
        if candidate_region_priority > target_region_priority:
            target_region_id = candidate_region_id
            target_region_health = candidate_region_health
            target_region_priority = candidate_region_priority
        elif candidate_region_priority == target_region_priority and candidate_region_health < target_region_health:
            target_region_id = candidate_region_id
            target_region_health = candidate_region_health
            target_region_priority = candidate_region_priority
    
    return target_region_id

def end_foreign_invasion(regdata_list):
    
    for region in regdata_list:
        control_data = ast.literal_eval(region[2])
        unit_data = ast.literal_eval(region[5])
        change_made = False
        if control_data[0] == 99:
            control_data[0] = 0
            change_made = True
        if control_data[1] == 99:
            control_data[1] = 0
            change_made = True
        if unit_data[0] != None:
            if unit_data[2] == 99:
                unit_data = [None, 99]
                change_made = True
        if change_made:
            region[2] = str(control_data)
            region[5] = str(unit_data)
    
    return regdata_list


#EVENT DICTIONARY
################################################################################

EVENT_DICT = {
    "Assassination": {
        "Type": "Standard Event",
        "Resolution": "Delayed Option",
        "Conditions List": ["Less Than 8 Stability >= 1"]
    },
    "Coup D'état": {
        "Type": "Standard Event",
        "Resolution": "Instant",
        "Conditions List": ["Cannot be First Event", "Less Than 4 Stability >= 1"]
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
    "Downward Spiral": {
        "Type": "Standard Event",
        "Resolution": "Instant",
        "Conditions List": ["Defeat Penalty >= 1"]
    },
    "Foreign Aid": {
        "Type": "Standard Event",
        "Resolution": "Instant",
        "Conditions List": ["Greater Than 5 Stability >= 1"]
    },
    "Foreign Interference": {
        "Type": "Standard Event",
        "Resolution": "Delayed Option",
        "Conditions List": ["Cannot be First Event"]
    },
    "Influence Through Trade": {
        "Type": "Standard Event",
        "Resolution": "Instant",
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
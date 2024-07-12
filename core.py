#STANDARD IMPORTS
import ast
import csv
from datetime import datetime
import json
import os
import random
import shutil

#UWS SOURCE IMPORTS
import map
import interpreter
import public_actions
import private_actions
import checks
import resgraphs
import events

#UWS ENVIROMENT IMPORTS
import gspread


#TURN PROCESSING PROCEDURE
################################################################################

def resolve_stage1_processing(full_game_id, starting_region_list, player_color_list):
    '''
    Resolves turn processing for a game in stage one.

    Parameters:
    - full_game_id: The full game_id of the active game.
    - starting_region_list: A list of player starting region ids gathered from turn resolution HTML form. 
    - player_color_list: A list of player colors gathered from turn resolution HTML form. 
    '''
    
    game_id = int(full_game_id[-1])
    hexadecimal_player_color_list = []
    for player_color in player_color_list:
        new_player_color = player_colors_hex[player_color]
        hexadecimal_player_color_list.append(new_player_color)
   
    #read and update regdata
    regdata_list = read_file(f'gamedata/{full_game_id}/regdata.csv', 0)
    random_assignment_list = []
    for index, region_id in enumerate(starting_region_list):
        player_id = index + 1
        region_found = False
        for region in regdata_list:
            if region[0] == region_id:
                region[2] = str([player_id, 0])
                region[4] = str(["Capital", 5])
                region_found = True
                break
        if region_found == False:
            random_assignment_list.append(player_id)
    for random_assignment_player_id in random_assignment_list:
        while True:
            conflict_detected = False
            random_region_roll = random.randint(2, len(regdata_list) - 1)
            random_region_id = regdata_list[random_region_roll][0]
            regions_in_radius = get_regions_in_radius(random_region_id, 3, regdata_list)
            for radius_region_id in regions_in_radius:
                for region in regdata_list:
                    if region[0] == radius_region_id:
                        control_data = ast.literal_eval(region[2])
                        if control_data[0] != 0:
                            conflict_detected = True
                            break
            if conflict_detected == False:
                for region in regdata_list:
                    if region[0] == random_region_id:
                        region[2] = str([random_assignment_player_id, 0])
                        region[4] = str(["Capital", 5])
                        break
                break
    with open(f'gamedata/{full_game_id}/regdata.csv', 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerows(regdata_list)
    
    #read and update playerdata
    playerdata_list = read_file(f'gamedata/{full_game_id}/playerdata.csv', 1)
    for index, player in enumerate(playerdata_list):
        player[2] = hexadecimal_player_color_list[index]
    early_player_data_header = ["Player","Nation Name","Color","Government","Foreign Policy","Military Capacity","Trade Fee","Stability Data","VC Set A","VC Set B","Dollars","Political Power","Technology","Coal","Oil","Green Energy","Basic Materials","Common Metals","Advanced Metals","Uranium","Rare Earth Elements","Alliance Data","Missile Data","Diplomatic Relations","Upkeep Manager","Miscellaneous Information","Income Details","Completed Research","Improvement Count"]
    with open(f'gamedata/{full_game_id}/playerdata.csv', 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(early_player_data_header)
        writer.writerows(playerdata_list)
    
    #update active_games.json
    with open('active_games.json', 'r') as json_file:
        active_games_dict = json.load(json_file)
    active_games_dict[full_game_id]["Current Turn"] = "Nation Setup in Progress"
    with open('active_games.json', 'w') as json_file:
        json.dump(active_games_dict, json_file, indent=4)
    
    #generate and update maps
    current_turn_num = get_current_turn_num(game_id)
    map_name = get_map_name(game_id)
    main_map = map.MainMap(game_id, map_name, current_turn_num)
    resource_map = map.ResourceMap(game_id, map_name)
    control_map = map.ControlMap(game_id, map_name)
    resource_map.create()
    main_map.place_random()
    main_map.update()
    resource_map.update()
    control_map.update()

    #update preview image
    map.update_preview_image(game_id, current_turn_num)

def resolve_stage2_processing(full_game_id, player_nation_name_list, player_government_list, player_foreign_policy_list, player_victory_condition_set_list):
    '''
    Resolves turn processing for a game in stage two.

    Parameters:
    - full_game_id: The full game_id of the active game.
    - player_nation_name_list: A list of player nation names gathered from turn resolution HTML form. 
    - player_government_list: A list of player government choices gathered from turn resolution HTML form. 
    - player_foreign_policy_list: A list of player fp choices gathered from turn resolution HTML form. 
    - player_victory_condition_set_list: A list of player vc set choices gathered from turn resolution HTML form. 
    '''

    game_id = int(full_game_id[-1])
    playerdata_filepath = f'gamedata/{full_game_id}/playerdata.csv'
    playerdata_list = read_file(playerdata_filepath, 1)
    player_count = len(playerdata_list)
    #read and update playerdata
    for index, player in enumerate(playerdata_list):
        if player[0] != "":
            #update basic nation info
            player[1] = player_nation_name_list[index].title()
            player[3] = player_government_list[index]
            player[4] = player_foreign_policy_list[index]
            #confirm victory condition set
            if player_victory_condition_set_list[index] == "Set A":
                del player[9]
            else:
                del player[8]
            #apply income rates
            if player[3] == 'Republic':
                rate_list = republic_rates
            elif player[3] == 'Technocracy':
                rate_list = technocracy_rates
            elif player[3] == 'Oligarchy':
                rate_list = oligarchy_rates
            elif player[3] == 'Totalitarian':
                rate_list = totalitarian_rates
            elif player[3] == 'Remnant':
                rate_list = remnant_rates
            elif player[3] == 'Protectorate':
                rate_list = protectorate_rates
            elif player[3] == 'Military Junta':
                rate_list = military_junta_rates
            elif player[3] == 'Crime Syndicate':
                rate_list = crime_syndicate_rates
            j = 9
            for rate in rate_list:
                resource_data = ast.literal_eval(playerdata_list[index][j])
                resource_data[3] = rate
                playerdata_list[index][j] = str(resource_data)
                j += 1
            #Determine stability value
            if player[3] == "Republic" or player[3] == "Technocracy" or player[3] == "Protectorate":
                player[7] = ["Stability 4/10", "4 from Chosen Government"]
            elif player[3] == "Oligarchy" or player[3] == "Totalitarian" or player[3] == "Military Junta":
                player[7] = ["Stability 3/10", "3 from Chosen Government"]
            else:
                player[7] = ["Stability 2/10", "2 from Chosen Government"]
            #Determine unlocked alliances OBSOLETE CODE DELETE ME
            if player[4] == "Diplomatic":
                player[20] = [True, True, True, False, False]
            elif player[4] == "Commercial":
                player[20] = [True, True, False, False, False]
            elif player[4] == "Isolationist":
                player[20] = [True, False, False, False, False]
            elif player[4] == "Imperialist":
                player[20] = [True, True, False, False, False]
            #Give starting research
            starting_list = []
            five_point_research_list = ['Coal Mining', 'Oil Drilling', 'Wind Turbines', 'City Resettlement', 'Surface Mining', 'Metallurgy', 'Infantry', 'Motorized Infantry', 'Standing Army', 'Basic Defenses']
            if player[3] == "Technocracy":
                random_hard_list = random.sample(five_point_research_list, len(five_point_research_list))
                for j in range(3):
                    starting_list.append(random_hard_list.pop())
                    j += 1
            player[26] = starting_list
    with open(playerdata_filepath, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(player_data_header)
        writer.writerows(playerdata_list)
    
    #create crime syndicate tracking file
    steal_tracking_dict = {}
    for playerdata in playerdata_list:
        if player[3] == 'Crime Syndicate':
            inner_dict = {
                'Nation Name': None,
                'Streak': 0,
            }
            steal_tracking_dict[player[1]] = inner_dict
    if steal_tracking_dict != {}:
        with open(f'gamedata/{full_game_id}/steal_tracking.json', 'w') as json_file:
            json.dump(steal_tracking_dict, json_file, indent=4)
    
    #create records
    file_names = ['largest_nation', 'strongest_economy', 'largest_military', 'most_research']
    starting_records_data = [['Turn', 0]]
    for playerdata in playerdata_list:
        starting_records_data.append([playerdata[1], 0])
    for file_name in file_names:
        with open(f'gamedata/{full_game_id}/{file_name}.csv', 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerows(starting_records_data)

    #create trucedata.csv
    with open(f'gamedata/{full_game_id}/trucedata.csv', 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(trucedata_header)

    #create statistics file
    statistics_dict = {
        'Region Dispute Count': 0
    }
    trade_count_dict = {}
    for playerdata in playerdata_list:
        trade_count_dict[playerdata[1]] = 0
    statistics_dict['Trade Count'] = trade_count_dict
    with open(f'gamedata/{full_game_id}/statistics.json', "w") as json_file:
        json.dump(statistics_dict, json_file, indent=4)

    #update misc info in playerdata
    for i in range(player_count):
        player_id = i + 1
        checks.update_misc_info(full_game_id, player_id)
    #update improvement count in playerdata
    for i in range(player_count):
        player_id = i + 1
        checks.update_improvement_count(full_game_id, player_id)
    #update income in playerdata
    current_turn_num = 0
    checks.update_income(full_game_id, current_turn_num)
    #gain starting resources
    for player in playerdata_list:
        dollars_data = ast.literal_eval(player[9])
        political_power_data = ast.literal_eval(player[10])
        technology_data = ast.literal_eval(player[11])
        dollars_data[0] = '5.00'
        political_power_data[0] = '1.00'
        technology_data[0] = '2.00'
        player[9] = str(dollars_data)
        player[10] = str(political_power_data)
        player[11] = str(technology_data)

    #update playerdata.csv
    with open(playerdata_filepath, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(player_data_header)
        writer.writerows(playerdata_list)
    
    #read and update game_settings
    with open('active_games.json', 'r') as json_file:
        active_games_dict = json.load(json_file)
    active_games_dict[full_game_id]["Current Turn"] = "1"
    current_date = datetime.today().date()
    current_date_string = current_date.strftime("%m/%d/%Y")
    active_games_dict[full_game_id]["Game Started"] = current_date_string
    active_games_dict[full_game_id]["Days Ellapsed"] = 0
    with open('active_games.json', 'w') as json_file:
        json.dump(active_games_dict, json_file, indent=4)
    
    #update visuals
    current_turn_num = 1
    update_announcements_sheet(full_game_id, [], [])
    map_name = active_games_dict[full_game_id]["Map"]
    main_map = map.MainMap(game_id, map_name, current_turn_num)
    main_map.update()
    map.update_preview_image(game_id, current_turn_num)

def resolve_turn_processing(full_game_id, public_actions_list, private_actions_list):
    '''
    Resolves turn processing for a game in stage three (an active and fully setup game).

    Parameters:
    - full_game_id: The full game_id of the active game.
    - public_actions_list: A list of player public actions gathered from turn resolution HTML form. 
    - private_actions_list: A list of player private actions gathered from turn resolution HTML form. 
    '''
    playerdata_filepath = f'gamedata/{full_game_id}/playerdata.csv'
    regdata_filepath = f'gamedata/{full_game_id}/regdata.csv'
    rmdata_filepath = f'gamedata/{full_game_id}/rmdata.csv'
    wardata_filepath = f'gamedata/{full_game_id}/wardata.csv'
    game_id = int(full_game_id[-1])
    playerdata_list = read_file(playerdata_filepath, 1)
    player_count = len(playerdata_list)
    current_turn_num = get_current_turn_num(game_id)
    map_name = get_map_name(game_id)
    
    #create logs
    diplomacy_log = []
    reminders_list = []
    player_action_logs = []
    for i in range(player_count):
        player_action_logs.append([])

    #filter
    library = get_library(full_game_id)
    for player_actions_list in public_actions_list:
        for i, action in enumerate(player_actions_list):
            player_actions_list[i] = interpreter.check_action(action, library)
    for player_actions_list in private_actions_list:
        for i, action in enumerate(player_actions_list):
            player_actions_list[i] = interpreter.check_action(action, library)

    steal_tracking_dict = {}
    for playerdata in playerdata_list:
        if playerdata[3] == 'Crime Syndicate':
            inner_dict = {
                'Nation Name': None,
                'Streak': 0,
            }
            steal_tracking_dict[playerdata[1]] = inner_dict
    if steal_tracking_dict != {}:
        with open(f'gamedata/{full_game_id}/steal_tracking.json', 'w') as json_file:
            json.dump(steal_tracking_dict, json_file, indent=4)


    #Declare Action Dictionaries
    public_actions_dict = {
        'Surrender': [],
        'White Peace': [],
        'Sanction': [],
        'Purchase': [],
        'Research': [],
        'Remove': [],
        'Build': [],
        'Alliance': [],
        'Republic': [],
        'Make': [],
        'Buy': [],
        'Sell': [],
        'Event': []
    }
    private_actions_dict = {
        'Steal': [],
        'Withdraw': [],
        'Disband': [],
        'Deploy': [],
        'War': [],
        'Launch': [],
        'Move': []
    }


    #Oppertunity to Resolve Active Events
    public_actions_dict, private_actions_dict, diplomacy_log = events.resolve_active_events("Before Actions", public_actions_dict, private_actions_dict, full_game_id, diplomacy_log)

    
    #Sort Player Entered Public Actions
    if public_actions_list != []:
        for i, player_public_actions_list in enumerate(public_actions_list):
            for public_action in player_public_actions_list:
                action_type = identify(public_action)
                action = [i + 1, public_action]
                if action_type in public_actions_dict:
                    public_actions_dict[action_type].append(action)
    #process actions
    public_actions.resolve_trades(playerdata_filepath, regdata_filepath, full_game_id, diplomacy_log)
    if public_actions_list != []:
        update_control_map = False
        if len(public_actions_dict['Surrender'] + public_actions_dict['White Peace']) > 0:
            peace_action_list = public_actions_dict['Surrender'] + public_actions_dict['White Peace']
            diplomacy_log, player_action_logs = public_actions.resolve_peace_actions(peace_action_list, full_game_id, current_turn_num, diplomacy_log, player_action_logs)
            update_control_map = True
        if len(public_actions_dict['Research']) > 0:
            player_action_logs = public_actions.resolve_research_actions(public_actions_dict['Research'], full_game_id, player_action_logs)
        if len(public_actions_dict['Sanction']) > 0:
            diplomacy_log, player_action_logs = public_actions.resolve_declared_sanctions(public_actions_dict['Sanction'], full_game_id, current_turn_num, diplomacy_log, player_action_logs)
        if len(public_actions_dict['Alliance']) > 0:
            diplomacy_log, player_action_logs = public_actions.resolve_alliance_creations(public_actions_dict['Alliance'], current_turn_num, full_game_id, diplomacy_log, player_action_logs)
        if len(public_actions_dict['Purchase']) > 0:
            player_action_logs = public_actions.resolve_region_purchases(public_actions_dict['Purchase'], full_game_id, player_action_logs)
            update_control_map = True
        if len(public_actions_dict['Remove']) > 0:
            player_action_logs = public_actions.resolve_improvement_removals(public_actions_dict['Remove'], full_game_id, player_action_logs)
        if len(public_actions_dict['Build']) > 0:
            player_action_logs = public_actions.resolve_improvement_builds(public_actions_dict['Build'], full_game_id, player_action_logs)
        if len(public_actions_dict['Republic']) > 0:
            government_actions_list = public_actions_dict['Republic']
            diplomacy_log, player_action_logs = public_actions.resolve_government_abilities(government_actions_list, full_game_id, diplomacy_log, player_action_logs)
        if len(public_actions_dict['Make']) > 0:
            player_action_logs = public_actions.resolve_missile_builds(public_actions_dict['Make'], full_game_id, player_action_logs)
        if len(public_actions_dict['Event']) > 0:
            player_action_logs = public_actions.resolve_event_actions(public_actions_dict['Event'], full_game_id, current_turn_num, player_action_logs)
        print('Public action processing completed!')


    #Post Public Action Checks
    #check for missing war justifications
    checks.prompt_for_missing_war_justifications(full_game_id)
    #update improvement count in playerdata
    for i in range(player_count):
        player_id = i + 1
        checks.update_improvement_count(full_game_id, player_id)
    #update military capacity
    checks.update_military_capacity(full_game_id)


    #Sort Player Entered Private Actions
    if private_actions_list != []:
        for i, player_private_actions_list in enumerate(private_actions_list):
            for private_action in player_private_actions_list:
                action_type = identify(private_action)
                action = [i + 1, private_action]
                if action_type in private_actions_dict:
                    private_actions_dict[action_type].append(action)
    #process actions
    player_resource_market_incomes = False
    player_action_logs, player_resource_market_incomes = public_actions.resolve_market_actions(public_actions_dict['Buy'], public_actions_dict['Sell'], private_actions_dict['Steal'], full_game_id, current_turn_num, player_count, player_action_logs)    
    if private_actions_list != []:
        player_action_logs = private_actions.resolve_unit_withdraws(private_actions_dict['Withdraw'], full_game_id, player_action_logs, current_turn_num)
        if len(private_actions_dict['Disband']) > 0:
            player_action_logs = private_actions.resolve_unit_disbands(private_actions_dict['Disband'], full_game_id, player_action_logs)
        if len(private_actions_dict['Deploy']) > 0:
            player_action_logs = private_actions.resolve_unit_deployments(private_actions_dict['Deploy'], full_game_id, player_action_logs)
        if len(private_actions_dict['War']) > 0:
            diplomacy_log, player_action_logs = private_actions.resolve_war_declarations(private_actions_dict['War'], full_game_id, current_turn_num, diplomacy_log, player_action_logs)
        if len(private_actions_dict['Launch']) > 0:
            player_action_logs = private_actions.resolve_missile_launches(private_actions_dict['Launch'], full_game_id, player_action_logs)
        if len(private_actions_dict['Move']) > 0:
            player_action_logs = private_actions.resolve_unit_movements(private_actions_dict['Move'], full_game_id, player_action_logs)
            update_control_map = True
        print('Private action processing completed!')


    #Save Player Logs
    for index, action_log in enumerate(player_action_logs):
        directory = f'gamedata/{full_game_id}/logs'
        os.makedirs(directory, exist_ok=True)
        filename = os.path.join(directory, f'Player #{index + 1}.txt')
        with open(filename, 'w') as file:
            for string in action_log:
                file.write(string + '\n')


    #Save War Logs
    wardata_list = read_file(wardata_filepath, 2)
    for wardata in wardata_list:
        war_id = int(wardata[0])
        war_status = wardata[13]
        war_log = ast.literal_eval(wardata[14])
        os.makedirs(directory, exist_ok=True)
        filename = os.path.join(directory, f'War #{war_id}.txt')
        if war_status == 'Ongoing':
            with open(filename, 'w') as file:
                for entry in war_log:
                    file.write(entry + '\n')
    for wardata in wardata_list:
        wardata[14] = str([])
    with open(wardata_filepath, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(wardata_header_a)
        writer.writerow(wardata_header_b)
        writer.writerows(wardata_list)


    #End of Turn Checks and Updates
    diplomacy_log = checks.total_occupation_forced_surrender(full_game_id, current_turn_num, diplomacy_log)
    diplomacy_log = run_end_of_turn_checks(full_game_id, current_turn_num, player_count, diplomacy_log)
    for i in range(player_count):
        player_id = i + 1
        checks.gain_income(full_game_id, player_id)
        
    
    #Oppertunity to Resolve Active Events
    public_actions_dict, private_actions_dict, diplomacy_log = events.resolve_active_events("After Actions", public_actions_dict, private_actions_dict, full_game_id, diplomacy_log)


    #Prepwork for the Next Turn
    #resolve improvements with countdowns
    checks.countdown(full_game_id, map_name)
    for i in range(player_count):
        player_id = i + 1
        #resolve upkeep shortages
        diplomacy_log = checks.resolve_shortages(full_game_id, player_id, diplomacy_log)
        #update improvement count in playerdata
        checks.update_improvement_count(full_game_id, player_id)
    #update sanctions
    diplomacy_log, reminders_list = checks.update_sanctions(full_game_id, diplomacy_log, reminders_list)
    #update alliances
    diplomacy_log, reminders_list = checks.update_alliances(full_game_id, current_turn_num, diplomacy_log, reminders_list)
    for i in range(player_count):
        player_id = i + 1
        #update stability
        checks.update_stability(full_game_id, player_id, current_turn_num)
        #zero stability check
        diplomacy_log = checks.check_stability(full_game_id, player_id, current_turn_num, diplomacy_log)
        #collect resource market income
        checks.gain_resource_market_income(full_game_id, player_id, player_resource_market_incomes)
    #update income in playerdata
    checks.update_income(full_game_id, current_turn_num)
    
    
    #Resolve Bonus Phase
    if current_turn_num % 4 == 0:
        checks.bonus_phase_heals(full_game_id)
        diplomacy_log.append('All units and defensive improvements have regained 2 health.')
    #event procedure
    if current_turn_num % 8 == 0:
        diplomacy_log = events.trigger_event(full_game_id, current_turn_num, diplomacy_log)
        checks.update_stability(full_game_id, player_id, current_turn_num)
        diplomacy_log = checks.check_stability(full_game_id, player_id, current_turn_num, diplomacy_log)
    event_pending = False
    with open(f'active_games.json', 'r') as json_file:
        active_games_dict = json.load(json_file)
    current_event_dict = active_games_dict[full_game_id]["Current Event"]
    if current_event_dict != {}:
        event_pending = True


    #Update Game_Settings
    update_turn_num(game_id)
    with open('active_games.json', 'r') as json_file:
        active_games_dict = json.load(json_file)
    start_date = active_games_dict[full_game_id]["Game Started"]
    current_date = datetime.today().date()
    current_date_string = current_date.strftime("%m/%d/%Y")
    current_date_obj = datetime.strptime(current_date_string, "%m/%d/%Y")
    start_date_obj = datetime.strptime(start_date, "%m/%d/%Y")
    date_difference = current_date_obj - start_date_obj
    active_games_dict[full_game_id]["Days Ellapsed"] = date_difference.days
    with open('active_games.json', 'w') as json_file:
        json.dump(active_games_dict, json_file, indent=4)
    #check if someone has won the game
    check_for_winner(full_game_id, player_count, current_turn_num)


    #Update Visuals
    current_turn_num = get_current_turn_num(game_id)
    update_announcements_sheet(full_game_id, event_pending, diplomacy_log, reminders_list)
    resgraphs.update_all(full_game_id)
    main_map = map.MainMap(game_id, map_name, current_turn_num)
    main_map.update()
    if update_control_map:
        control_map = map.ControlMap(game_id, map_name)
        control_map.update()
    map.update_preview_image(game_id, current_turn_num)


#TURN PROCESSING FUNCTIONS
################################################################################

def create_new_game(full_game_id, form_data_dict, profile_ids_list):
    '''
    Backend code for creating the files for a new game. Returns nothing.

    Parameters:
    - full_game_id: A valid game_id to be used for the new game.
    - form_data_dict: Dictionary of data gathered from the turn resolution HTML form.
    - profile_ids_list: A list of all the profile ids of players participating in the game.
    '''

    #open game record files
    with open('active_games.json', 'r') as json_file:
        active_games_dict = json.load(json_file)
    with open('game_records.json', 'r') as json_file:
        game_records_dict = json.load(json_file)

    #datetime stuff
    current_date = datetime.today().date()
    current_date_string = current_date.strftime("%m/%d/%Y")
    game_version = "Development"

    #erase old game files
    erase_game(full_game_id)
    
    #update active_games
    for key, value in form_data_dict.items():
        active_games_dict[full_game_id][key] = value
    active_games_dict[full_game_id]["Current Turn"] = "Starting Region Selection in Progress"
    active_games_dict[full_game_id]["Game #"] = len(game_records_dict) + 1
    active_games_dict[full_game_id]["Version"] = game_version
    active_games_dict[full_game_id]["Days Ellapsed"] = 0
    active_games_dict[full_game_id]["Game Started"] = current_date_string
    active_games_dict[full_game_id]["Inactive Events"] = []
    active_games_dict[full_game_id]["Active Events"] = []
    active_games_dict[full_game_id]["Current Event"] = ""
    active_games_dict[full_game_id]["Game Active"] = True
    with open('active_games.json', 'w') as json_file:
        json.dump(active_games_dict, json_file, indent=4)
    
    #update game_records
    new_game_entry = {}
    new_game_entry["Game #"] = len(game_records_dict) + 1
    new_game_entry["Player Count"] = int(form_data_dict["Player Count"])
    new_game_entry["Victory Conditions"] = form_data_dict["Victory Conditions"]
    new_game_entry["Map"] = form_data_dict["Map"]
    new_game_entry["Accelerated Schedule"] = form_data_dict["Accelerated Schedule"]
    new_game_entry["Turn Duration"] = form_data_dict["Turn Length"]
    new_game_entry["Fog of War"] = form_data_dict["Fog of War"]
    new_game_entry["Version"] = game_version
    new_game_entry["Game End Turn"] = 0
    new_game_entry["Days Ellapsed"] = 0
    new_game_entry["Game Started"] = current_date_string
    new_game_entry["Game Ended"] = 'Present'
    game_records_dict[form_data_dict["Game Name"]] = new_game_entry
    with open('game_records.json', 'w') as json_file:
        json.dump(game_records_dict, json_file, indent=4)

    #copy map data
    match form_data_dict["Map"]:
        case "United States 2.0":
            map = 'united_states'
        case _:
            map = 'united_states'
    starting_map_images = ['mainmap', 'resourcemap', 'controlmap']
    files_destination = f'gamedata/{full_game_id}'
    images_destination = f'{files_destination}/images'
    shutil.copy(f'maps/{map}/regdata.csv', files_destination)
    for map_filename in starting_map_images:
        shutil.copy(f'maps/{map}/{map_filename}.png', images_destination)
    shutil.copy(f'maps/{map}/mainmap.png', 'static')
    shutil.move('static/mainmap.png', f'static/{full_game_id}_image.png')

    #create rmdata file
    rmdata_filepath = f'{files_destination}/rmdata.csv'
    with open(rmdata_filepath, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(rm_header)
    
    #create wardata.csv file
    wardata_filepath = f'{files_destination}/wardata.csv'
    with open(wardata_filepath, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(wardata_header_a)
        writer.writerow(wardata_header_b)

    #create vc_overrides.json
    vc_overrides_dict = {
        "Dual Loyalty": [False, False, False, False, False, False, False, False, False, False],
        "Tight Leash": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        "Reliable Ally": "None 0",
        "Road to Recovery": [False, False, False, False, False, False, False, False, False, False],
    }
    with open(f'{files_destination}/vc_overrides.json', 'w') as json_file:
        json.dump(vc_overrides_dict, json_file, indent=4)

    #create playerdata file
    playerdata_filepath = f"{files_destination}/playerdata.csv"
    player_data_header = ["Player","Nation Name","Color","Government","Foreign Policy","Military Capacity","Trade Fee","Stability Data","VC Set A","VC Set B","Dollars","Political Power","Technology","Coal","Oil","Green Energy","Basic Materials","Common Metals","Advanced Metals","Uranium","Rare Earth Elements","Alliance Data","Missile Data","Diplomatic Relations","Upkeep Manager","Miscellaneous Information","Income Details","Completed Research","Improvement Count","Status","Global ID"]
    player_data_temp_a = ["TBD","#ffffff","TBD","TBD","0/0","1:1","TBD"]
    victory_conditions_list = []
    player_data_temp_b = [['0.00',100,'0.00',100],['0.00',50,'0.00',100],['0.00',50,'0.00',100],['0.00',50,'0.00',100],['0.00',50,'0.00',100],['0.00',50,'0.00',100],['0.00',50,'0.00',100],['0.00',50,'0.00',100],['0.00',50,'0.00',100],['0.00',50,'0.00',100],['0.00',50,'0.00',100],[False, False, False, False],[0,0],['Neutral','Neutral','Neutral','Neutral','Neutral','Neutral','Neutral','Neutral','Neutral','Neutral'],['0.00','0.00','0.00','0.00'],['Capital Resource: None.','Owned Regions: 0','Occupied Regions: 0','Undeveloped Regions: 0','You cannot issue Economic Sanctions.','You cannot issue Military Sanctions.'],"None","[]",[0] * len(improvement_data_dict), 'Independent Nation']
    with open(playerdata_filepath, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(player_data_header)
        for i in range(int(form_data_dict["Player Count"])):
            victory_conditions_list = []
            random_easy_list = random.sample(easy_list, len(easy_list))
            random_normal_list = random.sample(normal_list, len(normal_list))
            random_hard_list = random.sample(hard_list, len(hard_list))
            set_a = []
            set_a.append(random_easy_list.pop())
            set_a.append(random_normal_list.pop())
            set_a.append(random_hard_list.pop())
            set_b = []
            set_b.append(random_easy_list.pop())
            set_b.append(random_normal_list.pop())
            set_b.append(random_hard_list.pop())
            victory_conditions_list.append(set_a)
            victory_conditions_list.append(set_b)
            player_number = f"Player #{i+1}"
            player_data_line = player_data_temp_a + victory_conditions_list + player_data_temp_b
            player_data_line.append(profile_ids_list[i])
            player_data_line.insert(0, player_number)
            writer.writerow(player_data_line)
    relations_data_all = []
    for i in range(int(form_data_dict["Player Count"])):
        relations_row = []
        player_number = "Player #" + str(i+1)
        relations_row.append(player_number)
        for i in range(int(form_data_dict["Player Count"])):
            relations_row.append('Neutral')
        while len(relations_row) < 11:
            relations_row.append('-')
        relations_data_all.append(relations_row)
    for index, entry in enumerate(relations_data_all):
        entry[index + 1] = '-'
    playerdata_list = read_file(playerdata_filepath, 1)
    for index, entry in enumerate(playerdata_list):
        entry[23] = relations_data_all[index]
    with open(playerdata_filepath, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(player_data_header)
        writer.writerows(playerdata_list)

def erase_game(full_game_id):
    '''
    Erases all the game files of a given game. Returns nothing.
    Note: This does not erase anything from the game_records.json file.

    Parameters:
    - full_game_id: A valid game_id to be erased.
    '''
    shutil.rmtree(f'gamedata/{full_game_id}')
    os.makedirs(f'gamedata/{full_game_id}/images')
    os.makedirs(f'gamedata/{full_game_id}/logs')

def get_data_for_nation_sheet(game_id, player_id, current_turn_num):
    '''
    Gathers all the needed data for a player's nation sheet data and spits it out as massive unorganized list that only nation_sheet.html can make sense of.

    Parameters:
    - game_id: The full game_id of the active game.
    - player_id: The integer id of the active player.
    - current_turn_num: An integer number representing the game's current turn number.
    '''
    
    #get core lists
    playerdata_filepath = f'gamedata/{game_id}/playerdata.csv'
    regdata_filepath = f'gamedata/{game_id}/regdata.csv'
    wardata_filepath = f'gamedata/{game_id}/wardata.csv'
    playerdata_list = read_file(playerdata_filepath, 1)
    RELATIONS_NAME_LIST = ['Player #1', 'Player #2', 'Player #3', 'Player #4', 'Player #5', 'Player #6', 'Player #7', 'Player #8', 'Player #9', 'Player #10', ]
    playerdata = playerdata_list[player_id - 1]
    player_research_list = ast.literal_eval(playerdata[26])
    player_information_dict = {
        'Stability': {},
        'Victory Conditions Data': {},
        'Resource Data': {},
        'Alliance Data': {},
        'Missile Data': {},
        'Relations Data': {},
        'Upkeep Manager': {},
        'Misc Info': {},
    }

    #get general nation info
    player_information_dict['Nation Name'] = playerdata[1]
    player_information_dict['Color'] = playerdata[2]
    player_information_dict['Government'] = playerdata[3]
    player_information_dict['Foreign Policy'] = playerdata[4]
    player_information_dict['Military Capacity'] = playerdata[5]
    player_information_dict['Trade Fee'] = playerdata[6]
    player_information_dict['Status'] = playerdata[28]

    #get stability data
    stability_raw_list = ast.literal_eval(playerdata[7])
    player_information_dict['Stability']['Header'] = stability_raw_list.pop(0)
    stability_data = "<br>".join(stability_raw_list)
    player_information_dict['Stability']['Data'] = stability_data
    
    #get victory condition data
    victory_conditions_list = ast.literal_eval(playerdata[8])
    player_information_dict['Victory Conditions Data']['Conditions List'] = victory_conditions_list
    vc_results = checks.check_victory_conditions(game_id, player_id, current_turn_num)
    vc_colors = []
    for entry in vc_results:
        if entry:
            vc_colors.append('#00ff00')
        else:
            vc_colors.append('#ff0000')
    player_information_dict['Victory Conditions Data']['Color List'] = vc_colors

    #resource data
    player_information_dict['Resource Data']['Class List'] = ['dollars', 'political', 'technology', 'coal', 'oil', 'green', 'basic', 'common', 'advanced', 'uranium', 'rare']
    player_information_dict['Resource Data']['Name List'] = RESOURCE_LIST
    stored_list = []
    income_list = []
    rate_list = []
    for j in range(9, 20):
        data = ast.literal_eval(playerdata[j])
        stored_list.append(f'{data[0]}/{data[1]}')
        income_list.append(data[2])
        rate_list.append(f'{data[3]}%')
    player_information_dict['Resource Data']['Stored List'] = stored_list
    player_information_dict['Resource Data']['Income List'] = income_list
    player_information_dict['Resource Data']['Rate List'] = rate_list

    #alliance data
    alliance_count, alliance_capacity = get_alliance_count(playerdata)
    with open('active_games.json', 'r') as json_file:
        active_games_dict = json.load(json_file)
    if "Shared Fate" in active_games_dict[game_id]["Active Events"]:
        if active_games_dict[game_id]["Active Events"]["Shared Fate"]["Effect"] == "Cooperation":
            alliance_capacity += 1
    player_information_dict['Alliance Data']['Name List'] = ALLIANCE_LIST
    alliance_colors = []
    alliance_data_list = update_alliance_data(player_research_list)
    for entry in alliance_data_list:
        if entry:
            alliance_colors.append('#00ff00')
        else:
            alliance_colors.append('#ff0000')
    player_information_dict['Alliance Data']['Header'] = f'Alliances ({alliance_count}/{alliance_capacity})'
    player_information_dict['Alliance Data']['Color List'] = alliance_colors

    #missile data
    missile_data = ast.literal_eval(playerdata[21])
    player_information_dict['Missile Data']['Standard'] = f'{missile_data[0]}x Standard Missiles'
    player_information_dict['Missile Data']['Nuclear'] = f'{missile_data[1]}x Nuclear Missiles'

    #relations data
    relation_colors = []
    relations_status_list = []
    relations_data = ast.literal_eval(playerdata[22])
    for index, relation in enumerate(relations_data):
        if index == 0:
            continue
        entry_data = relation.split()
        if len(entry_data) > 1:
            entry_formatted = f'{entry_data[0]} {entry_data[1]}'
        else:
            entry_formatted = entry_data[0]
        if entry_formatted == "Defense Pact" or entry_formatted == "Trade Agreement" or entry_formatted == "Research Agreement":
            relation_colors.append('#3c78d8')
        elif entry_formatted == "Non-Aggression Pact":
            relation_colors.append('#00ff00')
        elif entry_formatted == "Neutral":
            relation_colors.append('#f1c232')
        elif entry_formatted == "At War":
            relation_colors.append('#ff0000')
        elif entry_formatted == "-":
            relation_colors.append('#000000')
        relations_status_list.append(entry_formatted)
    player_information_dict['Relations Data']['Name List'] = RELATIONS_NAME_LIST
    player_information_dict['Relations Data']['Color List'] = relation_colors
    player_information_dict['Relations Data']['Status List'] = relations_status_list

    #upkeep manager data
    upkeep_data = ast.literal_eval(playerdata[23])
    player_information_dict['Upkeep Manager']['Coal'] = upkeep_data[0]
    player_information_dict['Upkeep Manager']['Oil'] = upkeep_data[1]
    player_information_dict['Upkeep Manager']['Green Energy'] = upkeep_data[2]
    player_information_dict['Upkeep Manager']['Total'] = upkeep_data[3]

    #misc info data
    misc_info = ast.literal_eval(playerdata[24])
    player_information_dict['Misc Info']['Capital Resource'] = misc_info[0]
    player_information_dict['Misc Info']['Owned Regions'] = misc_info[1]
    player_information_dict['Misc Info']['Occupied Regions'] = misc_info[2]
    player_information_dict['Misc Info']['Undeveloped Regions'] = misc_info[3]
    if 'Sanctioning' not in misc_info[4]:
        player_information_dict['Misc Info']['Economic Sanctions'] = misc_info[4]
    else:
        player_information_dict['Misc Info']['Economic Sanctions'] = misc_info[4][:-5]
    if 'Sanctioning' not in misc_info[5]:
        player_information_dict['Misc Info']['Military Sanctions'] = misc_info[5]
    else:
        player_information_dict['Misc Info']['Military Sanctions'] = misc_info[5][:-5]

    #income details
    income_details = ast.literal_eval(playerdata[25])
    for i in range(len(income_details)):
        income_details[i] = income_details[i].replace('&Tab;', '&nbsp;&nbsp;&nbsp;&nbsp;')
    income_str = "<br>".join(income_details)
    player_information_dict['Income Details'] = income_str

    #research details
    research_details = player_research_list
    research_str = "<br>".join(research_details)
    player_information_dict['Research Details'] = research_str

    return player_information_dict

def check_for_winner(full_game_id, player_count, current_turn_num):
    '''
    Spaghetti code that checks if a player has won the game and ends the game if so.
    '''
    playerdata_filepath = f'gamedata/{full_game_id}/playerdata.csv'
    player_has_won = False
    for i in range(player_count):
        player_id = i + 1
        victory_list = checks.check_victory_conditions(full_game_id, player_id, current_turn_num)
        if victory_list == [True, True, True]:
            player_has_won = True
            break
    if player_has_won:
        game_name = get_game_name(full_game_id)
        current_date = datetime.today().date()
        current_date_string = current_date.strftime("%m/%d/%Y")
        with open('active_games.json', 'r') as json_file:
            active_games_dict = json.load(json_file)
        active_games_dict[full_game_id]["Game Active"] = False
        with open('active_games.json', 'w') as json_file:
            json.dump(active_games_dict, json_file, indent=4)
        with open('game_records.json', 'r') as json_file:
            game_records_dict = json.load(json_file)
        player_data_dict = {}
        playerdata_list = read_file(playerdata_filepath, 1)
        for index, playerdata in enumerate(playerdata_list):
            player_data_entry_dict = {
                "Nation Name": "",
                "Color": "",
                "Government": "",
                "Foreign Policy": "",
                "Score": 0,
                "Victory": 0
            }
            player_id = index + 1
            player_global_id = playerdata[29]
            player_data_entry_dict["Nation Name"] = playerdata[1]
            player_data_entry_dict["Color"] = playerdata[2]
            player_data_entry_dict["Government"] = playerdata[3]
            player_data_entry_dict["Foreign Policy"] = playerdata[4]
            victory_list = checks.check_victory_conditions(full_game_id, player_id, current_turn_num)
            player_score = 0
            for entry in victory_list:
                if entry:
                    player_score += 1
            player_data_entry_dict["Score"] = player_score
            if player_data_entry_dict["Score"] == 3:
                player_data_entry_dict["Victory"] = 1
            player_data_dict[player_global_id] = player_data_entry_dict
        game_records_dict[game_name]["Player Data"] = player_data_dict
        game_records_dict[game_name]["Game End Turn"] = current_turn_num
        game_records_dict[game_name]["Game Ended"] = current_date_string
        with open('game_records.json', 'w') as json_file:
            json.dump(game_records_dict, json_file, indent=4)

def get_game_name(full_game_id):
    with open('active_games.json', 'r') as json_file:
        active_games_dict = json.load(json_file)
    game_name = active_games_dict[full_game_id]["Game Name"]
    return game_name

def get_map_name(game_id):
    '''Retrieves map name string given a game id.'''
    full_game_id = f'game{game_id}'
    with open('active_games.json', 'r') as json_file:
        active_games_dict = json.load(json_file)
    map_name = active_games_dict[full_game_id]["Map"]
    return map_name

def get_current_turn_num(game_id):
    '''Gets current turn number given game id.'''
    full_game_id = f'game{game_id}'
    with open('active_games.json', 'r') as json_file:
        active_games_dict = json.load(json_file)
    try:
        current_turn_num = int(active_games_dict[full_game_id]["Current Turn"])
    except:
        current_turn_num = active_games_dict[full_game_id]["Current Turn"]
    return current_turn_num

def update_turn_num(game_id):
    '''Updates the turn number given game id.'''
    full_game_id = f'game{game_id}'
    with open('active_games.json', 'r') as json_file:
        active_games_dict = json.load(json_file)
    current_turn_num = int(active_games_dict[full_game_id]["Current Turn"])
    current_turn_num += 1
    active_games_dict[full_game_id]["Current Turn"] = str(current_turn_num)
    with open('active_games.json', 'w') as json_file:
        json.dump(active_games_dict, json_file, indent=4)

def identify(action):
    ACTIONS_LIST = ['Surrender', 'White Peace', 'Sanction', 'Purchase', 'Research', 'Remove', 'Build', 'Alliance', 'Republic', 'Steal', 'Buy', 'Sell', 'Make', 'Withdraw', 'Disband', 'Deploy', 'War', 'Launch', 'Move', 'Event']
    for action_type in ACTIONS_LIST:
        if action_type.lower() in action[:12].lower():
            return action_type
    return None

def get_regions_in_radius(random_region_id, radius, regdata_list):
    '''
    Returns a list of all regions within x regions of a provided region id.

    Parameters:
    - random_region_id: A valid five character id of a region.
    - radius: A positive integer value.
    - regdata_list: The regdata_list derived from the game's regdata.csv file.
    '''
    regions_in_radius = set([random_region_id])
    for i in range(0, radius):
        new_regions_in_radius = set()
        for select_region_id in regions_in_radius:
            select_region_adjacency_list = get_adjacency_list(regdata_list, select_region_id)
            new_regions_in_radius.update(select_region_adjacency_list)
        regions_in_radius.update(new_regions_in_radius)
    return regions_in_radius

def get_library(full_game_id):
    '''
    Returns a dictionary containing all game terms. Use this to check validity of actions.
    '''
    
    #get core lists
    playerdata_filepath = f'gamedata/{full_game_id}/playerdata.csv'
    regdata_filepath = f'gamedata/{full_game_id}/regdata.csv'
    playerdata_list = read_file(playerdata_filepath, 1)
    regdata_list = read_file(regdata_filepath, 2)

    #create library of game terms
    library = {
        'Nation Name List': [playerdata[1] for playerdata in playerdata_list],
        'Region IDs': [region[0] for region in regdata_list],
        'Sanction Type List': ['Economic Sanctions', 'Military Sanctions'],
        'Research Name List': list(agenda_data_dict.keys()) + list(research_data_dict.keys()),
        'Improvement List': list(improvement_data_dict.keys()),
        'Alliance Type List': ALLIANCE_LIST,
        'Resource Name List': RESOURCE_LIST,
        'Missile Type List': ['Standard Missile', 'Standard Missiles', 'Nuclear Missile', 'Nuclear Missiles'],
        'Unit Name List': list(unit_data_dict.keys()),
        'Unit Abbreviation List': [unit['Abbreviation'] for unit in unit_data_dict.values()],
        'War Justification Name List': ['Animosity', 'Border Skirmish', 'Conquest', 'Annexation', 'Independence', 'Subjugation']
    }

    return library

def run_end_of_turn_checks(full_game_id, current_turn_num, player_count, diplomacy_log):
    
    checks.update_military_capacity(full_game_id)
    for i in range(player_count):
        player_id = i + 1
        #update playerdata improvement counts
        checks.update_improvement_count(full_game_id, player_id)
        #check refinery ratios
        checks.ratio_check(full_game_id, player_id)
        #check military capacity
        diplomacy_log = checks.remove_excess_units(full_game_id, player_id, diplomacy_log)
        #refresh improvement count
        checks.update_improvement_count(full_game_id, player_id)
        #update stockpile limits in playerdata
        checks.update_stockpile_limits(full_game_id, player_id)
    #update income in playerdata
    checks.update_income(full_game_id, current_turn_num)
    #update misc info and trade tax in playerdata
    for i in range(player_count):
        player_id = i + 1
        checks.update_misc_info(full_game_id, player_id)
        checks.update_trade_tax(full_game_id, player_id)
    #update records
    checks.update_records(full_game_id, current_turn_num)
    #update income in playerdata now that records have been updated (important for political power bonuses)
    checks.update_income(full_game_id, current_turn_num)

    return diplomacy_log

#GENERAL PURPOSE GLOBAL FUNCTIONS
################################################################################

def read_file(filepath, skip_value):

    '''
    Reads a csv file given a filepath and returns it as a list of lists.

    Parameters:
    - filepath: The full filepath to the desired file relative to core.py.
    - skip_value: A positive integer value representing how many of the first rows to skip. Usually 0-2.
    '''
    output = []
    with open(filepath, 'r') as file:
        reader = csv.reader(file)
        for i in range(0, skip_value):
            next(reader, None)
        for row in reader:
            if row != []:
                output.append(row)
    return output

def read_rmdata(rmdata_filepath, current_turn_num, refine, keep_header):
    '''
    Reads rmdata.csv and generates a list of all currently relevant transactions.

    Parameters:
    - rmdata_filepath: The full relative filepath to rmdata.csv.
    - current_turn_num: An integer number representing the game's current turn number.
    - refine: A count representing how many turns back you want of resource market data. Define as a positive integer or False if you want all records.
    - keep_header: A boolean value. Enter as True if you don't care about the header rows being in your data.
    '''

    #Get list of all transactions
    rmdata_list = []
    if keep_header == True:
        with open(rmdata_filepath, 'r') as file:
            reader = csv.reader(file)
            for row in reader:
                if row != []:
                    rmdata_list.append(row)
    if keep_header == False:
        with open(rmdata_filepath, 'r') as file:
                reader = csv.reader(file)
                next(reader,None)
                for row in reader:
                    if row != []:
                        rmdata_list.append(row)
    #Refine list as needed
    rmdata_refined_list = []
    if refine == 12:
        limit = current_turn_num - 12
        for transaction in rmdata_list:
            transaction[0] = int(transaction[0])
            transaction[3] = int(transaction[3])
            if transaction[0] >= limit:
                rmdata_refined_list.append(transaction)
    elif refine == 11:
        limit = current_turn_num - 11
        for transaction in rmdata_list:
            transaction[0] = int(transaction[0])
            transaction[3] = int(transaction[3])
            if transaction[0] >= limit:
                rmdata_refined_list.append(transaction)
    elif refine == False:
        for transaction in rmdata_list:
            transaction[0] = int(transaction[0])
            transaction[3] = int(transaction[3])
            rmdata_refined_list.append(transaction)
    return rmdata_refined_list


#SHEETS API BULLSHIT
################################################################################

def update_announcements_sheet(full_game_id, event_pending, diplomacy_log, reminders_list):
    '''
    Updates the Announcements Google Sheet.

    Parameters:
    - full_game_id: The full game_id of the active game.
    - event_pending: A bool that will be true if there is a current event that needs to be handled.
    - diplomacy_log: A list of pre-generated diplomatic interaction logs.
    - reminders_list: A list of pre-generated reminders.
    '''

    playerdata_filepath = f'gamedata/{full_game_id}/playerdata.csv'
    wardata_filepath = f'gamedata/{full_game_id}/wardata.csv'
    trucedata_filepath = f'gamedata/{full_game_id}/trucedata.csv'
    playerdata_list = read_file(playerdata_filepath, 1)
    wardata_list = read_file(wardata_filepath, 2)
    trucedata_list = read_file(trucedata_filepath, 1)

    #get needed data from playerdata.csv
    nation_name_list = []
    for player in playerdata_list:
        nation_name = [player[1]]
        nation_name_list.append(nation_name)
    while len(nation_name_list) < 10:
        nation_name_list.append(['N/A'])


    #get needed data from active_games.json
    with open('active_games.json', 'r') as json_file:
        active_games_dict = json.load(json_file)
    game_name = active_games_dict[full_game_id]["Game Name"]
    current_turn_num = int(active_games_dict[full_game_id]["Current Turn"])
    accelerated_schedule_str = active_games_dict[full_game_id]["Accelerated Schedule"]
    
    #calculate date information
    if not event_pending:
        season, year = date_from_turn_num(current_turn_num)
        game_name_output = f'''"{game_name}"'''
        date_output = f'{season} {year} - Turn {current_turn_num}'
    else:
        current_turn_num -= 1
        season, year = date_from_turn_num(current_turn_num)
        game_name_output = f'''"{game_name}"'''
        date_output = f'{season} {year} - Turn {current_turn_num} Bonus Phase'

    #get needed data from wardata.csv
    for war in wardata_list:
        if war[13] == 'Ongoing':
            war_name = war[11]
            diplomacy_log.insert(0, f'{war_name} is ongoing.')

    #get needed data from trucedata.csv
    for truce in trucedata_list:
        truce_participants_list = []
        for i in range(1, 11):
            truce_status = ast.literal_eval(truce[i])
            if truce_status:
                select_nation_name = nation_name_list[i - 1][0]
                truce_participants_list.append(select_nation_name)
        truce_name = ' - '.join(truce_participants_list)
        if int(truce[11]) > current_turn_num:
            diplomacy_log.append(f"{truce_name} truce through turn {truce[11]}.")
        if int(truce[11]) == current_turn_num:
            diplomacy_log.append(f'{truce_name} truce has expired.')


    #API Bullshit
    #define access
    sa = gspread.service_account()
    sh_name = "United We Stood - Announcement Sheet"
    wks_name = "Sheet1"
    sh = sa.open(sh_name)
    wks = sh.worksheet(wks_name)

    #update header
    wks.update_cell(4, 2, game_name_output)
    wks.update_cell(5, 2, date_output)

    #update record displays
    ln_1st, ln_2nd, ln_3rd = checks.get_top_three(full_game_id, 'largest_nation', True)
    lm_1st, lm_2nd, lm_3rd = checks.get_top_three(full_game_id, 'largest_military', True)
    mr_1st, mr_2nd, mr_3rd = checks.get_top_three(full_game_id, 'most_research', True)
    se_1st, se_2nd, se_3rd = checks.get_top_three(full_game_id, 'strongest_economy', True)
    wks.update('B9:B11', [[ln_1st], [ln_2nd], [ln_3rd]])
    wks.update('B14:B16', [[lm_1st], [lm_2nd], [lm_3rd]])
    wks.update('B19:B21', [[mr_1st], [mr_2nd], [mr_3rd]])
    wks.update('D9:E11', [[se_1st], [se_2nd], [se_3rd]])

    #update reminders
    if current_turn_num <= 4:
        reminders_list.append('First year expansion rules are in effect.')
    elif current_turn_num == 5:
        reminders_list.append('Normal expansion rules are now in effect.')
    if accelerated_schedule_str == 'Enabled' and current_turn_num <= 10:
        reminders_list.append('Accelerated schedule is in effect through turn 10.')
    elif accelerated_schedule_str == 'Enabled' and current_turn_num == 11:
        reminders_list.append('Normal turn schedule is now in effect.')
    reminders_str = "\n".join(reminders_list)
    wks.update_cell(3, 7, reminders_str)

    #update leaderboard
    red_rgb = float(67/255)
    green_rgb = float(67/255)
    blue_rgb = float(67/255)
    wks.format("G12:I21", { 'backgroundColor': {'red':red_rgb,'green':green_rgb,'blue':blue_rgb}})
    for index, playerdata in enumerate(playerdata_list):
        player_id = index + 1
        player_color_hex = playerdata[2]
        player_color_rgb_list = player_colors_conversions[player_color_hex]
        red_rgb = float(player_color_rgb_list[0]/255)
        green_rgb = float(player_color_rgb_list[1]/255)
        blue_rgb = float(player_color_rgb_list[2]/255)
        vc_results = checks.check_victory_conditions(full_game_id, player_id, current_turn_num)
        player_vc_score = 0
        for result in vc_results:
            if result == True:
                player_vc_score += 1
        if player_vc_score != 0:
            bar_range = f'G{11+player_id}:{score_to_col[player_vc_score]}{11+player_id}'
            wks.format(bar_range, { 'backgroundColor': {'red':red_rgb,'green':green_rgb,'blue':blue_rgb}})
    wks.update('G12:G21', nation_name_list)

    #update diplomacy
    if diplomacy_log != []:
        diplomacy_log_str = "\n".join(diplomacy_log)
    else:
        diplomacy_log_str = ''
    wks.update_cell(3, 11, diplomacy_log_str)

def update_text_color(sheet_name, worksheet_name, cell_range, color):
    #Get API info again
    sa = gspread.service_account()
    sh = sa.open(sheet_name)
    wks = sh.worksheet(worksheet_name)
    #Determine color
    if color == 'green':
        red_rgb = 0/255
        green_rgb = 255/255
        blue_rgb = 0/255
    elif color == 'red':
        red_rgb = 255/255
        green_rgb = 0/255
        blue_rgb = 0/255
    elif color == 'yellow':
        red_rgb = 241/255
        green_rgb = 194/255
        blue_rgb = 50/255
    elif color == 'blue':
        red_rgb = 60/255
        green_rgb = 120/255
        blue_rgb = 216/255
    elif color == 'white':
        red_rgb = 255/255
        green_rgb = 255/255
        blue_rgb = 255/255
    else:
        red_rgb = 0/255
        green_rgb = 0/255
        blue_rgb = 0/255
    color_formatted = {'red':red_rgb, 'green':green_rgb, 'blue':blue_rgb}
    #Change text color
    wks.format(cell_range, { 
            'textFormat': {
                'foregroundColor': color_formatted,
                'fontFamily': 'Droid Serif'
            }
        })
    
def update_text_color_new(wks, cell_range, color):
    #determine color
    if color == 'green':
        red_rgb = 0/255
        green_rgb = 255/255
        blue_rgb = 0/255
    elif color == 'red':
        red_rgb = 255/255
        green_rgb = 0/255
        blue_rgb = 0/255
    elif color == 'yellow':
        red_rgb = 241/255
        green_rgb = 194/255
        blue_rgb = 50/255
    elif color == 'blue':
        red_rgb = 60/255
        green_rgb = 120/255
        blue_rgb = 216/255
    elif color == 'white':
        red_rgb = 255/255
        green_rgb = 255/255
        blue_rgb = 255/255
    else:
        red_rgb = 0/255
        green_rgb = 0/255
        blue_rgb = 0/255
    color_formatted = {'red':red_rgb, 'green':green_rgb, 'blue':blue_rgb}
    #Change text color
    wks.format(cell_range, { 
            'textFormat': {
                'foregroundColor': color_formatted,
                'fontFamily': 'Droid Serif'
            }
        })


#DIPLOMACY SUB-FUNCTIONS
################################################################################

def get_alliance_count(playerdata):
    '''
    Gets a count of a player's active alliances and their total alliance capacity.

    Parameters:
    - playerdata: A single playerdata list from playerdata.csv.
    '''
    alliance_count = 0
    relations_data = ast.literal_eval(playerdata[22])
    for index, relation in enumerate(relations_data):
        if index == 0:
            continue
        entry_data = relation.split()
        if len(entry_data) > 1:
            alliance_type = f'{entry_data[0]} {entry_data[1]}'
            if alliance_type in ALLIANCE_LIST and alliance_type != 'Non-Aggression Pact':
                alliance_count += 1
    alliance_limit = 2
    if 'International Cooperation' in ast.literal_eval(playerdata[26]):
        alliance_limit += 1
    return alliance_count, alliance_limit

def get_alliances(relations_data_list, requested_alliance_type):

    '''Takes a player's relations data. Returns all player ids with the specified alliance with that player.'''
    player_id_list = []
    for index, relation in enumerate(relations_data_list):
        if relation not in ignore_list:
            relation_data_list = relation.split()
            if relation_data_list[0] != 'At':
                alliance_type = f'{relation_data_list[0]} {relation_data_list[1]}'
                if alliance_type == requested_alliance_type:
                    selected_nation_id = index
                    player_id_list.append(selected_nation_id)
    return player_id_list

def get_subjects(playerdata_list, overlord_nation_name, subject_type):
    '''Returns a list of all player ids that are subjects of the given nation name.'''
    player_id_list = []
    for index, playerdata in enumerate(playerdata_list):
        status = playerdata[28]
        if overlord_nation_name in status and subject_type in status:
            selected_nation_id = index + 1
            player_id_list.append(selected_nation_id)
    return player_id_list

def get_truces(trucedata_list, player_id_1, player_id_2, current_turn_num, player_count):
    overlord_truce_list = []
    for select_player_id in range(1, player_count + 1):
        truce_found = check_for_truce(trucedata_list, player_id_1, player_id_2, current_turn_num)
        if truce_found:
            overlord_truce_list.append(select_player_id)
    return overlord_truce_list

def update_alliance_data(player_research_list):
    alliance_data = [False, False, False, False]
    if 'Peace Accords' in player_research_list:
        alliance_data[0] = True
    if 'Defensive Agreements' in player_research_list:
        alliance_data[1] = True
    if 'Trade Routes' in player_research_list:
        alliance_data[2] = True
    if 'Research Exchange' in player_research_list:
        alliance_data[3] = True
    return alliance_data


#ECONOMIC SUB-FUNCTIONS
################################################################################

def get_economy_info(playerdata_list, request_list):
    '''Generates a list of lists of lists for requested economy information. Sub-function for action functions.'''
    index_list = []
    for resource in request_list:
        if resource == 'Dollars':
            index_list.append(9)
        elif resource == 'Political Power':
            index_list.append(10)
        elif resource == 'Technology':
            index_list.append(11)
        elif resource == 'Coal':
            index_list.append(12)
        elif resource == 'Oil':
            index_list.append(13)
        elif resource == 'Green Energy':
            index_list.append(14)
        elif resource == 'Basic Materials':
            index_list.append(15)
        elif resource == 'Common Metals':
            index_list.append(16)
        elif resource == 'Advanced Metals':
            index_list.append(17)
        elif resource == 'Uranium':
            index_list.append(18)
        elif resource == 'Rare Earth Elements':
            index_list.append(19)
    economy_masterlist = []
    for playerdata in playerdata_list:
        economy_list = []
        for i in index_list:
            resource_data_list = ast.literal_eval(playerdata[i])
            economy_list.append(resource_data_list)
        economy_masterlist.append(economy_list)
    return economy_masterlist

def round_total_income(total_income):
    '''Forcibly rounds a given income number to two digits. Sub-function of update_income().'''
    total_income = round(total_income, 2)
    total_income = "{:.2f}".format(total_income)
    return total_income

def update_stockpile(stockpile, cost):
    '''Updates a stockpile by subtracting the improvement cost and then rounding it. Meant to be saved to economydata_masterlist.'''
    stockpile -= cost
    stockpile = round_total_income(stockpile)
    return stockpile

def get_upkeep_dictionary(upkeep_type, playerdata, unit_count_list):
    '''
    Returns a dictionary that represents upkeep cost drain on a specific nation.
    
    Parameters:
    - upkeep_type: String representing upkeep type. Either 'Dollars Upkeep' or 'Energy Upkeep'.
    - playerdata: A playerdata list for a player from playerdata.csv.
    '''

    #take needed info from playerdata and core
    improvement_name_list = sorted(improvement_data_dict.keys())
    improvement_count_list = ast.literal_eval(playerdata[27])
    unit_name_list = sorted(unit_data_dict.keys())
    completed_research_list = ast.literal_eval(playerdata[26])

    upkeep_dict = {}

    #calculate dollars upkeep dict
    match upkeep_type:
        case 'Dollars Upkeep':
            for index, improvement_count in enumerate(improvement_count_list):
                inner_dict = {}
                improvement_name = improvement_name_list[index]
                improvement_dollars_upkeep = improvement_data_dict[improvement_name]['Dollars Upkeep']
                #handle edge cases
                if improvement_name == 'Coal Mine' and 'Coal Subsidies' in completed_research_list:
                    improvement_dollars_upkeep = 1
                elif improvement_name == 'Oil Well' and 'Oil Subsidies' in completed_research_list:
                    improvement_dollars_upkeep = 1
                elif improvement_name == 'Research Laboratory' and 'Upgraded Facilities' in completed_research_list:
                    improvement_dollars_upkeep = 2
                #check for efficient bureaucracy
                if 'Efficient Bureaucracy' in completed_research_list:
                    improvement_dollars_upkeep *= 0.5
                #add improvement data to upkeep_dict
                if improvement_count > 0 and improvement_dollars_upkeep > 0:
                    inner_dict['Improvement Upkeep'] = improvement_dollars_upkeep
                    inner_dict['Improvement Count'] = improvement_count
                    upkeep_dict[improvement_name] = inner_dict
        #calculate energy upkeep dict
        case 'Energy Upkeep':
            for index, improvement_count in enumerate(improvement_count_list):
                inner_dict = {}
                improvement_name = improvement_name_list[index]
                improvement_energy_upkeep = improvement_data_dict[improvement_name]['Energy Upkeep']
                #handle edge cases
                if improvement_name == 'City' and 'Power Grid Restoration' in completed_research_list:
                    improvement_energy_upkeep = 1
                #add improvement data to upkeep_dict
                if improvement_count > 0 and improvement_energy_upkeep > 0:
                    inner_dict['Improvement Upkeep'] = improvement_energy_upkeep
                    inner_dict['Improvement Count'] = improvement_count
                    upkeep_dict[improvement_name] = inner_dict
        #calculate unit dollars upkeep dict
        case 'Unit Dollars Upkeep':
            for index, unit_count in enumerate(unit_count_list):
                inner_dict = {}
                unit_name = unit_name_list[index]
                unit_dollars_upkeep = unit_data_dict[unit_name]['Dollars Upkeep']
                #add improvement data to upkeep_dict
                if unit_count > 0:
                    inner_dict['Improvement Upkeep'] = unit_dollars_upkeep
                    inner_dict['Improvement Count'] = unit_count
                    upkeep_dict[unit_name] = inner_dict
        #calculate unit oil upkeep dict
        case 'Unit Oil Upkeep':
            for index, unit_count in enumerate(unit_count_list):
                inner_dict = {}
                unit_name = unit_name_list[index]
                unit_oil_upkeep = unit_data_dict[unit_name]['Oil Upkeep']
                #add improvement data to upkeep_dict
                if unit_count > 0:
                    inner_dict['Improvement Upkeep'] = unit_oil_upkeep
                    inner_dict['Improvement Count'] = unit_count
                    upkeep_dict[unit_name] = inner_dict


    #Sort Dictionary
    sorted_items = sorted(upkeep_dict.items(), key=upkeep_dict_custom_key)
    sorted_upkeep_dict = dict(sorted_items)
    upkeep_dict = sorted_upkeep_dict

    return upkeep_dict

def upkeep_dict_custom_key(item):
    return item[1]['Improvement Upkeep'], item[1]['Improvement Count']

def get_upkeep_sum(upkeep_dict):
    '''
    Calculates a total upkeep sum based on the provided upkeep dictionary.
    
    Parameters:
    - upkeep_dict: A dictionary that represents upkeep cost drain on a specific nation. Generated from get_upkeep_dictionary().
    '''

    upkeep_sum = 0
    for improvement_name, details in upkeep_dict.items():
        improvement_upkeep = details.get('Improvement Upkeep', 0)
        improvement_count = details.get('Improvement Count', 0)
        upkeep_total = improvement_upkeep * improvement_count
        upkeep_sum += upkeep_total

    return upkeep_sum

def get_unit_count_list(player_id, full_game_id):
    
    regdata_filepath = f'gamedata/{full_game_id}/regdata.csv'
    regdata_list = read_file(regdata_filepath, 2)
    unit_name_list = sorted(unit_data_dict.keys())

    count_list = []
    for unit_name in unit_name_list:
        unit_abbr = unit_data_dict[unit_name]['Abbreviation']
        count = 0
        for region in regdata_list:
            unit_data = ast.literal_eval(region[5])
            unit_name_in_region = unit_data[0]
            if unit_name_in_region != None:
                if unit_data[2] == player_id and unit_abbr == unit_name_in_region:
                    count += 1
        count_list.append(count)

    return count_list

def check_for_adjacent_improvement(player_id, region_id, improvement_list, regdata_list):
    '''
    Returns True if an improvement in the improvement list is found in the adjacency list.
    '''

    for region in regdata_list:
        if region_id == region[0]:
            adjacency_list = ast.literal_eval(region[8])
    
    for region in regdata_list:
        if region[0] in adjacency_list:
            control_data = ast.literal_eval(region[2])
            improvement_data = ast.literal_eval(region[4])
            if control_data[0] == player_id and improvement_data[0] in improvement_list:
                return True

    return False


#WAR SUB-FUNCTIONS
################################################################################

def read_military_capacity(player_military_capacity_data):
    player_military_capacity_list = player_military_capacity_data.split('/')
    used_mc = int(player_military_capacity_list[0])
    total_mc = float(player_military_capacity_list[1])
    return used_mc, total_mc

def check_military_capacity(player_military_capacity_data, amount):
    '''Calculates if a player has an amount of military capacity available.'''
    player_military_capacity_list = player_military_capacity_data.split('/')
    used_mc = int(player_military_capacity_list[0])
    total_mc = float(player_military_capacity_list[1])
    if used_mc + amount > total_mc:
        return False
    return True

def get_wars(relations_data_list):
    '''Takes a player's relations data. Returns all player ids who are at war with that player.'''
    player_id_list = []
    for index, relation in enumerate(relations_data_list):
        if relation not in ignore_list:
            relation_data_list = relation.split()
            if relation_data_list[0] == 'At':
                selected_nation_id = index
                player_id_list.append(selected_nation_id)
    return player_id_list

def join_ongoing_war(wardata_list, war_id, player_id, war_side):
    '''Given a information, add a player to a war.'''
    if war_side == 'Attacker':
        player_entry_data = ['Secondary Attacker', 'TBD', 0, 0, 0, 0]
    elif war_side == 'Defender':
        player_entry_data = ['Secondary Defender', 'TBD', 0, 0, 0, 0]
    for war in wardata_list:
        if war[0] == war_id:
            war[player_id] = player_entry_data
    return wardata_list

def calculate_unit_damage_modifier(friendly_unit_id, friendly_player_id, regdata_list, target_type, target_region_id):
    damage_modifier = 0

    unit_ids = [unit['Abbreviation'] for unit in unit_data_dict.values()]
    tank_type_units = [unit for unit, data in unit_data_dict.items() if data.get('Unit Type') == 'Tank']

    #damage bonus from nearby artillery
    target_adjacency_list = get_adjacency_list(regdata_list, target_region_id)
    for select_region_id in target_adjacency_list:
        select_region_data = get_region_data(regdata_list, select_region_id)
        select_unit_data = ast.literal_eval(select_region_data[5])
        select_unit_id = select_unit_data[0]
        if select_unit_id != None:
            select_unit_owner_id = select_unit_data[2]
            if select_unit_id == 'AR' and select_unit_owner_id == friendly_player_id:
                damage_modifier += 1
                break

    #damage bonus from heavy tank abilities
    if friendly_unit_id == 'HT' and target_type == 'LT':
        damage_modifier += 1
    elif friendly_unit_id == 'HT' and target_type not in unit_ids:
        damage_modifier += 1

    #damage bonus from main battle tank abilities
    if friendly_unit_id == 'BT' and target_type in tank_type_units:
        damage_modifier += 1
    elif friendly_unit_id == 'BT' and target_type not in unit_ids:
        damage_modifier += 1

    return damage_modifier

def calculate_unit_roll_modifier(friendly_unit_id, friendly_research_list, friendly_player_id, friendly_war_role, regdata_list, target_type, target_region_id):
    roll_modifier = 0

    infantry_type_units = [unit for unit, data in unit_data_dict.items() if data.get('Unit Type') == 'Infantry']

    #roll bonus from research
    if 'Attacker' in friendly_war_role and 'Superior Training' in friendly_research_list:
        roll_modifier += 1
    elif 'Defender' in friendly_war_role and 'Defensive Tactics' in friendly_research_list:
        roll_modifier += 1

    #roll bonus from special forces ability
    if friendly_unit_id == 'SF' and target_type in infantry_type_units:
        roll_modifier += 1

    #roll bonus from nearby light tank
    target_adjacency_list = get_adjacency_list(regdata_list, target_region_id)
    for select_region_id in target_adjacency_list:
        select_region_data = get_region_data(regdata_list, select_region_id)
        select_unit_data = ast.literal_eval(select_region_data[5])
        select_unit_id = select_unit_data[0]
        if select_unit_id != None:
            select_unit_owner_id = select_unit_data[2]
            if friendly_unit_id in infantry_type_units and select_unit_id == 'LT' and select_unit_owner_id == friendly_player_id:
                roll_modifier += 1
                break
    
    return roll_modifier

def conduct_combat(attacker_data_list, defender_data_list, war_statistics_list, playerdata_list, regdata_list, war_log):
    '''
    Conducts combat between two units or a unit and a defensive improvement.
    '''
    
    #get information
    attacker_unit_id, attacker_unit_health, attacker_player_id, attacker_war_role, attacker_region_id = attacker_data_list
    defender_name, defender_health, defender_player_id, defender_war_role, defender_region_id = defender_data_list
    attacker_battles_won, attacker_battles_lost, defender_battles_won, defender_battles_lost, = war_statistics_list
    attacker_nation_name = playerdata_list[attacker_player_id - 1][1]
    defender_nation_name = playerdata_list[defender_player_id - 1][1]
    attacker_research_list = ast.literal_eval(playerdata_list[attacker_player_id - 1][26])
    defender_research_list = ast.literal_eval(playerdata_list[defender_player_id - 1][26])

    #get modifiers
    attacker_roll_modifier = calculate_unit_roll_modifier(attacker_unit_id, attacker_research_list, attacker_player_id, attacker_war_role, regdata_list, defender_name, defender_region_id)
    defender_roll_modifier = calculate_unit_roll_modifier(defender_name, defender_research_list, defender_player_id, defender_war_role, regdata_list, attacker_unit_id, defender_region_id)
    attacker_damage_modifier = calculate_unit_damage_modifier(attacker_unit_id, attacker_player_id, regdata_list, defender_name, defender_region_id)

    #get damage values and hit values
    attacker_name = next((unit for unit, data in unit_data_dict.items() if data.get('Abbreviation') == attacker_unit_id), None)
    attacker_combat_value = unit_data_dict[attacker_name]['Combat Value']
    attacker_victory_damage = unit_data_dict[attacker_name]['Victory Damage'] + attacker_damage_modifier
    attacker_draw_damage = unit_data_dict[attacker_name]['Draw Damage']
    if defender_name in [unit['Abbreviation'] for unit in unit_data_dict.values()]:
        defender_damage_modifier = calculate_unit_damage_modifier(defender_name, defender_player_id, regdata_list, attacker_unit_id, defender_region_id)
        defender_name = next((unit for unit, data in unit_data_dict.items() if data.get('Abbreviation') == defender_name), None)
        defender_combat_value = unit_data_dict[defender_name]['Combat Value']
        defender_victory_damage = unit_data_dict[defender_name]['Victory Damage'] + defender_damage_modifier
        defender_draw_damage = unit_data_dict[defender_name]['Draw Damage']
    else:
        defender_combat_value = improvement_data_dict[defender_name]['Combat Value']
        defender_victory_damage = improvement_data_dict[defender_name]['Victory Damage']
        defender_draw_damage = improvement_data_dict[defender_name]['Draw Damage']
    
    #execute combat
    attacker_roll = random.randint(1, 10) + attacker_roll_modifier
    defender_roll = random.randint(1, 10) + defender_roll_modifier
    attacker_hit = False
    defender_hit = False
    if attacker_roll >= attacker_combat_value:
        attacker_hit = True
    if defender_roll >= defender_combat_value:
        defender_hit = True
    war_log.append(f'{attacker_nation_name} {attacker_name} {attacker_region_id} vs {defender_nation_name} {defender_name} {defender_region_id}')
    #attacker victory
    if attacker_hit and not defender_hit:
        defender_health -= attacker_victory_damage
        attacker_battles_won += 1
        defender_battles_lost += 1
        if attacker_roll_modifier > 0 and defender_roll_modifier > 0:
            war_log.append(f'    {attacker_nation_name} rolled {attacker_roll} (+{attacker_roll_modifier}). {defender_nation_name} rolled {defender_roll} (+{defender_roll_modifier}). Attacker victory!')
        elif attacker_roll_modifier > 0:
            war_log.append(f'    {attacker_nation_name} rolled {attacker_roll} (+{attacker_roll_modifier}). {defender_nation_name} rolled {defender_roll}. Attacker victory!')
        elif defender_roll_modifier > 0:
            war_log.append(f'    {attacker_nation_name} rolled {attacker_roll}. {defender_nation_name} rolled {defender_roll} (+{defender_roll_modifier}). Attacker victory!')
        else:
            war_log.append(f'    {attacker_nation_name} rolled {attacker_roll}. {defender_nation_name} rolled {defender_roll}. Attacker victory!')
        if attacker_damage_modifier > 0:
            war_log.append(f'        {attacker_nation_name} {attacker_name} dealt an additional {attacker_damage_modifier} damage.')
    #defender victory
    elif not attacker_hit and defender_hit or (attacker_hit == defender_hit and 'Counter Offensive' in defender_research_list):
        attacker_unit_health -= defender_victory_damage
        defender_battles_won += 1
        attacker_battles_lost += 1
        if attacker_roll_modifier > 0 and defender_roll_modifier > 0:
            war_log.append(f'    {attacker_nation_name} rolled {attacker_roll} (+{attacker_roll_modifier}). {defender_nation_name} rolled {defender_roll} (+{defender_roll_modifier}). Defender victory!')
        elif attacker_roll_modifier > 0:
            war_log.append(f'    {attacker_nation_name} rolled {attacker_roll} (+{attacker_roll_modifier}). {defender_nation_name} rolled {defender_roll}. Defender victory!')
        elif defender_roll_modifier > 0:
            war_log.append(f'    {attacker_nation_name} rolled {attacker_roll}. {defender_nation_name} rolled {defender_roll} (+{defender_roll_modifier}). Defender victory!')
        else:
            war_log.append(f'    {attacker_nation_name} rolled {attacker_roll}. {defender_nation_name} rolled {defender_roll}. Defender victory!')
        if defender_damage_modifier > 0:
            war_log.append(f'        {defender_nation_name} {defender_name} dealt an additional {defender_damage_modifier} damage.')
    #draw
    else:
        attacker_unit_health -= defender_draw_damage
        defender_health -= attacker_draw_damage
        if attacker_roll_modifier > 0 and defender_roll_modifier > 0:
            war_log.append(f'    {attacker_nation_name} rolled {attacker_roll} (+{attacker_roll_modifier}). {defender_nation_name} rolled {defender_roll} (+{defender_roll_modifier}). Draw!')
        elif attacker_roll_modifier > 0:
            war_log.append(f'    {attacker_nation_name} rolled {attacker_roll} (+{attacker_roll_modifier}). {defender_nation_name} rolled {defender_roll}. Draw!')
        elif defender_roll_modifier > 0:
            war_log.append(f'    {attacker_nation_name} rolled {attacker_roll}. {defender_nation_name} rolled {defender_roll} (+{defender_roll_modifier}). Draw!')
        else:
            war_log.append(f'    {attacker_nation_name} rolled {attacker_roll}. {defender_nation_name} rolled {defender_roll}. Draw!')
    return attacker_unit_health, attacker_battles_won, attacker_battles_lost, defender_health, defender_battles_won, defender_battles_lost, war_log

def war_resolution(player_id_1, war_justifications_list, signatories_list, current_turn_num, playerdata_list, regdata_list):
    '''Resolves a war that ends in an attacker or defender victory.'''
    
    looser_playerdata = playerdata_list[player_id_1 - 1]
    duration = current_turn_num + 11

    #resolve each winning war justification
    for war_justification in war_justifications_list:
        victor_player_id = war_justification[0]
        victor_war_justification = war_justification[1]
        victor_war_claims_list = war_justification[2]
        victor_playerdata = playerdata_list[victor_player_id - 1]
        victor_nation_name = victor_playerdata[1]
        defeat_penalty = 1
        #resolve war justification
        match victor_war_justification:
            case 'Border Skirmish' | 'Conquest' | 'Annexation':
                for region in regdata_list:
                    region_id = region[0]
                    if region_id in victor_war_claims_list:
                        control_data = ast.literal_eval(region[2])
                        if control_data[0] == player_id_1:
                            new_data = [victor_player_id, 0]
                            region[2] = str(new_data)
            case 'Animosity':
                pp_resource_data_winner = ast.literal_eval(victor_playerdata[10])
                pp_stockpile_winner = float(pp_resource_data_winner[0])
                pp_stockpile_winner += 10
                pp_resource_data_winner[0] = round_total_income(pp_stockpile_winner)
                victor_playerdata[10] = pp_resource_data_winner
                pp_resource_data_looser = ast.literal_eval(looser_playerdata[10])
                pp_resource_data_looser[0] = '0.00'
                looser_playerdata[10] = pp_resource_data_looser
                defeat_penalty = 2
            case 'Subjugation':
                looser_stability_data = ast.literal_eval(looser_playerdata[7])
                subject_type = 'Puppet State'
                looser_stability_data.append('-1 from Puppet State status')
                looser_playerdata[7] = str(looser_stability_data)
                looser_status = f'{subject_type} of {victor_nation_name}'
                looser_playerdata[28] = looser_status
            case 'Independence':
                winner_stability_data = ast.literal_eval(victor_playerdata[7])
                winner_stability_data_filtered = []
                for entry in winner_stability_data:
                    if entry != '-1 from Puppet State status':
                        winner_stability_data_filtered.append(entry)
                victor_playerdata[7] = str(winner_stability_data_filtered)
                looser_playerdata[28] = 'Independent Nation'
        #resolve stability bonus
        winner_stability_data = ast.literal_eval(victor_playerdata[7])
        winner_stability_data.append(f'1 from Victory through turn {duration}')
        victor_playerdata[7] = str(winner_stability_data)
        playerdata_list[victor_player_id - 1] = victor_playerdata
    
    
    #Resolve Stability Penalty
    looser_stability_data = ast.literal_eval(looser_playerdata[7])
    looser_stability_data.append(f'-{defeat_penalty} from Defeat through turn {duration}')
    looser_playerdata[7] = str(looser_stability_data)
    playerdata_list[player_id_1 - 1] = looser_playerdata


    #End Remaining Occupations
    for region in regdata_list:
        if len(region[0]) == 5:
            control_data = ast.literal_eval(region[2])
            owner_id = control_data[0]
            occupier_id = control_data[1]
            if signatories_list[owner_id - 1] and signatories_list[occupier_id - 1]:
                new_data = [owner_id, 0]
                region[2] = str(new_data)

    return playerdata_list, regdata_list

def add_truce_period(full_game_id, signatories_list, war_outcome, current_turn_num):
    '''Creates a truce period between the players marked in the signatories list. Length depends on war outcome.'''

    #get core lists
    trucedata_filepath = f'gamedata/{full_game_id}/trucedata.csv'
    trucedata_list = read_file(trucedata_filepath, 0)

    #determine truce period length
    if war_outcome == 'Animosity' or war_outcome == 'Border Skirmish':
        truce_length = 4
    else:
        truce_length = 8

    #generate output
    truce_id = len(trucedata_list)
    signatories_list.insert(0, truce_id)
    signatories_list.append(current_turn_num + truce_length)
    trucedata_list.append(signatories_list)

    #update trucedata.csv
    with open(trucedata_filepath, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerows(trucedata_list)

def repair_relations(diplomatic_relations_masterlist, wardata_list):
    '''
    Restores diplomatic relations to neutral if there is no longer a war between two players.
    '''

    for i, diplomatic_relations_list in enumerate(diplomatic_relations_masterlist):
        player_id_1 = i + 1
        for player_id_2, relation in enumerate(diplomatic_relations_list):
            if relation == 'At War':
                war_found = False
                for war in wardata_list:
                    if war[player_id_1] != '-' and war[player_id_2] != '-' and war[13] == 'Ongoing':
                        wardata_1 = ast.literal_eval(war[player_id_1])
                        war_role_1 = wardata_1[0]
                        wardata_2 = ast.literal_eval(war[player_id_2])
                        war_role_2 = wardata_2[0]
                        if ('Attacker' in war_role_1 and 'Defender' in war_role_2) or ('Attacker' in war_role_2 and 'Defender' in war_role_1):
                            war_found = True
                            break
                if war_found == False:
                    diplomatic_relations_masterlist[i][player_id_2] = 'Neutral'
    
    return diplomatic_relations_masterlist

def check_for_truce(trucedata_list, player_id_1, player_id_2, current_turn_num):
    '''Checks for a truce between two players. Returns True if one is found, otherwise returns False.'''
    for truce in trucedata_list:
        attacker_truce = ast.literal_eval(truce[player_id_1])
        defender_truce = ast.literal_eval(truce[player_id_2])
        if attacker_truce and defender_truce and int(truce[11]) >= current_turn_num:
            return True
    return False

def attempt_missile_defense(missile_type, improvement_data, target_nation_name, target_player_research, war_log):
    
    improvement_name = improvement_data[0]
    improvement_health = improvement_data[1]
    missile_defense_roll = random.randint(1, 10)
    defense_hit_value = 9999999
    
    match missile_type:
        case 'Standard Missile':
            if improvement_name == 'Missile Defense System':
                defense_hit_value = 6
            elif improvement_name == 'Missile Defense Network':
                defense_hit_value = 3
            elif 'Localized Missile Defense' in target_player_research and improvement_health != 99 and improvement_health != 0:
                defense_hit_value = improvement_data_dict[improvement_name]['Combat Value']
        case 'Nuclear Missile':
            if improvement_name == 'Missile Defense Network':
                defense_hit_value = 6
    
    if defense_hit_value != 9999999:
        war_log.append(f'    {target_nation_name} {improvement_name} rolled a {missile_defense_roll}.')
        if missile_defense_roll >= defense_hit_value:
            war_log.append(f'    Hit! Incoming {missile_type} was shot down!')
            return False
        else:
            war_log.append(f'    Miss! {improvement_name} defenses failed!')
    return True


#MISC SUB-FUNCTIONS
################################################################################

def date_from_turn_num(current_turn_num):
    remainder = current_turn_num % 4
    if remainder == 0:
        season = 'Winter'
    elif remainder == 1:
        season = 'Spring'
    elif remainder == 2:
        season = 'Summer'
    elif remainder == 3:
        season = 'Fall'
    quotient = current_turn_num // 4
    year = 2021 + quotient
    if season == 'Winter':
        year -= 1
    return season, year

def filter_region_names(regdata_list, action_list):
    '''Removes player actions with bad region names. Sub-function for action functions.'''
    region_id_list = []
    for region in regdata_list:
        region_id_list.append(region[0])
    action_list_filtered = []
    for action in action_list:
        region_id = action[1][-5:]
        if region_id in region_id_list:
            action_list_filtered.append(action)
        else:
            error_str = 'The action: ' + str(action) + ' failed due to an invalid region name.'
            print(error_str)
    return action_list_filtered

def get_region_data(regdata_list, region_id):
    for region in regdata_list:
        if region[0] == region_id:
            region_data = region
            return region_data

def get_adjacency_list(regdata_list, region_id):
    for region in regdata_list:
         if region[0] == region_id:
            adjacency_list = ast.literal_eval(region[8])
            return adjacency_list

def get_nation_info(playerdata_list):
    '''Gets each nation's name, color, government, and fp info. Sub-function for resolve_research_actions()'''
    nation_info_masterlist = []
    for player in playerdata_list:
        player_nation_name = player[1]
        player_color = player[2]
        player_government = player[3]
        player_fp = player[4]
        player_military_capacity = player[5]
        player_trade_fee = player[6]
        if player_trade_fee != 'No Trade Fee':
            player_trade_fee = player_trade_fee[0]
            player_trade_fee = int(player_trade_fee)
        else:
            player_trade_fee = 0
        nation_info_list = [player_nation_name, player_color, player_government, player_fp, player_military_capacity, player_trade_fee]
        nation_info_masterlist.append(nation_info_list)
    return nation_info_masterlist

def search_and_destroy(player_id, desired_improvement, regdata_list):
    candidate_region_ids = []
    for region in regdata_list:
        region_id = region[0]
        control_data = ast.literal_eval(region[2])
        owner_id = control_data[0]
        improvement_data = ast.literal_eval(region[4])
        improvement_name = improvement_data[0]
        if improvement_name == desired_improvement and player_id == owner_id:
            candidate_region_ids.append(region_id)

    #randomly select one of the candidate regions
    random.shuffle(candidate_region_ids)
    chosen_region_id = candidate_region_ids.pop()
    for region in regdata_list:
        if region[0] == chosen_region_id:
            region[4] = '[None, 99]'
            break
    return chosen_region_id, regdata_list

def search_and_destroy_unit(player_id, desired_unit_id, regdata_list):
    '''Randomly destroys one unit of a given type belonging to a specific player.'''

    #get list of regions with desired_unit_id owned by player_id
    candidate_region_ids = []
    if desired_unit_id in unit_ids:
        for region in regdata_list:
            region_id = region[0]
            unit_data = ast.literal_eval(region[5])
            if unit_data[0] == desired_unit_id:
                if unit_data[2] == player_id:
                    candidate_region_ids.append(region_id)
    elif desired_unit_id == 'ANY':
        for region in regdata_list:
            region_id = region[0]
            unit_data = ast.literal_eval(region[5])
            if unit_data[0] in unit_ids:
                if unit_data[2] == player_id:
                    candidate_region_ids.append(region_id)

    #randomly select one of the candidate regions
    random.shuffle(candidate_region_ids)
    chosen_region_id = candidate_region_ids.pop()
    for region in regdata_list:
        if region[0] == chosen_region_id:
            region[5] = '[None, 99]'
            break

    return chosen_region_id, regdata_list

def update_improvement_data(regdata_list, region_id, improvement_data):
    '''Replaces the unit data of a region with the inputed list.'''
    for region in regdata_list:
        if region[0] == region_id:
            region[4] = str(improvement_data)
            break
    return regdata_list

def update_unit_data(regdata_list, region_id, unit_data):
    '''Replaces the unit data of a region with the inputed list.'''
    for region in regdata_list:
        if region[0] == region_id:
            region[5] = str(unit_data)
            break
    return regdata_list

def update_nuke_data(regdata_list, region_id, nuke_data):
    for region in regdata_list:
        if region[0] == region_id:
            region[6] = str(nuke_data)
            break
    return regdata_list

def verify_ownership(regdata_list, region_id, player_id):
    '''Verifies a region is controlled by a specific player and that it is unoccupied. Sub-function for action functions.'''
    for region in regdata_list:
        if region[0] == region_id:
            control_data = ast.literal_eval(region[2])
            if control_data[0] == player_id and control_data[1] == 0:
                return True
            else:
                return False

def verify_ratio(improvement_count_list, improvement_name):
    refinery_list = ['Advanced Metals Refinery', 'Oil Refinery', 'Uranium Refinery']
    improvement_name_list = sorted(improvement_data_dict.keys())
    if improvement_name in refinery_list:
        if improvement_name == 'Advanced Metals Refinery':
            ref_index = improvement_name_list.index('Advanced Metals Refinery')
            sub_index = improvement_name_list.index('Advanced Metals Mine')
        elif improvement_name == 'Oil Refinery':
            ref_index = improvement_name_list.index('Oil Refinery')
            sub_index = improvement_name_list.index('Oil Well')
        elif improvement_name == 'Uranium Refinery':
            ref_index = improvement_name_list.index('Uranium Refinery')
            sub_index = improvement_name_list.index('Uranium Mine')
        ref_count = improvement_count_list[ref_index]
        sub_count = improvement_count_list[sub_index]
        if sub_count == 0:
            return False
        if (ref_count + 1) / sub_count > 0.5:
            return False
    return True

#THE EXEMPT LIST NEEDS TO GET GENERATED FROM THE IMPROVEMENT DICT
def verify_region_resource(regdata_list, region_id, improvement_name):
    '''Verifies a region has the resource needed for the desired improvement. Sub-function for resolve_improvement_builds().'''
    exempt_list = ['Boot Camp', 'Central Bank', 'City', 'Crude Barrier', 'Military Base', 'Military Outpost', 'Missile Defense Network', 'Missile Defense System', 'Nuclear Power Plant', 'Oil Refinery', 'Research Institute', 'Research Laboratory', 'Missile Silo', 'Solar Farm', 'Surveillance Center', 'Wind Farm']
    if improvement_name not in exempt_list:
        for region in regdata_list:
            if region[0] == region_id:
                region_resource = region[3]
                break
        if region_resource != improvement_data_dict[improvement_name]['Required Resource']:
            return False
    return True

def verify_required_research(required_research, player_research):
    '''
    Checks if a certain research has been researched by a specific player.

    Parameters:
    - required_research: The name of the research in question (string).
    - player_research: A list of all research researched by a specific player.
    '''
    if required_research != None:
        if required_research not in player_research:
            return False
    return True


#GLOBAL DICTIONARIES AND LISTS
################################################################################

#file headers
player_data_header = ["Player", "Nation Name", "Color", "Government", "Foreign Policy", "Military Capacity", "Trade Fee", "Stability Data", "Victory Conditions", "Dollars", "Political Power", "Technology", "Coal", "Oil", "Green Energy", "Basic Materials", "Common Metals", "Advanced Metals", "Uranium", "Rare Earth Elements", "Alliance Data", "Missile Data", "Diplomatic Relations", "Upkeep Manager", "Miscellaneous Information", "Income Details", "Completed Research", "Improvement Count", "Status", "Global ID"]
regdata_header_a = ['Region ID','Region Name','Control Data','Resource Data','Improvement Data','Unit Data','Nuke Data','Purchase Cost','Adjacency Data', 'Edge of Map', 'Contains Regional Capital', 'Quarantine', 'Infection']
regdata_header_b = ["5 Letter ID","Full Name","[Owner #, Occupier #]","Resource Name","[Type Name, Health #]","[Type Name, Health #, Owner #]","[True/False, Duration #]","Cost","[List of Region IDs]", "True/False", "True/False", "True/False", "Infection #"]
rmdata_header = ["Turn", "Nation", "Bought/Sold", "Count", "Resource Exchanged"]
rm_header = ["Turn", "Nation", "Bought/Sold", "Count", "Resource Exchanged"]
wardata_header_a = ['War ID','Player #1 Info','Player #2 Info','Player #3 Info','Player #4 Info','Player #5 Info','Player #6 Info','Player #7 Info','Player #8 Info','Player #9 Info','Player #10 Info','War Name','War Start','War Status','War Log','War End']
wardata_header_b = ['ID #',"['War Role', 'War Justification, 'Battles Won', 'Battles Lost', 'Unit Casualties', 'Improvements Lost', 'Justification Details']","['War Role', 'War Justification, 'Battles Won', 'Battles Lost', 'Unit Casualties', 'Improvements Lost', 'Justification Details']","['War Role', 'War Justification, 'Battles Won', 'Battles Lost', 'Unit Casualties', 'Improvements Lost', 'Justification Details']","['War Role', 'War Justification, 'Battles Won', 'Battles Lost', 'Unit Casualties', 'Improvements Lost', 'Justification Details']","['War Role', 'War Justification, 'Battles Won', 'Battles Lost', 'Unit Casualties', 'Improvements Lost', 'Justification Details']","['War Role', 'War Justification, 'Battles Won', 'Battles Lost', 'Unit Casualties', 'Improvements Lost', 'Justification Details']","['War Role', 'War Justification, 'Battles Won', 'Battles Lost', 'Unit Casualties', 'Improvements Lost', 'Justification Details']","['War Role', 'War Justification, 'Battles Won', 'Battles Lost', 'Unit Casualties', 'Improvements Lost', 'Justification Details']","['War Role', 'War Justification, 'Battles Won', 'Battles Lost', 'Unit Casualties', 'Improvements Lost', 'Justification Details']","['War Role', 'War Justification, 'Battles Won', 'Battles Lost', 'Unit Casualties', 'Improvements Lost', 'Justification Details']",'Name','Turn #','Ongoing/Attacker Victory/Defender Victory/White Peace',"[]",'Turn #']
trucedata_header = ['Truce ID', 'Player #1', 'Player #2', 'Player #3', 'Player #4', 'Player #5', 'Player #6', 'Player #7', 'Player #8', 'Player #9', 'Player #10', 'Expire Turn #']
vc_extra_header = ['Nation Name', 'Government Projects', 'Opportunist', 'Reliable Ally', 'Road to Recovery', 'Tight Leash']
game_settings_header = ["Game Name", "Current Turn", "URL", "Image", "Players", "Victory Conditions", "Map", "Accelerated Schedule", "Turn Duration", "Fog of War", "Game Active"]
settings_template = ["Open Game Slot", "Turn N/A", 'settings', "UWS-2.png", "Players: N/A", "Victory Conditions: N/A", "Map: N/A", "Accelerated Schedule: N/A", "Turn Duration: N/A", "Fog of War: N/A", "True"]

#government and fp list data
republic_rates = [100, 100, 100, 100, 100, 100, 100, 100, 100, 100, 100]
technocracy_rates = [100, 100, 120, 100, 100, 100, 100, 100, 100, 100, 100]
oligarchy_rates = [120, 100, 100, 120, 120, 120, 100, 100, 100, 100, 100]
totalitarian_rates = [100, 100, 100, 100, 100, 100, 100, 100, 100, 100, 100]
remnant_rates = [100, 100, 100, 100, 100, 100, 100, 100, 100, 100, 100]
protectorate_rates = [100, 80, 100, 100, 100, 100, 120, 100, 100, 100, 100]
military_junta_rates = [100, 100, 80, 100, 100, 100, 100, 100, 100, 100, 100]
crime_syndicate_rates = [80, 100, 100, 100, 100, 100, 100, 100, 100, 100, 100]

#war and unit/improvement list data
ALLIANCE_LIST = ['Non-Aggression Pact', 'Defense Pact', 'Trade Agreement', 'Research Agreement']
RESOURCE_LIST = ['Dollars', 'Political Power', 'Technology', 'Coal', 'Oil', 'Green Energy', 'Basic Materials', 'Common Metals', 'Advanced Metals', 'Uranium', 'Rare Earth Elements']
war_justifications_list = ['Animosity', 'Border Skirmish', 'Conquest', 'Annexation', 'Independence', 'Subjugation']
unit_names = ['Infantry', 'Artillery', 'Mechanized Infantry', 'Special Forces', 'Motorized Infantry', 'Light Tank', 'Heavy Tank', 'Main Battle Tank']
unit_ids = ['IN', 'AR', 'ME', 'SF', 'MO', 'LT', 'HT', 'BT']
ten_health_improvements_list = ['military outpost', 'military base', 'Military Outpost', 'Military Base']

#victory conditions
easy_list = ["Energy Economy", "Dual Loyalty", "Major Exporter", "Reconstruction Effort", "Secure Strategic Resources", "Tight Leash"]
normal_list = ["Establish Sovereignty", "Diversified Army", "Diversified Economy", "Hegemony", "Reliable Ally", "Road to Recovery"]
hard_list = ["Economic Domination", "Empire Building", "Military Superpower", "Nuclear Deterrent", "Scientific Leader", "Sphere of Influence"]

#other
empty_improvement_data = [None, 99]
empty_unit_data = [None, 99]
ignore_list = ['Player #1', 'Player #2', 'Player #3', 'Player #4', 'Player #5', 'Player #6', 'Player #7', 'Player #8', 'Player #9', 'Player #10', 'Neutral', '-']
score_to_col = {
    1: 'G',
    2: 'H',
    3: 'I'
}

#important dictionaries
agenda_data_dict = {
    'Peace Accords': {
        'Agenda Type': 'Diplomacy',
        'Prerequisite': None,
        'Cost': 15,
        'Location': 'A1',
    },
    'Defensive Agreements': {
        'Agenda Type': 'Diplomacy',
        'Prerequisite': 'Peace Accords',
        'Cost': 15,
        'Location': 'A2',
    },
    'Military Sanctions': {
        'Agenda Type': 'Diplomacy',
        'Prerequisite': 'Defensive Agreements',
        'Cost': 15,
        'Location': 'A3',
    },
    'International Cooperation': {
        'Agenda Type': 'Diplomacy',
        'Prerequisite': 'Military Sanctions',
        'Cost': 15,
        'Location': 'A4',
    },
    'Trade Routes': {
        'Agenda Type': 'Economy',
        'Prerequisite': None,
        'Cost': 15,
        'Location': 'B1',
    },
    'Research Exchange': {
        'Agenda Type': 'Economy',
        'Prerequisite': 'Trade Routes',
        'Cost': 15,
        'Location': 'B2',
    },
    'Economic Sanctions': {
        'Agenda Type': 'Economy',
        'Prerequisite': 'Research Exchange',
        'Cost': 15,
        'Location': 'B3',
    },
    'Efficient Bureaucracy': {
        'Agenda Type': 'Economy',
        'Prerequisite': 'Economic Sanctions',
        'Cost': 15,
        'Location': 'B4',
    },
    'Defensive Tactics': {
        'Agenda Type': 'Security',
        'Prerequisite': None,
        'Cost': 15,
        'Location': 'C1',
    },
    'Mobilization': {
        'Agenda Type': 'Security',
        'Prerequisite': 'Defensive Tactics',
        'Cost': 15,
        'Location': 'C2',
    },
    'Cost of War': {
        'Agenda Type': 'Security',
        'Prerequisite': 'Mobilization',
        'Cost': 15,
        'Location': 'C3',
    },
    'Counter Offensive': {
        'Agenda Type': 'Security',
        'Prerequisite': 'Cost of War',
        'Cost': 15,
        'Location': 'C4',
    },
    'Superior Training': {
        'Agenda Type': 'Warfare',
        'Prerequisite': None,
        'Cost': 15,
        'Location': 'D1',
    },
    'Early Expansion': {
        'Agenda Type': 'Warfare',
        'Prerequisite': 'Superior Training',
        'Cost': 15,
        'Location': 'D2',
    },
    'Dominion': {
        'Agenda Type': 'Warfare',
        'Prerequisite': 'Early Expansion',
        'Cost': 15,
        'Location': 'D3',
    },
    'New Empire': {
        'Agenda Type': 'Warfare',
        'Prerequisite': 'Dominion',
        'Cost': 15,
        'Location': 'D4',
    },
}

research_data_dict = {
    'Coal Mining': {
        'Research Type': 'Energy',
        'Prerequisite': None,
        'Cost': 5,
        'Location': 'A1',
    },
    'Coal Subsidies': {
        'Research Type': 'Energy',
        'Prerequisite': 'Coal Mining',
        'Cost': 10,
        'Location': 'A2',
    },
    'Strip Mining': {
        'Research Type': 'Energy',
        'Prerequisite': 'Coal Subsidies',
        'Cost': 15,
        'Location': 'A3',
    },
    'Open Pit Mining': {
        'Research Type': 'Energy',
        'Prerequisite': 'Strip Mining',
        'Cost': 20,
        'Location': 'A4',
    },
    'Oil Drilling': {
        'Research Type': 'Energy',
        'Prerequisite': None,
        'Cost': 5,
        'Location': 'B1',
    },
    'Oil Subsidies': {
        'Research Type': 'Energy',
        'Prerequisite': 'Oil Drilling',
        'Cost': 10,
        'Location': 'B2',
    },
    'Oil Refinement': {
        'Research Type': 'Energy',
        'Prerequisite': 'Oil Subsidies',
        'Cost': 15,
        'Location': 'B3',
    },
    'Fracking': {
        'Research Type': 'Energy',
        'Prerequisite': 'Oil Refinement',
        'Cost': 20,
        'Location': 'B4',
    },
    'Wind Turbines': {
        'Research Type': 'Energy',
        'Prerequisite': None,
        'Cost': 5,
        'Location': 'C1',
    },
    'Solar Panels': {
        'Research Type': 'Energy',
        'Prerequisite': 'Wind Turbines',
        'Cost': 5,
        'Location': 'C2',
    },
    'Nuclear Power': {
        'Research Type': 'Energy',
        'Prerequisite': 'Solar Panels',
        'Cost': 5,
        'Location': 'C3',
    },
    'City Resettlement': {
        'Research Type': 'Infrastructure',
        'Prerequisite': None,
        'Cost': 5,
        'Location': 'A1',
    },
    'Power Grid Restoration': {
        'Research Type': 'Infrastructure',
        'Prerequisite': 'City Resettlement',
        'Cost': 10,
        'Location': 'A2',
    },
    'Central Banking System': {
        'Research Type': 'Infrastructure',
        'Prerequisite': 'Power Grid Restoration',
        'Cost': 15,
        'Location': 'A3',
    },
    'Surface Mining': {
        'Research Type': 'Infrastructure',
        'Prerequisite': None,
        'Cost': 5,
        'Location': 'B1',
    },
    'Industrial Advancements': {
        'Research Type': 'Infrastructure',
        'Prerequisite': 'Surface Mining',
        'Cost': 10,
        'Location': 'B2',
    },
    'Underground Mining': {
        'Research Type': 'Infrastructure',
        'Prerequisite': 'Industrial Advancements',
        'Cost': 15,
        'Location': 'B3',
    },
    'Uranium Refinement': {
        'Research Type': 'Infrastructure',
        'Prerequisite': 'Underground Mining',
        'Cost': 20,
        'Location': 'B4',
    },
    'Metallurgy': {
        'Research Type': 'Infrastructure',
        'Prerequisite': None,
        'Cost': 5,
        'Location': 'C1',
    },
    'Metal Refinement': {
        'Research Type': 'Infrastructure',
        'Prerequisite': 'Metallurgy',
        'Cost': 10,
        'Location': 'C2',
    },
    'Uranium Extraction': {
        'Research Type': 'Infrastructure',
        'Prerequisite': 'Metal Refinement',
        'Cost': 15,
        'Location': 'C3',
    },
    'REE Mining': {
        'Research Type': 'Infrastructure',
        'Prerequisite': 'Uranium Extraction',
        'Cost': 20,
        'Location': 'C4',
    },
    'Laboratories': {
        'Research Type': 'Infrastructure',
        'Prerequisite': None,
        'Cost': 10,
        'Location': 'D1',
    },
    'Upgraded Facilities': {
        'Research Type': 'Infrastructure',
        'Prerequisite': 'Laboratories',
        'Cost': 20,
        'Location': 'D2',
    },
    'Research Institutes': {
        'Research Type': 'Infrastructure',
        'Prerequisite': 'Upgraded Facilities',
        'Cost': 30,
        'Location': 'D3',
    },
    'Infantry': {
        'Research Type': 'Military',
        'Prerequisite': None,
        'Cost': 5,
        'Location': 'A1',
    },
    'Artillery': {
        'Research Type': 'Military',
        'Prerequisite': 'Infantry',
        'Cost': 10,
        'Location': 'A2',
    },
    'Mechanized Infantry': {
        'Research Type': 'Military',
        'Prerequisite': 'Artillery',
        'Cost': 15,
        'Location': 'A3',
    },
    'Special Operations': {
        'Research Type': 'Military',
        'Prerequisite': 'Mechanized Infantry',
        'Cost': 20,
        'Location': 'A4',
    },
    'Motorized Infantry': {
        'Research Type': 'Military',
        'Prerequisite': None,
        'Cost': 5,
        'Location': 'B1',
    },
    'Light Tanks': {
        'Research Type': 'Military',
        'Prerequisite': 'Motorized Infantry',
        'Cost': 10,
        'Location': 'B2',
    },
    'Heavy Tanks': {
        'Research Type': 'Military',
        'Prerequisite': 'Light Tanks',
        'Cost': 15,
        'Location': 'B3',
    },
    'Main Battle Tanks': {
        'Research Type': 'Military',
        'Prerequisite': 'Heavy Tanks',
        'Cost': 20,
        'Location': 'B4',
    },
    'Launch Codes': {
        'Research Type': 'Military',
        'Prerequisite': None,
        'Cost': 10,
        'Location': 'C1',
    },
    'Missile Technology': {
        'Research Type': 'Military',
        'Prerequisite': 'Launch Codes',
        'Cost': 20,
        'Location': 'C2',
    },
    'Nuclear Warhead': {
        'Research Type': 'Military',
        'Prerequisite': 'Missile Technology',
        'Cost': 30,
        'Location': 'C3',
    },
    'Standing Army': {
        'Research Type': 'Military',
        'Prerequisite': None,
        'Cost': 5,
        'Location': 'D1',
    },
    'Draft': {
        'Research Type': 'Military',
        'Prerequisite': 'Standing Army',
        'Cost': 10,
        'Location': 'D2',
    },
    'Mandatory Service': {
        'Research Type': 'Military',
        'Prerequisite': 'Draft',
        'Cost': 15,
        'Location': 'D3',
    },
    'Basic Defenses': {
        'Research Type': 'Defense',
        'Prerequisite': None,
        'Cost': 5,
        'Location': 'A1',
    },
    'Military Outposts': {
        'Research Type': 'Defense',
        'Prerequisite': 'Basic Defenses',
        'Cost': 10,
        'Location': 'A2',
    },
    'Military Bases': {
        'Research Type': 'Defense',
        'Prerequisite': 'Military Outposts',
        'Cost': 15,
        'Location': 'A3',
    },
    'Missile Defense System': {
        'Research Type': 'Defense',
        'Prerequisite': None,
        'Cost': 10,
        'Location': 'B1',
    },
    'Localized Missile Defense': {
        'Research Type': 'Defense',
        'Prerequisite': 'Missile Defense System',
        'Cost': 20,
        'Location': 'B2',
    },
    'Missile Defense Network': {
        'Research Type': 'Defense',
        'Prerequisite': 'Localized Missile Defense',
        'Cost': 30,
        'Location': 'B3',
    },
    'Surveillance Operations': {
        'Research Type': 'Defense',
        'Prerequisite': None,
        'Cost': 5,
        'Location': 'C1',
    },
    'Economic Reports': {
        'Research Type': 'Defense',
        'Prerequisite': 'Surveillance Operations',
        'Cost': 10,
        'Location': 'C2',
    },
    'Military Intelligence': {
        'Research Type': 'Defense',
        'Prerequisite': 'Economic Reports',
        'Cost': 15,
        'Location': 'C3',
    },
}

unit_data_dict = {
    'Infantry': {
        'Required Research': 'Infantry',
        'Unit Type': 'Infantry',
        'Abbreviation': 'IN',
        'Health': 6,
        'Victory Damage': 2,
        'Draw Damage': 1,
        'Combat Value': 9,
        'Dollars Upkeep': 0.25,
        'Oil Upkeep': 0,
        'Dollars Cost': 5,
        'Basic Materials Cost': 5,
        'Common Metals Cost': 0,
        'Advanced Metals Cost': 0,
        'Rare Earth Elements Cost': 0,
    },
    'Artillery': {
        'Required Research': 'Artillery',
        'Unit Type': 'Infantry',
        'Abbreviation': 'AR',
        'Health': 6,
        'Victory Damage': 2,
        'Draw Damage': 1,
        'Combat Value': 9,
        'Dollars Upkeep': 0.5,
        'Oil Upkeep': 0,
        'Dollars Cost': 10,
        'Basic Materials Cost': 10,
        'Common Metals Cost': 0,
        'Advanced Metals Cost': 0,
        'Rare Earth Elements Cost': 0,
    },
    'Mechanized Infantry': {
        'Required Research': 'Mechanized Infantry',
        'Unit Type': 'Infantry',
        'Abbreviation': 'ME',
        'Health': 8,
        'Victory Damage': 3,
        'Draw Damage': 2,
        'Combat Value': 7,
        'Dollars Upkeep': 0.5,
        'Oil Upkeep': 0,
        'Dollars Cost': 10,
        'Basic Materials Cost': 10,
        'Common Metals Cost': 0,
        'Advanced Metals Cost': 0,
        'Rare Earth Elements Cost': 0,
    },
    'Special Forces': {
        'Required Research': 'Special Operations',
        'Unit Type': 'Infantry',
        'Abbreviation': 'SF',
        'Health': 10,
        'Victory Damage': 4,
        'Draw Damage': 2,
        'Combat Value': 5,
        'Dollars Upkeep': 1,
        'Oil Upkeep': 0,
        'Dollars Cost': 15,
        'Basic Materials Cost': 15,
        'Common Metals Cost': 0,
        'Advanced Metals Cost': 0,
        'Rare Earth Elements Cost': 0,
    },
    'Motorized Infantry': {
        'Required Research': 'Motorized Infantry',
        'Unit Type': 'Infantry',
        'Abbreviation': 'MO',
        'Health': 6,
        'Victory Damage': 2,
        'Draw Damage': 1,
        'Combat Value': 8,
        'Dollars Upkeep': 0,
        'Oil Upkeep': 0.25,
        'Dollars Cost': 5,
        'Basic Materials Cost': 0,
        'Common Metals Cost': 5,
        'Advanced Metals Cost': 0,
        'Rare Earth Elements Cost': 0,
    },
    'Light Tank': {
        'Required Research': 'Light Tanks',
        'Unit Type': 'Tank',
        'Abbreviation': 'LT',
        'Health': 8,
        'Victory Damage': 3,
        'Draw Damage': 1,
        'Combat Value': 6,
        'Dollars Upkeep': 0,
        'Oil Upkeep': 0.5,
        'Dollars Cost': 0,
        'Basic Materials Cost': 0,
        'Common Metals Cost': 10,
        'Advanced Metals Cost': 1,
        'Rare Earth Elements Cost': 0,
    },
    'Heavy Tank': {
        'Required Research': 'Heavy Tanks',
        'Unit Type': 'Tank',
        'Abbreviation': 'HT',
        'Health': 10,
        'Victory Damage': 4,
        'Draw Damage': 2,
        'Combat Value': 6,
        'Dollars Upkeep': 0,
        'Oil Upkeep': 0.5,
        'Dollars Cost': 0,
        'Basic Materials Cost': 0,
        'Common Metals Cost': 12,
        'Advanced Metals Cost': 3,
        'Rare Earth Elements Cost': 0,
    },
    'Main Battle Tank': {
        'Required Research': 'Main Battle Tanks',
        'Unit Type': 'Tank',
        'Abbreviation': 'BT',
        'Health': 10,
        'Victory Damage': 4,
        'Draw Damage': 2,
        'Combat Value': 4,
        'Dollars Upkeep': 0,
        'Oil Upkeep': 1,
        'Dollars Cost': 0,
        'Basic Materials Cost': 0,
        'Common Metals Cost': 15,
        'Advanced Metals Cost': 5,
        'Rare Earth Elements Cost': 1,
    }
}

improvement_data_dict = {
    'Advanced Metals Mine': {
        'Health': 99,
        'Required Research': 'Metallurgy',
        'Required Resource': 'Advanced Metals',
        'Dollars Upkeep': 0,
        'Energy Upkeep': 0,
        'Dollars Cost': 0,
        'Basic Materials Cost': 0,
        'Common Metals Cost': 5,
        'Advanced Metals Cost': 0,
        'Rare Earth Elements Cost': 0
    },
    'Advanced Metals Refinery': {
        'Health': 99,
        'Required Research': 'Metal Refinement',
        'Required Resource': None,
        'Dollars Upkeep': 0,
        'Energy Upkeep': 1,
        'Dollars Cost': 0,
        'Basic Materials Cost': 0,
        'Common Metals Cost': 10,
        'Advanced Metals Cost': 0,
        'Rare Earth Elements Cost': 0
    },
    'Boot Camp': {
        'Health': 5,
        'Victory Damage': 3,
        'Combat Value': 9,
        'Draw Damage': 1,
        'Required Research': 'Standing Army',
        'Required Resource': None,
        'Dollars Upkeep': 0,
        'Energy Upkeep': 0,
        'Dollars Cost': 0,
        'Basic Materials Cost': 10,
        'Common Metals Cost': 0,
        'Advanced Metals Cost': 0,
        'Rare Earth Elements Cost': 0
    },
    'Capital': {
        'Health': 5,
        'Required Resource': None,
        'Victory Damage': 3,
        'Draw Damage': 1,
        'Combat Value': 9,
        'Dollars Upkeep': 0,
        'Energy Upkeep': 0
    },
    'Central Bank': {
        'Health': 5,
        'Victory Damage': 3,
        'Combat Value': 9,
        'Draw Damage': 1,
        'Required Research': 'Central Banking System',
        'Required Resource': None,
        'Dollars Upkeep': 0,
        'Energy Upkeep': 1,
        'Basic Materials Cost': 10,
        'Dollars Cost': 0,
        'Basic Materials Cost': 0,
        'Common Metals Cost': 10,
        'Advanced Metals Cost': 0,
        'Rare Earth Elements Cost': 0
    },
    'City': {
        'Health': 5,
        'Victory Damage': 3,
        'Combat Value': 9,
        'Draw Damage': 1,
        'Required Research': 'City Resettlement',
        'Required Resource': None,
        'Dollars Upkeep': 0,
        'Energy Upkeep': 0,
        'Dollars Cost': 0,
        'Basic Materials Cost': 10,
        'Common Metals Cost': 0,
        'Advanced Metals Cost': 0,
        'Rare Earth Elements Cost': 0
    },
    'Coal Mine': {
        'Health': 99,
        'Required Research': 'Coal Mining',
        'Required Resource': 'Coal',
        'Dollars Upkeep': 0,
        'Energy Upkeep': 0,
        'Dollars Cost': 5,
        'Basic Materials Cost': 0,
        'Common Metals Cost': 0,
        'Advanced Metals Cost': 0,
        'Rare Earth Elements Cost': 0
    },
    'Common Metals Mine': {
        'Health': 99,
        'Required Research': 'Surface Mining',
        'Required Resource': 'Common Metals',
        'Dollars Upkeep': 0,
        'Energy Upkeep': 0,
        'Dollars Cost': 0,
        'Basic Materials Cost': 5,
        'Common Metals Cost': 0,
        'Advanced Metals Cost': 0,
        'Rare Earth Elements Cost': 0
    },
    'Crude Barrier': {
        'Health': 5,
        'Victory Damage': 4,
        'Combat Value': 9,
        'Draw Damage': 2,
        'Required Research': 'Basic Defenses',
        'Required Resource': None,
        'Dollars Upkeep': 0,
        'Energy Upkeep': 0,
        'Dollars Cost': 0,
        'Basic Materials Cost': 5,
        'Common Metals Cost': 0,
        'Advanced Metals Cost': 0,
        'Rare Earth Elements Cost': 0
    },
    'Industrial Zone': {
        'Health': 99,
        'Required Research': None,
        'Required Resource': 'Basic Materials',
        'Dollars Upkeep': 0,
        'Energy Upkeep': 0,
        'Dollars Cost': 5,
        'Basic Materials Cost': 0,
        'Common Metals Cost': 0,
        'Advanced Metals Cost': 0,
        'Rare Earth Elements Cost': 0
    },
    'Military Base': {
        'Health': 10,
        'Victory Damage': 4,
        'Draw Damage': 2,
        'Combat Value': 5,
        'Required Research': 'Military Bases',
        'Required Resource': None,
        'Dollars Upkeep': 0,
        'Energy Upkeep': 2,
        'Dollars Cost': 0,
        'Basic Materials Cost': 0,
        'Common Metals Cost': 5,
        'Advanced Metals Cost': 5,
        'Rare Earth Elements Cost': 0
    },
    'Military Outpost': {
        'Health': 10,
        'Victory Damage': 4,
        'Draw Damage': 2,
        'Combat Value': 7,
        'Required Research': 'Military Outposts',
        'Required Resource': None,
        'Dollars Upkeep': 0,
        'Energy Upkeep': 1,
        'Dollars Cost': 0,
        'Basic Materials Cost': 5,
        'Common Metals Cost': 5,
        'Advanced Metals Cost': 0,
        'Rare Earth Elements Cost': 0
    },
    'Missile Defense Network': {
        'Health': 99,
        'Required Research': 'Missile Defense Network',
        'Required Resource': None,
        'Dollars Upkeep': 0,
        'Energy Upkeep': 2,
        'Dollars Cost': 0,
        'Basic Materials Cost': 0,
        'Common Metals Cost': 10,
        'Advanced Metals Cost': 5,
        'Rare Earth Elements Cost': 1
    },
    'Missile Defense System': {
        'Health': 99,
        'Required Research': 'Missile Defense System',
        'Required Resource': None,
        'Dollars Upkeep': 0,
        'Energy Upkeep': 1,
        'Dollars Cost': 0,
        'Basic Materials Cost': 0,
        'Common Metals Cost': 10,
        'Advanced Metals Cost': 0,
        'Rare Earth Elements Cost': 1
    },
    'Nuclear Power Plant': {
        'Health': 99,
        'Required Research': 'Nuclear Power',
        'Required Resource': None,
        'Dollars Upkeep': 0,
        'Energy Upkeep': 0,
        'Dollars Cost': 0,
        'Basic Materials Cost': 0,
        'Common Metals Cost': 10,
        'Advanced Metals Cost': 10,
        'Rare Earth Elements Cost': 0
    },
    'Oil Refinery': {
        'Health': 99,
        'Required Research': 'Oil Refinement',
        'Required Resource': None,
        'Dollars Upkeep': 2,
        'Energy Upkeep': 0,
        'Dollars Cost': 0,
        'Basic Materials Cost': 0,
        'Common Metals Cost': 10,
        'Advanced Metals Cost': 0,
        'Rare Earth Elements Cost': 0
    },
    'Oil Well': {
        'Health': 99,
        'Required Research': 'Oil Drilling',
        'Required Resource': 'Oil',
        'Dollars Upkeep': 0,
        'Energy Upkeep': 0,
        'Dollars Cost': 0,
        'Basic Materials Cost': 5,
        'Common Metals Cost': 0,
        'Advanced Metals Cost': 0,
        'Rare Earth Elements Cost': 0
    },
    'Uranium Mine': {
        'Health': 99,
        'Required Research': 'Uranium Extraction',
        'Required Resource': 'Uranium',
        'Dollars Upkeep': 0,
        'Energy Upkeep': 0,
        'Dollars Cost': 0,
        'Basic Materials Cost': 0,
        'Common Metals Cost': 0,
        'Advanced Metals Cost': 5,
        'Rare Earth Elements Cost': 0
    },
    'Uranium Refinery': {
        'Health': 99,
        'Required Research': 'Uranium Refinement',
        'Required Resource': None,
        'Dollars Upkeep': 0,
        'Energy Upkeep': 1,
        'Dollars Cost': 0,
        'Basic Materials Cost': 0,
        'Common Metals Cost': 10,
        'Advanced Metals Cost': 0,
        'Rare Earth Elements Cost': 0
    },
    'Rare Earth Elements Mine': {
        'Health': 99,
        'Required Research': 'REE Mining',
        'Required Resource': 'Rare Earth Elements',
        'Dollars Upkeep': 0,
        'Energy Upkeep': 0,
        'Dollars Cost': 0,
        'Basic Materials Cost': 0,
        'Common Metals Cost': 0,
        'Advanced Metals Cost': 5,
        'Rare Earth Elements Cost': 0
    },
    'Research Institute': {
        'Health': 99,
        'Required Research': 'Research Institutes',
        'Required Resource': None,
        'Dollars Upkeep': 5,
        'Energy Upkeep': 1,
        'Dollars Cost': 0,
        'Basic Materials Cost': 10,
        'Common Metals Cost': 5,
        'Advanced Metals Cost': 0,
        'Rare Earth Elements Cost': 0
    },
    'Research Laboratory': {
        'Health': 99,
        'Required Research': 'Laboratories',
        'Required Resource': None,
        'Dollars Upkeep': 0,
        'Energy Upkeep': 0,
        'Dollars Cost': 0,
        'Basic Materials Cost': 5,
        'Common Metals Cost': 0,
        'Advanced Metals Cost': 0,
        'Rare Earth Elements Cost': 0
    },
    'Missile Silo': {
        'Health': 5,
        'Victory Damage': 4,
        'Draw Damage': 2,
        'Combat Value': 7,
        'Required Research': 'Launch Codes',
        'Required Resource': None,
        'Dollars Upkeep': 0,
        'Energy Upkeep': 2,
        'Dollars Cost': 0,
        'Basic Materials Cost': 0,
        'Common Metals Cost': 10,
        'Advanced Metals Cost': 0,
        'Rare Earth Elements Cost': 0
    },
    'Solar Farm': {
        'Health': 99,
        'Required Research': 'Solar Panels',
        'Required Resource': None,
        'Dollars Upkeep': 0,
        'Energy Upkeep': 0,
        'Dollars Cost': 0,
        'Basic Materials Cost': 0,
        'Common Metals Cost': 0,
        'Advanced Metals Cost': 0,
        'Rare Earth Elements Cost': 2
    },
    'Strip Mine': {
        'Health': 99,
        'Required Research': 'Strip Mining',
        'Required Resource': 'Coal',
        'Dollars Upkeep': 0,
        'Energy Upkeep': 0,
        'Dollars Cost': 25,
        'Basic Materials Cost': 0,
        'Common Metals Cost': 0,
        'Advanced Metals Cost': 0,
        'Rare Earth Elements Cost': 0
    },
    'Surveillance Center': {
        'Health': 99,
        'Required Research': 'Surveillance Operations',
        'Required Resource': None,
        'Dollars Upkeep': 0,
        'Energy Upkeep': 1,
        'Dollars Cost': 0,
        'Basic Materials Cost': 10,
        'Common Metals Cost': 0,
        'Advanced Metals Cost': 0,
        'Rare Earth Elements Cost': 0
    },
    'Wind Farm': {
        'Health': 99,
        'Required Research': 'Wind Turbines',
        'Required Resource': None,
        'Dollars Upkeep': 0,
        'Energy Upkeep': 0,
        'Dollars Cost': 0,
        'Basic Materials Cost': 0,
        'Common Metals Cost': 5,
        'Advanced Metals Cost': 0,
        'Rare Earth Elements Cost': 0
    }
}

#color dictionaries
player_colors_hex = {
    "Brown": "#603913",
    "Coral": "#ff974e",
    "Dark Blue": "#003b84",
    "Dark Green": "#105500",
    "Dark Purple": "#5a009d",
    "Dark Red": "#b30000",
    "Light Blue": "#0096ff",
    "Light Green": "#5bb000",
    "Light Purple": "#b654ff",
    "Light Red": "#ff3d3d",
    "Maroon": "#8b2a1a",
    "Metallic Gold": "#9f8757",
    "Orange": "#ff9600",
    "Pink": "#f384ae",
    "Terracotta": "#b66317",
    "Yellow": "#ffd64b",
    None: "None" 
}

player_colors_rgb = {
    "Brown": (96, 57, 19, 255),
    "Coral": (255, 151, 78, 255),
    "Dark Blue": (0, 59, 132, 255),
    "Dark Green": (16, 85, 0, 255),
    "Dark Purple": (90, 0, 157, 255),
    "Dark Red": (179, 0, 0, 255),
    "Light Blue": (0, 150, 255, 255),
    "Light Green": (91, 176, 0, 255),
    "Light Purple": (182, 84, 255, 255),
    "Light Red": (255, 61, 61, 255),
    "Maroon": (139, 42, 26, 255),
    "Metallic Gold": (159, 135, 87, 255),
    "Orange": (255, 150, 0, 255),
    "Pink": (243, 132, 174, 255),
    "Terracotta": (182, 99, 23, 255),
    "Yellow": (255, 214, 75, 255)
}

player_colors_conversions = {
    "#603913": (96, 57, 19, 255),
    "#ff974e": (255, 151, 78, 255),
    "#003b84": (0, 59, 132, 255),
    "#105500": (16, 85, 0, 255),
    "#5a009d": (90, 0, 157, 255),
    "#b30000": (179, 0, 0, 255),
    "#0096ff": (0, 150, 255, 255),
    "#5bb000": (91, 176, 0, 255),
    "#b654ff": (182, 84, 255, 255),
    "#ff3d3d": (255, 61, 61, 255),
    "#8b2a1a": (139, 42, 26, 255),
    "#9f8757": (159, 135, 87, 255),
    "#ff9600": (255, 150, 0, 255),
    "#f384ae": (243, 132, 174, 255),
    "#b66317": (182, 99, 23, 255),
    "#ffd64b": (255, 214, 75, 255)
}

player_colors_normal_to_occupied = {
    (96, 57, 19, 255): (144, 87, 33, 255),
    (255, 151, 78, 255): (255, 170, 111, 255),
    (0, 59, 132, 255): (0, 78, 174, 255),
    (16, 85, 0, 255): (24, 126, 0, 255),
    (90, 0, 157, 255): (126, 0, 221, 255),
    (179, 0, 0, 255): (212, 0, 0, 255),
    (0, 150, 255, 255): (87, 186, 255, 255),
    (91, 176, 0, 255): (110, 212, 0, 255),
    (182, 84, 255, 255): (200, 127, 255, 255),
    (255, 61, 61, 255): (255, 102, 102, 255),
    (139, 42, 26, 255): (184, 56, 35, 255),
    (159, 135, 87, 255): (175, 154, 110, 255),
    (255, 150, 0, 255): (255, 175, 61, 255),
    (243, 132, 174, 255): (244, 160, 192, 255),
    (182, 99, 23, 255): (197, 116, 41, 255),
    (255, 214, 75, 255): (255, 230, 142, 255),
}

player_colors_normal_to_occupied_hex = {
    (96, 57, 19, 255): "#905721",
    (255, 151, 78, 255): "#ffaa6f",
    (0, 59, 132, 255): "#004eae",
    (16, 85, 0, 255): "#187e00",
    (90, 0, 157, 255): "#7e00dd",
    (179, 0, 0, 255): "#d40000",
    (0, 150, 255, 255): "#57baff",
    (91, 176, 0, 255): "#6ed400",
    (182, 84, 255, 255): "#c87fff",
    (255, 61, 61, 255): "#ff6666",
    (139, 42, 26, 255): "#b83823",
    (159, 135, 87, 255): "#af9a6e",
    (255, 150, 0, 255): "#ffaf3d",
    (243, 132, 174, 255): "#f4a0c0",
    (182, 99, 23, 255): "#c57429",
    (255, 214, 75, 255): "#ffe68e",
}

resource_colors = {
    "Coal": (166, 124, 82, 255),
    "Oil": (96, 57, 19, 255),
    "Basic Materials": (149, 149, 149, 255),
    "Common Metals": (99, 99, 99, 255),
    "Advanced Metals": (71, 157, 223, 255),
    "Uranium": (0, 255, 0, 255),
    "Rare Earth Elements": (241, 194, 50, 255)
}
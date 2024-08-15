#STANDARD IMPORTS
import ast
import csv
import json
import random

#UWS SOURCE IMPORTS
import core

#PRIVATE ACTION FUNCTIONS
def resolve_unit_withdraws(unit_withdraw_list, full_game_id, player_action_logs, current_turn_num):
    '''Preforms unit withdraws.'''

    #define core lists
    playerdata_filepath = f'gamedata/{full_game_id}/playerdata.csv'
    regdata_filepath = f'gamedata/{full_game_id}/regdata.csv'
    wardata_filepath = f'gamedata/{full_game_id}/wardata.csv'
    playerdata_list = core.read_file(playerdata_filepath, 1)
    regdata_list = core.read_file(regdata_filepath, 0)
    wardata_list = core.read_file(wardata_filepath, 2)

    #get needed info from each player
    military_capacity_masterlist = []
    diplomatic_relations_masterlist = []
    for player in playerdata_list:
        player_military_capacity = player[5]
        military_capacity_masterlist.append(player_military_capacity)
        diplomatic_relations_masterlist.append(ast.literal_eval(player[22]))

    
    #Execute Actions
    for unit_withdraw in unit_withdraw_list:
        player_id = unit_withdraw[0]
        region_str = unit_withdraw[1][9:]
        move_list = region_str.split('-')
        current_region_id = move_list[0]
        target_region_id = move_list[1]
        player_action_log = player_action_logs[player_id - 1]

        #get info on current region
        current_region = None
        for region in regdata_list:
            if region[0] == current_region_id:
                current_region = region
                break
        if current_region == None:
            print(f'Action {unit_withdraw} failed. Bad starting region id given.')
            continue
        current_unit_data = ast.literal_eval(current_region[5])
        current_unit_id = current_unit_data[0]
        current_unit_owner_id = 0
        if current_unit_id != None:
            current_unit_health = current_unit_data[1]
            current_unit_owner_id = current_unit_data[2]

        #unit present check
        if current_unit_id == None or player_id != current_unit_owner_id:
            player_action_log.append(f'Failed to perform a withdraw action from {current_region_id}. You do not control a unit there.')
            player_action_logs[player_id - 1] = player_action_log
            continue

        #get information on target region
        target_region = None
        for region in regdata_list:
            if region[0] == target_region_id:
                target_region = region
                break
        if target_region == None:
            print(f'Action {unit_withdraw} failed. Bad target region id given.')
            continue
        target_control_data = ast.literal_eval(target_region[2])
        target_owner_id = target_control_data[0]
        target_occupier_id = target_control_data[1]
        target_unit_data = ast.literal_eval(target_region[5])
        target_unit_id = target_unit_data[0]

        #destination owned by player check
        if target_owner_id != player_id and target_occupier_id != player_id:
            player_action_log.append(f'Failed to withdraw {current_unit_id} {current_region_id} - {target_region_id}. The destination region is not controlled by you.')
            player_action_logs[player_id - 1] = player_action_log
            continue

        #destination unoccupied check
        if target_unit_id != None:
            player_action_log.append(f'Failed to withdraw {current_unit_id} {current_region_id} - {target_region_id}. The destination region is occupied by another unit.')
            player_action_logs[player_id - 1] = player_action_log
            continue
        
        #withdraw unit
        for region in regdata_list:
            if region[0] == target_region_id:
                region[5] = str(current_unit_data)
                break
        for region in regdata_list:
            if region[0] == current_region_id:
                empty_data = [None, 99]
                region[5] = str(empty_data)
                break
        player_action_log.append(f'Withdrew {current_unit_id} {current_region_id} - {target_region_id}.')
        player_action_logs[player_id - 1] = player_action_log

    #Remove Units That Did Not Withdraw
    for index, player in enumerate(playerdata_list):
        player_id = index + 1
        military_capacity_data = military_capacity_masterlist[player_id - 1]
        used_mc, total_mc = core.read_military_capacity(military_capacity_data)
        diplomatic_relations_list = diplomatic_relations_masterlist[player_id - 1]
        player_action_log = player_action_logs[player_id - 1]
        
        #build disallowed list
        disallowed_list = []
        for player_id_2, relation in enumerate(diplomatic_relations_list):
            war_recently_ended = False
            for war in wardata_list:
                if war[player_id] != '-' and war[player_id_2] != '-' and war[15] == str(current_turn_num):
                    war_recently_ended = True
                    break
            if relation != 'At War' and relation != 'Defense Pact' and relation != '-' and not war_recently_ended:
                disallowed_list.append(player_id_2)
        
        #remove units
        for region in regdata_list:
            if len(region[0]) == 5:
                region_id = region[0]
                control_data = ast.literal_eval(region[2])
                owner_id = control_data[0]
                unit_data = ast.literal_eval(region[5])
                unit_id = unit_data[0]
                if unit_id != None:
                    if unit_data[2] == player_id and owner_id in disallowed_list:
                        empty_data = [None, 99]
                        region[5] = str(empty_data)
                        used_mc -= 1
                        player_action_log.append(f'{unit_id} {region_id} was lost due to no withdraw order.')
                        player_action_logs[player_id - 1] = player_action_log
        diplomatic_relations_masterlist[player_id - 1] = diplomatic_relations_list
        military_capacity_masterlist[player_id - 1] = f'{used_mc}/{total_mc}'

    
    #Update playerdata.csv
    for index, playerdata in enumerate(playerdata_list):
        playerdata[5] = military_capacity_masterlist[index]
    with open(playerdata_filepath, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(core.player_data_header)
        writer.writerows(playerdata_list)

    #Update regiondata.csv
    with open(regdata_filepath, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerows(regdata_list)

    return player_action_logs

def resolve_unit_disbands(unit_disband_list, full_game_id, player_action_logs):
    '''Resolves all unit disband actions.'''

    #define core lists
    playerdata_filepath = f'gamedata/{full_game_id}/playerdata.csv'
    regdata_filepath = f'gamedata/{full_game_id}/regdata.csv'
    playerdata_list = core.read_file(playerdata_filepath, 1)
    regdata_list = core.read_file(regdata_filepath, 0)

    #remove actions with bad region names
    unit_disband_list = core.filter_region_names(regdata_list, unit_disband_list)

    #get needed info from each player
    military_capacity_masterlist = []
    for player in playerdata_list:
        player_military_capacity = player[5]
        military_capacity_masterlist.append(player_military_capacity)


    #Execute Actions
    for disband_action in unit_disband_list:
        player_id = disband_action[0]
        region_id = disband_action[1][-5:]
        player_military_capacity = military_capacity_masterlist[player_id - 1]
        player_action_log = player_action_logs[player_id - 1]

        #get unit data
        for region in regdata_list:
            if region[0] == region_id:
                unit_data = ast.literal_eval(region[5])
                #attempt removal
                unit_id = unit_data[0]
                if unit_id:
                    index = core.unit_ids.index(unit_id)
                    unit_name = core.unit_names[index]
                    owner_id = unit_data[2]
                else:
                    player_action_log.append(f'Failed to disband a unit in {region_id}. There is no unit to disband.')
                    continue
                if owner_id == player_id and unit_id:
                    #success
                    region[5] = str([None, 99])
                    player_military_capacity_list = player_military_capacity.split('/')
                    used_mc = int(player_military_capacity_list[0]) - 1
                    total_mc = player_military_capacity_list[1]
                    player_military_capacity = f'{used_mc}/{total_mc}'
                    military_capacity_masterlist[player_id - 1] = player_military_capacity
                    player_action_log.append(f'Disbanded {unit_name} in {region_id}.')
                else:
                    player_action_log.append(f'Failed to disband {unit_name} in {region_id}.')
        player_action_logs[player_id - 1] = player_action_log
        
    
    #Update playerdata.csv
    for index, playerdata in enumerate(playerdata_list):
        playerdata[5] = military_capacity_masterlist[index]
    with open(playerdata_filepath, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(core.player_data_header)
        writer.writerows(playerdata_list)
    

    #Update regiondata.csv
    with open(regdata_filepath, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerows(regdata_list)

    return player_action_logs

def resolve_unit_deployments(unit_deploy_list, full_game_id, player_action_logs):
    '''Resolves all unit deployment actions.'''

    #define core lists
    playerdata_filepath = f'gamedata/{full_game_id}/playerdata.csv'
    regdata_filepath = f'gamedata/{full_game_id}/regdata.csv'
    playerdata_list = core.read_file(playerdata_filepath, 1)
    regdata_list = core.read_file(regdata_filepath, 0)
    with open('active_games.json', 'r') as json_file:
        active_games_dict = json.load(json_file)

    #get needed economy information from each player
    nation_info_masterlist = core.get_nation_info(playerdata_list)
    request_list = ['Dollars', 'Basic Materials', 'Common Metals', 'Advanced Metals', 'Rare Earth Elements']
    economy_masterlist = core.get_economy_info(playerdata_list, request_list)
    military_capacity_masterlist = []
    research_masterlist = []
    for player in playerdata_list:
        player_military_capacity = player[5]
        military_capacity_masterlist.append(player_military_capacity)
        player_research_list = ast.literal_eval(player[26])
        research_masterlist.append(player_research_list)

    #Execute Actions
    for deploy_action in unit_deploy_list:
        player_id = deploy_action[0]
        unit_name = deploy_action[1][7:-6]
        region_id = deploy_action[1][-5:]
        if "Foreign Invasion" not in active_games_dict[full_game_id]["Active Events"] and player_id != 99:
            player_government = nation_info_masterlist[player_id - 1][2]
            player_military_capacity = military_capacity_masterlist[player_id - 1]
            player_research = research_masterlist[player_id - 1]
            player_action_log = player_action_logs[player_id - 1]

        #unit name check
        if unit_name in core.unit_names:
            index = core.unit_names.index(unit_name)
            unit_id = core.unit_ids[index]
        elif unit_name in core.unit_ids:
            unit_id = unit_name
            index = core.unit_ids.index(unit_id)
            unit_name = core.unit_names[index]
        else:
            player_action_log.append(f'Failed to deploy {unit_name} {region_id}. Unit name/id not recognized.')
            player_action_logs[player_id - 1] = player_action_log
            continue

        if "Foreign Invasion" not in active_games_dict[full_game_id]["Active Events"] and player_id != 99:
            #get resource stockpiles of player
            stockpile_list = []
            for i in range(len(request_list)):
                stockpile_list.append(economy_masterlist[player_id - 1][i][0])
            dollars_stockpile = float(stockpile_list[0])
            basic_stockpile = float(stockpile_list[1])
            common_stockpile = float(stockpile_list[2])
            advanced_stockpile = float(stockpile_list[3])
            rare_stockpile = float(stockpile_list[4])

            #ownership check
            ownership_check = core.verify_ownership(regdata_list, region_id, player_id)
            if ownership_check == False:
                player_action_log.append(f'Failed to deploy {unit_name} in region {region_id}. You do not own this region.')
                player_action_logs[player_id - 1] = player_action_log
                continue
            
            #required research check
            research_check = core.verify_required_research(core.unit_data_dict[unit_name]['Required Research'], player_research)
            if research_check == False:
                player_action_log.append(f'Failed to deploy {unit_name} in region {region_id}. You do not have the required research.')
                player_action_logs[player_id - 1] = player_action_log
                continue

            #capacity check
            capacity_check = core.check_military_capacity(military_capacity_masterlist[player_id - 1], 1)
            if capacity_check == False:
                player_action_log.append(f'Failed to deploy {unit_name} in region {region_id}. Insufficient military capacity.')
                player_action_logs[player_id - 1] = player_action_log
                continue

            #attempt to deploy unit
            dollars_cost = core.unit_data_dict[unit_name]['Dollars Cost']
            basic_cost = core.unit_data_dict[unit_name]['Basic Materials Cost']
            common_cost = core.unit_data_dict[unit_name]['Common Metals Cost']
            advanced_cost = core.unit_data_dict[unit_name]['Advanced Metals Cost']
            rare_cost = core.unit_data_dict[unit_name]['Rare Earth Elements Cost']
            if player_government == 'Military Junta':
                dollars_cost *= 0.8
                basic_cost *= 0.8
                common_cost *= 0.8
                advanced_cost *= 0.8
            if (dollars_stockpile - dollars_cost >= 0) and (basic_stockpile - basic_cost >= 0) and (common_stockpile - common_cost >= 0) and (advanced_stockpile - advanced_cost >= 0):
                #unit successfully purchased
                economy_masterlist[player_id - 1][0][0] = core.update_stockpile(dollars_stockpile, dollars_cost)
                economy_masterlist[player_id - 1][1][0] = core.update_stockpile(basic_stockpile, basic_cost)
                economy_masterlist[player_id - 1][2][0] = core.update_stockpile(common_stockpile, common_cost)
                economy_masterlist[player_id - 1][3][0] = core.update_stockpile(advanced_stockpile, advanced_cost)
                economy_masterlist[player_id - 1][4][0] = core.update_stockpile(rare_stockpile, rare_cost)
                for region in regdata_list:
                    if region[0] == region_id:
                        region[5] = [unit_id, core.unit_data_dict[unit_name]['Health'], player_id]
                player_military_capacity_list = player_military_capacity.split('/')
                used_mc = int(player_military_capacity_list[0]) + 1
                total_mc = float(player_military_capacity_list[1])
                player_military_capacity = f'{used_mc}/{total_mc}'
                military_capacity_masterlist[player_id - 1] = player_military_capacity
                player_action_log.append(f'Deployed {unit_name} in region {region_id}.')
            else:
                #unit too expensive
                player_action_log.append(f'Failed to deploy {unit_name} in region {region_id}. Insufficient resources.')
            player_action_logs[player_id - 1] = player_action_log
        else:
            for region in regdata_list:
                if region[0] == region_id:
                    region[5] = [unit_id, core.unit_data_dict[unit_name]['Health'], player_id]


    #Update playerdata.csv
    for economy_list in economy_masterlist:
        for resource_data_list in economy_list:
            resource_data_list = str(resource_data_list)
    i = 0
    for playerdata in playerdata_list:
        playerdata[5] = military_capacity_masterlist[i]
        playerdata[9] = economy_masterlist[i][0]
        playerdata[15] = economy_masterlist[i][1]
        playerdata[16] = economy_masterlist[i][2]
        playerdata[17] = economy_masterlist[i][3]
        playerdata[19] = economy_masterlist[i][4]
        i += 1
    with open(playerdata_filepath, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(core.player_data_header)
        writer.writerows(playerdata_list)


    #Update regiondata.csv
    with open(regdata_filepath, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerows(regdata_list)

    return player_action_logs

def resolve_war_declarations(war_declaration_list, full_game_id, current_turn_num, diplomacy_log, player_action_logs):  
    '''Resolves all war declarations.'''

    #define core lists
    playerdata_filepath = f'gamedata/{full_game_id}/playerdata.csv'
    regdata_filepath = f'gamedata/{full_game_id}/regdata.csv'
    wardata_filepath = f'gamedata/{full_game_id}/wardata.csv'
    trucedata_filepath = f'gamedata/{full_game_id}/trucedata.csv'
    playerdata_list = core.read_file(playerdata_filepath, 1)
    wardata_list = core.read_file(wardata_filepath, 2)
    trucedata_list = core.read_file(trucedata_filepath, 1)

    #get needed player info
    nation_info_masterlist = core.get_nation_info(playerdata_list)
    nation_name_list = []
    for nation_info in nation_info_masterlist:
        nation_name_list.append(nation_info[0])
    military_capacity_masterlist = []
    relations_data_masterlist = []
    research_masterlist = []
    for player in playerdata_list:
        player_military_capacity = player[5]
        military_capacity_masterlist.append(player_military_capacity)
        relations_data = ast.literal_eval(player[22])
        relations_data_masterlist.append(relations_data)
        player_research_list = ast.literal_eval(player[26])
        research_masterlist.append(player_research_list)


    #Execute Actions
    for war_declaration in war_declaration_list:
        attacker_player_id = war_declaration[0]
        attacker_nation_name = nation_info_masterlist[attacker_player_id - 1][0]
        war_declaration_str = war_declaration[1][4:]
        defender_nation_name = ""
        for name in nation_name_list:
            if name.lower() in war_declaration_str.lower():
               defender_nation_name = name
        defender_player_id = nation_name_list.index(defender_nation_name) + 1
        war_justification = ""
        for justification in core.war_justifications_list:
            if justification in war_declaration_str:
                war_justification = justification
        attacker_mc_data = military_capacity_masterlist[attacker_player_id - 1]
        attacker_research_list = research_masterlist[attacker_player_id - 1]
        attacker_status = playerdata_list[attacker_player_id - 1][28]
        attacker_relations_data = relations_data_masterlist[attacker_player_id - 1]
        defender_relations_data = relations_data_masterlist[defender_player_id - 1]
        player_action_log = player_action_logs[attacker_player_id - 1]

        #valid order check
        if defender_nation_name == "" or war_justification == "":
            player_action_log.append('Failed to declare war. Either the main defender or war justification was not recognized.')
            player_action_logs[attacker_player_id - 1] = player_action_log
            continue

        #research check
        valid_war_justification = False
        match war_justification:
            case 'Animosity':
                valid_war_justification = True
            case 'Border Skirmish':
                valid_war_justification = True
            case 'Conquest':
                if 'Early Expansion' in attacker_research_list:
                    valid_war_justification = True
            case 'Annexation':
                if 'New Empire' in attacker_research_list:
                    valid_war_justification = True
            case 'Independence':
                if "Puppet State" in attacker_status and defender_nation_name in attacker_status:
                    valid_war_justification = True
            case 'Subjugation':
                if 'Dominion' in attacker_research_list:
                    valid_war_justification = True
        if not valid_war_justification:
            player_action_log.append(f'Failed to declare a {war_justification} war on {defender_nation_name}. You do not have the required foreign policy agenda.')
            player_action_logs[attacker_player_id - 1] = player_action_log
            continue

        #military capacity check
        used_mc, total_mc = core.read_military_capacity(attacker_mc_data)
        if used_mc == 0:
            player_action_log.append(f'Failed to declare a {war_justification} war on {defender_nation_name}. You do not own at least one unit.')
            player_action_logs[attacker_player_id - 1] = player_action_log
            continue

        #truce check
        truce_check = core.check_for_truce(trucedata_list, attacker_player_id, defender_player_id, current_turn_num)
        if truce_check:
            player_action_log.append(f'Failed to declare a {war_justification} war on {defender_nation_name}. You have an active truce with that player.')
            player_action_logs[attacker_player_id - 1] = player_action_log
            continue

        #independence check
        if attacker_status != "Independent Nation":
            if defender_nation_name not in attacker_status and "Puppet State" in attacker_status:
                player_action_log.append(f'Failed to declare a {war_justification} war on {defender_nation_name}. As a puppet state, you cannot declare war.')
                player_action_logs[attacker_player_id - 1] = player_action_log
                continue

        #already at war check
        already_at_war_check = False
        attacker_at_war_list = core.get_wars(attacker_relations_data)
        for select_player_id in attacker_at_war_list:
            if select_player_id == defender_player_id:
                already_at_war_check = True
        if already_at_war_check:
            player_action_log.append(f'Failed to declare a {war_justification} war on {defender_nation_name}. You are already at war with this nation.')
            player_action_logs[attacker_player_id - 1] = player_action_log
            continue

        #resolve war declaration
        new_war_data = ['ID #', '-', '-', '-', '-', '-', '-', '-', '-', '-', '-', 'War Name', current_turn_num, 'Ongoing', [], 'TBD']
        war_count = len(wardata_list)
        war_id = war_count + 1
        new_war_data[0] = war_id
        #main attacker entry
        main_attacker_entry = ['Main Attacker', war_justification, 0, 0, 0, 0]
        if war_justification == 'Border Skirmish' or war_justification == 'Conquest' or war_justification == 'Annexation':
            war_justification_details = input(f'List the regions that {attacker_nation_name} is claiming using {war_justification}: ')
            main_attacker_entry.append(war_justification_details)
        new_war_data[attacker_player_id] = main_attacker_entry
        #main defender entry
        main_defender_entry = ['Main Defender', 'TBD', 0, 0, 0, 0]
        new_war_data[defender_player_id] = main_defender_entry
        #call in main attacker allies
        secondary_attacker_entry = ['Secondary Attacker', 'TBD', 0, 0, 0, 0]
        attacker_puppet_states_list = core.get_subjects(playerdata_list, attacker_nation_name, "Puppet State")
        for select_player_id in attacker_puppet_states_list:
            subject_truce_check = core.check_for_truce(trucedata_list, select_player_id, defender_player_id, current_turn_num)
            if not subject_truce_check:
                new_war_data[select_player_id] = secondary_attacker_entry
                select_player_relations_data = relations_data_masterlist[select_player_id - 1]
                select_player_relations_data[defender_player_id] = 'At War'
                relations_data_masterlist[select_player_id - 1] = select_player_relations_data
        #call in main defender allies
        secondary_defender_entry = ['Secondary Defender', 'TBD', 0, 0, 0, 0]
        defender_puppet_states_list = core.get_subjects(playerdata_list, defender_nation_name, "Puppet State")
        for select_player_id in defender_puppet_states_list:
            subject_truce_check = core.check_for_truce(trucedata_list, select_player_id, attacker_player_id, current_turn_num)
            if not subject_truce_check:
                new_war_data[select_player_id] = secondary_defender_entry
                select_player_relations_data = relations_data_masterlist[select_player_id - 1]
                select_player_relations_data[attacker_player_id] = 'At War'
                relations_data_masterlist[select_player_id - 1] = select_player_relations_data
        defender_status = playerdata_list[defender_player_id - 1][28]
        if defender_status != "Independent Nation":
            overlord_nation_name = False
            for name in nation_name_list:
                if name.lower() in defender_status.lower():
                    overlord_nation_name = name
            if overlord_nation_name:
                overlord_player_id = nation_name_list.index(overlord_nation_name) + 1
                subject_truce_check = core.check_for_truce(trucedata_list, overlord_player_id, attacker_player_id, current_turn_num)
                if not subject_truce_check:
                    new_war_data[overlord_player_id] = secondary_defender_entry
                    select_player_relations_data = relations_data_masterlist[overlord_player_id - 1]
                    select_player_relations_data[attacker_player_id] = 'At War'
                    relations_data_masterlist[overlord_player_id - 1] = select_player_relations_data
        defender_defensive_pacts_list = core.get_alliances(defender_relations_data, "Defense Pact")
        for select_player_id in defender_defensive_pacts_list:
            subject_truce_check = core.check_for_truce(trucedata_list, select_player_id, attacker_player_id, current_turn_num)
            if not subject_truce_check:
                new_war_data[select_player_id] = secondary_defender_entry
                select_player_relations_data = relations_data_masterlist[select_player_id - 1]
                select_player_relations_data[attacker_player_id] = 'At War'
                relations_data_masterlist[select_player_id - 1] = select_player_relations_data

        #generate war name
        war_names_list = []
        war_prefixes = ['2nd', '3rd', '4th', '5th', '6th', '7th', '8th', '9th', '10th']
        for war in wardata_list:
            war_names_list.append(war[11])
        if war_justification == 'Animosity' or war_justification == 'Border Skirmish':
            base_war_name = f'{attacker_nation_name} - {defender_nation_name} Conflict'
        elif war_justification == 'Conquest' or war_justification == 'Annexation':
            base_war_name = f'{attacker_nation_name} - {defender_nation_name} War'
        elif war_justification == 'Independence':
            base_war_name = f'{attacker_nation_name} War for Independence'
        elif war_justification == 'Subjugation':
            base_war_name = f'{attacker_nation_name} Subjugation War'
        attempts = 0
        while True:
            if base_war_name not in war_names_list:
                new_war_name = base_war_name
                break
            new_war_name = f'{war_prefixes[attempts]} {base_war_name}'
            if new_war_name not in war_names_list:
                break
            else:
                attempts += 1
        new_war_data[11] = new_war_name
        diplomacy_log.append(f'{attacker_nation_name} declared war on {defender_nation_name}.')
        wardata_list.append(new_war_data)
        player_action_log.append(f'Declared war on {defender_nation_name}.')
        player_action_logs[attacker_player_id - 1] = player_action_log

        #update relations
        attacker_relations_data[defender_player_id] = 'At War'
        defender_relations_data[attacker_player_id] = 'At War'
        relations_data_masterlist[attacker_player_id - 1] = attacker_relations_data
        relations_data_masterlist[defender_player_id - 1] = defender_relations_data

        
    #Update wardata.csv
    with open(wardata_filepath, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(core.wardata_header_a)
        writer.writerow(core.wardata_header_b)
        writer.writerows(wardata_list)


    #Update playerdata.csv
    for index, player in enumerate(playerdata_list):
        player[22] = str(relations_data_masterlist[index])
    with open(playerdata_filepath, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(core.player_data_header)
        writer.writerows(playerdata_list)

    return diplomacy_log, player_action_logs

def resolve_missile_launches(missile_launch_list, full_game_id, player_action_logs):
    '''Resolves all missile launch actions and missile defense abilities.'''
    
    #define core lists
    playerdata_filepath = f'gamedata/{full_game_id}/playerdata.csv'
    regdata_filepath = f'gamedata/{full_game_id}/regdata.csv'
    wardata_filepath = f'gamedata/{full_game_id}/wardata.csv'
    playerdata_list = core.read_file(playerdata_filepath, 1)
    regdata_list = core.read_file(regdata_filepath, 2)
    wardata_list = core.read_file(wardata_filepath, 2)

    #remove actions with bad region names
    missile_launch_list = core.filter_region_names(regdata_list, missile_launch_list)

    #get needed player info
    nation_name_list = []
    missile_data_masterlist = []
    research_masterlist = []
    for player in playerdata_list:
        nation_name = player[1]
        nation_name_list.append(nation_name)
        player_missile_data = ast.literal_eval(player[21])
        missile_data_masterlist.append(player_missile_data)
        player_research_list = ast.literal_eval(player[26])
        research_masterlist.append(player_research_list)


    #Execute Actions
    missiles_launched = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    for missile_launch in missile_launch_list:
        player_id = missile_launch[0]
        missile_launch_list = missile_launch[1].split(' ')
        target_region_id = missile_launch_list[-1]
        missile_type = ' '.join(missile_launch_list[1:3])
        player_missile_data = missile_data_masterlist[player_id - 1]
        player_action_log = player_action_logs[player_id - 1]

        #player has missile to launch check
        missile_check = True
        if missile_type == 'Standard Missile':
            if player_missile_data[0] == 0:
                missile_check = False
        else:
            if player_missile_data[1] == 0:
                missile_check = False
        if missile_check == False:
            player_action_log.append(f'Failed to launch {missile_type} at {target_region_id}. You do not have a {missile_type} in storage.')
            player_action_logs[player_id - 1] = player_action_log
            continue

        #target region belongs to target player check
        for region in regdata_list:
            if region[0] == target_region_id:
                target_control_data = ast.literal_eval(region[2])
                target_improvement_data = ast.literal_eval(region[4])
                target_unit_data = ast.literal_eval(region[5])
                if target_unit_data[0] != None:
                    target_unit_owner_id = target_unit_data[2]
                player_id_2 = target_control_data[0]
                break
        
        #player at war with target player check
        war_check = False
        if player_id != player_id_2:
            for war in wardata_list:
                if war[player_id] != '-' and war[player_id_2] != '-' and war[13] == 'Ongoing':
                    wardata_1 = ast.literal_eval(war[player_id])
                    war_role_1 = wardata_1[0]
                    wardata_2 = ast.literal_eval(war[player_id_2])
                    war_role_2 = wardata_2[0]
                    if target_unit_data[0] != None:
                        if target_unit_owner_id != player_id_2:
                            wardata_3 = ast.literal_eval(war[target_unit_owner_id])
                    #make sure player 1 is at war with player 2 in selected war
                    if ('Attacker' in war_role_1 and 'Defender' in war_role_2) or ('Defender' in war_role_1 and 'Attacker' in war_role_2):
                        war_check = True
                        war_log = ast.literal_eval(war[14])
                        break
        if war_check == False:
            player_action_log.append(f'Failed to launch {missile_type} at {target_region_id}. You are not at war with the player who controls {target_region_id}.')
            player_action_logs[player_id - 1] = player_action_log
            continue

        #launch capacity check
        improvement_name_list = sorted(core.improvement_data_dict.keys())
        improvement_count_list = ast.literal_eval(playerdata_list[player_id_2 - 1][27])
        silo_index = improvement_name_list.index('Missile Silo')
        silo_count = improvement_count_list[silo_index]
        effective_launch_capacity = silo_count * 2
        for region in regdata_list:
            select_improvement_data = ast.literal_eval(region[4])
            if select_improvement_data[0] == 'Missile Silo':
                effective_launch_capacity += 2
        if missile_type == 'Standard Missile':
            if effective_launch_capacity - missiles_launched[player_id - 1] - 1 < 0:
                player_action_log.append(f'Failed to launch {missile_type} at {target_region_id}. Insufficient launch capacity!')
                player_action_logs[player_id - 1] = player_action_log
                continue
        elif missile_type == 'Nuclear Missile':
            if effective_launch_capacity - missiles_launched[player_id - 1] - 2 < 0:
                player_action_log.append(f'Failed to launch {missile_type} at {target_region_id}. Insufficient launch capacity!')
                player_action_logs[player_id - 1] = player_action_log
                continue

        
        #Missile Launch Procedure
        missile_alive = True
        attacker_nation_name = nation_name_list[player_id - 1]
        target_nation_name = nation_name_list[player_id_2 - 1]
        target_improvement_name = target_improvement_data[0]
        target_improvement_health = target_improvement_data[1]
        target_player_research = research_masterlist[player_id_2 - 1]
        target_unit_id = target_unit_data[0]
        #unit present in region may not belong to target player
        target_unit_owner_id = 0
        if target_unit_id != None:
            target_unit_owner_id = target_unit_data[2]
            nation_name_3 = nation_name_list[target_unit_owner_id - 1]

        #fire missile
        if missile_type == 'Standard Missile':
            player_missile_data[0] -= 1
            missiles_launched[player_id - 1] += 1
            war_log.append(f'{attacker_nation_name} launched a Standard Missile toward {target_region_id} in {target_nation_name}.')
        elif missile_type == 'Nuclear Missile':
            player_missile_data[0] -= 1
            missiles_launched[player_id - 1] += 2
            war_log.append(f'{attacker_nation_name} launched a Nuclear Missile toward {target_region_id} in {target_nation_name}.')
        missile_data_masterlist[player_id - 1] = player_missile_data

        #missile defense oppertunity
        if target_improvement_name == 'Missile Defense System' or target_improvement_name == 'Missile Defense Network' or ('Localized Missile Defense' in target_player_research and target_improvement_health != 99 and target_improvement_health != 0):
            missile_alive = core.attempt_missile_defense(missile_type, target_improvement_data, target_nation_name, target_player_research, war_log)
        else:
            defense_improvement_data = None
            #find defense network if able
            missile_defense_network_candidates_list = core.get_regions_in_radius(target_region_id, 2, regdata_list)
            for select_region_id in missile_defense_network_candidates_list:
                region_data_list = core.get_region_data(regdata_list, select_region_id)
                control_data = ast.literal_eval(region_data_list[2])
                improvement_data = ast.literal_eval(region_data_list[4])
                if improvement_data[0] == 'Missile Defense Network' and control_data[0] == player_id_2:
                    defense_improvement_data = improvement_data
                    break
            #find defense system if able
            if defense_improvement_data == None:
                missile_defense_system_candidates_list = core.get_regions_in_radius(target_region_id, 1, regdata_list)
                for select_region_id in missile_defense_system_candidates_list:
                    region_data_list = core.get_region_data(regdata_list, select_region_id)
                    control_data = ast.literal_eval(region_data_list[2])
                    improvement_data = ast.literal_eval(region_data_list[4])
                    if improvement_data[0] == 'Missile Defense System' and control_data[0] == player_id_2:
                        defense_improvement_data = improvement_data
                        break
            if defense_improvement_data != None:
                missile_alive = core.attempt_missile_defense(missile_type, defense_improvement_data, target_nation_name, target_player_research, war_log)

        #missile strike
        if missile_alive and missile_type == 'Standard Missile':
            if target_improvement_name != None:
                if target_improvement_health != 99:
                    target_improvement_health -= 2
                    if target_improvement_health <= 0:
                        war_log.append(f'    Standard Missile successfully struck the {target_improvement_name} in {target_region_id}. Improvement destroyed!')
                        if target_improvement_name != 'Capital':
                            updated_improvement_data = [None, 99]
                            wardata_2[4] += 1
                        else:
                            updated_improvement_data = ['Capital', 0]
                        regdata_list = core.update_improvement_data(regdata_list, target_region_id, updated_improvement_data)
                    else:
                        war_log.append(f'    Standard Missile successfully struck the {target_improvement_name} in {target_region_id} and dealt 2 damage.')
                        updated_improvement_data = [target_improvement_name, target_improvement_health]
                        regdata_list = core.update_improvement_data(regdata_list, target_region_id, updated_improvement_data)
                else:
                    missile_accuracy_roll = random.randint(1, 10)
                    war_log.append(f'    Standard Missile rolled a {missile_accuracy_roll} for accuracy.')
                    if missile_accuracy_roll >= 8:
                        war_log.append(f'    Standard Missile struck {target_nation_name} {target_improvement_name}. Improvement destroyed!')
                        updated_improvement_data = [None, 99]
                        regdata_list = core.update_improvement_data(regdata_list, target_region_id, updated_improvement_data)
                        wardata_2[4] += 1
                    else:
                        war_log.append(f'    Standard Missile missed {target_nation_name} {target_improvement_name}.')
            else:
                war_log.append(f'    Standard Missile successfully struck {target_region_id}, but damaged nothing of importance.')
        elif missile_alive and missile_type == 'Nuclear Missile':
            if target_improvement_name != None:
                war_log.append(f'    Nuclear Missile destroyed {target_nation_name} {target_improvement_name}.')
                if target_improvement_name != 'Capital':
                    updated_improvement_data = [None, 99]
                    wardata_2[4] += 1
                else:
                    updated_improvement_data = ['Capital', 0]
                regdata_list = core.update_improvement_data(regdata_list, target_region_id, updated_improvement_data)
            if target_unit_id != None:
                target_unit_name = next((unit for unit, data in core.unit_data_dict.items() if data.get('Abbreviation') == target_unit_id), None)
                war_log.append(f'    Nuclear Missile destroyed {nation_name_3} {target_unit_name}.')
                updated_unit_data = [None, 99]
                regdata_list = core.update_unit_data(regdata_list, target_region_id, updated_unit_data)
                if target_unit_owner_id == player_id_2:
                    wardata_2[5] += 1
                else:
                    wardata_3[5] += 1
            if target_improvement_name == None and target_unit_id == None:
                war_log.append(f'    Nuclear Missile successfully struck {target_region_id}, but damaged nothing of importance.')
            nuke_data = [True, 2]
            regdata_list = core.update_nuke_data(regdata_list, target_region_id, nuke_data)
        

        #update war info
        for war in wardata_list:
            if war[player_id] != '-' and war[player_id_2] != '-' and war[13] == 'Ongoing':
                if ('Attacker' in war_role_1 and 'Defender' in war_role_2) or ('Defender' in war_role_1 and 'Attacker' in war_role_2):
                    war[player_id] = str(wardata_1)
                    war[player_id_2] = str(wardata_2)
                    if target_unit_data[0] != None:
                        if target_unit_owner_id != player_id_2:
                            war[target_unit_owner_id] = str(wardata_3)
                    war[14] = str(war_log)
                    break
        if missile_alive:
            player_action_log.append(f'Launched {missile_type} at {target_region_id}.')
        else:
           player_action_log.append(f'{missile_type} launched at {target_region_id} was shot down before reaching target.')
        player_action_logs[player_id - 1] = player_action_log
    
    
    #Update playerdata.csv
    for index, playerdata in enumerate(playerdata_list):
        playerdata[21] = str(missile_data_masterlist[index])
    with open(playerdata_filepath, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(core.player_data_header)
        writer.writerows(playerdata_list)


    #Update regdata.csv
    with open(regdata_filepath, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(core.regdata_header_a)
        writer.writerow(core.regdata_header_b)
        writer.writerows(regdata_list)


    #Update wardata.csv
    with open(wardata_filepath, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(core.wardata_header_a)
        writer.writerow(core.wardata_header_b)
        writer.writerows(wardata_list)

    return player_action_logs

def resolve_unit_movements(unit_movement_list, full_game_id, player_action_logs):
    '''Resolves all unit movements, including the resulting combat and occupation.'''

    #define core lists
    playerdata_filepath = f'gamedata/{full_game_id}/playerdata.csv'
    regdata_filepath = f'gamedata/{full_game_id}/regdata.csv'
    wardata_filepath = f'gamedata/{full_game_id}/wardata.csv'
    playerdata_list = core.read_file(playerdata_filepath, 1)
    regdata_list = core.read_file(regdata_filepath, 0)
    wardata_list = core.read_file(wardata_filepath, 2)
    with open('active_games.json', 'r') as json_file:
        active_games_dict = json.load(json_file)
    current_turn_num = int(active_games_dict[full_game_id]["Current Turn"])

    #get needed player info
    nation_name_list = []
    relations_data_masterlist = []
    research_masterlist = []
    for playerdata in playerdata_list:
        nation_name_list.append(playerdata[1])
        relations_data_masterlist.append(ast.literal_eval(playerdata[22]))
        research_masterlist.append(ast.literal_eval(playerdata[26]))

    #determine movement order
    players_moving_units = []
    for unit_movement in unit_movement_list:
        player_id = unit_movement[0]
        if player_id not in players_moving_units:
            players_moving_units.append(player_id)
    random.shuffle(players_moving_units)
    ordered_unit_movement_list = []
    for player_id in players_moving_units:
        for unit_movement in unit_movement_list:
            if unit_movement[0] == player_id:
                ordered_unit_movement_list.append(unit_movement)
    print(f"Movement Order - Turn {current_turn_num}")
    for index, player_id in enumerate(players_moving_units):
        position = index + 1
        nation_name = nation_name_list[player_id - 1]
        print(f'{position}. {nation_name}')


    #Execute Actions
    for unit_movement in ordered_unit_movement_list:
        attacker_player_id = unit_movement[0]
        region_str = unit_movement[1][5:]
        move_list = region_str.split('-')
        origin_region_id = move_list.pop(0)
        if attacker_player_id != 99:
            attacker_nation_name = playerdata_list[attacker_player_id - 1][1]
            attacker_relations_data = relations_data_masterlist[attacker_player_id - 1]
            player_action_log = player_action_logs[attacker_player_id - 1]
        else:
            attacker_nation_name = "Foreign Invasion"

        #move the unit one region at a time
        current_region_id = origin_region_id
        for target_region_id in move_list:
            #get information on current region
            current_region_data = core.get_region_data(regdata_list, current_region_id)
            current_unit_data = ast.literal_eval(current_region_data[5])
            current_unit_id = current_unit_data[0]
            current_unit_owner_id = 0
            if current_unit_id != None:
                current_unit_health = current_unit_data[1]
                current_unit_owner_id = current_unit_data[2]
            current_adjacency_list = core.get_adjacency_list(regdata_list, current_region_id)
            current_unit_index = core.unit_ids.index(current_unit_id)
            current_unit_name = core.unit_names[current_unit_index]
            #current region checks
            if current_unit_id == None or attacker_player_id != current_unit_owner_id:
                if attacker_player_id != 99:
                    player_action_log.append(f'Failed to perform a move action from {current_region_id}. You do not control a unit there.')
                    player_action_logs[attacker_player_id - 1] = player_action_log
                continue
            if target_region_id not in current_adjacency_list:
                if attacker_player_id != 99:
                    player_action_log.append(f'Failed to move {current_unit_id} {current_region_id} - {target_region_id}. Target region not adjacent to current region.')
                    player_action_logs[attacker_player_id - 1] = player_action_log
                continue
            if target_region_id == current_region_id:
                continue
            #get information on target region
            target_region_data = core.get_region_data(regdata_list, target_region_id)
            target_control_data = ast.literal_eval(target_region_data[2])
            target_improvement_data = ast.literal_eval(target_region_data[4])
            target_unit_data = ast.literal_eval(target_region_data[5])
            target_owner_id = target_control_data[0]
            target_occupier_id = target_control_data[1]
            target_improvement_name = target_improvement_data[0]
            target_improvement_health = target_improvement_data[1]
            target_unit_id = target_unit_data[0]
            target_unit_owner_id = 0
            if target_unit_id != None:
                target_unit_health = target_unit_data[1]
                target_unit_owner_id = target_unit_data[2]
            #generate player_id lists
            if attacker_player_id != 99:
                at_war_with_active_player_list = core.get_wars(attacker_relations_data)
                defensive_pact_with_active_player_list = core.get_alliances(attacker_relations_data, "Defense Pact")
                puppet_state_of_active_player_list = core.get_subjects(playerdata_list, attacker_nation_name, "Puppet State")
                revolting_puppet_state_of_active_player_list = []
                for select_player_id in puppet_state_of_active_player_list:
                    if select_player_id in at_war_with_active_player_list:
                        revolting_puppet_state_of_active_player_list.append(select_player_id)
            else:
                at_war_with_active_player_list = [i for i in range(1, len(playerdata_list) + 1)]
                defensive_pact_with_active_player_list = []
                puppet_state_of_active_player_list = []
                revolting_puppet_state_of_active_player_list = []
            #target region checks
            if target_owner_id == 0:
                if attacker_player_id != 99:
                    player_action_log.append(f'Failed to move {current_unit_id} {current_region_id} - {target_region_id}. You cannot move a unit to an unclaimed region.')
                    player_action_logs[attacker_player_id - 1] = player_action_log
            #illegal move check
            both_units_owned_by_attacker = (attacker_player_id == target_unit_owner_id)
            defending_unit_owned_by_ally = (target_unit_owner_id in defensive_pact_with_active_player_list)
            defending_unit_owned_by_loyal_puppet_state = (target_unit_owner_id in puppet_state_of_active_player_list and target_unit_owner_id not in at_war_with_active_player_list)
            if both_units_owned_by_attacker or defending_unit_owned_by_ally or defending_unit_owned_by_loyal_puppet_state:
                if attacker_player_id != 99:
                    player_action_log.append(f'Failed to move {current_unit_id} {current_region_id} - {target_region_id}. A friendly unit is present in the target region.')
                    player_action_logs[attacker_player_id - 1] = player_action_log
                    continue
            if target_owner_id not in at_war_with_active_player_list and target_owner_id not in defensive_pact_with_active_player_list and target_owner_id not in puppet_state_of_active_player_list:
                if target_owner_id != attacker_player_id:
                    if attacker_player_id != 99:
                        player_action_log.append(f'Failed to move {current_unit_id} {current_region_id} - {target_region_id}. Region is controlled by a player that is neither your ally nor enemy.')
                        player_action_logs[attacker_player_id - 1] = player_action_log
                        continue
            
            #combat will occur if hostile unit present and/or defensive improvement present
            attacking_unit_alive = True
            no_opposition = True
            hostile_unit_present = target_unit_id != None and target_unit_owner_id in at_war_with_active_player_list
            hostile_improvement_present = (target_owner_id in at_war_with_active_player_list and target_improvement_health != 99) or (target_improvement_name == 'Capital' and target_improvement_health != 0 and (target_owner_id in at_war_with_active_player_list or target_occupier_id in at_war_with_active_player_list))
            if hostile_unit_present or hostile_improvement_present:
                #identify war this combat is a part of and get war data
                if attacker_player_id != 99 or target_owner_id != 99 or target_unit_owner_id != 99:
                    war_role_1 = None
                    war_role_2 = None
                    for war in wardata_list:
                        if war[attacker_player_id] != '-' and war[target_unit_owner_id] != '-' and war[13] == 'Ongoing':
                            attacker_war_data = ast.literal_eval(war[attacker_player_id])
                            if target_unit_id != None:
                                    defender_war_data = ast.literal_eval(war[target_unit_owner_id])
                            else: 
                                defender_war_data = ast.literal_eval(war[target_owner_id])
                            attacker_role = attacker_war_data[0]
                            defender_role = defender_war_data[0]
                            war_role_1 = attacker_role
                            war_role_2 = defender_role
                            if ('Attacker' in war_role_1 and 'Defender' in war_role_2) or ('Defender' in war_role_1 and 'Attacker' in war_role_2):
                                attacker_battles_won = attacker_war_data[2]
                                attacker_battles_lost = attacker_war_data[3]
                                attacker_unit_casualties = attacker_war_data[4]
                                attacker_improvements_lost = attacker_war_data[5]
                                defender_battles_won = defender_war_data[2]
                                defender_battles_lost = defender_war_data[3]
                                defender_unit_casualties = defender_war_data[4]
                                defender_improvements_lost = defender_war_data[5]
                                war_log = ast.literal_eval(war[14])
                                break
                    else:
                        attacker_battles_won = 0
                        attacker_battles_lost = 0
                        attacker_unit_casualties = 0
                        attacker_improvements_lost = 0
                        defender_battles_won = 0
                        defender_battles_lost = 0
                        defender_unit_casualties = 0
                        defender_improvements_lost = 0
                        war_log = []
                        if attacker_nation_name == "Foreign Invasion":
                            war_role_1 = "Main Attacker"
                            war_role_2 = "Main Defender"
                        else:
                            war_role_1 = "Main Defender"
                            war_role_2 = "Main Attacker"
                #unit vs unit combat
                if hostile_unit_present:
                    target_player_id = target_unit_owner_id
                    if "Foreign Invasion" not in active_games_dict[full_game_id]["Active Events"]:
                        defender_nation_name = nation_name_list[target_player_id - 1]
                    else:
                        defender_nation_name = "Foreign Invasion"
                    target_unit_index = core.unit_ids.index(target_unit_id)
                    target_unit_name = core.unit_names[target_unit_index]
                    #conduct combat
                    attacker_data_list = [current_unit_id, current_unit_health, attacker_player_id, war_role_1, current_region_id]
                    defender_data_list = [target_unit_id, target_unit_health, target_player_id, war_role_2, target_region_id]
                    war_statistics_list = [attacker_battles_won, attacker_battles_lost, defender_battles_won, defender_battles_lost]
                    current_unit_health, attacker_battles_won, attacker_battles_lost, target_unit_health, defender_battles_won, defender_battles_lost, war_log = core.conduct_combat(attacker_data_list, defender_data_list, war_statistics_list, playerdata_list, regdata_list, war_log)
                    if current_unit_health > 0:
                        current_unit_data = [current_unit_id, current_unit_health, current_unit_owner_id]
                        regdata_list = core.update_unit_data(regdata_list, current_region_id, current_unit_data)
                    else:
                        attacker_unit_casualties += 1
                        attacking_unit_alive = False
                        regdata_list = core.update_unit_data(regdata_list, current_region_id, core.empty_unit_data)
                        war_log.append(f'    {attacker_nation_name} {current_unit_name} {current_region_id} has been lost.')
                    if target_unit_health > 0:
                        no_opposition = False
                        target_unit_data = [target_unit_id, target_unit_health, target_player_id]
                        regdata_list = core.update_unit_data(regdata_list, target_region_id, target_unit_data)
                    else:
                        defender_unit_casualties += 1
                        regdata_list = core.update_unit_data(regdata_list, target_region_id, core.empty_unit_data)
                        war_log.append(f'    {defender_nation_name} {target_unit_name} {target_region_id} has been lost.')
                #unit vs defensive improvement
                if attacking_unit_alive and hostile_improvement_present:
                    target_player_id = target_owner_id
                    if "Foreign Invasion" not in active_games_dict[full_game_id]["Active Events"]:
                        defender_nation_name = nation_name_list[target_owner_id - 1]
                    else:
                        defender_nation_name = "Foreign Invasion"
                    #conduct combat
                    attacker_data_list = [current_unit_id, current_unit_health, attacker_player_id, war_role_1, current_region_id]
                    defender_data_list = [target_improvement_name, target_improvement_health, target_player_id, war_role_2, target_region_id]
                    war_statistics_list = [attacker_battles_won, attacker_battles_lost, defender_battles_won, defender_battles_lost]
                    current_unit_health, attacker_battles_won, attacker_battles_lost, target_improvement_health, defender_battles_won, defender_battles_lost, war_log = core.conduct_combat(attacker_data_list, defender_data_list, war_statistics_list, playerdata_list, regdata_list, war_log)
                    #resolve combat outcome
                    if current_unit_health > 0:
                        current_unit_data = [current_unit_id, current_unit_health, current_unit_owner_id]
                        regdata_list = core.update_unit_data(regdata_list, current_region_id, current_unit_data)
                    else:
                        attacker_unit_casualties += 1
                        attacking_unit_alive = False
                        regdata_list = core.update_unit_data(regdata_list, current_region_id, core.empty_unit_data)
                        war_log.append(f'    {attacker_nation_name} {current_unit_name} {current_region_id} has been lost.')
                    if target_improvement_health > 0:
                        no_opposition = False
                        target_improvement_data = [target_improvement_name, target_improvement_health]
                        regdata_list = core.update_improvement_data(regdata_list, target_region_id, target_improvement_data)
                    else:
                        if target_improvement_name != 'Capital':
                            defender_improvements_lost += 1
                            regdata_list = core.update_improvement_data(regdata_list, target_region_id, core.empty_improvement_data)
                            war_log.append(f'    {defender_nation_name} {target_improvement_name} {target_region_id} has been destroyed.')
                        else:
                            target_improvement_data = ['Capital', 0]
                            regdata_list = core.update_improvement_data(regdata_list, target_region_id, target_improvement_data)
                            war_log.append(f'    {defender_nation_name} {target_improvement_name} {target_region_id} has been defeated.')
                #repackage war data now that combat is over
                if attacker_player_id != 99 or target_owner_id != 99 or target_unit_owner_id != 99:
                    for war in wardata_list:
                        if war[attacker_player_id] != '-' and war[target_unit_owner_id] != '-' and war[13] == 'Ongoing':
                            if ('Attacker' in war_role_1 and 'Defender' in war_role_2) or ('Defender' in war_role_1 and 'Attacker' in war_role_2):
                                attacker_war_data[2] = attacker_battles_won
                                attacker_war_data[3] = attacker_battles_lost
                                attacker_war_data[4] = attacker_unit_casualties
                                attacker_war_data[5] = attacker_improvements_lost
                                war[attacker_player_id] = str(attacker_war_data)
                                defender_war_data[2] = defender_battles_won
                                defender_war_data[3] = defender_battles_lost
                                defender_war_data[4] = defender_unit_casualties
                                defender_war_data[5] = defender_improvements_lost
                                if target_unit_id != None:
                                    war[target_unit_owner_id] = str(defender_war_data)
                                else: 
                                    war[target_owner_id] = str(defender_war_data)
                                war[14] = str(war_log)
            
            #resolve movement
            if target_unit_owner_id == attacker_player_id:
                no_opposition = False
            if attacking_unit_alive and no_opposition:
                current_unit_data = [current_unit_id, current_unit_health, current_unit_owner_id]
                regdata_list = core.update_unit_data(regdata_list, target_region_id, current_unit_data)
                regdata_list = core.update_unit_data(regdata_list, current_region_id, core.empty_unit_data)
                if attacker_player_id != 99:
                    player_action_log.append(f'Successfully moved {current_unit_id} {current_region_id} - {target_region_id}.')
                    player_action_logs[attacker_player_id - 1] = player_action_log
                #resolve occupation
                if target_owner_id in at_war_with_active_player_list:
                    if target_occupier_id not in at_war_with_active_player_list:
                        for region in regdata_list:
                            if region[0] == target_region_id:
                                new_data = [target_owner_id, attacker_player_id]
                                region[2] = str(new_data)
                                if target_improvement_name != 'Capital' and target_improvement_name != None:
                                    empty_data = [None, 99]
                                    region[4] = str(empty_data)
                                    for war in wardata_list:
                                        if war[attacker_player_id] != '-' and war[target_owner_id] != '-' and war[13] == 'Ongoing':
                                            defender_war_data = ast.literal_eval(war[target_owner_id])
                                            defender_war_data[5] += 1
                                            war[target_owner_id] = str(defender_war_data)
                                            break
                                break
                elif attacker_player_id == target_owner_id:
                    if target_occupier_id != 0:
                        for region in regdata_list:
                            if region[0] == target_region_id:
                                new_data = [target_owner_id, 0]
                                region[2] = str(new_data)
                                break
                current_region_id = target_region_id
            else:
                if attacker_player_id != 99:
                    player_action_log.append(f'Failed to move {current_unit_id} {current_region_id} - {target_region_id}.')
                    player_action_logs[attacker_player_id - 1] = player_action_log


    #Update regdata.csv
    with open(regdata_filepath, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerows(regdata_list)


    #Update wardata.csv
    with open(wardata_filepath, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(core.wardata_header_a)
        writer.writerow(core.wardata_header_b)
        writer.writerows(wardata_list)

    return player_action_logs

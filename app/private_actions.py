#STANDARD IMPORTS
import ast
import csv
import json
import random

#UWS SOURCE IMPORTS
from app import core
from app.region import Region
from app.improvement import Improvement
from app.unit import Unit
from app.wardata import WarData

#PRIVATE ACTION FUNCTIONS
def resolve_unit_withdraws(unit_withdraw_list, game_id, player_action_logs, current_turn_num):
    '''Preforms unit withdraws.'''

    #define core lists
    playerdata_filepath = f'gamedata/{game_id}/playerdata.csv'
    playerdata_list = core.read_file(playerdata_filepath, 1)
    wardata_list = []
    with open(f'gamedata/{game_id}/regdata.json', 'r') as json_file:
        regdata_dict = json.load(json_file)

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
        current_region_unit = Unit(current_region_id, game_id)
        current_unit_name = current_region_unit.name
        current_unit_owner_id = current_region_unit.owner_id

        #unit present check
        if current_unit_name == None or player_id != current_unit_owner_id:
            player_action_log.append(f'Failed to perform a withdraw action from {current_region_id}. You do not control a unit there.')
            player_action_logs[player_id - 1] = player_action_log
            continue

        #get information on target region
        target_region = Region(target_region_id, game_id)
        target_region_unit = Unit(target_region_id, game_id)
        target_owner_id = target_region.owner_id
        target_occupier_id = target_region.occupier_id
        target_unit_name = target_region_unit.name

        #destination owned by player check
        if target_owner_id != player_id and target_occupier_id != player_id:
            player_action_log.append(f'Failed to withdraw {current_unit_name} {current_region_id} - {target_region_id}. The destination region is not controlled by you.')
            player_action_logs[player_id - 1] = player_action_log
            continue

        #destination unoccupied check
        if target_unit_name != None:
            player_action_log.append(f'Failed to withdraw {current_unit_name} {current_region_id} - {target_region_id}. The destination region is occupied by another unit.')
            player_action_logs[player_id - 1] = player_action_log
            continue
        
        #withdraw unit
        movement_status = target_region_unit.move(target_region, withdraw=True)
        player_action_log.append(f'Withdrew {current_unit_name} {current_region_id} - {target_region_id}.')
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
        for region_id in regdata_dict:
            region = Region(region_id, game_id)
            region_unit = Unit(region_id, game_id)
            if region_unit.owner_id == player_id and region.owner_id in disallowed_list:
                region_unit.clear()
                used_mc -= 1
                player_action_log.append(f'{region_unit.name} {region_id} was lost due to no withdraw order.')
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

    return player_action_logs

def resolve_unit_disbands(unit_disband_list, game_id, player_action_logs):
    '''
    Resolves all unit disband actions.
    '''

    #define core lists
    playerdata_filepath = f'gamedata/{game_id}/playerdata.csv'
    playerdata_list = core.read_file(playerdata_filepath, 1)

    #get needed info from each player
    military_capacity_masterlist = []
    for player in playerdata_list:
        player_military_capacity = player[5]
        military_capacity_masterlist.append(player_military_capacity)


    #Execute Actions
    for disband_action in unit_disband_list:
        player_id = disband_action[0]
        region_id = disband_action[1][-5:]
        region = Region(region_id, game_id)
        region_unit = Unit(region_id, game_id)
        unit_name = region_unit.name
        player_military_capacity = military_capacity_masterlist[player_id - 1]
        player_action_log = player_action_logs[player_id - 1]

        # unit present check
        if unit_name is None:
            player_action_log.append(f'Failed to disband unit in {region_id}. There is no unit to disband.')
            player_action_logs[player_id - 1] = player_action_log
            continue

        # region ownership check
        if region.owner_id != player_id:
            player_action_log.append(f'Failed to disband unit in region {region_id}. You do not own or control this region.')
            player_action_logs[player_id - 1] = player_action_log
            continue

        # disband unit
        region_unit.clear()
        player_military_capacity_list = player_military_capacity.split('/')
        used_mc = int(player_military_capacity_list[0]) - 1
        total_mc = player_military_capacity_list[1]
        player_military_capacity = f'{used_mc}/{total_mc}'
        military_capacity_masterlist[player_id - 1] = player_military_capacity
        player_action_log.append(f'Disbanded {unit_name} in {region_id}.')
        player_action_logs[player_id - 1] = player_action_log
        
    
    #Update playerdata.csv
    for index, playerdata in enumerate(playerdata_list):
        playerdata[5] = military_capacity_masterlist[index]
    with open(playerdata_filepath, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(core.player_data_header)
        writer.writerows(playerdata_list)

    return player_action_logs

def resolve_unit_deployments(unit_deploy_list, game_id, player_action_logs):
    '''Resolves all unit deployment actions.'''

    # define core lists
    playerdata_filepath = f'gamedata/{game_id}/playerdata.csv'
    playerdata_list = core.read_file(playerdata_filepath, 1)
    with open('active_games.json', 'r') as json_file:
        active_games_dict = json.load(json_file)

    # get scenario data
    unit_data_dict = core.get_scenario_dict(game_id, "Units")

    # get needed economy information from each player
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

    # Execute Actions
    for deploy_action in unit_deploy_list:
        player_id = deploy_action[0]
        unit_name = deploy_action[1][7:-6]
        region_id = deploy_action[1][-5:]
        region = Region(region_id, game_id)
        region_unit = Unit(region_id, game_id)
        if "Foreign Invasion" not in active_games_dict[game_id]["Active Events"] and player_id != 99:
            player_government = nation_info_masterlist[player_id - 1][2]
            player_military_capacity = military_capacity_masterlist[player_id - 1]
            player_research = research_masterlist[player_id - 1]
            player_action_log = player_action_logs[player_id - 1]

        # foreign invasion case
        if "Foreign Invasion" in active_games_dict[game_id]["Active Events"] and player_id == 99:
            region_unit = Unit(region_id, game_id)
            region_unit.set_unit(unit_name, player_id)
            continue

        #get resource stockpiles of player
        stockpile_list = []
        for i in range(len(request_list)):
            stockpile_list.append(economy_masterlist[player_id - 1][i][0])
        player_stockpile_dict = {
            "Dollars": float(stockpile_list[0]),
            "Basic Materials": float(stockpile_list[1]),
            "Common Metals": float(stockpile_list[2]),
            "Advanced Metals": float(stockpile_list[3]),
            "Rare Earth Elements": float(stockpile_list[4])
        }

        # ownership check
        if region.owner_id != player_id:
            player_action_log.append(f'Failed to deploy {unit_name} in region {region_id}. You do not own this region.')
            player_action_logs[player_id - 1] = player_action_log
            continue

        # occupied check
        if region.occupier_id != 0:
            player_action_log.append(f'Failed to deploy {unit_name} in region {region_id}. This region is occupied.')
            player_action_logs[player_id - 1] = player_action_log
            continue
        
        # required research check
        if unit_data_dict[unit_name]['Required Research'] not in player_research:
            player_action_log.append(f'Failed to deploy {unit_name} in region {region_id}. You do not have the required research.')
            player_action_logs[player_id - 1] = player_action_log
            continue

        # capacity check
        capacity_check = core.check_military_capacity(military_capacity_masterlist[player_id - 1], 1)
        if capacity_check == False:
            player_action_log.append(f'Failed to deploy {unit_name} in region {region_id}. Insufficient military capacity.')
            player_action_logs[player_id - 1] = player_action_log
            continue
        
        # calculate deploy cost
        build_cost_dict = unit_data_dict[unit_name]["Build Costs"]
        if player_government == 'Military Junta':
            for key in build_cost_dict:
                build_cost_dict[key] *= 0.8
        
        # cost check
        cost_check_passed = True
        for key in build_cost_dict:
            cost = build_cost_dict[key]
            stockpile = player_stockpile_dict[key]
            if stockpile - cost < 0:
                cost_check_passed = False
        if not cost_check_passed:
            player_action_log.append(f'Failed to deploy {unit_name} in region {region_id}. Insufficient resources.')
            player_action_logs[player_id - 1] = player_action_log
            continue

        # pay for unit
        i = 0
        costs_list = []
        for key in build_cost_dict:
            cost = build_cost_dict[key]
            stockpile = player_stockpile_dict[key]
            economy_masterlist[player_id - 1][i][0] = core.update_stockpile(stockpile, cost)
            if cost > 0:
                costs_list.append(f"{cost} {key.lower()}")
            i += 1

        # deploy unit
        region_unit.set_unit(unit_name, player_id)
        if len(costs_list) <= 2:
            costs_str = " and ".join(costs_list)
        else:
            costs_str = ", ".join(costs_list)
            costs_str = " and ".join(costs_str.rsplit(", ", 1))
        player_military_capacity_list = player_military_capacity.split('/')
        used_mc = int(player_military_capacity_list[0]) + 1
        total_mc = float(player_military_capacity_list[1])
        player_military_capacity = f'{used_mc}/{total_mc}'
        military_capacity_masterlist[player_id - 1] = player_military_capacity
        player_action_log.append(f"Deployed {unit_name} in region {region_id} for {costs_str}.")
        player_action_logs[player_id - 1] = player_action_log


    # Update playerdata.csv
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

    return player_action_logs

def resolve_war_declarations(war_declaration_list, game_id, current_turn_num, diplomacy_log, player_action_logs):  
    '''Resolves all war declarations.'''

    #define core lists
    playerdata_filepath = f'gamedata/{game_id}/playerdata.csv'
    trucedata_filepath = f'gamedata/{game_id}/trucedata.csv'
    playerdata_list = core.read_file(playerdata_filepath, 1)
    trucedata_list = core.read_file(trucedata_filepath, 1)
    wardata = WarData(game_id)

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
        defender_nation_name = None
        for name in nation_name_list:
            if name.lower() in war_declaration_str.lower():
               defender_nation_name = name
        defender_player_id = nation_name_list.index(defender_nation_name) + 1
        war_justification = None
        for justification in core.WAR_JUSTIFICATIONS_LIST:
            if justification in war_declaration_str:
                war_justification = justification
        attacker_mc_data = military_capacity_masterlist[attacker_player_id - 1]
        attacker_research_list = research_masterlist[attacker_player_id - 1]
        attacker_status = playerdata_list[attacker_player_id - 1][28]
        player_action_log = player_action_logs[attacker_player_id - 1]

        #valid order check
        if not defender_nation_name or not war_justification:
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

        #already at war check
        if wardata.are_at_war(attacker_player_id, defender_player_id):
            player_action_log.append(f'Failed to declare a {war_justification} war on {defender_nation_name}. You are already at war with this nation.')
            player_action_logs[attacker_player_id - 1] = player_action_log
            continue

        #independence check
        if attacker_status != "Independent Nation":
            if defender_nation_name not in attacker_status and "Puppet State" in attacker_status:
                player_action_log.append(f'Failed to declare a {war_justification} war on {defender_nation_name}. As a puppet state, you cannot declare war.')
                player_action_logs[attacker_player_id - 1] = player_action_log
                continue

        #resolve war declaration
        region_claims_list = []
        if war_justification == 'Border Skirmish' or war_justification == 'Conquest' or war_justification == 'Annexation':
            region_claims_str = input(f'List the regions that {attacker_nation_name} is claiming using {war_justification}: ')
            region_claims_list = region_claims_str.split(',')
        war_name = wardata.create_war(attacker_player_id, defender_player_id, war_justification, current_turn_num, region_claims_list)
        diplomacy_log.append(f'{attacker_nation_name} declared war on {defender_nation_name}.')
        player_action_log.append(f'Declared war on {defender_nation_name}.')
        player_action_logs[attacker_player_id - 1] = player_action_log

        #update relations
        combatant_list = wardata.get_combatant_names(war_name)
        attacker_ids = []
        defender_ids = []
        for nation_name in combatant_list:
            player_id = nation_name_list.index(nation_name) + 1
            war_role = wardata.get_war_role(nation_name, war_name)
            if 'Attacker' in war_role:
                attacker_ids.append(player_id)
            elif 'Defender' in war_role:
                defender_ids.append(player_id)
        for nation_name in combatant_list:
            player_id = nation_name_list.index(nation_name) + 1
            war_role = wardata.get_war_role(nation_name, war_name)
            match war_role:
                case 'Main Attacker' | 'Secondary Attacker':
                    relations_data = relations_data_masterlist[player_id - 1]
                    for enemy_id in defender_ids:
                        relations_data[enemy_id] = 'At War'
                    relations_data_masterlist[player_id - 1] = relations_data
                case 'Main Defender' | 'Secondary Defender':
                    relations_data = relations_data_masterlist[player_id - 1]
                    for enemy_id in attacker_ids:
                        relations_data[enemy_id] = 'At War'
                    relations_data_masterlist[player_id - 1] = relations_data
        

    #Update playerdata.csv
    for index, player in enumerate(playerdata_list):
        player[22] = str(relations_data_masterlist[index])
    with open(playerdata_filepath, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(core.player_data_header)
        writer.writerows(playerdata_list)

    return diplomacy_log, player_action_logs

def resolve_missile_launches(missile_launch_list, game_id, player_action_logs):
    '''Resolves all missile launch actions and missile defense abilities.'''
    
    #define core lists
    playerdata_filepath = f'gamedata/{game_id}/playerdata.csv'
    regdata_filepath = f'gamedata/{game_id}/regdata.csv'
    wardata_filepath = f'gamedata/{game_id}/wardata.csv'
    playerdata_list = core.read_file(playerdata_filepath, 1)
    regdata_list = core.read_file(regdata_filepath, 2)
    wardata_list = core.read_file(wardata_filepath, 2)

    #get scenario data
    improvement_data_dict = core.get_scenario_dict(game_id, "Improvements")
    unit_data_dict = core.get_scenario_dict(game_id, "Units")

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
        improvement_name_list = sorted(improvement_data_dict.keys())
        improvement_count_list = ast.literal_eval(playerdata_list[player_id_2 - 1][27])
        silo_index = improvement_name_list.index('Missile Silo')
        silo_count = improvement_count_list[silo_index]
        effective_launch_capacity = silo_count * 3
        if missile_type == 'Standard Missile':
            if effective_launch_capacity - missiles_launched[player_id - 1] - 1 < 0:
                player_action_log.append(f'Failed to launch {missile_type} at {target_region_id}. Insufficient launch capacity!')
                player_action_logs[player_id - 1] = player_action_log
                continue
        elif missile_type == 'Nuclear Missile':
            if effective_launch_capacity - missiles_launched[player_id - 1] - 3 < 0:
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
        if target_improvement_name == 'Missile Defense System' or target_improvement_name == 'Missile Defense Network' or ('Local Missile Defense' in target_player_research and target_improvement_health != 99 and target_improvement_health != 0):
            missile_alive = core.attempt_missile_defense(game_id, missile_type, target_improvement_data, target_nation_name, target_player_research, war_log)
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
                missile_alive = core.attempt_missile_defense(game_id, missile_type, defense_improvement_data, target_nation_name, target_player_research, war_log)

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
                target_unit_name = next((unit for unit, data in unit_data_dict.items() if data.get('Abbreviation') == target_unit_id), None)
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

def resolve_unit_movements(unit_movement_list, game_id, player_action_logs):
    '''
    Resolves all unit movements, including the resulting combat and occupation.
    '''

    # define core lists
    playerdata_filepath = f'gamedata/{game_id}/playerdata.csv'
    playerdata_list = core.read_file(playerdata_filepath, 1)
    with open('active_games.json', 'r') as json_file:
        active_games_dict = json.load(json_file)
    current_turn_num = int(active_games_dict[game_id]["Statistics"]["Current Turn"])

    # get needed player info
    nation_name_list = []
    relations_data_masterlist = []
    research_masterlist = []
    for playerdata in playerdata_list:
        nation_name_list.append(playerdata[1])
        relations_data_masterlist.append(ast.literal_eval(playerdata[22]))
        research_masterlist.append(ast.literal_eval(playerdata[26]))

    # determine movement order
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


    # Execute Actions
    for unit_movement in ordered_unit_movement_list:
        attacker_player_id = unit_movement[0]
        region_str = unit_movement[1][5:]
        move_list = region_str.split('-')
        origin_region_id = move_list.pop(0)
        if attacker_player_id != 99:
            player_action_log = player_action_logs[attacker_player_id - 1]

        # Move Unit One Region at a Time
        current_region_id = origin_region_id
        for target_region_id in move_list:
            
            # get current region classes
            current_region = Region(current_region_id, game_id)
            current_region_unit = Unit(current_region_id, game_id)

            # current region checks
            if current_region_unit.name == None or attacker_player_id != current_region_unit.owner_id:
                if attacker_player_id != 99:
                    player_action_log.append(f'Failed to perform a move action from {current_region_id}. You do not control a unit there.')
                    player_action_logs[attacker_player_id - 1] = player_action_log
                continue
            if target_region_id not in current_region.adjacent_regions():
                if attacker_player_id != 99:
                    player_action_log.append(f'Failed to move {current_region_unit.name} {current_region_id} - {target_region_id}. Target region not adjacent to current region.')
                    player_action_logs[attacker_player_id - 1] = player_action_log
                continue
            if target_region_id == current_region_id:
                continue

            # get target region classes
            target_region = Region(target_region_id, game_id)
            target_region_unit = Unit(target_region_id, game_id)

            #target region checks
            if target_region.owner_id == 0:
                if attacker_player_id != 99:
                    player_action_log.append(f'Failed to move {target_region_unit.name} {current_region_id} - {target_region_id}. You cannot move a unit to an unclaimed region.')
                    player_action_logs[attacker_player_id - 1] = player_action_log
            #illegal move check
            if target_region_unit.name != None and not target_region_unit.is_hostile(current_region_unit.owner_id):
                if attacker_player_id != 99:
                    player_action_log.append(f'Failed to move {current_region_unit.name} {current_region_id} - {target_region_id}. A friendly unit is present in the target region.')
                    player_action_logs[attacker_player_id - 1] = player_action_log
                    continue
            if not target_region.is_valid_move(current_region_unit.owner_id):
                if attacker_player_id != 99:
                    player_action_log.append(f'Failed to move {current_region_unit.name} {current_region_id} - {target_region_id}. Region is controlled by a player that is not an enemy.')
                    player_action_logs[attacker_player_id - 1] = player_action_log
                    continue
            
            # Execute Movement Order
            movement_status = current_region_unit.move(target_region)
            # update player log
            if movement_status == True:
                player_action_log.append(f'Successfully moved {current_region_unit.name} {current_region_id} - {target_region_id}.')
            else:
                player_action_log.append(f'Failed to complete move {current_region_unit.name} {current_region_id} - {target_region_id}. Check combat log for details.')
            player_action_logs[attacker_player_id - 1] = player_action_log
            continue

    return player_action_logs
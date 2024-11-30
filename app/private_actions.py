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

        # validate war claims
        region_claims_list = []
        if war_justification == 'Border Skirmish' or war_justification == 'Conquest':
            all_claims_valid = False
            while not all_claims_valid:
                # get region claims
                region_claims_str = input(f'List the regions that {attacker_nation_name} is claiming using {war_justification}: ')
                region_claims_list = region_claims_str.split(',')
                all_claims_valid, playerdata_list = wardata.validate_war_claims(war_justification, region_claims_list, attacker_player_id, playerdata_list)
        
        #resolve war declaration
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
    
    # get game data
    playerdata_filepath = f'gamedata/{game_id}/playerdata.csv'
    playerdata_list = core.read_file(playerdata_filepath, 1)
    wardata = WarData(game_id)
    
    # get scenario data
    improvement_data_dict = core.get_scenario_dict(game_id, "Improvements")
    improvement_name_list = sorted(improvement_data_dict.keys())

    # get needed player info
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


    # Calculate Missile Launch Capacity
    missiles_launched_list = [0] * len(playerdata_list)
    launch_capacity_list = [0] * len(playerdata_list)
    for index, playerdata in enumerate(playerdata_list):
        improvement_count_list = ast.literal_eval(playerdata_list[index][27])
        silo_index = improvement_name_list.index('Missile Silo')
        silo_count = improvement_count_list[silo_index]
        launch_capacity_list[index] = silo_count * 3

    
    # Execute Actions
    for missile_launch in missile_launch_list:
        player_id = missile_launch[0]
        nation_name = nation_name_list[player_id - 1]
        missile_launch_list = missile_launch[1].split(' ')
        target_region_id = missile_launch_list[-1]
        missile_type = ' '.join(missile_launch_list[1:3])
        player_missile_data = missile_data_masterlist[player_id - 1]
        player_research_list = research_masterlist[player_id - 1]
        player_action_log = player_action_logs[player_id - 1]
        target_region = Region(target_region_id, game_id)
        target_region_improvement = Improvement(target_region_id, game_id)
        target_region_unit = Unit(target_region_id, game_id)
        
        # check if player actually has a missile to launch
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

        # check if target region is valid
        # notice we are not checking if region actually has something to hit - you are allowed to waste missiles
        if missile_type == 'Nuclear Missile':
            if player_id == target_region.owner_id:
                player_action_log.append(f'Failed to launch {missile_type} at {target_region_id}. You cannot nuke your own region.')
                player_action_logs[player_id - 1] = player_action_log
                continue
        target_region_is_valid = False
        # you can strike an enemy region provided it is unoccupied
        if wardata.are_at_war(player_id, target_region.owner_id) and target_region.owner_id == 0:
            target_player_id = target_region.owner_id
            target_region_is_valid = True
        # you can strike your own region provided it is occupied
        elif target_region.owner_id == player_id and target_region.occupier_id != 0 and wardata.are_at_war(player_id, target_region.occupier_id):
            target_player_id = target_region.occupier_id
            target_region_is_valid = True
        # if either case true strike is valid
        if not target_region_is_valid:
            player_action_log.append(f'Failed to launch {missile_type} at {target_region_id}. You are not at war with the nation that controls this region.')
            player_action_logs[player_id - 1] = player_action_log
            continue

        # launch capacity check
        launch_capacity_check = True
        if missile_type == 'Standard Missile':
            if missiles_launched_list[player_id - 1] + 1 > launch_capacity_list[player_id - 1]:
                launch_capacity_check = False
        elif missile_type == 'Nuclear Missile':
            if missiles_launched_list[player_id - 1] + 3 > launch_capacity_list[player_id - 1]:
                launch_capacity_check = False
        if not launch_capacity_check:
            player_action_log.append(f'Failed to launch {missile_type} at {target_region_id}. Insufficient launch capacity!')
            player_action_logs[player_id - 1] = player_action_log
            continue

        # all checks passed - fire missile
        if missile_type == 'Standard Missile':
            player_missile_data[0] -= 1
            missiles_launched_list[player_id - 1] += 1
        elif missile_type == 'Nuclear Missile':
            player_missile_data[1] -= 1
            missiles_launched_list[player_id - 1] += 3
        missile_data_masterlist[player_id - 1] = player_missile_data

        # identify war and log launch
        target_nation_name = nation_name_list[target_player_id - 1]
        war_name = wardata.are_at_war(player_id, target_player_id , True)
        war_role = wardata.get_war_role(nation_name, war_name)
        log_str = f'{nation_name} launched a {missile_type} at {target_region_id} in {target_nation_name}.'
        wardata.append_war_log(war_name, log_str)
        player_action_log.append(f'Launched {missile_type} at {target_region_id}. See combat log for details.')
        player_action_logs[player_id - 1] = player_action_log

        # engage missile defenses
        if "Local Missile Defense" in player_research_list:
            local_missile_defense = True
        else:
            local_missile_defense = False
        missile_intercepted, log_str_1, log_str_2 = target_region.activate_missile_defenses(missile_type, local_missile_defense)
        if log_str_1:
            wardata.append_war_log(war_name, log_str_1)
        if log_str_2:
            wardata.append_war_log(war_name, log_str_2)

        # conduct missile strike
        from app import combat
        if not missile_intercepted:
            
            if missile_type == 'Standard Missile':

                # update statistic
                wardata.statistic_add(war_name, nation_name, "missilesLaunched")
                
                # attempt to damage improvement
                if target_region_improvement.name != None and target_region_improvement.health != 0 and target_region_improvement.health != 99:
                    accuracy_roll = random.randint(1, 10)
                    wardata.append_war_log(war_name, f'    Standard Missile rolled a {accuracy_roll} for accuracy.')
                    if accuracy_roll > 3:
                        target_region_improvement.health -= 1
                        # improvement survived - save damage
                        if target_region_improvement.health > 0:
                            wardata.append_war_log(war_name, f'    Standard Missile struck {target_region_improvement.name} in {target_region_id} and dealt 1 damage.')
                            target_region_improvement._save_changes()
                        # improvement destroyed
                        elif target_region_improvement.health <= 0 and target_region_improvement.name != 'Capital':
                            wardata.statistic_add(war_name, nation_name, "enemyImprovementsDestroyed")
                            wardata.statistic_add(war_name, target_nation_name, "friendlyImprovementsDestroyed")
                            wardata.warscore_add(war_name, war_role, "enemyImprovementsDestroyed", 2)
                            wardata.append_war_log(war_name, f'    Standard Missile struck {target_region_improvement.name} in {target_region_id} and dealt 1 damage. Improvement destroyed!')
                            target_region_improvement.clear()
                        # improvement destroyed but is capital so set health to zero instead
                        elif target_region_improvement.health <= 0 and target_region_improvement.name == 'Capital':
                            wardata.append_war_log(war_name, f'    Standard Missile struck {target_region_improvement.name} in {target_region_id} and dealt 1 damage. Improvement devastated!')
                            target_region_improvement.health = 0
                            target_region_improvement._save_changes()
                    # if accuracy roll failed print war log
                    else:
                        wardata.append_war_log(war_name, f'    Standard Missile missed its target.')
                elif target_region_improvement.name != None and target_region_improvement.health == 99:
                    accuracy_roll = random.randint(1, 10)
                    wardata.append_war_log(war_name, f'    Standard Missile rolled a {accuracy_roll} for accuracy.')
                    if accuracy_roll > 7:
                        wardata.append_war_log(war_name, f'    Standard Missile destroyed {target_region_improvement.name} in {target_region_id}.')
                        wardata.statistic_add(war_name, nation_name, "enemyImprovementsDestroyed")
                        wardata.statistic_add(war_name, target_nation_name, "friendlyImprovementsDestroyed")
                        wardata.warscore_add(war_name, war_role, "enemyImprovementsDestroyed", 2)
                        target_region_improvement.clear()
                    else:
                        wardata.append_war_log(war_name, f'    Standard Missile missed its target.')

                # attempt to damage unit
                if target_region_unit.name != None:
                    accuracy_roll = random.randint(1, 10)
                    wardata.append_war_log(war_name, f'    Standard Missile rolled a {accuracy_roll} for accuracy.')
                    if accuracy_roll > 3:
                        target_region_unit.health -= 1
                        # unit survived - save damage
                        if target_region_unit.health > 0:
                            wardata.append_war_log(war_name, f'    Standard Missile struck {target_region_unit.name} in {target_region_id} and dealt 1 damage.')
                            target_region_unit._save_changes()
                        # unit destroyed
                        elif target_region_unit.health <= 0:
                            wardata.append_war_log(war_name, f'    Standard Missile struck {target_region_unit.name} in {target_region_id} and dealt 1 damage. Unit destroyed!')
                            wardata.statistic_add(war_name, nation_name, "enemyUnitsDestroyed")
                            wardata.statistic_add(war_name, target_nation_name, "friendlyUnitsDestroyed")
                            unit_bounty = combat._get_warscore_from_unit(target_region_unit.name)
                            wardata.warscore_add(war_name, war_role, "enemyUnitsDestroyed", unit_bounty)
                            target_region_unit.clear()
                    # if accuracy roll failed print war log
                    else:
                        wardata.append_war_log(war_name, f'    Standard Missile missed its target.')

                # add message if missile hit nothing
                if target_region_improvement.name is None and target_region_unit.name is None:
                    wardata.append_war_log(war_name, f'    Standard Missile has struck {target_region_id}, but destroyed nothing of importance.')
            
            elif missile_type == 'Nuclear Missile':
                
                # update statistic and add fallout
                wardata.statistic_add(war_name, nation_name, "nukesLaunched")
                wardata.warscore_add(war_name, war_role, "nukedEnemyRegions", 5)
                if target_region_improvement.name != 'Capital':
                    target_region.set_fallout()
                
                # destroy improvement if present
                if target_region_improvement.name != None and target_region_improvement.name != 'Capital':
                    wardata.append_war_log(war_name, f'    Nuclear Missile destroyed {target_region_improvement.name} in {target_region_id}.')
                    wardata.statistic_add(war_name, nation_name, "enemyImprovementsDestroyed")
                    wardata.statistic_add(war_name, target_nation_name, "friendlyImprovementsDestroyed")
                    wardata.warscore_add(war_name, war_role, "enemyImprovementsDestroyed", 2)
                    target_region_improvement.clear()
                # improvement destroyed but is capital so set health to zero instead
                elif target_region_improvement.name == 'Capital':
                    wardata.append_war_log(war_name, f'    Nuclear Missile devastated {target_region_improvement.name} in {target_region_id}.')
                    target_region_improvement.health = 0
                    target_region_improvement._save_changes()
                
                # destroy unit if present
                if target_region_unit.name != None:
                    wardata.append_war_log(war_name, f'    Nuclear Missile destroyed {target_region_unit.name} in {target_region_id}.')
                    wardata.statistic_add(war_name, nation_name, "enemyUnitsDestroyed")
                    wardata.statistic_add(war_name, target_nation_name, "friendlyUnitsDestroyed")
                    unit_bounty = combat._get_warscore_from_unit(target_region_unit.name)
                    wardata.warscore_add(war_name, war_role, "enemyUnitsDestroyed", unit_bounty)
                    target_region_unit.clear()

                # add message if missile hit nothing
                if target_region_improvement.name is None and target_region_unit.name is None:
                    wardata.append_war_log(war_name, f'    Nuclear Missile successfully struck {target_region_id}, but destroyed nothing.')

    
    #Update playerdata.csv
    for index, playerdata in enumerate(playerdata_list):
        playerdata[21] = str(missile_data_masterlist[index])
    with open(playerdata_filepath, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(core.player_data_header)
        writer.writerows(playerdata_list)

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
            unit_name = current_region_unit.name
            movement_status = current_region_unit.move(target_region)
            # update player log
            if movement_status == True:
                player_action_log.append(f'Successfully moved {unit_name} {current_region_id} - {target_region_id}.')
            else:
                player_action_log.append(f'Failed to complete move {unit_name} {current_region_id} - {target_region_id}. Check combat log for details.')
            player_action_logs[attacker_player_id - 1] = player_action_log
            continue

    return player_action_logs
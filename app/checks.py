#STANDARD IMPORTS
import ast
import csv
import json
import random
import re

#UWS SOURCE IMPORTS
from app import core
from app import map
from app.region import Region
from app.improvement import Improvement
from app.unit import Unit
from app.wardata import WarData
from app.notifications import Notifications
from app.alliance import AllianceTable
from app.alliance import Alliance

#END OF TURN CHECKS
def update_improvement_count(game_id, player_id):
    '''Gets a count of all improvements for a specific player using regdata_dict. Updates regdata.csv.'''
    
    #define core lists
    playerdata_filepath = f'gamedata/{game_id}/playerdata.csv'
    playerdata_list = core.read_file(playerdata_filepath, 1)
    with open(f'gamedata/{game_id}/regdata.json', 'r') as json_file:
        regdata_dict = json.load(json_file)


    #Procedure
    improvement_data_dict = core.get_scenario_dict(game_id, "Improvements")
    improvement_name_list = sorted(improvement_data_dict.keys())
    improvement_data_list = [0] * len(improvement_name_list)
    for region_id in regdata_dict:
        region = Region(region_id, game_id)
        region_improvement = Improvement(region_id, game_id)
        improvement_name = region_improvement.name
        if region.owner_id == int(player_id):
            if improvement_name:
                index = improvement_name_list.index(improvement_name)
                improvement_data_list[index] += 1
    
    
    #Update playerdata.csv
    improvement_data_list = str(improvement_data_list)
    for player in playerdata_list:
        desired_player_id = player[0][-1]
        if desired_player_id == str(player_id):
            player[27] = improvement_data_list
    with open(playerdata_filepath, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(core.player_data_header)
        writer.writerows(playerdata_list)

def ratio_check(game_id, player_id):
    '''Check if ratios for refineries are still valid.'''

    #define core lists
    playerdata_filepath = f'gamedata/{game_id}/playerdata.csv'
    playerdata_list = core.read_file(playerdata_filepath, 1)

    #get needed economy information from each player
    nation_info_masterlist = core.get_nation_info(playerdata_list)
    desired_nation_name = nation_info_masterlist[player_id - 1][0]
    for player in playerdata_list:
        if player[1] == desired_nation_name:
            improvement_count_list = ast.literal_eval(player[27])


    #Test Ratios
    improvement_data_dict = core.get_scenario_dict(game_id, "Improvements")
    improvement_name_list = sorted(improvement_data_dict.keys())
    refinery_list = ['Oil Refinery']
    for refinery_improvement in refinery_list:
        adjustment = 0
        while True:
            #get counts
            if refinery_improvement == 'Oil Refinery':
                ref_index = improvement_name_list.index('Oil Refinery')
                sub_index = improvement_name_list.index('Oil Well')
            ref_count = improvement_count_list[ref_index] - adjustment
            sub_count = improvement_count_list[sub_index]
            #remove a refinery if too many, otherwise move on to next refinery type
            if ref_count == 0 and sub_count == 0:
                break
            if ref_count != 0 and sub_count == 0:
                adjustment += 1
                region_id = core.search_and_destroy(game_id, player_id, refinery_improvement)
                adjustment_str = f'{desired_nation_name} lost {refinery_improvement} in {region_id}. Not enough supporting improvements.'
                print(adjustment_str)
                continue
            if ref_count / sub_count > 0.5:
                adjustment += 1
                region_id = core.search_and_destroy(game_id, player_id, refinery_improvement)
                adjustment_str = f'{desired_nation_name} lost {refinery_improvement} in {region_id}. Not enough supporting improvements.'
                print(adjustment_str)
            else:
                break

def update_military_capacity(game_id):
    '''Updates a player's military capacity.'''

    #define core lists
    playerdata_filepath = f'gamedata/{game_id}/playerdata.csv'
    playerdata_list = core.read_file(playerdata_filepath, 1)
    with open(f'gamedata/{game_id}/regdata.json', 'r') as json_file:
        regdata_dict = json.load(json_file)
    with open('active_games.json', 'r') as json_file:
        active_games_dict = json.load(json_file)

    #get needed info from players
    misc_info_masterlist = []
    status_masterlist = []
    for playerdata in playerdata_list:
        misc_info_list = ast.literal_eval(playerdata[24])
        misc_info_masterlist.append(misc_info_list)
        status_masterlist.append(playerdata[28])
    

    #Procedure
    improvement_data_dict = core.get_scenario_dict(game_id, "Improvements")
    improvement_name_list = sorted(improvement_data_dict.keys())
    military_capacity_gross = []
    military_capacity_output = []
    for index, playerdata in enumerate(playerdata_list):
        player_id = index + 1
        nation_info_masterlist = core.get_nation_info(playerdata_list)
        player_name = nation_info_masterlist[player_id - 1][0]
        player_gov = nation_info_masterlist[player_id - 1][2]
        player_research_list = ast.literal_eval(playerdata[26])
        player_improvement_count_list = ast.literal_eval(playerdata[27])
        nation_status = status_masterlist[player_id - 1]
        defensive_improvements_list = []
        for key, value in improvement_data_dict.items():
            if value.get("Health") != 99:
                defensive_improvements_list.append(key)
        di_count = 0
        for defensive_improvement_name in defensive_improvements_list:
            if defensive_improvement_name == "Boot Camp":
                bc_index = improvement_name_list.index(defensive_improvement_name)
                bc_count = player_improvement_count_list[bc_index]
            elif defensive_improvement_name == 'Capital':
                cap_index = improvement_name_list.index(defensive_improvement_name)
                cap_count = player_improvement_count_list[cap_index]
            else:
                di_index = improvement_name_list.index(defensive_improvement_name)
                di_count += player_improvement_count_list[di_index]
        
        #Calculate Military Capacity
        used_military_capacity = 0
        for region_id in regdata_dict:
            region_unit = Unit(region_id, game_id)
            if region_unit.owner_id == player_id:
                used_military_capacity += 1
        
        if 'Draft' in player_research_list:
            bc_capacity_value = 3
        else:
            bc_capacity_value = 2
        
        if 'Mandatory Service' in player_research_list:
            di_capacity_value = 0.5
        else:
            di_capacity_value = 0

        if 'Defensive Tactics' in player_research_list:
            cap_capacity_value = 2
        else:
            cap_capacity_value = 0
        
        if "Shared Fate" in active_games_dict[game_id]["Active Events"]:
            if active_games_dict[game_id]["Active Events"]["Shared Fate"]["Effect"] == "Conflict":
                bc_capacity_value += 1
        
        # calculate final military capacity
        military_capacity_total = (bc_count * bc_capacity_value) + (di_count * di_capacity_value) + (cap_count * cap_capacity_value)
        military_capacity_gross.append(military_capacity_total)
        #gain military capacity bonus from your puppet states
        for j, nation_status in enumerate(status_masterlist):
            if player_name in nation_status and 'Puppet State' in nation_status:
                troll_toll = military_capacity_gross[j] * 0.2
                military_capacity_total += troll_toll
        
        #gain military capacity bonus from government choice
        mct_modifier = 1.0
        if player_gov == 'Totalitarian':
            mct_modifier += 0.2
       #loose military capacity from being a puppet state
        if 'Puppet State' in nation_status:
            mct_modifier -= 0.2
        if "Threat Containment" in active_games_dict[game_id]["Active Events"]:
            if active_games_dict[game_id]["Active Events"]["Threat Containment"]["Chosen Nation Name"] == player_name:
                mct_modifier -= 0.2
        #apply military capacity modifiers
        if mct_modifier != 1.0:
            military_capacity_total *= mct_modifier
        elif mct_modifier < 0:
            military_capacity_total *= 0
        military_capacity_total = round(military_capacity_total, 2)
        military_capacity_output.append(f'{used_military_capacity}/{military_capacity_total}')

    #Update playerdata.csv
    for index, playerdata in enumerate(playerdata_list):
        playerdata[5] = military_capacity_output[index]
    with open(playerdata_filepath, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(core.player_data_header)
        writer.writerows(playerdata_list)

def remove_excess_units(game_id, player_id):
    '''
    Removes excess units if a players military capacity has been exceeded.
    '''

    # define core lists
    playerdata_filepath = f'gamedata/{game_id}/playerdata.csv'
    playerdata_list = core.read_file(playerdata_filepath, 1)
    notifications = Notifications(game_id)

    # Process
    playerdata = playerdata_list[player_id - 1]
    player_nation_name = playerdata[1]
    player_military_capacity_data = playerdata[5]
    used_mc, total_mc = core.read_military_capacity(player_military_capacity_data)
    units_lost = 0
    while used_mc > total_mc:
        chosen_region_id = core.search_and_destroy_unit(game_id, player_id, 'ANY')
        used_mc -= 1
        units_lost += 1
    if units_lost > 0:
        notifications.append(f'{player_nation_name} lost {units_lost} units due to insufficient military capacity.', 5)

    # Update playerdata.csv
    output_str = f'{used_mc}/{total_mc}'
    playerdata[5] = output_str
    playerdata_list[player_id - 1] = playerdata
    with open(playerdata_filepath, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(core.player_data_header)
        writer.writerows(playerdata_list)

def update_misc_info(game_id, player_id):
    '''
    Updates misc info list in playerdata.
    '''
    
    #get core lists
    playerdata_filepath = f'gamedata/{game_id}/playerdata.csv'
    playerdata_list = core.read_file(playerdata_filepath, 1)
    with open(f'gamedata/{game_id}/regdata.json', 'r') as json_file:
        regdata_dict = json.load(json_file)
    with open(f'gamedata/{game_id}/vc_overrides.json', 'r') as json_file:
        vc_overrides_dict = json.load(json_file)
    
    #get needed information from player
    nation_name_list = []
    for player in playerdata_list:
        nation_name_list.append(player[1])
    i = player_id - 1
    playerdata = playerdata_list[i]
    pp_data = ast.literal_eval(playerdata[10])
    political_power_stored = float(pp_data[0])
    misc_info = ast.literal_eval(playerdata[24])
    completed_research_list = ast.literal_eval(playerdata[26])

    
    #Update Capital Resource (if one not already active)
    if misc_info[0] == 'Capital Resource: None.':
        for region_id in regdata_dict:
            region = Region(region_id, game_id)
            region_improvement = Improvement(region_id, game_id)
            if region.owner_id == player_id and region.occupier_id == 0 and region_improvement.name == 'Capital':
                match region.resource:
                    case 'Coal':
                        if 'Coal Mining' in completed_research_list:
                            misc_info[0] = 'Capital Resource: Coal.'
                    case 'Oil':
                        if 'Oil Drilling' in completed_research_list:
                            misc_info[0] = 'Capital Resource: Oil.'
                    case 'Basic Materials':
                        misc_info[0] = 'Capital Resource: Basic Materials.'
                    case 'Common Metals':
                        if 'Surface Mining' in completed_research_list:
                            misc_info[0] = 'Capital Resource: Common Metals.'
                    case 'Advanced Metals':
                        if 'Metallurgy' in completed_research_list:
                            misc_info[0] = 'Capital Resource: Advanced Metals.'
                    case 'Uranium':
                        if 'Uranium Extraction' in completed_research_list:
                            misc_info[0] = 'Capital Resource: Uranium.'
                    case 'Rare Earth Elements':
                        if 'REE Mining' in completed_research_list:
                            misc_info[0] = 'Capital Resource: Rare Earth Elements.'
                    
    #Update Region Counts
    owned_regions = 0
    occupied_regions = 0
    undeveloped_regions = 0
    for region_id in regdata_dict:
        region = Region(region_id, game_id)
        region_improvement = Improvement(region_id, game_id)
        if region.owner_id == player_id and region.occupier_id == 0:
            owned_regions += 1
            if region_improvement.name == None:
                undeveloped_regions += 1
        elif region.owner_id == player_id and region.occupier_id != 0:
            occupied_regions += 1
    misc_info[1] = f'Owned Regions: {owned_regions}'
    misc_info[2] = f'Occupied Regions: {occupied_regions}'
    misc_info[3] = f'Undeveloped Regions: {undeveloped_regions}'
    
    
    #Update playerdata.csv
    misc_info = str(misc_info)
    full_player_id = f'Player #{player_id}'
    for player in playerdata_list:
        if player[0] == full_player_id:
            player[24] = misc_info
    with open(playerdata_filepath, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(core.player_data_header)
        writer.writerows(playerdata_list)

    #Update vc_extra.csv
    with open(f'gamedata/{game_id}/vc_overrides.json', 'w') as json_file:
        json.dump(vc_overrides_dict, json_file, indent=4)

def update_trade_tax(game_id, player_id):
    '''
    Calculate's a player's trade tax.
    '''
    
    playerdata_filepath = f'gamedata/{game_id}/playerdata.csv'
    playerdata_list = core.read_file(playerdata_filepath, 1)
    with open('active_games.json', 'r') as json_file:
        active_games_dict = json.load(json_file)

    change = 0
    player_name = playerdata_list[player_id - 1][1]
    player_research = ast.literal_eval(playerdata_list[player_id - 1][26])

    # check if Improved Logistics in player research
    if 'Improved Logistics' in player_research:
        change -= 1
    # if threat containment applies to target nation count it
    if "Threat Containment" in active_games_dict[game_id]["Active Events"]:
        if active_games_dict[game_id]["Active Events"]["Threat Containment"]["Chosen Nation Name"] == player_name:
            change += 1

    if change >= 0:
        trade_tax_str = f"{change + 1}:1"
    elif change < 0:
        trade_tax_str = f"1:{abs(change) + 1}"
    playerdata_list[player_id - 1][6] = trade_tax_str

def update_stockpile_limits(game_id, player_id):
    '''
    Updates a player's resource stockpile capacity.
    '''
    
    #get needed data
    playerdata_filepath = f'gamedata/{game_id}/playerdata.csv'
    playerdata_list = core.read_file(playerdata_filepath, 1)
    playerdata = playerdata_list[player_id - 1]
    improvement_count_list = ast.literal_eval(playerdata[27])
    player_central_bank_count = improvement_count_list[3] # yes this index is hardcoded. too bad!
    request_list = ['Dollars', 'Political Power', 'Technology', 'Coal', 'Oil', 'Green Energy', 'Basic Materials', 'Common Metals', 'Advanced Metals', 'Uranium', 'Rare Earth Elements']
    economy_masterlist = core.get_economy_info(playerdata_list, request_list)
    
    #get new resource stockpile limits
    new_stockpile_limit_dollars = 100 + (20 * player_central_bank_count)
    new_stockpile_limit_general = 50 + (20 * player_central_bank_count)
    
    #update resource data lists
    player_resource_masterlist = economy_masterlist[player_id - 1]
    updated_player_resource_masterlist = []
    i = 0
    for resource_data_list in player_resource_masterlist:
        stockpile_value = resource_data_list[0]
        income_value = resource_data_list[2]
        rate_value = resource_data_list[3]
        if i > 0:
            updated_resource_data_list = [stockpile_value, new_stockpile_limit_general, income_value, rate_value]
        else:
            updated_resource_data_list = [stockpile_value, new_stockpile_limit_dollars, income_value, rate_value]
        updated_player_resource_masterlist.append(updated_resource_data_list)
        i += 1
    for resource_data_list in updated_player_resource_masterlist:
        resource_data_list = str(resource_data_list)
    
    
    #Update playerdata.csv
    for player in playerdata_list:
        desired_player_id = player[0][-1]
        if desired_player_id == str(player_id):
            k = 9
            while k <= 19:
                player[k] = updated_player_resource_masterlist[k-9]
                k += 1
    with open(playerdata_filepath, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(core.player_data_header)
        writer.writerows(playerdata_list)

def update_income(game_id, current_turn_num):
    '''Updates income by resource and updates the income list in playerdata.'''
    
    #define core lists
    playerdata_filepath = f'gamedata/{game_id}/playerdata.csv'
    playerdata_list = core.read_file(playerdata_filepath, 1)
    with open(f'gamedata/{game_id}/regdata.json', 'r') as json_file:
        regdata_dict = json.load(json_file)
    with open('active_games.json', 'r') as json_file:
        active_games_dict = json.load(json_file)

    #get needed information from players
    nation_info_masterlist = core.get_nation_info(playerdata_list)
    nation_name_list = []
    for entry in nation_info_masterlist:
        nation_name_list.append(entry[0])
    request_list = ['Dollars', 'Political Power', 'Technology', 'Coal', 'Oil', 'Green Energy', 'Basic Materials', 'Common Metals', 'Advanced Metals', 'Uranium', 'Rare Earth Elements']
    economy_masterlist = core.get_economy_info(playerdata_list, request_list)
    playercount = len(playerdata_list)

    #indexes
    dollars_index = request_list.index('Dollars')
    pp_index = request_list.index('Political Power')
    tech_index = request_list.index('Technology')
    coal_index = request_list.index('Coal')
    oil_index = request_list.index('Oil')
    green_index = request_list.index('Green Energy')
    basic_index = request_list.index('Basic Materials')
    common_index = request_list.index('Common Metals')
    advanced_index = request_list.index('Advanced Metals')
    uranium_index = request_list.index('Uranium')
    rare_index = request_list.index('Rare Earth Elements')

    #get top three records
    if current_turn_num > 4:
        top_largest_list = get_top_three(game_id, 'largest_nation', True)
        top_economy_list = get_top_three(game_id, 'strongest_economy', True)
        top_military_list = get_top_three(game_id, 'largest_military', True)
        top_research_list = get_top_three(game_id, 'most_research', True)
        top_transactions_list = core.get_top_three_transactions(game_id)
        largest_score_not_tied = check_top_three(top_largest_list)
        economy_score_not_tied = check_top_three(top_economy_list)
        military_score_not_tied = check_top_three(top_military_list)
        research_score_not_tied = check_top_three(top_research_list)
        transactions_score_not_tied = check_top_three(top_transactions_list)

    #create income lists
    income_strings_masterlist = []
    rate_income_masterlist = []
    gross_income_masterlist = []
    for i in range(playercount):
        income_strings_masterlist.append([[], [], [], [], [], [], [], [], [], [], []])
        rate_income_masterlist.append([0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00])
        gross_income_masterlist.append([0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00])
    

    #Calculate Gross Income
    for index, playerdata in enumerate(playerdata_list):
        player_id = index + 1
        nation_name = nation_info_masterlist[player_id - 1][0]
        player_government = nation_info_masterlist[player_id - 1][2]
        military_capacity = playerdata[5]
        player_research_list = ast.literal_eval(playerdata[26])
        improvement_count_list = ast.literal_eval(playerdata[27])
        
        #calculate improvement incomes based on research
        if 'Power Grid Restoration' in player_research_list and 'Central Banking System' in player_research_list:
            city_income = 7
        elif 'Power Grid Restoration' in player_research_list:
            city_income = 5
        else:
            city_income = 3
        if 'Coal Subsidies' in player_research_list:
            coal_mine_income = 2
        else:
            coal_mine_income = 1
        if 'Underground Mining' in player_research_list:
            common_metals_mine_income = 2
        else:
            common_metals_mine_income = 1
        if 'Industrial Advancements' in player_research_list:
            industrial_zone_income = 2
        else:
            industrial_zone_income = 1
        if 'Oil Subsidies' in player_research_list and 'Fracking' in player_research_list:
            oil_well_income = 3
        elif 'Oil Subsidies' in player_research_list:
            oil_well_income = 2
        else:
            oil_well_income = 1
        if 'Upgraded Facilities' in player_research_list:
            research_lab_income = 2
        else:
            research_lab_income = 1
        if 'Green Energy Subsidies' in player_research_list:
            solar_farm_income = 3
        else:
            solar_farm_income = 2
        if 'Open Pit Mining' in player_research_list:
            strip_mine_coal_income = 6
        else:
            strip_mine_coal_income = 4
        if 'Green Energy Subsidies' in player_research_list:
            wind_farm_income = 2
        else:
            wind_farm_income = 1
        if 'Resource Enrichment'  in player_research_list:
            amm_mine_income = 2
        else:
            amm_mine_income = 1
        if 'Resource Enrichment'  in player_research_list:
            uranium_mine_income = 2
        else:
            uranium_mine_income = 1
        
        #get income from improvements
        for region_id in regdata_dict:
            region = Region(region_id, game_id)
            region_improvement = Improvement(region_id, game_id)
            region_resource = region.resource
            improvement_name = region_improvement.name
            #skip if no improvement
            if improvement_name == None:
                continue
            #get plural improvement name
            if improvement_name[-1] != 'y':
                plural_improvement_name = f'{improvement_name}s'
            else:
                plural_improvement_name = f'{improvement_name[:-1]}ies'
            #get remnant multiplier
            if player_government == 'Remnant' and region.check_for_adjacent_improvement(improvement_names = {'Capital'}):
                multiplier = 2
            else:
                multiplier = 1
            #get central bank multiplier
            if region.check_for_adjacent_improvement(improvement_names = {'Central Bank'}):
                multiplier *= 1.2
            #get pandemic multiplier
            if "Pandemic" in active_games_dict[game_id]["Active Events"]:
                region_quarantine = region.is_quarantined()
                infection_score = region.infection()
                infection_penalty = 0
                if infection_score > 0:
                    infection_penalty = infection_score * (0.1 * multiplier)
                quarantine_penalty = 0
                if region_quarantine is True:
                    quarantine_penalty = multiplier * 0.5
                multiplier -= infection_penalty
                multiplier -= quarantine_penalty
                if multiplier < 0:
                    multiplier = 0
            #get income based on improvement type
            if region.owner_id == player_id and region.occupier_id == 0:
                match improvement_name:
                    case 'Advanced Metals Mine':
                        gross_income_masterlist = update_gross_income_masterlist(gross_income_masterlist, player_id, advanced_index, amm_mine_income, multiplier)
                        income_strings_masterlist = update_income_strings_masterlist(income_strings_masterlist, player_id, advanced_index, amm_mine_income, multiplier, plural_improvement_name)
                    case 'Capital':
                        gross_income_masterlist[player_id - 1][dollars_index] += 5
                        gross_income_masterlist[player_id - 1][tech_index] += 2
                        gross_income_masterlist[player_id - 1][pp_index] += 1
                        income_strings_masterlist[player_id - 1][dollars_index] += [f'&Tab;+5 from {plural_improvement_name}']
                        income_strings_masterlist[player_id - 1][tech_index] += [f'&Tab;+2 from {plural_improvement_name}']
                        income_strings_masterlist[player_id - 1][pp_index] += [f'&Tab;+1 from {plural_improvement_name}']
                        if region_resource == 'Coal' and 'Coal Mining' in player_research_list:
                            gross_income_masterlist[player_id - 1][coal_index] += 1
                            income_strings_masterlist[player_id - 1][coal_index] += [f'&Tab;+1 from capital location.']
                        elif region_resource == 'Oil' and 'Oil Drilling' in player_research_list:
                            gross_income_masterlist[player_id - 1][oil_index] += 1
                            income_strings_masterlist[player_id - 1][oil_index] += [f'&Tab;+1 from capital location.']
                        elif region_resource == 'Basic Materials':
                            gross_income_masterlist[player_id - 1][basic_index] += 1
                            income_strings_masterlist[player_id - 1][basic_index] += [f'&Tab;+1 from capital location.']
                        elif region_resource == 'Common Metals' and 'Surface Mining' in player_research_list:
                            gross_income_masterlist[player_id - 1][common_index] += 1
                            income_strings_masterlist[player_id - 1][common_index] += [f'&Tab;+1 from capital location.']
                        elif region_resource == 'Advanced Metals' and 'Metallurgy' in player_research_list:
                            gross_income_masterlist[player_id - 1][advanced_index] += 1
                            income_strings_masterlist[player_id - 1][advanced_index] += [f'&Tab;+1 from capital location.']
                        elif region_resource == 'Uranium' and 'Uranium Extraction' in player_research_list:
                            gross_income_masterlist[player_id - 1][uranium_index] += 1
                            income_strings_masterlist[player_id - 1][uranium_index] += [f'&Tab;+1 from capital location.']
                        elif region_resource == 'Rare Earth Elements' and 'REE Mining' in player_research_list:
                            gross_income_masterlist[player_id - 1][rare_index] += 1
                            income_strings_masterlist[player_id - 1][rare_index] += [f'&Tab;+1 from capital location.']
                    case 'City':
                        gross_income_masterlist = update_gross_income_masterlist(gross_income_masterlist, player_id, dollars_index, city_income, multiplier)
                        income_strings_masterlist = update_income_strings_masterlist(income_strings_masterlist, player_id, dollars_index, city_income, multiplier, plural_improvement_name)
                    case 'Coal Mine':
                        gross_income_masterlist = update_gross_income_masterlist(gross_income_masterlist, player_id, coal_index, coal_mine_income, multiplier)
                        income_strings_masterlist = update_income_strings_masterlist(income_strings_masterlist, player_id, coal_index, coal_mine_income, multiplier, plural_improvement_name)
                    case 'Common Metals Mine':
                        gross_income_masterlist = update_gross_income_masterlist(gross_income_masterlist, player_id, common_index, common_metals_mine_income, multiplier)
                        income_strings_masterlist = update_income_strings_masterlist(income_strings_masterlist, player_id, common_index, common_metals_mine_income, multiplier, plural_improvement_name)
                    case 'Industrial Zone':
                        gross_income_masterlist = update_gross_income_masterlist(gross_income_masterlist, player_id, basic_index, industrial_zone_income, multiplier)
                        income_strings_masterlist = update_income_strings_masterlist(income_strings_masterlist, player_id, basic_index, industrial_zone_income, multiplier, plural_improvement_name)
                    case 'Nuclear Power Plant':
                        gross_income_masterlist = update_gross_income_masterlist(gross_income_masterlist, player_id, uranium_index, 6, multiplier)
                        income_strings_masterlist = update_income_strings_masterlist(income_strings_masterlist, player_id, green_index, 6, multiplier, plural_improvement_name)
                    case 'Oil Refinery':
                        gross_income_masterlist = update_gross_income_masterlist(gross_income_masterlist, player_id, oil_index, 2, multiplier)
                        income_strings_masterlist = update_income_strings_masterlist(income_strings_masterlist, player_id, oil_index, 2, multiplier, plural_improvement_name)
                    case 'Oil Well':
                        gross_income_masterlist = update_gross_income_masterlist(gross_income_masterlist, player_id, oil_index, oil_well_income, multiplier)
                        income_strings_masterlist = update_income_strings_masterlist(income_strings_masterlist, player_id, oil_index, oil_well_income, multiplier, plural_improvement_name)
                    case 'Rare Earth Elements Mine':
                        gross_income_masterlist = update_gross_income_masterlist(gross_income_masterlist, player_id, rare_index, 1, multiplier)
                        income_strings_masterlist = update_income_strings_masterlist(income_strings_masterlist, player_id, rare_index, 1, multiplier, plural_improvement_name)
                    case 'Research Institute':
                        gross_income_masterlist = update_gross_income_masterlist(gross_income_masterlist, player_id, tech_index, 5, multiplier)
                        income_strings_masterlist = update_income_strings_masterlist(income_strings_masterlist, player_id, tech_index, 5, multiplier, plural_improvement_name)
                    case 'Research Laboratory':
                        gross_income_masterlist = update_gross_income_masterlist(gross_income_masterlist, player_id, tech_index, research_lab_income, multiplier)
                        income_strings_masterlist = update_income_strings_masterlist(income_strings_masterlist, player_id, tech_index, research_lab_income, multiplier, plural_improvement_name)
                    case 'Solar Farm':
                        gross_income_masterlist = update_gross_income_masterlist(gross_income_masterlist, player_id, green_index, solar_farm_income, multiplier)
                        income_strings_masterlist = update_income_strings_masterlist(income_strings_masterlist, player_id, green_index, solar_farm_income, multiplier, plural_improvement_name)
                    case 'Strip Mine':
                        gross_income_masterlist = update_gross_income_masterlist(gross_income_masterlist, player_id, coal_index, strip_mine_coal_income, multiplier)
                        gross_income_masterlist = update_gross_income_masterlist(gross_income_masterlist, player_id, common_index, 2, multiplier)
                        income_strings_masterlist = update_income_strings_masterlist(income_strings_masterlist, player_id, coal_index, strip_mine_coal_income, multiplier, plural_improvement_name)
                        income_strings_masterlist = update_income_strings_masterlist(income_strings_masterlist, player_id, common_index, 2, multiplier, plural_improvement_name)
                    case 'Uranium Mine':
                        gross_income_masterlist = update_gross_income_masterlist(gross_income_masterlist, player_id, uranium_index, uranium_mine_income, multiplier)
                        income_strings_masterlist = update_income_strings_masterlist(income_strings_masterlist, player_id, uranium_index, uranium_mine_income, multiplier, plural_improvement_name)
                    case 'Wind Farm':
                        gross_income_masterlist = update_gross_income_masterlist(gross_income_masterlist, player_id, green_index, wind_farm_income, multiplier)
                        income_strings_masterlist = update_income_strings_masterlist(income_strings_masterlist, player_id, green_index, wind_farm_income, multiplier, plural_improvement_name)
        
        #political power income from top three
        if current_turn_num > 4:
            bonus_from_top_three = [1, 0.5, 0.25]
            for i in range(0, 3):
                bonus = bonus_from_top_three[i]
                if largest_score_not_tied[i] and nation_name in top_largest_list[i]:
                    gross_income_masterlist[player_id - 1][pp_index] += bonus
                    income_strings_masterlist[player_id - 1][pp_index] += [f'&Tab;+{bonus} from relative nation size.']
                if economy_score_not_tied[i] and nation_name in top_economy_list[i]:
                    gross_income_masterlist[player_id - 1][pp_index] += bonus
                    income_strings_masterlist[player_id - 1][pp_index] += [f'&Tab;+{bonus} from relative economic power.']
                if military_score_not_tied[i] and nation_name in top_military_list[i]:
                    gross_income_masterlist[player_id - 1][pp_index] += bonus
                    income_strings_masterlist[player_id - 1][pp_index] += [f'&Tab;+{bonus} from relative military size.']
                if research_score_not_tied[i] and nation_name in top_research_list[i]:
                    gross_income_masterlist[player_id - 1][pp_index] += bonus
                    income_strings_masterlist[player_id - 1][pp_index] += [f'&Tab;+{bonus} from relative research progress.']
                if transactions_score_not_tied[i] and nation_name in top_transactions_list[i]:
                    gross_income_masterlist[player_id - 1][pp_index] += bonus
                    income_strings_masterlist[player_id - 1][pp_index] += [f'&Tab;+{bonus} from trade.']

        #political power income from alliances
        alliance_count, alliance_capacity = core.get_alliance_count(game_id, playerdata)
        if 'Power Broker' in player_research_list:
            alliance_income = 0.75
        else:
            alliance_income = 0.5
        if alliance_income * alliance_count > 0:
            gross_income_masterlist[player_id - 1][pp_index] += alliance_income * alliance_count
            for i in range(alliance_count):
                income_strings_masterlist[player_id - 1][pp_index] += [f'&Tab;+{alliance_income} from alliances']

        #political power from military junta bonus
        if player_government == 'Military Junta':
            used_mc, total_mc = core.read_military_capacity(military_capacity)
            gross_income_masterlist[player_id - 1][pp_index] += (used_mc * 0.1)
            while used_mc > 0:
                income_strings_masterlist[player_id - 1][pp_index] += [f'&Tab;+0.1 from Military Junta bonus.']
                used_mc -= 0.1

        #political power from events
        if "Influence Through Trade" in active_games_dict[game_id]["Active Events"]:
            income_bonus_winner = active_games_dict[game_id]["Active Events"]["Influence Through Trade"]["Income Bonus Winner"]
            if nation_name == income_bonus_winner:
                gross_income_masterlist[player_id - 1][pp_index] += 0.5
                income_strings_masterlist[player_id - 1][pp_index] += [f'+0.5 from events.']
        if "Faustian Bargain" in active_games_dict[game_id]["Active Events"]:
            chosen_nation_name = active_games_dict[game_id]["Active Events"]["Faustian Bargain"]["Chosen Nation Name"]
            if nation_name == chosen_nation_name:
                pp_from_lease = 0.2 * len(active_games_dict[game_id]["Active Events"]["Faustian Bargain"]["Leased Regions List"])
                if pp_from_lease > 0:
                    gross_income_masterlist[player_id - 1][pp_index] += pp_from_lease
                    income_strings_masterlist[player_id - 1][pp_index] += [f'+{pp_from_lease} from events.']
    
    #Apply Rate to Gross Income
    for index, player in enumerate(playerdata_list):
        player_id = index + 1
        rate_list = []
        for i in range(len(request_list)):
            rate_list.append(economy_masterlist[player_id - 1][i][3])
        for index, rate in enumerate(rate_list):
            gross_income = gross_income_masterlist[player_id - 1][index]
            rate = float(rate) / 100
            final_gross_income = gross_income * rate
            rate_diff = final_gross_income - gross_income
            rate_diff = core.round_total_income(rate_diff)
            if float(rate_diff) > 0:
                string_list = income_strings_masterlist[player_id - 1][index]
                string_list.insert(0, f'&Tab;+{rate_diff} from income rate.')
                income_strings_masterlist[player_id - 1][index] == string_list
            elif float(rate_diff) < 0:
                string_list = income_strings_masterlist[player_id - 1][index]
                string_list.insert(0, f'&Tab;{rate_diff} from income rate.')
                income_strings_masterlist[player_id - 1][index] == string_list
            rate_income_masterlist[player_id - 1][index] = rate_diff
            final_gross_income = round(final_gross_income, 2)
            gross_income_masterlist[player_id - 1][index] = final_gross_income
    

    #Calculate Net Income
    net_income_masterlist = gross_income_masterlist
    for index, playerdata in enumerate(playerdata_list):
        player_id = index + 1
        nation_name = nation_info_masterlist[player_id - 1][0]
        player_government = nation_info_masterlist[player_id - 1][2]
        misc_info_list = ast.literal_eval(playerdata[24])
        player_research_list = ast.literal_eval(playerdata[26])
        improvement_count_list = ast.literal_eval(playerdata[27])
        nation_status = playerdata[28]
        
        #account for subject dues
        if 'Puppet State' in nation_status:
            for nation_name in nation_name_list:
                if nation_name in nation_status:
                    overlord_name = nation_name
                    break
            overlord_id = nation_name_list.index(overlord_name) + 1
            for i in range(0, 11):
                if i == 1:
                    continue
                selected_income = net_income_masterlist[player_id - 1][i]
                tax_amount = selected_income * 0.2
                net_income_masterlist[player_id - 1][i] -= round(tax_amount, 2)
                net_income_masterlist[overlord_id - 1][i] += round(tax_amount, 2)
                income_strings_masterlist[player_id - 1][i] += [f'&Tab;-{tax_amount} from puppet state status.']
                income_strings_masterlist[overlord_id - 1][i] += [f'&Tab;+{tax_amount} from puppet states.']
        
        
        #Pay Upkeep Costs
        unit_count_list = core.get_unit_count_list(player_id, game_id)
        improvement_dollar_upkeep_dict = core.get_upkeep_dictionary(game_id, 'Dollars Upkeep', playerdata, unit_count_list)
        improvement_energy_upkeep_dict = core.get_upkeep_dictionary(game_id, 'Energy Upkeep', playerdata, unit_count_list)
        unit_dollar_upkeep_dict = core.get_upkeep_dictionary(game_id, 'Unit Dollars Upkeep', playerdata, unit_count_list)
        unit_energy_upkeep_dict = core.get_upkeep_dictionary(game_id, 'Unit Oil Upkeep', playerdata, unit_count_list)
        improvement_dollar_upkeep_count = core.get_upkeep_sum(improvement_dollar_upkeep_dict)
        improvement_energy_upkeep_count = core.get_upkeep_sum(improvement_energy_upkeep_dict)
        unit_dollar_upkeep_count = core.get_upkeep_sum(unit_dollar_upkeep_dict)
        unit_energy_upkeep_count = core.get_upkeep_sum(unit_energy_upkeep_dict)
        total_upkeep_costs = improvement_energy_upkeep_count + unit_energy_upkeep_count
        unit_oil_upkeep_costs = unit_energy_upkeep_count
        dollars_upkeep_costs = improvement_dollar_upkeep_count + unit_dollar_upkeep_count
        
        #upkeep manager bullshit
        coal_income = net_income_masterlist[player_id - 1][coal_index]
        oil_income = net_income_masterlist[player_id - 1][oil_index]
        green_energy = net_income_masterlist[player_id - 1][green_index]
        if total_upkeep_costs > 0:
            upkeep_manager_list = ast.literal_eval(playerdata[23])
            allocated_coal = upkeep_manager_list[0]
            allocated_oil = upkeep_manager_list[1]
            allocated_green = upkeep_manager_list[2]
            upkeep_manager_total = float(allocated_coal) + float(allocated_oil) + float(allocated_green)
            #prompt for allocation if total upkeep costs have changed since last turn
            if upkeep_manager_total != total_upkeep_costs:
                total_upkeep_costs = core.round_total_income(total_upkeep_costs)
                #run upkeep manager
                upkeep_manager_header = f'Upkeep Manager for {nation_name}'
                upkeep_manager_total_str = f'Total upkeep costs: -{total_upkeep_costs}. From units: -{unit_oil_upkeep_costs}.'
                print(upkeep_manager_header)
                print(upkeep_manager_total_str)
                print("{:<20s}{:<20s}{:<20s}".format('Resource', 'Gross Income', 'Currently Allocated'))
                print("{:<20s}{:<20s}{:<20s}".format('Coal', str(coal_income), allocated_coal))
                print("{:<20s}{:<20s}{:<20s}".format('Oil', str(oil_income), allocated_oil))
                print("{:<20s}{:<20s}{:<20s}".format('Green Energy', str(green_energy), allocated_green))
                while True:
                    upkeep_manager_input = input('Please enter new upkeep allocations as a three-item list: ')
                    upkeep_manager_input_list = upkeep_manager_input.split(',')
                    if len(upkeep_manager_input_list) == 3:
                        allocated_coal = float(upkeep_manager_input_list[0])
                        allocated_oil = float(upkeep_manager_input_list[1])
                        allocated_green = float(upkeep_manager_input_list[2])
                        allocated_coal = core.round_total_income(allocated_coal)
                        allocated_oil = core.round_total_income(allocated_oil)
                        allocated_green = core.round_total_income(allocated_green)
                        break
                print('==================================================')
                #update playerdata
                upkeep_manager_list = [allocated_coal, allocated_oil, allocated_green, total_upkeep_costs]
                playerdata[23] = str(upkeep_manager_list)
            #make payments
            if float(allocated_coal) > 0:
                net_income_masterlist[player_id - 1][coal_index] -= float(allocated_coal)
                income_strings_masterlist[player_id - 1][coal_index] += [f'&Tab;-{allocated_coal} from upkeep allocations.']
            #pay oil upkeep
            if float(allocated_oil) > 0:
                net_income_masterlist[player_id - 1][oil_index] -= float(allocated_oil)
                income_strings_masterlist[player_id - 1][oil_index] += [f'&Tab;-{allocated_oil} from upkeep allocations.']
            #pay green energy upkeep
            if float(allocated_green) > 0:
                net_income_masterlist[player_id - 1][green_index] -= float(allocated_green)
                income_strings_masterlist[player_id - 1][green_index] += [f'&Tab;-{allocated_green} from upkeep allocations.']
        #pay uranium upkeep
        nuclear_power_plant_count = improvement_count_list[15]
        if nuclear_power_plant_count > 0:
            net_income_masterlist[player_id - 1][uranium_index] -= (nuclear_power_plant_count * 0.5)
            income_strings_masterlist[player_id - 1][uranium_index] += [f'&Tab;-0.5 from Nuclear Power Plant upkeep [{nuclear_power_plant_count}x]']
        #pay dollars upkeep
        if dollars_upkeep_costs > 0:
            net_income_masterlist[player_id - 1][dollars_index] -= dollars_upkeep_costs
            income_strings_masterlist[player_id - 1][dollars_index] += [f'&Tab;-{dollars_upkeep_costs} from upkeep allocations.']
    
    #update economy masterlist
    for i in range(len(economy_masterlist)):
        for j in range(0, 11):
            economy_masterlist[i][j][2] = core.round_total_income(net_income_masterlist[i][j])
    

    #Filter Income Strings
    filtered_income_string_masterlist = []
    for i in range(playercount):
        filtered_income_string_masterlist.append([[], [], [], [], [], [], [], [], [], [], []])
    for i in range(len(income_strings_masterlist)):
        income_string_dic = {
            'Dollars': {},
            'Political Power': {},
            'Technology': {},
            'Coal': {},
            'Oil': {},
            'Green Energy': {},
            'Basic Materials': {},
            'Common Metals': {},
            'Advanced Metals': {},
            'Uranium': {},
            'Rare Earth Elements': {},
        }
        for j in range(0, 11):
            resource_type = request_list[j]
            string_list = income_strings_masterlist[i][j]
            for string in string_list:
                if string in income_string_dic[resource_type]:
                    income_string_dic[resource_type][string] += 1
                else:
                    income_string_dic[resource_type][string] = 1
        for category, inner_dict in income_string_dic.items():
            j = request_list.index(category)
            for string, value in inner_dict.items():
                exclude_substrings = ['upkeep', 'income rate', 'Puppet State', 'Puppet States', 'from relative']
                if all(substring not in string for substring in exclude_substrings):
                    output_str = f'{string} [{value}x]'
                else:
                    output_str = string
                filtered_income_string_masterlist[i][j] += [output_str]
    
    #add calculated totals to income strings
    for i in range(len(filtered_income_string_masterlist)):
        for j in range(0, 11):
            net_income = economy_masterlist[i][j][2]
            resource_type = request_list[j]
            income_list = filtered_income_string_masterlist[i][j]
            if float(net_income) > 0:
                income_list.insert(0, f'+{net_income} {resource_type}')
            elif float(net_income) < 0:
                income_list.insert(0, f'{net_income} {resource_type}')
            elif float(net_income) == 0:
                income_list.insert(0, f'REMOVE ME')
            filtered_income_string_masterlist[i][j] == income_list
    
    #package income strings
    joined_income_strings_masterlist = []
    for player_income_string_list in filtered_income_string_masterlist:
        merged_contents = []
        for inner_list in player_income_string_list:
            if inner_list[0] != 'REMOVE ME':
                merged_contents += inner_list
        joined_income_strings_masterlist.append(merged_contents)


    #Update playerdata.csv
    for index, playerdata in enumerate(playerdata_list):
        playerdata[9:20] = economy_masterlist[index][:11]
        playerdata[25] = joined_income_strings_masterlist[index]
    with open(playerdata_filepath, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(core.player_data_header)
        writer.writerows(playerdata_list)

def gain_income(game_id, player_id):
    '''
    Updates resource stockpiles by adding given income totals to stockpile totals.
    '''

    #get core lists
    playerdata_filepath = f'gamedata/{game_id}/playerdata.csv'
    playerdata_list = core.read_file(playerdata_filepath, 1)

    #get needed data
    playerdata_list = core.read_file(playerdata_filepath, 1)
    playerdata = playerdata_list[player_id - 1]
    resource_data_masterlist = []
    j = 9
    while j <= 19:
        resource_data = ast.literal_eval(playerdata[j])
        resource_data_masterlist.append(resource_data)
        j += 1
    

    #Gain Resource Incomes
    for resource_data in resource_data_masterlist:
        resource_stockpile = float(resource_data[0])
        resource_stockpile_limit = float(resource_data[1])
        resource_income = float(resource_data[2])
        resource_stockpile += resource_income
        #check if stockpile limit has been exceeded
        if resource_stockpile > resource_stockpile_limit:
            resource_stockpile = resource_stockpile_limit
        #round resource stockpiles and update resource_data_masterlist
        resource_stockpile_formatted = core.round_total_income(resource_stockpile)
        resource_data[0] = resource_stockpile_formatted
    

    #Update playerdata.csv
    for player in playerdata_list:
        desired_player_id = player[0][-1]
        if desired_player_id == str(player_id):
            k = 9
            while k <= 19:
                player[k] = resource_data_masterlist[k-9]
                k += 1
    with open(playerdata_filepath, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(core.player_data_header)
        writer.writerows(playerdata_list)

def countdown(game_id, map_name):
    '''
    Resolves improvements/units that have countdowns associated with them.
    '''
    with open(f'gamedata/{game_id}/regdata.json', 'r') as json_file:
        regdata_dict = json.load(json_file)

    # Resolve Strip Mines
    removed_strip_mine = False
    for region_id in regdata_dict:
        region = Region(region_id, game_id)
        region_improvement = Improvement(region_id, game_id)
        if region_improvement.name == "Strip Mine":
            region_improvement.decrease_timer()
            if region_improvement.turn_timer <= 0:
                region_improvement.clear()
                region.set_resource("Empty")
    
    # Resolve Nuked Regions
    for region_id in regdata_dict:
        region = Region(region_id, game_id)
        if region.fallout != 0:
            region.decrease_fallout()

    # Update Resource Map if Needed
    if removed_strip_mine:
        resource_map = map.ResourceMap(int(game_id[-1]), map_name)
        resource_map.update()

def resolve_shortages(game_id, player_id): 
    '''
    Resolves negative resource values after income is processed.
    '''

    # define core lists
    playerdata_filepath = f'gamedata/{game_id}/playerdata.csv'
    playerdata_list = core.read_file(playerdata_filepath, 1)
    notifications = Notifications(game_id)

    # get needed information from player
    playerdata = playerdata_list[player_id - 1]
    nation_name = playerdata[1]
    request_list = ['Dollars', 'Coal', 'Oil', 'Green Energy']
    economy_masterlist = core.get_economy_info(playerdata_list, request_list)
    unit_count_list = core.get_unit_count_list(player_id, game_id)
    upkeep_manager_list = ast.literal_eval(playerdata[23])

    # get resource stockpiles
    stockpile_list = []
    for i in range(len(request_list)):
        stockpile_list.append(economy_masterlist[player_id - 1][i][0])
    dollars_stockpile = float(stockpile_list[0])
    coal_stockpile = float(stockpile_list[1])
    oil_stockpile = float(stockpile_list[2])
    green_stockpile = float(stockpile_list[3])

    # get upkeep costs
    dollars_upkeep_dict = core.get_upkeep_dictionary(game_id, 'Dollars Upkeep', playerdata, unit_count_list)
    energy_upkeep_dict = core.get_upkeep_dictionary(game_id, 'Energy Upkeep', playerdata, unit_count_list)
    dollars_unit_upkeep_dict = core.get_upkeep_dictionary(game_id, 'Dollars Unit Upkeep', playerdata, unit_count_list)
    oil_unit_upkeep_dict = core.get_upkeep_dictionary(game_id, 'Oil Unit Upkeep', playerdata, unit_count_list)


    # Resolve Energy Shortages
    while oil_stockpile < 0:
        for improvement_name in energy_upkeep_dict:
            improvement_upkeep = energy_upkeep_dict[improvement_name]['Improvement Upkeep']
            while energy_upkeep_dict[improvement_name]['Improvement Count'] > 0:
                # destroy random improvement of that type
                region_id = core.search_and_destroy(game_id, player_id, improvement_name)
                notifications.append(f'{nation_name} lost a {improvement_name} in {region_id} due to oil shortages.', 6)
                oil_stockpile += improvement_upkeep
                energy_upkeep_dict[improvement_name]['Improvement Count'] -= 1
                # adjust upkeep manager
                total_dedicated_upkeep = float(upkeep_manager_list[3])
                total_dedicated_upkeep -= improvement_upkeep
                upkeep_manager_list[3] = core.round_total_income(total_dedicated_upkeep)
                dedicated_oil_upkeep = float(upkeep_manager_list[1])
                dedicated_oil_upkeep -= improvement_upkeep
                upkeep_manager_list[1] = core.round_total_income(dedicated_oil_upkeep)
        for unit_name in oil_unit_upkeep_dict:
            unit_upkeep = oil_unit_upkeep_dict[unit_name]['Improvement Upkeep']
            while oil_unit_upkeep_dict[unit_name]['Improvement Count'] > 0:
                # destroy random unit of that type
                region_id = core.search_and_destroy_unit(game_id, player_id, unit_name)
                notifications.append(f'{nation_name} lost a {unit_name} in {region_id} due to oil shortages.', 6)
                oil_stockpile += unit_upkeep
                oil_unit_upkeep_dict[unit_name]['Improvement Count'] -= 1
                # adjust upkeep manager
                total_dedicated_upkeep = float(upkeep_manager_list[3])
                total_dedicated_upkeep -= unit_upkeep
                upkeep_manager_list[3] = core.round_total_income(total_dedicated_upkeep)
                dedicated_oil_upkeep = float(upkeep_manager_list[1])
                dedicated_oil_upkeep -= unit_upkeep
                upkeep_manager_list[1] = core.round_total_income(dedicated_oil_upkeep)
    while coal_stockpile < 0:
        for improvement_name in energy_upkeep_dict:
            improvement_upkeep = energy_upkeep_dict[improvement_name]['Improvement Upkeep']
            while energy_upkeep_dict[improvement_name]['Improvement Count'] > 0:
                # destroy random improvement of that type
                region_id = core.search_and_destroy(game_id, player_id, improvement_name)
                notifications.append(f'{nation_name} lost a {improvement_name} in {region_id} due to coal shortages.', 6)
                coal_stockpile += improvement_upkeep
                energy_upkeep_dict[improvement_name]['Improvement Count'] -= 1
                # adjust upkeep manager
                total_dedicated_upkeep = float(upkeep_manager_list[3])
                total_dedicated_upkeep -= improvement_upkeep
                upkeep_manager_list[3] = core.round_total_income(total_dedicated_upkeep)
                dedicated_coal_upkeep = float(upkeep_manager_list[0])
                dedicated_coal_upkeep -= improvement_upkeep
                upkeep_manager_list[0] = core.round_total_income(dedicated_coal_upkeep)
    while green_stockpile < 0:
        for improvement_name in energy_upkeep_dict:
            improvement_upkeep = energy_upkeep_dict[improvement_name]['Improvement Upkeep']
            while energy_upkeep_dict[improvement_name]['Improvement Count'] > 0:
                # destroy random improvement of that type
                region_id = core.search_and_destroy(game_id, player_id, improvement_name)
                notifications.append(f'{nation_name} lost a {improvement_name} in {region_id} due to green energy shortages.', 6)
                green_stockpile += improvement_upkeep
                energy_upkeep_dict[improvement_name]['Improvement Count'] -= 1
                # adjust upkeep manager
                total_dedicated_upkeep = float(upkeep_manager_list[3])
                total_dedicated_upkeep -= improvement_upkeep
                upkeep_manager_list[3] = core.round_total_income(total_dedicated_upkeep)
                dedicated_green_upkeep = float(upkeep_manager_list[2])
                dedicated_green_upkeep -= improvement_upkeep
                upkeep_manager_list[2] = core.round_total_income(dedicated_green_upkeep)


    # Resolve Dollars Shortages
    while dollars_stockpile < 0:
        for improvement_name in dollars_upkeep_dict:
            improvement_upkeep = dollars_upkeep_dict[improvement_name]['Improvement Upkeep']
            while dollars_upkeep_dict[improvement_name]['Improvement Count'] > 0:
                region_id = core.search_and_destroy(game_id, player_id, improvement_name)
                notifications.append(f'{nation_name} lost a {improvement_name} in {region_id} due to dollars shortages.', 6)
                dollars_stockpile += improvement_upkeep
                dollars_upkeep_dict[improvement_name]['Improvement Count'] -= 1
        for unit_name in dollars_unit_upkeep_dict:
            unit_upkeep = dollars_unit_upkeep_dict[unit_name]['Improvement Upkeep']
            while dollars_unit_upkeep_dict[unit_name]['Improvement Count'] > 0:
                region_id = core.search_and_destroy_unit(game_id, player_id, unit_name)
                notifications.append(f'{nation_name} lost a {unit_name} in {region_id} due to dollars shortages.', 6)
                dollars_stockpile += unit_upkeep
                dollars_unit_upkeep_dict[unit_name]['Improvement Count'] -= 1
        # escape hatch because dollars income is allowed to be negative
        if dollars_stockpile < 0:
            break
    
    
    # Update playerdata.csv
    stockpile_list = [dollars_stockpile, coal_stockpile, oil_stockpile, green_stockpile]
    for i, stockpile in enumerate(stockpile_list):
        stockpile = core.round_total_income(stockpile)
        economy_masterlist[player_id - 1][i][0] = stockpile
    for economy_list in economy_masterlist:
        for resource_data_list in economy_list:
            resource_data_list = str(resource_data_list)
    for i, playerdata in enumerate(playerdata_list):
        playerdata[9] = economy_masterlist[i][0]
        playerdata[12] = economy_masterlist[i][1]
        playerdata[13] = economy_masterlist[i][2]
        playerdata[14] = economy_masterlist[i][3]
    with open(playerdata_filepath, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(core.player_data_header)
        writer.writerows(playerdata_list)

def gain_resource_market_income(game_id, player_id, player_resource_market_incomes):
    '''Applies the resources gained/lost from resource market activities to player stockpiles.'''
    
    #define core lists
    playerdata_filepath = f'gamedata/{game_id}/playerdata.csv'
    playerdata_list = core.read_file(playerdata_filepath, 1)
    with open('active_games.json', 'r') as json_file:
        active_games_dict = json.load(json_file)

    #get needed economy information from each player
    nation_name_list = []
    for playerdata in playerdata_list:
        nation_name_list.append(playerdata[1])
    request_list = ['Dollars', 'Technology', 'Coal', 'Oil', 'Basic Materials', 'Common Metals', 'Advanced Metals', 'Uranium', 'Rare Earth Elements']
    economy_masterlist = core.get_economy_info(playerdata_list, request_list)


    #Apply Resource Market Income
    resource_market_income = player_resource_market_incomes[player_id - 1]

    #get resource stockpile data
    stockpile_list = []
    stockpile_limit_list = []
    for i in range(len(request_list)):
        stockpile_list.append(economy_masterlist[player_id - 1][i][0])
        stockpile_limit_list.append(economy_masterlist[player_id - 1][i][1])

    #update stockpiles and statistics file
    for i, stockpile in enumerate(stockpile_list):
        if resource_market_income[i] > 0:
            #update stockpile of resource
            stockpile = float(stockpile)
            stockpile += resource_market_income[i]
            if stockpile > stockpile_limit_list[i]:
                stockpile = stockpile_limit_list[i]
            stockpile = core.round_total_income(stockpile)
            economy_masterlist[player_id - 1][i][0] = stockpile
            #update statistics
            if i != 0:
                transactions_dict = active_games_dict[game_id]["Transactions Record"]
                transactions_dict[nation_name_list[player_id - 1]] += resource_market_income[i]


    #Update playerdata.csv
    for economy_list in economy_masterlist:
        for resource_data_list in economy_list:
            resource_data_list = str(resource_data_list)
    i = 0
    for playerdata in playerdata_list:
        playerdata[9] = economy_masterlist[i][0]
        playerdata[11] = economy_masterlist[i][1]
        playerdata[12] = economy_masterlist[i][2]
        playerdata[13] = economy_masterlist[i][3]
        playerdata[15] = economy_masterlist[i][4]
        playerdata[16] = economy_masterlist[i][5]
        playerdata[17] = economy_masterlist[i][6]
        playerdata[18] = economy_masterlist[i][7]
        playerdata[19] = economy_masterlist[i][8]
        i += 1
    with open(playerdata_filepath, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(core.player_data_header)
        writer.writerows(playerdata_list)

def update_records(game_id, current_turn_num):
    '''Updates the four records that are saved in a file.'''
    playerdata_filepath = f'gamedata/{game_id}/playerdata.csv'
    playerdata_list = core.read_file(playerdata_filepath, 0)
    largest_military_filepath = f'gamedata/{game_id}/largest_military.csv'
    largest_nation_filepath = f'gamedata/{game_id}/largest_nation.csv'
    most_research_filepath = f'gamedata/{game_id}/most_research.csv'
    strongest_economy_filepath = f'gamedata/{game_id}/strongest_economy.csv'
    largest_military_list = core.read_file(largest_military_filepath, 0)
    largest_nation_list = core.read_file(largest_nation_filepath, 0)
    most_research_list = core.read_file(most_research_filepath, 0)
    strongest_economy_list = core.read_file(strongest_economy_filepath, 0)
    player_count = len(playerdata_list)

    #update largest military record
    for index, entry in enumerate(largest_military_list):
        if index == 0:
            entry.append(current_turn_num)
            continue
        player_military_capacity_data = playerdata_list[index][5]
        used_mc, total_mc = core.read_military_capacity(player_military_capacity_data)
        entry.append(used_mc)
    
    #update largest nation record
    for index, entry in enumerate(largest_nation_list):
        if index == 0:
            entry.append(current_turn_num)
            continue
        player_misc_info = ast.literal_eval(playerdata_list[index][24])
        region_count_str = player_misc_info[1][-2:]
        region_count = region_count_str.strip()
        occupied_count_str = player_misc_info[2][-2:]
        occupied_count = occupied_count_str.strip()
        entry.append(str(int(region_count) + int(occupied_count)))

    #update most research record
    for index, entry in enumerate(most_research_list):
        if index == 0:
            entry.append(current_turn_num)
            continue
        player_research_list = ast.literal_eval(playerdata_list[index][26])
        player_research_count = len(player_research_list)
        agenda_data_dict = core.get_scenario_dict(game_id, "Agendas")
        for completed_research in player_research_list:
            if completed_research in list(agenda_data_dict.keys()):
                player_research_count -= 1
        entry.append(player_research_count)

    #update strongest economy record
    for index, entry in enumerate(strongest_economy_list):
        if index == 0:
            entry.append(current_turn_num)
            continue
        playerdata = playerdata_list[index]
        player_income = 0
        j = 9
        while j < 20:
            resource_data = ast.literal_eval(playerdata[j])
            resource_income = float(resource_data[2])
            player_income += resource_income
            j += 1
        player_income = core.round_total_income(player_income)
        entry.append(player_income)

    #save records
    filepath_list = [largest_military_filepath, largest_nation_filepath, most_research_filepath, strongest_economy_filepath]
    record_list = [largest_military_list, largest_nation_list, most_research_list, strongest_economy_list]
    for index, filepath in enumerate(filepath_list):
        with open(filepath, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerows(record_list[index])

def get_top_three(game_id, record_name, display_values):
    '''
    Returns the top three of a recorded record.
    TO-DO: Move this function to core.
    '''

    #get core lists
    playerdata_filepath = f'gamedata/{game_id}/playerdata.csv'
    playerdata_list = core.read_file(playerdata_filepath, 1)
    record_filepath = f'gamedata/{game_id}/{record_name}.csv'
    record_list = core.read_file(record_filepath, 0)

    #get nation names
    nation_name_list = []
    for playerdata in playerdata_list:
        nation_name_list.append(playerdata[1])
    
    #get top three
    candidates = []
    for index, record in enumerate(record_list):
        if index == 0:
            continue
        if record_name == 'strongest_economy':
            value = float(record[-1])
        else:
            value = int(record[-1])
        nation_name = nation_name_list[index - 1]
        candidates.append([nation_name, value])
    sorted_candidates = sorted(candidates, key = lambda x: x[-1], reverse = True)
    if display_values:
        first_place = f'1. {sorted_candidates[0][0]} ({sorted_candidates[0][1]})'
        second_place = f'2. {sorted_candidates[1][0]} ({sorted_candidates[1][1]})'
        third_place = f'3. {sorted_candidates[2][0]} ({sorted_candidates[2][1]})'
    else:
        first_place = f'1. {sorted_candidates[0][0]}'
        second_place = f'2. {sorted_candidates[1][0]}'
        third_place = f'3. {sorted_candidates[2][0]}'

    return first_place, second_place, third_place

def check_top_three(top_three_list):
    
    scores = []
    for entry in top_three_list:
        pattern = r'\((.*?)\)'
        match = re.search(pattern, entry)
        if match:
            scores.append(match.group(1))
        else:
            scores.append("")
    
    if scores[0] == scores[1] and scores[0] == scores[2]:
        bool_list = [False, False, False]
    elif scores[0] == scores[1]:
        bool_list = [False, False, False]
    elif scores[1] == scores[2]:
        bool_list = [True, False, False]
    else:
        bool_list = [True, True, True]
    
    for index, score in enumerate(scores):
        if score == '0':
            bool_list[index] = False

    return bool_list

def check_victory_conditions(game_id, player_id, current_turn_num):
    '''Checks victory conditions of a player.'''
    
    # get game data
    playerdata_filepath = f'gamedata/{game_id}/playerdata.csv'
    rmdata_filepath = f'gamedata/{game_id}/rmdata.csv'
    playerdata_list = core.read_file(playerdata_filepath, 1)
    rmdata_all_transaction_list = core.read_rmdata(rmdata_filepath, current_turn_num, False, False)
    wardata = WarData(game_id)
    improvement_data_dict = core.get_scenario_dict(game_id, "Improvements")
    improvement_name_list = sorted(improvement_data_dict.keys())
    with open(f'gamedata/{game_id}/regdata.json', 'r') as json_file:
        regdata_dict = json.load(json_file)
    with open(f'gamedata/{game_id}/vc_overrides.json', 'r') as json_file:
        vc_overrides_dict = json.load(json_file)

    nation_name_masterlist = []
    for playerdata in playerdata_list:
        nation_name_masterlist.append(playerdata[1])

    # get needed information from player
    playerdata = playerdata_list[player_id - 1]
    victory_conditions_list = ast.literal_eval(playerdata[8])
    nation_name = playerdata[1]
    economy_data_list = []
    j = 9
    while j < 20:
        resource_data = ast.literal_eval(playerdata[j])
        economy_data_list.append(resource_data)
        j += 1
    completed_research_list = ast.literal_eval(playerdata[26])
    improvement_count_list = ast.literal_eval(playerdata[27])

    
    #Check Easy Victory Condition
    vc_1_completed = False
    victory_condition_1 = victory_conditions_list[0]
    match victory_condition_1:
        case 'Energy Economy':
            coal_mine_index = improvement_name_list.index('Coal Mine')
            strip_mine_index = improvement_name_list.index('Strip Mine')
            oil_well_index = improvement_name_list.index('Oil Well')
            oil_refinery_index = improvement_name_list.index('Oil Refinery')
            energy_economy_count_list = []
            for player in playerdata_list:
                temp_improvement_count_list = ast.literal_eval(player[27])
                score = 0
                for improvement_index in range(len(temp_improvement_count_list)):
                    if improvement_index in [coal_mine_index, strip_mine_index, oil_well_index, oil_refinery_index]: 
                        score += temp_improvement_count_list[improvement_index]
                energy_economy_count_list.append(score)
            greatest_count = 0
            greatest_count_player_id = []
            for j, count in enumerate(energy_economy_count_list):
                if count > greatest_count:
                    greatest_count = count
                    greatest_count_player_id = [j + 1]
                elif count == greatest_count:
                    greatest_count_player_id.append(j + 1)
            if len(greatest_count_player_id) == 1 and player_id in greatest_count_player_id:
                vc_1_completed = True
        case 'Dual Loyalty':
            pass
        case 'Major Exporter':
            export_count = 0
            for transaction in rmdata_all_transaction_list:
                if transaction[1] == nation_name and transaction[2] == "Sold":
                    export_count += int(transaction[3])
            if export_count >= 100:
                vc_1_completed = True
        case 'Reconstruction Effort':
            improvement_index = improvement_name_list.index('City')
            city_count_list = []
            for player in playerdata_list:
                temp_improvement_count_list = ast.literal_eval(player[27])
                city_count = temp_improvement_count_list[improvement_index]
                city_count_list.append(city_count)
            greatest_count = 0
            greatest_count_player_id = []
            for j, count in enumerate(city_count_list):
                if count > greatest_count:
                    greatest_count = count
                    greatest_count_player_id = [j + 1]
                elif count == greatest_count:
                    greatest_count_player_id.append(j + 1)
            if len(greatest_count_player_id) == 1 and player_id in greatest_count_player_id:
                vc_1_completed = True
        case 'Secure Strategic Resources':
            player_has_advanced = False
            player_has_uranium = False
            player_has_rare = False
            for region_id in regdata_dict:
                region = Region(region_id, game_id)
                owner_id = region.owner_id
                region_resource = region.resource
                if owner_id == player_id and region_resource == 'Advanced Metals':
                    player_has_advanced = True
                elif owner_id == player_id and region_resource == 'Uranium':
                    player_has_uranium = True
                elif owner_id == player_id and region_resource == 'Rare Earth Elements':
                    player_has_rare = True
            if player_has_advanced and player_has_uranium and player_has_rare:
                vc_1_completed = True
        case 'Tight Leash':
            player_tight_leash_score = vc_overrides_dict['Tight Leash'][player_id - 1]
            if player_tight_leash_score >= 1:
                vc_1_completed = True


    #Check Normal Victory Condition
    vc_2_completed = False
    victory_condition_2 = victory_conditions_list[1]
    match victory_condition_2:
        case 'Establish Sovereignty':
            improvement_index = improvement_name_list.index('Capital')
            improvement_count = improvement_count_list[improvement_index]
            if improvement_count >= 2:
                vc_2_completed = True
            if wardata.query(nation_name, 'Main', 'Defender', 'Defender Victory'):
                vc_2_completed = True
        case 'Diversified Army':
            unit_types_found = []
            for region_id in regdata_dict:
                region_unit = Unit(region_id, game_id)
                if region_unit.name != None and region_unit.owner_id == player_id:
                    if region_unit.name not in unit_types_found:
                        unit_types_found.append(region_unit.name)
            if len(unit_types_found) >= 5:
                vc_2_completed = True
        case 'Diversified Economy':
            non_zero_count = 0
            for improvement_count in improvement_count_list:
                if improvement_count > 0:
                    non_zero_count += 1
            if non_zero_count >= 12:
                vc_2_completed = True
        case 'Hegemony':
            puppet_str = f'{nation_name} Puppet State'
            for player in playerdata_list:
                status_str = player[28]
                if puppet_str == status_str:
                    vc_2_completed = True
                    break
        case 'Reliable Ally':
            pass
        case 'Road to Recovery':
            player_road_to_recovery_bool = vc_overrides_dict['Road to Recovery'][player_id - 1]
            if player_road_to_recovery_bool:
                vc_2_completed = True
    
    
    #Check Hard Victory Condition
    vc_3_completed = False
    victory_condition_3 = victory_conditions_list[2]
    match victory_condition_3:
        case 'Economic Domination':
            economy_1st, economy_2nd, economy_3rd =  get_top_three(game_id, 'strongest_economy', True)
            if nation_name in economy_1st and (economy_1st[-6:] != economy_2nd[-6:]):
                vc_3_completed = True
        case 'Empire Building':
            size_1st, size_2nd, size_3rd =  get_top_three(game_id, 'largest_nation', True)
            if nation_name in size_1st and (size_1st[-4:] != size_2nd[-4:]):
                vc_3_completed = True
        case 'Military Superpower':
            military_1st, military_2nd, military_3rd =  get_top_three(game_id, 'largest_military', True)
            if nation_name in military_1st and (military_1st[-4:] != military_2nd[-4:]):
                vc_3_completed = True
        case 'Nuclear Deterrent':
            most_nukes_value = 0
            most_nukes_player_ids = []
            for index, player in enumerate(playerdata_list):
                temp_missile_data = ast.literal_eval(player[21])
                temp_nuke_storage = temp_missile_data[1]
                if temp_nuke_storage > most_nukes_value:
                    most_nukes_value = temp_nuke_storage
                    most_nukes_player_ids = [index + 1]
                elif temp_nuke_storage == most_nukes_value:
                    most_nukes_player_ids.append(index + 1)
            if len(most_nukes_player_ids) == 1 and player_id in most_nukes_player_ids:
                vc_3_completed = True
        case 'Scientific Leader':
            research_1st, research_2nd, research_3rd =  get_top_three(game_id, 'most_research', True)
            if nation_name in research_1st and (research_1st[-4:] != research_2nd[-4:]):
                vc_3_completed = True
        case 'Sphere of Influence':
            agenda_count = 0
            agenda_data_dict = core.get_scenario_dict(game_id, "Agendas")
            for research_name in completed_research_list:
                if research_name in agenda_data_dict:
                    agenda_count += 1
            if agenda_count >= 8:
                vc_3_completed = True


    #Update vc_extra.csv and return vc score
    with open(f'gamedata/{game_id}/vc_overrides.json', 'w') as json_file:
        json.dump(vc_overrides_dict, json_file, indent=4)
    result = [vc_1_completed, vc_2_completed, vc_3_completed]

    return result

def bonus_phase_heals(player_id, game_id):
    '''
    Heals all units and defensive improvements by 2 health.
    '''
    wardata = WarData(game_id)
    playerdata_filepath = f'gamedata/{game_id}/playerdata.csv'
    playerdata_list = core.read_file(playerdata_filepath, 1)
    with open(f'gamedata/{game_id}/regdata.json', 'r') as json_file:
        regdata_dict = json.load(json_file)

    playerdata = playerdata_list[player_id - 1]
    player_research_list = ast.literal_eval(playerdata[26])
    
    for region_id in regdata_dict:
        region = Region(region_id, game_id)
        region_improvement = Improvement(region_id, game_id)
        region_unit = Unit(region_id, game_id)
        
        # unit heal checks
        heal_allowed = False
        if region_unit.name == 'Special Forces':
            heal_allowed = True
        elif "Scorched Earth" in player_research_list:
            heal_allowed = True
        elif region.owner_id == region_unit.owner_id:
            heal_allowed = True
        else:
            for adjacent_region_id in region.adjacent_regions:
                adjacent_region_unit = Unit(adjacent_region_id, game_id)
                if adjacent_region_unit.owner_id == region_unit.owner_id:
                    heal_allowed = True

        # heal unit or improvement
        if region.owner_id != 0 and region_improvement.name != None and region_improvement.health != 99:
            region_improvement.heal(2)
            if 'Peacetime Recovery' in player_research_list and wardata.is_at_peace(player_id):
                region_improvement.heal(100)
        unit_name = region_unit.name
        if unit_name != None and heal_allowed:
            region_unit.heal(2)
            if 'Peacetime Recovery' in player_research_list and wardata.is_at_peace(player_id):
                region_unit.heal(100)

def prompt_for_missing_war_justifications(game_id):
    '''
    Prompts in terminal when a war justification has not been entered for an ongoing war.

    :param game_id: The full game_id of the active game.
    '''
    wardata = WarData(game_id)

    for war_name, war_data in wardata.wardata_dict.items():
        if war_data["outcome"] == "TBD":
            wardata.add_missing_war_justifications(war_name)

def total_occupation_forced_surrender(game_id: str) -> None:
    """
    Forces a player to surrender if they are totally occupied.

    Params:
        game_id (str): Game ID string.
    """
    
    # get core lists
    wardata = WarData(game_id)
    notifications = Notifications(game_id)
    playerdata_filepath = f'gamedata/{game_id}/playerdata.csv'
    playerdata_list = core.read_file(playerdata_filepath, 1)
    nation_name_list = []
    for playerdata in playerdata_list:
        nation_name_list.append(playerdata[1])
    diplomatic_relations_masterlist = []
    for player in playerdata_list:
        diplomatic_relations_masterlist.append(ast.literal_eval(player[22]))
    with open(f'gamedata/{game_id}/regdata.json', 'r') as json_file:
        regdata_dict = json.load(json_file)

    # check all regions for occupation
    non_occupied_found_list = [False] * len(playerdata_list)
    for region_id in regdata_dict:
        region = Region(region_id, game_id)
        owner_id = region.owner_id
        if owner_id != 0 and owner_id != 99 and region.occupier_id == 0:
            non_occupied_found_list[owner_id - 1] = True
    
    # if no unoccupied region found for a player force surrender if main combatant
    for index, region_found in enumerate(non_occupied_found_list):
        player_id_1 = index + 1
        nation_name_1 = nation_name_list[player_id_1 - 1]
        if not region_found:
            #look for wars to surrender to
            for war_name, war_data in wardata.wardata_dict.items():
                combatant_dict = war_data["combatants"]
                if war_data["outcome"] == "TBD" and nation_name_1 in combatant_dict and 'Main' in combatant_dict[nation_name_1]["role"]:
                    war_role_1 = combatant_dict[nation_name_1]["role"]
                    for nation_name in combatant_dict:
                        if 'Main' in combatant_dict[nation_name]["role"] and war_role_1 != combatant_dict[nation_name]["role"]:
                            nation_name_2 = nation_name
                            war_role_2 = combatant_dict[nation_name_2]["role"]
                            break
                    # process surrender
                    if 'Attacker' in war_role_1:
                        outcome = 'Attacker Victory'
                    else:
                        outcome = 'Defender Victory'
                    wardata.end_war(war_name, outcome)
                    notifications.append(f'{nation_name_1} surrendered to {nation_name_2}.', 4)
                    notifications.append(f'{war_name} has ended due to total occupation.', 4)

    # update playerdata.csv
    for index, player in enumerate(playerdata_list):
        player[22] = str(diplomatic_relations_masterlist[index])
    with open(playerdata_filepath, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(core.player_data_header)
        writer.writerows(playerdata_list)

def war_score_forced_surrender(game_id: str) -> None:
    """
    Forces a side to surrender if critical war score difference reached.

    Params:
        game_id (str): Game ID string.
    """

    # get core lists
    wardata = WarData(game_id)
    notifications = Notifications(game_id)
    playerdata_filepath = f'gamedata/{game_id}/playerdata.csv'
    playerdata_list = core.read_file(playerdata_filepath, 1)
    nation_name_list = []
    for playerdata in playerdata_list:
        nation_name_list.append(playerdata[1])
    diplomatic_relations_masterlist = []
    for player in playerdata_list:
        diplomatic_relations_masterlist.append(ast.literal_eval(player[22]))

    for war_name, war_data in wardata.wardata_dict.items():
        if war_data["outcome"] == "TBD":
        
            # get war score information
            attacker_war_score = war_data["attackerWarScore"]["total"]
            defender_war_score = war_data["defenderWarScore"]["total"]
            attacker_threshold, defender_threshold = wardata.calculate_score_threshold(war_name)
            ma_name, md_name = wardata.get_main_combatants(war_name)

            # end war if a threshold was met
            if attacker_threshold and attacker_war_score >= attacker_threshold:
                wardata.end_war(war_name, "Attacker Victory")
                notifications.append(f'{md_name} surrendered to {ma_name}.', 4)
                notifications.append(f'{war_name} has ended due to war score.', 4)
            elif defender_threshold and defender_war_score >= defender_threshold:
                wardata.end_war(war_name, "Defender Victory")
                notifications.append(f'{ma_name} surrendered to {md_name}.', 4)
                notifications.append(f'{war_name} has ended due to war score.', 4)

    # update playerdata.csv
    for index, player in enumerate(playerdata_list):
        player[22] = str(diplomatic_relations_masterlist[index])
    with open(playerdata_filepath, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(core.player_data_header)
        writer.writerows(playerdata_list)

def prune_alliances(game_id: str) -> None:
    """
    Ends all alliances that have less than 2 members.

    Params:
        game_id (str): Game ID string.
    """

    alliance_table = AllianceTable(game_id)
    notifications = Notifications(game_id)

    for alliance in alliance_table:
        if len(alliance.current_members) < 2:
            alliance.end()
            alliance_table.save(alliance)
            notifications.append(f"{alliance.name} has dissolved.", 7)
    

#UPDATE INCOME HELPER FUNCTIONS
def update_gross_income_masterlist(gross_income_masterlist, player_id, index, income, remnant_multiplier):
    gross_income_masterlist[player_id - 1][index] += income * remnant_multiplier
    return gross_income_masterlist

def update_income_strings_masterlist(income_strings_masterlist, player_id, index, income, remnant_multiplier, plural_improvement_name):
    income_strings_masterlist[player_id - 1][index] += [f'&Tab;+{income * remnant_multiplier} from {plural_improvement_name}']
    return income_strings_masterlist
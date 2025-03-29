#STANDARD IMPORTS
import ast
import copy
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
from app.nationdata import NationTable
from app.nationdata import Nation
from app.alliance import AllianceTable

#END OF TURN CHECKS

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

def update_trade_tax(game_id: str, player_id: int) -> None:
    """
    Calculate's a player's trade tax.
    """
    
    playerdata_filepath = f'gamedata/{game_id}/playerdata.csv'
    playerdata_list = core.read_file(playerdata_filepath, 1)
    with open('active_games.json', 'r') as json_file:
        active_games_dict = json.load(json_file)

    trade_index = 3
    trade_fee_list = ["1:5","1:4", "1:3", "1:2", "1:1", "2:1", "3:1"]
    # dollars : resources
    player_name = playerdata_list[player_id - 1][1]
    player_research = ast.literal_eval(playerdata_list[player_id - 1][26])

    # check if Improved Logistics in player research
    if 'Improved Logistics' in player_research:
        trade_index -= 1
    # if threat containment applies to target nation count it
    if "Threat Containment" in active_games_dict[game_id]["Active Events"]:
        if active_games_dict[game_id]["Active Events"]["Threat Containment"]["Chosen Nation Name"] == player_name:
            trade_index += 1

    trade_tax_str = trade_fee_list[trade_index]
    playerdata_list[player_id - 1][6] = trade_tax_str
    
    with open(playerdata_filepath, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(core.player_data_header)
        writer.writerows(playerdata_list)

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

def update_income(game_id: str) -> None:
    """
    Updates the incomes of all players and saves results to playerdata.

    Params:
        game_id (str): Game ID string.

    Returns:
        None
    """
    
    # get game data
    nation_table = NationTable(game_id)
    alliance_table = AllianceTable(game_id)
    with open(f"gamedata/{game_id}/regdata.json", 'r') as json_file:
        regdata_dict = json.load(json_file)
    with open("active_games.json", 'r') as json_file:
        active_games_dict = json.load(json_file)

    # reset gross income and create dict for tracking income strings
    text_dict = {}
    for nation in nation_table:
        text_dict[nation.name] = {}
        for resource_name in nation._resources:
            text_dict[nation.name][resource_name] = {}
            if resource_name == "Military Capacity":
                nation.update_used_mc(0.00, overwrite=True)
                nation.update_max_mc(0.00, overwrite=True)
            else:
                nation.update_gross_income(resource_name, 0.00, overwrite=True)
        nation_table.save(nation)

    # create dicts for tracking improvement yields and upkeep costs
    yield_dict = {}
    upkeep_dict = {}
    for nation in nation_table:
        yield_dict[nation.name] = core.create_player_yield_dict(game_id, nation)
        upkeep_dict[nation.name] = core.create_player_upkeep_dict(game_id, nation)


    ### calculate gross income ###

    # add income from regions
    for region_id in regdata_dict:
        region = Region(region_id, game_id)
        region_improvement = Improvement(region_id, game_id)
        region_unit = Unit(region_id, game_id)
        # skip if region is unowned or region is empty
        if region.owner_id == 0 or region.owner_id == 99:
            continue
        if region_improvement.name is None and region_unit.name is None:
            continue
        # add improvement yields
        if region_improvement.name is not None and region.occupier_id == 0:
            if region_improvement.name[-1] != 'y':
                plural_improvement_name = f'{region_improvement.name}s'
            else:
                plural_improvement_name = f'{region_improvement.name[:-1]}ies'
            nation = nation_table.get(region.owner_id)
            improvement_income_dict = yield_dict[nation.name][region_improvement.name]
            improvement_yield_dict = region_improvement.calculate_yield(copy.deepcopy(improvement_income_dict))
            for resource_name, amount_gained in improvement_yield_dict.items():
                if amount_gained != 0:
                    nation.update_gross_income(resource_name, amount_gained)
                    income_str = f'&Tab;+{amount_gained:.2f} from {plural_improvement_name}'
                    _update_text_dict(text_dict, nation.name, resource_name, income_str)
                    nation_table.save(nation)
        # add unit military capacity cost
        if region_unit.name is not None:
            nation = nation_table.get(region_unit.owner_id)
            nation.update_used_mc(1.00)
            if nation.gov == "Military Junta":
                nation.update_gross_income("Political Power", 0.1)
                income_str = "&Tab;+0.10 from Military Junta bonus."
                _update_text_dict(text_dict, nation.name, "Political Power", income_str)
                nation_table.save(nation)

    # political power income from alliances
    for nation in nation_table:
        alliance_count, alliance_capacity = core.get_alliance_count(game_id, nation)
        if 'Power Broker' in nation.completed_research:
            alliance_income = 0.75
        else:
            alliance_income = 0.5
        if alliance_income * alliance_count == 0:
            continue
        nation.update_gross_income("Political Power", alliance_income * alliance_count)
        for i in range(alliance_count):
            income_str = f'&Tab;+{alliance_income:.2f} from alliances'
            _update_text_dict(text_dict, nation.name, "Political Power", income_str)
        nation_table.save(nation)

    # political power from events
    for nation in nation_table:
        if "Faustian Bargain" in active_games_dict[game_id]["Active Events"]:
            chosen_nation_name = active_games_dict[game_id]["Active Events"]["Faustian Bargain"]["Chosen Nation Name"]
            if nation.name != chosen_nation_name:
                continue
            pp_from_lease = 0.2 * len(active_games_dict[game_id]["Active Events"]["Faustian Bargain"]["Leased Regions List"])
            if pp_from_lease != 0:
                nation.update_gross_income("Political Power", pp_from_lease)
                income_str = f'+{pp_from_lease:.2f} from events.'
                _update_text_dict(text_dict, nation.name, "Political Power", income_str)
                nation_table.save(nation)

    # dollars from trade agreements
    for alliance in alliance_table:
        if not alliance.is_active or alliance.type != "Trade Agreement":
            continue
        total = 0.0
        for ally_name in alliance.current_members:
            nation = nation_table.get(ally_name)
            total += nation.improvement_counts["City"]
            total += nation.improvement_counts["Central Bank"]
            total += nation.improvement_counts["Capital"]
        if total == 0.0:
            continue
        for ally_name in alliance.current_members:
            nation = nation_table.get(ally_name)
            trade_agreement_yield = total * 0.5
            nation.update_gross_income("Dollars", trade_agreement_yield)
            income_str = f'&Tab;+{trade_agreement_yield:.2f} from {alliance.name}.'
            _update_text_dict(text_dict, nation.name, "Dollars", income_str)
            nation_table.save(nation)

    # tech from research agreements
    for alliance in alliance_table:
        if not alliance.is_active or alliance.type != "Research Agreement":
            continue
        tech_set = set()
        for ally_name in alliance.current_members:
            nation = nation_table.get(ally_name)
            ally_research_list = list(nation.completed_research.keys())
            tech_set.update(ally_research_list)
        if len(tech_set) == 0:
            continue
        for ally_name in alliance.current_members:
            nation = nation_table.get(ally_name)
            research_agreement_yield = len(tech_set) * 0.2
            nation.update_gross_income("Technology", research_agreement_yield)
            income_str = f'&Tab;+{research_agreement_yield:.2f} from {alliance.name}.'
            _update_text_dict(text_dict, nation.name, "Technology", income_str)
            nation_table.save(nation)

    # military capacity from defense agreements
    for nation in nation_table:
        for alliance in alliance_table:
            if alliance.is_active and nation.name in alliance.current_members and alliance.type == "Defense Agreement":
                defense_agreement_yield = len(alliance.current_members)
                nation.update_max_mc(defense_agreement_yield)
                income_str = f'+{len(alliance.current_members)} from {alliance.name}.'
                _update_text_dict(text_dict, nation.name, "Military Capacity", income_str)
                nation_table.save(nation)

    # military capacity from other sources
    if "Threat Containment" in active_games_dict[game_id]["Active Events"]:
        for nation in nation_table:
            if active_games_dict[game_id]["Active Events"]["Threat Containment"]["Chosen Nation Name"] == nation.name:
                nation.update_rate("Military Capacity", -20)
                nation_table.save(nation)
        
    # apply income rate to gross income
    for nation in nation_table:
        for resource_name in nation._resources:
            total = float(nation.get_gross_income(resource_name))
            rate = float(nation.get_rate(resource_name)) / 100
            final_total = total * rate
            final_total = round(final_total, 2)
            rate_diff = round(final_total - total, 2)
            if rate_diff > 0:
                income_str = f'&Tab;+{rate_diff:.2f} from income rate.'
                _update_text_dict(text_dict, nation.name, resource_name, income_str)
            elif rate_diff < 0:
                income_str = f'&Tab;{rate_diff:.2f} from income rate.'
                _update_text_dict(text_dict, nation.name, resource_name, income_str)
            nation.update_gross_income(resource_name, final_total, overwrite=True)
        nation_table.save(nation)
    

    ### calculate net income ###

    # reset income
    for nation in nation_table:
        for resource_name in nation._resources:
            gross_income = float(nation.get_gross_income(resource_name))
            nation.update_income(resource_name, gross_income, overwrite=True)
        nation_table.save(nation)

    for nation in nation_table:
        
        # account for puppet state dues
        if 'Puppet State' in nation.status:
            for temp in nation_table:
                if temp in nation.status:
                    overlord = temp
                    break
            for resource_name in nation._resources:
                if resource_name == "Military Capacity":
                    continue
                tax_amount = nation.get_gross_income(resource_name) * 0.2
                tax_amount = round(tax_amount, 2)
                # take tax from puppet state
                nation.update_income(resource_name, -1 * tax_amount)
                income_str = f"&Tab;-{tax_amount:.2f} from puppet state tribute."
                _update_text_dict(text_dict, nation.name, resource_name, income_str)
                # give tax to overlord
                overlord.update_income(resource_name, tax_amount)
                income_str = f"&Tab;{tax_amount:.2f} from puppet state tribute."
                _update_text_dict(text_dict, overlord.name, resource_name, income_str)
                nation_table.save(overlord)

        # calculate player upkeep costs
        player_upkeep_costs_dict = {}
        upkeep_resources = ["Dollars", "Oil", "Uranium", "Energy"]
        for resource_name in upkeep_resources:
            inner_dict = {
                "From Units": core.calculate_upkeep(resource_name, upkeep_dict[nation.name], nation.unit_counts),
                "From Improvements": core.calculate_upkeep(resource_name, upkeep_dict[nation.name], nation.improvement_counts)
            }
            player_upkeep_costs_dict[resource_name] = copy.deepcopy(inner_dict)
        
        # pay non-energy upkeep
        for resource_name in upkeep_resources:
            if resource_name == "Energy":
                continue
            upkeep = player_upkeep_costs_dict[resource_name]["From Units"] + player_upkeep_costs_dict[resource_name]["From Improvements"]
            if upkeep > 0:
                nation.update_income(resource_name, -1 * upkeep)
                income_str = f'&Tab;-{upkeep:.2f} from upkeep costs.'
                _update_text_dict(text_dict, nation.name, resource_name, income_str)

        # pay energy upkeep
        energy_upkeep = player_upkeep_costs_dict["Energy"]["From Units"] + player_upkeep_costs_dict["Energy"]["From Improvements"]
        nation.update_income("Energy", -1 * energy_upkeep)
        if energy_upkeep > 0:
            income_str = f'&Tab;-{energy_upkeep:.2f} from energy upkeep costs.'
            _update_text_dict(text_dict, nation.name, resource_name, income_str)
        
        # pay energy upkeep - spend coal income if needed
        energy_income = float(nation.get_income("Energy"))
        coal_income = float(nation.get_income("Coal"))
        if energy_income < 0 and coal_income > 0:
            nation = _pay_energy(text_dict, nation, energy_income, "Coal", coal_income)
        
        # pay energy upkeep - spend oil income if needed
        energy_income = float(nation.get_income("Energy"))
        oil_income = float(nation.get_income("Oil"))
        if energy_income < 0 and oil_income > 0:
            nation = _pay_energy(text_dict, nation, energy_income, "Oil", oil_income)
        
        # pay energy upkeep - spend coal reserves if needed
        energy_income = float(nation.get_income("Energy"))
        coal_reserves = float(nation.get_stockpile("Coal"))
        if energy_income < 0 and coal_reserves > 0:
            nation = _pay_energy(text_dict, nation, energy_income, "Coal", coal_reserves, income=False)
        
        # pay energy upkeep - spend oil reserves if needed
        energy_income = float(nation.get_income("Energy"))
        oil_reserves = float(nation.get_stockpile("Oil"))
        if energy_income < 0 and coal_reserves > 0:
            nation = _pay_energy(text_dict, nation, energy_income, "Oil", oil_reserves, income=False)

        nation_table.save(nation)


    ### refine income strings ###
    
    # create strings for net incomes
    final_income_strings = {}
    for nation in nation_table:
        final_income_strings[nation.name] = {}
        for resource_name in nation._resources:
            str_list = []
            resource_total = float(nation.get_income(resource_name))
            if resource_total >= 0:
                str_list.append(f'+{resource_total:.2f} {resource_name}')
            elif resource_total < 0:
                str_list.append(f'{resource_total:.2f} {resource_name}')
            final_income_strings[nation.name][resource_name] = str_list

    # add counts
    for nation in nation_table:
        for resource_name in nation._resources:
            for income_string, count in text_dict[nation.name][resource_name].items():
                if count > 1:
                    income_string = f'{income_string} [{count}x]'
                final_income_strings[nation.name][resource_name].append(income_string)

    # save income strings
    for nation in nation_table:
        resource_string_lists = final_income_strings[nation.name]
        temp = []
        for resource_name, string_list in resource_string_lists.items():
            if len(string_list) > 1:
                temp += string_list
        nation.income_details = temp
        nation_table.save(nation)

def _update_text_dict(text_dict: dict, nation_name: str, resource_name: str, income_str: str) -> None:
    """
    Adds income string to text dictionary. Helper function for update_income().
    """
    if income_str not in text_dict[nation_name][resource_name]:
        text_dict[nation_name][resource_name][income_str] = 1
    else:
        text_dict[nation_name][resource_name][income_str] += 1

def _pay_energy(text_dict: dict, nation: Nation, energy_income: float, resouce_name: str, resource_amount: float, income=True):
    """
    Handles paying off energy upkeep. Helper function for update_income().
    """

    sum = float(energy_income) + float(resource_amount)
    if income:
        source = "income"
    else:
        source = "reserves"

    if sum > 0:
        upkeep_payment = resource_amount - sum
        nation.update_income("Energy", upkeep_payment)
        nation.update_income(resouce_name, -1 * upkeep_payment)
        income_str = f'&Tab;+{upkeep_payment:.2f} from {resouce_name.lower()} {source}.'
        _update_text_dict(text_dict, nation.name, "Energy", income_str)
        income_str = f'&Tab;-{upkeep_payment:.2f} from energy upkeep costs.'
        _update_text_dict(text_dict, nation.name, resouce_name, income_str)
    else:
        nation.update_income("Energy", resource_amount)
        nation.update_income(resouce_name, 0.00, overwrite=True)
        income_str = f'&Tab;+{resource_amount:.2f} from {resouce_name.lower()} {source}.'
        _update_text_dict(text_dict, nation.name, "Energy", income_str)
        income_str = f'&Tab;-{resource_amount:.2f} from energy upkeep costs.'
        _update_text_dict(text_dict, nation.name, resouce_name, income_str)

    return nation

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

def resolve_resource_shortages(game_id: str) -> None:
    """
    Resolves resource shortages by pruning units and improvements that cost upkeep.
    """

    # get game info
    playerdata_filepath = f'gamedata/{game_id}/playerdata.csv'
    playerdata_list = core.read_file(playerdata_filepath, 1)
    notifications = Notifications(game_id)
    unit_data_dict = core.get_scenario_dict(game_id, "Units")
    unit_name_list = sorted(unit_data_dict.keys())
    improvement_data_dict = core.get_scenario_dict(game_id, "Improvements")
    improvement_name_list = sorted(improvement_data_dict.keys())
    nation_name_list = []
    for playerdata in playerdata_list:
        nation_name_list.append(playerdata[1])
    request_list = ['Dollars', 'Coal', 'Oil', 'Green Energy', 'Uranium']

    # create dict for tracking improvement upkeep costs
    upkeep_dict = {}
    for playerdata in playerdata_list:
        nation_name = playerdata[1]
        player_id = nation_name_list.index(nation_name) + 1
        upkeep_dict[playerdata[1]] = core.create_player_upkeep_dict(player_id, game_id)

    for playerdata in playerdata_list:

        # get player information
        nation_name = playerdata[1]
        player_id = nation_name_list.index(nation_name) + 1
        economy_masterlist = core.get_economy_info(playerdata_list, request_list)
        improvement_count_list = ast.literal_eval(playerdata[27])
        unit_count_list = core.get_unit_count_list(player_id, game_id)
        upkeep_manager_list = ast.literal_eval(playerdata[23])  # 0-coal    #1-oil  #2-green    #3-total

        # temporary stopgap that turns the count lists into dicts
        player_unit_count_dict = {}
        for index, count in enumerate(unit_count_list):
            player_unit_count_dict[unit_name_list[index]] = count
        player_improvement_count_dict = {}
        for index, count in enumerate(improvement_count_list):
            player_improvement_count_dict[improvement_name_list[index]] = count

        # ignore upkeep data for improvements and units the player does not have
        player_upkeep_dict = upkeep_dict[nation_name]
        player_count_dict = player_unit_count_dict | player_improvement_count_dict
        del player_unit_count_dict
        del player_improvement_count_dict
        keys_to_remove = [name for name, count in player_count_dict.items() if count == 0]
        for name in keys_to_remove:
            if name in player_upkeep_dict:
                del player_upkeep_dict[name]

        # get resource stockpiles
        stockpile_list = []
        for i in range(len(request_list)):
            stockpile_list.append(economy_masterlist[player_id - 1][i][0])
        dollars_stockpile = float(stockpile_list[0])
        coal_stockpile = float(stockpile_list[1])
        oil_stockpile = float(stockpile_list[2])
        green_stockpile = float(stockpile_list[3])
        uranium_stockpile = float(stockpile_list[4])

        # get pool of oil consumers
        oil_consumers = []
        for target_name, resource_upkeep_dict in player_upkeep_dict.items():
            if "Oil" in resource_upkeep_dict and resource_upkeep_dict["Oil"]["Upkeep"] > 0 and resource_upkeep_dict["Oil"]["Upkeep Multiplier"] > 0:
                oil_consumers.append(target_name)
        # prune until oil shortage eliminated
        while oil_stockpile < 0 and oil_consumers != []:
            oil_consumer = random.choice(oil_consumers)
            if player_count_dict.get(oil_consumer, 0) > 0:
                consumer_upkeep = player_upkeep_dict[oil_consumer]["Oil"]["Upkeep"] * player_upkeep_dict[oil_consumer]["Oil"]["Upkeep Multiplier"]
                # destroy random consumer
                region_id = core.search_and_destroy(game_id, player_id, oil_consumer)
                notifications.append(f'{nation_name} lost a {oil_consumer} in {region_id} due to oil shortages.', 6)
                oil_stockpile += consumer_upkeep
                player_count_dict[oil_consumer] -= 1
                # adjust upkeep manager
                total_dedicated_upkeep = float(upkeep_manager_list[3])
                total_dedicated_upkeep -= consumer_upkeep
                upkeep_manager_list[3] = core.round_total_income(total_dedicated_upkeep)
                dedicated_oil_upkeep = float(upkeep_manager_list[1])
                dedicated_oil_upkeep -= consumer_upkeep
                upkeep_manager_list[1] = core.round_total_income(dedicated_oil_upkeep)
            else:
                # no more of that consumer remaining
                oil_consumers.remove(oil_consumer)
                del player_upkeep_dict[oil_consumer]

        # get pool of energy consumers
        # energy upkeep can be covered by either coal, oil, or green energy
        energy_consumers = []
        for target_name, resource_upkeep_dict in player_upkeep_dict.items():
            if "Energy" in resource_upkeep_dict and resource_upkeep_dict["Energy"]["Upkeep"] > 0 and resource_upkeep_dict["Energy"]["Upkeep Multiplier"] > 0:
                energy_consumers.append(target_name)
        for target_name, resource_upkeep_dict in player_upkeep_dict.items():
            if "Oil" in resource_upkeep_dict and resource_upkeep_dict["Oil"]["Upkeep"] > 0 and resource_upkeep_dict["Oil"]["Upkeep Multiplier"] > 0:
                energy_consumers.append(target_name)
        # prune until energy shortage eliminated
        while coal_stockpile < 0 and energy_consumers != []:
            energy_consumer = random.choice(energy_consumers)
            if player_count_dict.get(energy_consumer, 0) > 0:
                consumer_upkeep = player_upkeep_dict[energy_consumer]["Energy"]["Upkeep"] * player_upkeep_dict[energy_consumer]["Energy"]["Upkeep Multiplier"]
                # destroy random consumer
                region_id = core.search_and_destroy(game_id, player_id, energy_consumer)
                notifications.append(f'{nation_name} lost a {energy_consumer} in {region_id} due to energy shortages.', 6)
                coal_stockpile += consumer_upkeep
                player_count_dict[energy_consumer] -= 1
                # adjust upkeep manager
                total_dedicated_upkeep = float(upkeep_manager_list[3])
                total_dedicated_upkeep -= consumer_upkeep
                upkeep_manager_list[3] = core.round_total_income(total_dedicated_upkeep)
                dedicated_coal_upkeep = float(upkeep_manager_list[0])
                dedicated_coal_upkeep -= consumer_upkeep
                upkeep_manager_list[0] = core.round_total_income(dedicated_coal_upkeep)
        while oil_stockpile < 0 and energy_consumers != []:
            # if there is still oil debt, we know it is because of energy since we already pruned all exclusively oil dependent upkeep
            energy_consumer = random.choice(energy_consumers)
            if player_count_dict.get(energy_consumer, 0) > 0:
                consumer_upkeep = player_upkeep_dict[energy_consumer]["Energy"]["Upkeep"] * player_upkeep_dict[energy_consumer]["Energy"]["Upkeep Multiplier"]
                # destroy random consumer
                region_id = core.search_and_destroy(game_id, player_id, energy_consumer)
                notifications.append(f'{nation_name} lost a {energy_consumer} in {region_id} due to energy shortages.', 6)
                oil_stockpile += consumer_upkeep
                player_count_dict[energy_consumer] -= 1
                # adjust upkeep manager
                total_dedicated_upkeep = float(upkeep_manager_list[3])
                total_dedicated_upkeep -= consumer_upkeep
                upkeep_manager_list[3] = core.round_total_income(total_dedicated_upkeep)
                dedicated_oil_upkeep = float(upkeep_manager_list[1])
                dedicated_oil_upkeep -= consumer_upkeep
                upkeep_manager_list[1] = core.round_total_income(dedicated_oil_upkeep)
        while green_stockpile < 0 and energy_consumers != []:
            energy_consumer = random.choice(energy_consumers)
            if player_count_dict.get(energy_consumer, 0) > 0:
                consumer_upkeep = player_upkeep_dict[energy_consumer]["Energy"]["Upkeep"] * player_upkeep_dict[energy_consumer]["Energy"]["Upkeep Multiplier"]
                # destroy random consumer
                region_id = core.search_and_destroy(game_id, player_id, energy_consumer)
                notifications.append(f'{nation_name} lost a {energy_consumer} in {region_id} due to energy shortages.', 6)
                green_stockpile += consumer_upkeep
                player_count_dict[energy_consumer] -= 1
                # adjust upkeep manager
                total_dedicated_upkeep = float(upkeep_manager_list[3])
                total_dedicated_upkeep -= consumer_upkeep
                upkeep_manager_list[3] = core.round_total_income(total_dedicated_upkeep)
                dedicated_green_upkeep = float(upkeep_manager_list[2])
                dedicated_green_upkeep -= consumer_upkeep
                upkeep_manager_list[2] = core.round_total_income(dedicated_green_upkeep)
        
        # get pool of uranium consumers
        uranium_consumers = []
        for target_name, resource_upkeep_dict in player_upkeep_dict.items():
            if "Uranium" in resource_upkeep_dict and resource_upkeep_dict["Uranium"]["Upkeep"] > 0 and resource_upkeep_dict["Uranium"]["Upkeep Multiplier"] > 0:
                uranium_consumers.append(target_name)
        # prune until uranium shortage eliminated
        while uranium_stockpile < 0 and uranium_consumers != []:
            uranium_consumer = random.choice(uranium_consumers)
            if player_count_dict.get(uranium_consumer, 0) > 0:
                consumer_upkeep = player_upkeep_dict[uranium_consumer]["Uranium"]["Upkeep"] * player_upkeep_dict[uranium_consumer]["Uranium"]["Upkeep Multiplier"]
                # destroy random consumer
                region_id = core.search_and_destroy(game_id, player_id, uranium_consumer)
                notifications.append(f'{nation_name} lost a {uranium_consumer} in {region_id} due to uranium shortages.', 6)
                uranium_stockpile += consumer_upkeep
                player_count_dict[uranium_consumer] -= 1
            else:
                # no more of that consumer remaining
                uranium_consumers.remove(uranium_consumer)
                del player_upkeep_dict[uranium_consumer]
        
        # get pool of dollars consumers
        dollars_consumers = []
        for target_name, resource_upkeep_dict in player_upkeep_dict.items():
            if "Dollars" in resource_upkeep_dict and resource_upkeep_dict["Dollars"]["Upkeep"] > 0 and resource_upkeep_dict["Dollars"]["Upkeep Multiplier"] > 0:
                dollars_consumers.append(target_name)
        # prune until dollars shortage eliminated
        while dollars_stockpile < 0 and dollars_consumers != []:
            dollars_consumer = random.choice(dollars_consumers)
            if player_count_dict.get(dollars_consumer, 0) > 0:
                consumer_upkeep = player_upkeep_dict[dollars_consumer]["Dollars"]["Upkeep"] * player_upkeep_dict[dollars_consumer]["Dollars"]["Upkeep Multiplier"]
                # destroy random consumer
                region_id = core.search_and_destroy(game_id, player_id, dollars_consumer)
                notifications.append(f'{nation_name} lost a {dollars_consumer} in {region_id} due to dollars shortages.', 6)
                dollars_stockpile += consumer_upkeep
                player_count_dict[dollars_consumer] -= 1
            else:
                # no more of that consumer remaining
                dollars_consumers.remove(dollars_consumer)
                del player_upkeep_dict[dollars_consumer]

        # save changes to economy data
        stockpile_list = [dollars_stockpile, coal_stockpile, oil_stockpile, green_stockpile, uranium_stockpile]
        for i, stockpile in enumerate(stockpile_list):
            stockpile = core.round_total_income(stockpile)
            economy_masterlist[player_id - 1][i][0] = stockpile
        for economy_list in economy_masterlist:
            for resource_data_list in economy_list:
                resource_data_list = str(resource_data_list)

    # update playerdata.csv
    for i, playerdata in enumerate(playerdata_list):
        playerdata[9] = economy_masterlist[i][0]
        playerdata[12] = economy_masterlist[i][1]
        playerdata[13] = economy_masterlist[i][2]
        playerdata[14] = economy_masterlist[i][3]
        playerdata[18] = economy_masterlist[i][4]
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

def check_victory_conditions(game_id: str, player_id: int, current_turn_num: int) -> list:
    """
    Checks victory conditions of a player.
    """
    
    # get game info
    playerdata_filepath = f'gamedata/{game_id}/playerdata.csv'
    rmdata_filepath = f'gamedata/{game_id}/rmdata.csv'
    playerdata_list = core.read_file(playerdata_filepath, 1)
    rmdata_all_transaction_list = core.read_rmdata(rmdata_filepath, current_turn_num, False, False)
    alliance_table = AllianceTable(game_id)
    wardata = WarData(game_id)
    tech_data_dict = core.get_scenario_dict(game_id, "Technologies")
    improvement_data_dict = core.get_scenario_dict(game_id, "Improvements")
    improvement_name_list = sorted(improvement_data_dict.keys())
    with open(f'gamedata/{game_id}/regdata.json', 'r') as json_file:
        regdata_dict = json.load(json_file)
    with open(f'gamedata/{game_id}/gamedata.json', 'r') as json_file:
        gamedata_dict = json.load(json_file)
    with open(f'gamedata/{game_id}/gross_income_results.json', 'r') as json_file:
        gross_income_dict = json.load(json_file)

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
    vc_1_completed = gamedata_dict["victoryConditions"][nation_name][0]
    victory_condition_1 = victory_conditions_list[0]
    if not vc_1_completed:
        match victory_condition_1:
            
            case 'Breakthrough':
                # build set of all techs other players have researched so we can compare
                completed_research_all = set()
                for player in playerdata_list:
                    if player[1] != nation_name:
                        temp = ast.literal_eval(player[26])
                        completed_research_all.update(temp)
                # find 15 point or greater tech that is not in completed_research_all
                for tech_name in completed_research_list:
                    if (
                        tech_name in tech_data_dict
                        and tech_name not in completed_research_all
                        and tech_data_dict[tech_name]["Cost"] >= 15
                    ):
                        vc_1_completed = True
                        gamedata_dict["victoryConditions"][nation_name][0] = True    # vc is permanently fulfilled
            
            case 'Diversified Economy':
                non_zero_count = 0
                for improvement_count in improvement_count_list:
                    if improvement_count > 0:
                        non_zero_count += 1
                if non_zero_count >= 12:
                    vc_1_completed = True
            
            case 'Energy Economy':
                # get gross income sums for each nation using gross income data
                sum_dict = {}
                for temp_nation_name in nation_name_masterlist:
                    sum_dict[temp_nation_name] = 0
                for temp_nation_name, gross_data in gross_income_dict.items():
                    for resource_name, gross_income in gross_data["Total Income"].items():
                        match resource_name:
                            case "Coal" | "Oil" | "Energy":
                                sum_dict[temp_nation_name] += gross_income
                # check if nation has the greatest sum
                nation_name_sum = sum_dict[temp_nation_name]
                for temp_nation_name, sum in sum_dict.items():
                    if sum >= nation_name_sum:
                        nation_name_sum = False
                if nation_name_sum:
                    vc_1_completed = True

            case 'Industrial Focus':
                # get gross income sums for each nation using gross income data
                sum_dict = {}
                for temp_nation_name in nation_name_masterlist:
                    sum_dict[temp_nation_name] = 0
                for temp_nation_name, gross_data in gross_income_dict.items():
                    for resource_name, gross_income in gross_data["Total Income"].items():
                        match resource_name:
                            case "Basic Materials" | "Common Metals":
                                sum_dict[temp_nation_name] += gross_income
                # check if nation has the greatest sum
                nation_name_sum = sum_dict[temp_nation_name]
                for temp_nation_name, sum in sum_dict.items():
                    if sum >= nation_name_sum:
                        nation_name_sum = False
                if nation_name_sum:
                    vc_1_completed = True
            
            case 'Leading Defense':
                # get gross improvement counts using improvement count list
                sum_dict = {}
                for temp_nation_name in nation_name_masterlist:
                    sum_dict[temp_nation_name] = 0
                for player in playerdata_list:
                    temp_improvement_count_list = ast.literal_eval(player[27])
                    sum_dict[player[1]] += temp_improvement_count_list[improvement_name_list.index('Military Outpost')]
                    sum_dict[player[1]] += temp_improvement_count_list[improvement_name_list.index('Military Base')]
                    sum_dict[player[1]] += temp_improvement_count_list[improvement_name_list.index('Missile Defense System')]
                    sum_dict[player[1]] += temp_improvement_count_list[improvement_name_list.index('Missile Defense Network')]
                # check if nation has the greatest sum
                nation_name_sum = sum_dict[temp_nation_name]
                for temp_nation_name, sum in sum_dict.items():
                    if sum >= nation_name_sum:
                        nation_name_sum = False
                if nation_name_sum:
                    vc_1_completed = True

            case 'Major Exporter':
                export_count = 0
                for transaction in rmdata_all_transaction_list:
                    if transaction[1] == nation_name and transaction[2] == "Sold":
                        export_count += int(transaction[3])
                if export_count >= 150:
                    vc_1_completed = True
                    gamedata_dict["victoryConditions"][nation_name][0] = True    # vc is permanently fulfilled
            
            case 'Reconstruction Effort':
                # get gross improvement counts using improvement count list
                sum_dict = {}
                for temp_nation_name in nation_name_masterlist:
                    sum_dict[temp_nation_name] = 0
                for player in playerdata_list:
                    temp_improvement_count_list = ast.literal_eval(player[27])
                    sum_dict[player[1]] += temp_improvement_count_list[improvement_name_list.index('City')]
                # check if nation has the greatest sum
                nation_name_sum = sum_dict[temp_nation_name]
                for temp_nation_name, sum in sum_dict.items():
                    if sum >= nation_name_sum:
                        nation_name_sum = False
                if nation_name_sum:
                    vc_1_completed = True
            
            case 'Secure Strategic Resources':
                if (
                    improvement_count_list[improvement_name_list.index('Advanced Metals Mine')] > 0
                    and improvement_count_list[improvement_name_list.index('Uranium Mine')] > 0
                    and improvement_count_list[improvement_name_list.index('Rare Earth Elements Mine')] > 0
                ):
                    vc_1_completed = True


    #Check Normal Victory Condition
    vc_2_completed = gamedata_dict["victoryConditions"][nation_name][1]
    victory_condition_2 = victory_conditions_list[1]
    if not vc_2_completed:
        match victory_condition_2:

            case 'Backstab':
                # get set of all nations defeated in war
                nations_defeated = set()
                for war_name, war_dict in wardata.wardata_dict.items():
                    if war_dict["outcome"] == "TBD" or nation_name not in war_dict["combatants"]:
                        # we do not care about wars player was not involved in
                        continue
                    nation_role = war_dict["combatants"][nation_name]["role"]
                    if "Attacker" in nation_role:
                        nation_side = "Attacker"
                    else:
                        nation_side = "Defender"
                    if nation_side not in war_dict["outcome"]:
                        # we do not care about wars the player lost or white peaced
                        continue
                    for combatant_name, combatant_data in war_dict["combatants"].items():
                        if nation_side not in combatant_data["role"]:
                            nations_defeated.add(combatant_name)
                # get set of all nations you lost a war to
                nations_lost_to = set()
                for war_name, war_dict in wardata.wardata_dict.items():
                    if war_dict["outcome"] == "TBD" or nation_name not in war_dict["combatants"]:
                        # we do not care about wars player was not involved in
                        continue
                    nation_role = war_dict["combatants"][nation_name]["role"]
                    if "Attacker" in nation_role:
                        nation_side = "Attacker"
                    else:
                        nation_side = "Defender"
                    if nation_side in war_dict["outcome"] or "White Peace" == war_dict["outcome"]:
                        # we do not care about wars the player won or white peaced
                        continue
                    for combatant_name, combatant_data in war_dict["combatants"].items():
                        if nation_side not in combatant_data["role"]:
                            nations_lost_to.add(combatant_name)
                # get set of all former allies
                current_allies = set()
                former_allies = set()
                for alliance in alliance_table:
                    if alliance.is_active and nation_name in alliance.current_members:
                        for ally_name in alliance.current_members:
                            current_allies.add(ally_name)
                        for ally_name in alliance.former_members:
                            former_allies.add(ally_name)
                    elif not alliance.is_active and nation_name in alliance.former_members:
                        for ally_name in alliance.former_members:
                            former_allies.add(ally_name)
                if nation_name in current_allies:
                    current_allies.remove(nation_name)
                if nation_name in former_allies:
                    former_allies.remove(nation_name)
                former_allies_filtered = set()
                for ally_name in former_allies:
                    if ally_name not in current_allies:
                        former_allies_filtered.add(ally_name)
                former_allies = former_allies_filtered
                # win a war against a former ally
                for former_ally in former_allies:
                    if former_ally in nations_defeated:
                        vc_2_completed = True
                        gamedata_dict["victoryConditions"][nation_name][1] = True    # vc is permanently fulfilled
                # win a war against someone you lost to
                for enemy_nation in nations_lost_to:
                    if enemy_nation in nations_defeated:
                        vc_2_completed = True
                        gamedata_dict["victoryConditions"][nation_name][1] = True    # vc is permanently fulfilled

            case 'Diversified Army':
                unit_types_found = []
                for region_id in regdata_dict:
                    region_unit = Unit(region_id, game_id)
                    if region_unit.name != None and region_unit.owner_id == player_id:
                        if region_unit.name not in unit_types_found:
                            unit_types_found.append(region_unit.name)
                if len(unit_types_found) >= 5:
                    vc_2_completed = True

            case 'Hegemony':
                puppet_str = f'{nation_name} Puppet State'
                for player in playerdata_list:
                    status_str = player[28]
                    if puppet_str == status_str:
                        vc_2_completed = True
                        break

            case 'New Empire':
                # if two capitals
                improvement_index = improvement_name_list.index('Capital')
                improvement_count = improvement_count_list[improvement_index]
                if improvement_count >= 2:
                    vc_2_completed = True
                # or most edges
                # to do - income calc should update edge counts so we dont have to do a bunch of work here
                edge_counts = [0] * len(playerdata_list)
                for i in range(len(playerdata_list)):
                    for region_id in regdata_dict:
                        region = Region(region_id, game_id)
                        if region.owner_id == i + 1 and region.is_edge:
                            edge_counts[i] += 1
                nation_edge_count = edge_counts[player_id - 1]
                for edge_count in edge_counts:
                    if edge_count >= nation_edge_count:
                        nation_edge_count = False
                if nation_edge_count:
                     vc_2_completed = True

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
                    vc_2_completed = True

            case 'Reliable Ally':
                longest_alliance_name, duration = alliance_table.get_longest_alliance()
                if longest_alliance_name is not None:
                    longest_alliance = alliance_table.get(longest_alliance_name)
                    if longest_alliance.is_active and nation_name in longest_alliance.current_members:
                        vc_2_completed = True
                    elif not longest_alliance.is_active and nation_name in longest_alliance.former_members:
                        vc_2_completed = True

            case 'Sphere of Influence':
                agenda_count = 0
                agenda_data_dict = core.get_scenario_dict(game_id, "Agendas")
                for research_name in completed_research_list:
                    if research_name in agenda_data_dict:
                        agenda_count += 1
                if agenda_count >= 8:
                    vc_2_completed = True
                    gamedata_dict["victoryConditions"][nation_name][1] = True    # vc is permanently fulfilled
                    
            case 'Warmonger':
                count = 0
                for war_name, war_dict in wardata.wardata_dict.items():
                    if war_dict["outcome"] == "Attacker Victory" and war_dict["combatants"][nation_name]["role"] == "Main Attacker":
                        count += 1
                if count >= 3:
                    vc_2_completed = True
                    gamedata_dict["victoryConditions"][nation_name][1] = True    # vc is permanently fulfilled


    #Check Hard Victory Condition
    vc_3_completed = gamedata_dict["victoryConditions"][nation_name][2]
    victory_condition_3 = victory_conditions_list[2]
    if not vc_3_completed:
        match victory_condition_3:

            case 'Economic Domination':
                economy_1st, economy_2nd, economy_3rd = get_top_three(game_id, 'strongest_economy', True)
                if nation_name in economy_1st and (economy_1st[-6:] != economy_2nd[-6:]):
                    vc_3_completed = True

            case 'Influence Through Trade':
                trade_1st, trade_2nd, trade_3rd = core.get_top_three_transactions(game_id)
                if nation_name in trade_1st and (trade_1st[-4:] != trade_2nd[-4:]):
                    vc_3_completed = True

            case 'Military Superpower':
                military_1st, military_2nd, military_3rd = get_top_three(game_id, 'largest_military', True)
                if nation_name in military_1st and (military_1st[-4:] != military_2nd[-4:]):
                    vc_3_completed = True

            case 'Scientific Leader':
                research_1st, research_2nd, research_3rd = get_top_three(game_id, 'most_research', True)
                if nation_name in research_1st and (research_1st[-4:] != research_2nd[-4:]):
                    vc_3_completed = True

            case 'Territorial Control':
                size_1st, size_2nd, size_3rd = get_top_three(game_id, 'largest_nation', True)
                if nation_name in size_1st and (size_1st[-4:] != size_2nd[-4:]):
                    vc_3_completed = True
        

    # save gamedata
    with open(f'gamedata/{game_id}/gamedata.json', 'w') as json_file:
        json.dump(gamedata_dict, json_file, indent=4)

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
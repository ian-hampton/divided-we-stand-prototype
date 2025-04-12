import ast
import copy
import csv
import json
import random

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
        nation.regions_owned = 0
        nation.regions_occupied = 0
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
        # skip if region is unowned
        if region.owner_id == 0 or region.owner_id == 99:
            continue
        # update statistics
        nation = nation_table.get(region.owner_id)
        nation.regions_owned += 1
        if region.occupier_id != 0:
            nation.regions_occupied += 1
        nation_table.save(nation)
        # skip if region is empty
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

def countdown(game_id: str) -> None:
    """
    Resolves improvements/units that have countdowns associated with them.
    """

    with open(f'gamedata/{game_id}/regdata.json', 'r') as json_file:
        regdata_dict = json.load(json_file)

    # resolve strip mines
    for region_id in regdata_dict:
        region = Region(region_id, game_id)
        region_improvement = Improvement(region_id, game_id)
        if region_improvement.name == "Strip Mine":
            region_improvement.decrease_timer()
            if region_improvement.turn_timer <= 0:
                region_improvement.clear()
                region.set_resource("Empty")
    
    # resolve nuked regions
    for region_id in regdata_dict:
        region = Region(region_id, game_id)
        if region.fallout != 0:
            region.decrease_fallout()

def resolve_resource_shortages(game_id: str) -> None:
    """
    Resolves resource shortages by pruning units and improvements that cost upkeep.
    """

    # get game info
    nation_table = NationTable(game_id)
    notifications = Notifications(game_id)

    for i in range(len(nation_table)):
        nation_id = str(i + 1)

        nation = nation_table.get(nation_id)
        upkeep_dict = core.create_player_upkeep_dict(game_id, nation)

        # filter out upkeep data for units/improvements player does not have
        for improvement_name, count in nation.improvement_counts.items():
            if count == 0 and improvement_name in upkeep_dict:
                del upkeep_dict[improvement_name]
        for unit_name, count in nation.unit_counts.items():
            if count == 0 and unit_name in upkeep_dict:
                del upkeep_dict[unit_name]

        # handle shortages
        _resolve_shortage("Oil", upkeep_dict, game_id, nation.id, notifications)
        _resolve_shortage("Coal", upkeep_dict, game_id, nation.id, notifications)
        _resolve_shortage("Energy", upkeep_dict, game_id, nation.id, notifications)
        _resolve_shortage("Uranium", upkeep_dict, game_id, nation.id, notifications)
        _resolve_shortage("Dollars", upkeep_dict, game_id, nation.id, notifications)
    
        # update nation data
        nation_table.reload()
        nation = nation_table.get(nation_id)
        nation_table.save(nation)

def _resolve_shortage(resource_name: str, upkeep_dict: dict, game_id: str, player_id: str, notifications: Notifications) -> None:
    """
    Helper function for resolve_resource_shortages().
    """

    # get player data
    nation_table = NationTable(game_id)
    nation = nation_table.get(player_id)

    # get pool of resource consumers
    consumers_list = []
    for target_name, resource_upkeep_dict in upkeep_dict.items():
        if resource_name in resource_upkeep_dict and resource_upkeep_dict[resource_name]["Upkeep"] > 0 and resource_upkeep_dict[resource_name]["Upkeep Multiplier"] > 0:
            consumers_list.append(target_name)
    
    # prune until resource shortage eliminated or no consumers left
    resource_stockpile = float(nation.get_stockpile(resource_name))
    while resource_stockpile < 0 and consumers_list != []:
        
        # select random consumer and identify if it is an improvement or unit
        consumer_name = random.choice(consumers_list)
        if consumer_name in nation.unit_counts:
            consumer_type = "unit"
        else:
            consumer_type = "improvement"
        
        # remove consumer
        if consumer_type == "improvement":
            region_id = core.search_and_destroy(game_id, player_id, consumer_name)
        else:
            region_id, victim = core.search_and_destroy_unit(game_id, player_id, consumer_name)
        
        # refresh nation data and add notification
        nation_table.reload()
        nation = nation_table.get(player_id)
        notifications.append(f'{nation.name} lost a {consumer_name} in {region_id} due to {resource_name.lower()} shortages.', 6)
        
        # update stockpile
        consumer_upkeep = upkeep_dict[consumer_name][resource_name]["Upkeep"] * upkeep_dict[consumer_name][resource_name]["Upkeep Multiplier"]
        resource_stockpile += consumer_upkeep
        nation.update_stockpile(resource_name, consumer_upkeep)
        
        # remove consumer from selection pool if no more of it remains
        if consumer_type == "improvement":
            count_dict = nation.improvement_counts
        else:
            count_dict = nation.unit_counts
        if count_dict[consumer_name] == 0:
            consumers_list.remove(consumer_name)
            del upkeep_dict[consumer_name]

    nation_table.save(nation)

def resolve_military_capacity_shortages(game_id: str) -> None:
    """
    Resolves military capacity shortages for each player by removing units randomly.
    """

    nation_table = NationTable(game_id)
    notifications = Notifications(game_id)

    for i in range(len(nation_table)):
        nation_id = str(i + 1)
        
        while True:
            
            # check for shortage
            nation = nation_table.get(nation_id)
            if float(nation.get_used_mc()) <= float(nation.get_max_mc()):
                break
            
            # disband a random unit
            region_id, victim = core.search_and_destroy_unit(game_id, nation_id, 'ANY')
            notifications.append(f'{nation.name} lost {victim} {region_id} due to insufficient military capacity.', 5)

            # update nation data
            nation_table.reload()
            nation = nation_table.get(nation_id)
            nation_table.save(nation)

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

def check_victory_conditions(game_id: str, player_id: int, current_turn_num: int) -> tuple[dict, int]:
    """
    Checks victory conditions of a player.

    Params:
        game_id (str): Game ID string.
        player_id (int): Nation ID of current nation.
        current_turn_num (int): Integer representing current turn number.

    Returns:
        tuple:
            dict: Dictionary of string-bool pairs representing victory condition progress.
            int: Nations current VC score.
    """
    
    # get game info
    nation_table = NationTable(game_id)
    alliance_table = AllianceTable(game_id)
    wardata = WarData(game_id)
    rmdata_filepath = f'gamedata/{game_id}/rmdata.csv'
    rmdata_all_transaction_list = core.read_rmdata(rmdata_filepath, current_turn_num, False, False)
    tech_data_dict = core.get_scenario_dict(game_id, "Technologies")
    agenda_data_dict = core.get_scenario_dict(game_id, "Agendas")
    with open(f'gamedata/{game_id}/regdata.json', 'r') as json_file:
        regdata_dict = json.load(json_file)

    # get player victory conditions
    nation = nation_table.get(player_id)
    score = 0
    vc_dict = nation.victory_conditions

    vc_list = list(nation.victory_conditions.keys())
    victory_condition_1 = vc_list[0]
    victory_condition_2 = vc_list[1]
    victory_condition_3 = vc_list[2]
    vc_1_completed = vc_dict[victory_condition_1]
    vc_2_completed = vc_dict[victory_condition_2]
    vc_3_completed = vc_dict[victory_condition_3]
    
    # Check Easy Victory Condition
    if not vc_1_completed:
        match victory_condition_1:
            
            case 'Breakthrough':
                # build set of all techs other players have researched so we can compare
                completed_research_all = set()
                for temp in nation_table:
                    if temp.name != nation.name:
                        temp_research_list = list(temp.completed_research.keys())
                        completed_research_all.update( temp_research_list)
                # find 15 point or greater tech that is not in completed_research_all
                for tech_name in nation.completed_research:
                    if (
                        tech_name in tech_data_dict
                        and tech_name not in completed_research_all
                        and tech_data_dict[tech_name]["Cost"] >= 15
                    ):
                        score += 1
                        vc_dict[victory_condition_1] = True    # vc is permanently fulfilled
            
            case 'Diversified Economy':
                non_zero_count = 0
                for improvement_name, improvement_count in nation.improvement_counts.items():
                    if improvement_count > 0:
                        non_zero_count += 1
                if non_zero_count >= 12:
                    score += 1
            
            case 'Energy Economy':
                # get gross income sums for each nation using gross income data
                sum_dict = {}
                for temp in nation_table:
                    sum_dict[temp.name] = 0
                    for resource_name in temp._resources:
                        if resource_name in ["Coal", "Oil", "Energy"]:
                            sum_dict[temp.name] += float(temp.get_gross_income(resource_name))
                # check if nation has the greatest sum
                nation_name_sum = sum_dict[nation.name]
                for temp_nation_name, sum in sum_dict.items():
                    if sum >= nation_name_sum:
                        nation_name_sum = False
                if nation_name_sum:
                    score += 1

            case 'Industrial Focus':
                # get gross income sums for each nation using gross income data
                sum_dict = {}
                for temp in nation_table:
                    sum_dict[temp.name] = 0
                    for resource_name in temp._resources:
                        if resource_name in ["Basic Materials", "Common Metals"]:
                            sum_dict[temp.name] += float(temp.get_gross_income(resource_name))
                # check if nation has the greatest sum
                nation_name_sum = sum_dict[nation.name]
                for temp_nation_name, sum in sum_dict.items():
                    if sum >= nation_name_sum:
                        nation_name_sum = False
                if nation_name_sum:
                    score += 1
            
            case 'Leading Defense':
                # get gross improvement counts using improvement count list
                sum_dict = {}
                for temp in nation_table:
                    sum_dict[temp.name] = 0
                    sum_dict[temp.name] += temp.improvement_counts["Military Outpost"]
                    sum_dict[temp.name] += temp.improvement_counts["Military Base"]
                    sum_dict[temp.name] += temp.improvement_counts["Missile Defense System"]
                    sum_dict[temp.name] += temp.improvement_counts["Missile Defense Network"]
                # check if nation has the greatest sum
                nation_name_sum = sum_dict[nation.name]
                for temp_nation_name, sum in sum_dict.items():
                    if sum >= nation_name_sum:
                        nation_name_sum = False
                if nation_name_sum:
                    score += 1

            case 'Major Exporter':
                export_count = 0
                for transaction in rmdata_all_transaction_list:
                    if transaction[1] == nation.name and transaction[2] == "Sold":
                        export_count += int(transaction[3])
                if export_count >= 150:
                    score += 1
                    vc_dict[victory_condition_1] = True    # vc is permanently fulfilled
            
            case 'Reconstruction Effort':
                # get gross improvement counts using improvement count list
                sum_dict = {}
                for temp in nation_table:
                    sum_dict[temp.name] = 0
                    sum_dict[temp.name] += temp.improvement_counts["City"]
                # check if nation has the greatest sum
                nation_name_sum = sum_dict[nation.name]
                for temp_nation_name, sum in sum_dict.items():
                    if sum >= nation_name_sum:
                        nation_name_sum = False
                if nation_name_sum:
                    score += 1
            
            case 'Secure Strategic Resources':
                if (nation.improvement_counts["Advanced Metals Mine"] > 0
                    and nation.improvement_counts["Uranium Mine"] > 0
                    and nation.improvement_counts["Rare Earth Elements Mine"] > 0):
                    score += 1


    # Check Normal Victory Condition
    if not vc_2_completed:
        match victory_condition_2:

            case 'Backstab':
                # get set of all nations defeated in war
                nations_defeated = set()
                for war_name, war_dict in wardata.wardata_dict.items():
                    if war_dict["outcome"] == "TBD" or nation.name not in war_dict["combatants"]:
                        # we do not care about wars player was not involved in
                        continue
                    nation_role = war_dict["combatants"][nation.name]["role"]
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
                    if war_dict["outcome"] == "TBD" or nation.name not in war_dict["combatants"]:
                        # we do not care about wars player was not involved in
                        continue
                    nation_role = war_dict["combatants"][nation.name]["role"]
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
                    if alliance.is_active and nation.name in alliance.current_members:
                        for ally_name in alliance.current_members:
                            current_allies.add(ally_name)
                        for ally_name in alliance.former_members:
                            former_allies.add(ally_name)
                    elif not alliance.is_active and nation.name in alliance.former_members:
                        for ally_name in alliance.former_members:
                            former_allies.add(ally_name)
                if nation.name in current_allies:
                    current_allies.remove(nation.name)
                if nation.name in former_allies:
                    former_allies.remove(nation.name)
                former_allies_filtered = set()
                for ally_name in former_allies:
                    if ally_name not in current_allies:
                        former_allies_filtered.add(ally_name)
                former_allies = former_allies_filtered
                # win a war against a former ally
                for former_ally in former_allies:
                    if former_ally in nations_defeated:
                        score += 1
                        vc_dict[victory_condition_2] = True    # vc is permanently fulfilled
                # win a war against someone you lost to
                for enemy_nation in nations_lost_to:
                    if enemy_nation in nations_defeated:
                        score += 1
                        vc_dict[victory_condition_2] = True    # vc is permanently fulfilled

            case 'Diversified Army':
                unit_types_found = 0
                for unit_type, count in nation.unit_counts.items():
                    if count > 0:
                        unit_types_found += 1
                if unit_types_found >= 5:
                    score += 1

            case 'Hegemony':
                puppet_str = f'{nation.name} Puppet State'
                for temp in nation_table:
                    if puppet_str == temp.status:
                        score += 1
                        break

            case 'New Empire':
                # if two capitals
                if nation.improvement_counts["Capital"] >= 2:
                    score += 1
                # or most edges
                else:
                    edge_counts = [0] * len(nation_table)
                    for region_id in regdata_dict:
                        region = Region(region_id, game_id)
                        if region.is_edge:
                            edge_counts[region.owner_id - 1] += 1
                    nation_edge_count = edge_counts[player_id - 1]
                    for edge_count in edge_counts:
                        if edge_count >= nation_edge_count:
                            nation_edge_count = False
                    if nation_edge_count:
                        score += 1

            case 'Nuclear Deterrent':
                most_nukes_value = 0
                most_nukes_player_ids = []
                for temp in nation_table:
                    if temp.nuke_count > most_nukes_value:
                        most_nukes_value = temp.nuke_count
                        most_nukes_player_ids = [temp.id]
                    elif temp.nuke_count == most_nukes_value:
                        most_nukes_player_ids.append(temp.id)
                if len(most_nukes_player_ids) == 1 and player_id in most_nukes_player_ids:
                    score += 1

            case 'Reliable Ally':
                longest_alliance_name, duration = alliance_table.get_longest_alliance()
                if longest_alliance_name is not None:
                    longest_alliance = alliance_table.get(longest_alliance_name)
                    if longest_alliance.is_active and nation.name in longest_alliance.current_members:
                        vc_2_completed = True
                    elif not longest_alliance.is_active and nation.name in longest_alliance.former_members:
                        vc_2_completed = True

            case 'Sphere of Influence':
                agenda_count = 0
                for research_name in nation.completed_research:
                    if research_name in agenda_data_dict:
                        agenda_count += 1
                if agenda_count >= 8:
                    score += 1
                    vc_dict[victory_condition_2] = True    # vc is permanently fulfilled
                    
            case 'Warmonger':
                count = 0
                for war_name, war_dict in wardata.wardata_dict.items():
                    if war_dict["outcome"] == "Attacker Victory" and war_dict["combatants"][nation.name]["role"] == "Main Attacker":
                        count += 1
                if count >= 3:
                    score += 1
                    vc_dict[victory_condition_2] = True    # vc is permanently fulfilled


    # Check Hard Victory Condition
    if not vc_3_completed:
        match victory_condition_3:

            case 'Economic Domination':
                first, second, third = nation_table.get_top_three("netIncome")
                if nation.name in first[0] and (first[1] > second[1]):
                    score += 1

            case 'Influence Through Trade':
                first, second, third = nation_table.get_top_three("transactionCount")
                if nation.name in first[0] and (first[1] > second[1]):
                    score += 1

            case 'Military Superpower':
                first, second, third = nation_table.get_top_three("militaryStrength")
                if nation.name in first[0] and (first[1] > second[1]):
                    score += 1

            case 'Scientific Leader':
                first, second, third = nation_table.get_top_three("researchCount")
                if nation.name in first[0] and (first[1] > second[1]):
                    score += 1

            case 'Territorial Control':
                first, second, third = nation_table.get_top_three("nationSize")
                if nation.name in first[0] and (first[1] > second[1]):
                    score += 1

    return vc_dict, score

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

def prompt_for_missing_war_justifications(game_id: str) -> None:
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
    
    # get game data
    nation_table = NationTable(game_id)
    wardata = WarData(game_id)
    notifications = Notifications(game_id)
    with open(f'gamedata/{game_id}/regdata.json', 'r') as json_file:
        regdata_dict = json.load(json_file)

    # check all regions for occupation
    non_occupied_found_list = [False] * len(nation_table)
    for region_id in regdata_dict:
        region = Region(region_id, game_id)
        owner_id = region.owner_id
        if owner_id != 0 and owner_id != 99 and region.occupier_id == 0:
            non_occupied_found_list[owner_id - 1] = True
    
    # if no unoccupied region found for a player force surrender if main combatant
    for index, region_found in enumerate(non_occupied_found_list):
        player_id_1 = index + 1
        nation_name_1 = nation_table.get(player_id_1).name
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

def war_score_forced_surrender(game_id: str) -> None:
    """
    Forces a side to surrender if critical war score difference reached.

    Params:
        game_id (str): Game ID string.
    """

    # get game data
    wardata = WarData(game_id)
    notifications = Notifications(game_id)

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
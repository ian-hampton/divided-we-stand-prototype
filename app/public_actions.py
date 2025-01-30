# STANDARD IMPORTS
import ast
import csv
import random
import json

# MY IMPORTS
from app import core
from app import events
from app.region import Region
from app.improvement import Improvement
from app.unit import Unit
from app.wardata import WarData
from app.notifications import Notifications
from app.alliance import Alliance
from app.alliance import AllianceTable

def resolve_alliance_creations(alliance_create_list: list, game_id: str, player_action_logs: list) -> list:
    """
    Resolves all Alliance Create actions.

    Params:
        alliance_create_list (list): List of alliance creation actions.
        game_id (str): Game ID.
        player_action_logs (list): Action logs.

    Returns:
        list: List of player action logs.
    """

    # get game info
    playerdata_filepath = f'gamedata/{game_id}/playerdata.csv'
    playerdata_list = core.read_file(playerdata_filepath, 1)
    nation_info_masterlist = core.get_nation_info(playerdata_list)
    nation_name_list = []
    research_masterlist = []
    for player in playerdata_list:
        nation_name_list.append(player[1])
        research_masterlist.append(ast.literal_eval(player[26]))
    alliance_table = AllianceTable(game_id)
    notifications = Notifications(game_id)

    # process actions
    alliance_creation_dict = {}
    for action in alliance_create_list:
        
        # decode action
        player_id = action[0]
        nation_name = nation_info_masterlist[player_id - 1][0]
        action_data_str = action[1]
        action_data_list = action_data_str.split(" ")
        alliance_type = " ".join(action_data_list[2:4])
        alliance_name = " ".join(action_data_list[4:])

        # get playerdata
        player_research_list = research_masterlist[player_id - 1]
        player_action_log = player_action_logs[player_id - 1]

        # required research check
        research_check_success = True
        match alliance_type:
            case 'Non-Aggression Pact':
                if 'Peace Accords' not in player_research_list:
                   research_check_success = False 
            case 'Defense Pact':
                if 'Defensive Agreements' not in player_research_list:
                   research_check_success = False 
            case 'Trade Agreement':
                if 'Trade Routes' not in player_research_list:
                   research_check_success = False 
            case 'Research Agreement':
                if 'Research Exchange' not in player_research_list:
                   research_check_success = False 
        if not research_check_success:
            player_action_log.append(f'Failed to form {alliance_name} alliance. You do not have the required foreign policy agenda.')
            player_action_logs[player_id - 1] = player_action_log
            continue

        # check alliance capacity
        if alliance_type != 'Non-Aggression Pact':
            alliance_count, alliance_capacity = core.get_alliance_count(game_id, playerdata_list[player_id - 1])
            if (alliance_count + 1) > alliance_capacity:
                player_action_log.append(f'Failed to form {alliance_name}. You do not have enough alliance capacity.')
                player_action_logs[player_id - 1] = player_action_log
                continue

        # check that an alliance with this name does not already exist
        if alliance_name in alliance_table.data:
            player_action_log.append(f'Failed to form {alliance_name} alliance. An alliance with that name has already been created.')
            player_action_logs[player_id - 1] = player_action_log
            continue

        # update alliance_creation_dict
        if alliance_name in alliance_creation_dict:
            alliance_creation_dict[alliance_name]["members"].append(nation_name)
        else:
            entry = {}
            entry["type"] = alliance_type
            entry["members"] = [nation_name]
            alliance_creation_dict[alliance_name] = entry

    # create the alliance if more than two founders
    for alliance_name, alliance_data in alliance_creation_dict.items():
        if len(alliance_data["members"]) > 1:
            # alliance creation success
            alliance = alliance_table.create(alliance_name, alliance_data["type"], alliance_data["members"])
            for nation_name in alliance_data["members"]:
                # update log
                notifications.append(f"{alliance.name} has formed.", 7)
                player_id = nation_name_list.index(nation_name) + 1
                player_action_log = player_action_logs[player_id - 1]
                player_action_log.append(f'Successfully formed {alliance_name}.')
                player_action_logs[player_id - 1] = player_action_log
        else:
            # alliance creation failed
            nation_name = alliance_data["members"][0]
            player_id = nation_name_list.index(nation_name)
            player_action_log = player_action_logs[player_id - 1]
            player_action_log.append(f'Failed to form {alliance_name} alliance. Not enough players agreed to establish it.')
            player_action_logs[player_id - 1] = player_action_log


    # update playerdata.csv
    with open(playerdata_filepath, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(core.player_data_header)
        writer.writerows(playerdata_list)

    return player_action_logs

def resolve_alliance_joins(alliance_join_list: list, game_id: str, player_action_logs: list) -> list:
    """
    Resolves all Alliance Join actions.

    Params:
        alliance_join_list (list): List of alliance join actions.
        game_id (str): Game ID.
        player_action_logs (list): Action logs.
    
    Returns:
        list: List of player action logs.
    """
    
    # get game info
    playerdata_filepath = f'gamedata/{game_id}/playerdata.csv'
    playerdata_list = core.read_file(playerdata_filepath, 1)
    nation_info_masterlist = core.get_nation_info(playerdata_list)
    nation_name_list = []
    research_masterlist = []
    for player in playerdata_list:
        nation_name_list.append(player[1])
        research_masterlist.append(ast.literal_eval(player[26]))
    alliance_table = AllianceTable(game_id)
    notifications = Notifications(game_id)

    # process actions
    for action in alliance_join_list:
        
        # decode action
        player_id = action[0]
        nation_name = nation_info_masterlist[player_id - 1][0]
        action_data_str = action[1]
        action_data_list = action_data_str.split(" ")
        alliance_name = " ".join(action_data_list[2:])

        # get playerdata
        player_research_list = research_masterlist[player_id - 1]
        player_action_log = player_action_logs[player_id - 1]

        # get alliance
        alliance = alliance_table.get(alliance_name)
        if alliance is None or not alliance.is_active:
            player_action_log.append(f'Failed to join {alliance_name}. Alliance not found.')
            player_action_logs[player_id - 1] = player_action_log
            continue

        # required research check
        research_check_success = False
        for ally_name in alliance.founding_members:
            if ally_name in alliance.current_members:
                ally_id = nation_name_list.index(ally_name) + 1
                ally_research_list = research_masterlist[ally_id - 1]
                if "With Open Arms" in ally_research_list:
                    research_check_success = True
                    break
        if not research_check_success:
            match alliance.type:
                case 'Non-Aggression Pact':
                    if 'Peace Accords' in player_research_list:
                        research_check_success = True
                case 'Defense Pact':
                    if 'Defensive Agreements' in player_research_list:
                        research_check_success = True
                case 'Trade Agreement':
                    if 'Trade Routes' in player_research_list:
                        research_check_success = True
                case 'Research Agreement':
                    if 'Research Exchange' in player_research_list:
                        research_check_success = True
        if not research_check_success:
            player_action_log.append(f'Failed to join {alliance_name}. You do not have the required foreign policy agenda.')
            player_action_logs[player_id - 1] = player_action_log
            continue

        # check alliance capacity
        if alliance.type != 'Non-Aggression Pact':
            alliance_count, alliance_capacity = core.get_alliance_count(game_id, playerdata_list[player_id - 1])
            if (alliance_count + 1) > alliance_capacity:
                player_action_log.append(f'Failed to form {alliance_name}. You do not have enough alliance capacity.')
                player_action_logs[player_id - 1] = player_action_log
                continue

        # add player to the alliance
        alliance.add_member(nation_name)
        alliance_table.save(alliance)
        notifications.append(f"{nation_name} has joined the {alliance.name}.", 7)
        player_action_log.append(f'Joined {alliance_name}.')
        player_action_logs[player_id - 1] = player_action_log
    
    return player_action_logs

def resolve_alliance_leaves(alliance_leave_list: list, game_id: str, player_action_logs: list) -> list:
    """
    Resolves all Alliance Leave actions.

    Params:
        alliance_leave_list (list): List of alliance join actions.
        game_id (str): Game ID.
        player_action_logs (list): Action logs.
    
    Returns:
        list: List of player action logs.
    """
    
    # get game info
    playerdata_filepath = f'gamedata/{game_id}/playerdata.csv'
    playerdata_list = core.read_file(playerdata_filepath, 1)
    nation_info_masterlist = core.get_nation_info(playerdata_list)
    nation_name_list = []
    research_masterlist = []
    for player in playerdata_list:
        nation_name_list.append(player[1])
        research_masterlist.append(ast.literal_eval(player[26]))
    alliance_table = AllianceTable(game_id)
    notifications = Notifications(game_id)

    # process actions
    for action in alliance_leave_list:
        
        # decode action
        player_id = action[0]
        nation_name = nation_info_masterlist[player_id - 1][0]
        action_data_str = action[1]
        action_data_list = action_data_str.split(" ")
        alliance_name = " ".join(action_data_list[2:])

        # get playerdata
        player_research_list = research_masterlist[player_id - 1]
        player_action_log = player_action_logs[player_id - 1]

        # get alliance
        alliance = alliance_table.get(alliance_name)
        if alliance is None:
            player_action_log.append(f'Failed to join {alliance_name}. Alliance not found.')
            player_action_logs[player_id - 1] = player_action_log
            continue

        # remove player from alliance
        alliance.remove_member(nation_name)
        alliance_table.save(alliance)
        notifications.append(f"{nation_name} has left the {alliance.name}.", 7)
        player_action_log.append(f'Left {alliance_name}.')
        player_action_logs[player_id - 1] = player_action_log
    
    return player_action_logs

def resolve_government_abilities(government_actions_list, full_game_id, player_action_logs):
    '''
    Resolves government-specific actions. Currently, this is only the Republic government action.

    Parameters:
    - government_actions_list: A list of player government action data stored as an integer-string lists.
    - full_game_id: The full game id of the current game.
    - player_action_logs: A list of lists that contains player action logs as strings.
    '''

    #define core lists
    playerdata_filepath = f'gamedata/{full_game_id}/playerdata.csv'
    playerdata_list = core.read_file(playerdata_filepath, 1)
    notifications = Notifications(full_game_id)

    #get nation information
    request_list = ['Dollars', 'Political Power', 'Technology', 'Coal', 'Oil', 'Green Energy', 'Basic Materials', 'Common Metals', 'Advanced Metals', 'Uranium', 'Rare Earth Elements']
    economy_masterlist = core.get_economy_info(playerdata_list, request_list)


    #Execute Actions
    for action in government_actions_list:
        player_id = action[0]
        playerdata = playerdata_list[player_id - 1]
        nation_name = playerdata[1]
        player_government = playerdata[3]
        player_action_log = player_action_logs[player_id - 1]

        #get resource stockpiles of player
        stockpile_list = []
        for i in range(len(request_list)):
            stockpile_list.append(economy_masterlist[player_id - 1][i][0])
        political_power_stockpile = float(stockpile_list[1])

        #republic action procedure
        if 'Republic' in action[1] and player_government == 'Republic':
            raw_action_data_list = action[1].split(' ')
            resource_type = ' '.join(raw_action_data_list[1:])
            political_power_cost = 5
            if political_power_stockpile - political_power_cost >= 0:
                economy_masterlist[player_id - 1][1][0] = core.update_stockpile(political_power_stockpile, political_power_cost)
                resource_type_index = request_list.index(resource_type)
                rate_list = [100, 100, 100, 100, 100, 100, 100, 100, 100, 100, 100]
                rate_list[resource_type_index] = 120
                for index, value in enumerate(rate_list):
                    economy_masterlist[player_id - 1][index][3] = value
                notifications.append(f'{nation_name} used Republic government action to boost {resource_type} income.', 8)
                player_action_log.append(f"Used Republic government action to boost {resource_type} income. ")
            else:
                player_action_log.append(f"Failed to preform the Republic government action. Insufficient political power.")
        elif 'Republic' in action[1] and player_government != 'Republic':
            player_action_log.append(f"Failed to preform the Republic government action. Your nation does not have the Republic government.")
        player_action_logs[player_id - 1] = player_action_log


        #Update playerdata.csv
        for economy_list in economy_masterlist:
            for resource_data_list in economy_list:
                resource_data_list = str(resource_data_list)
        for i, playerdata in enumerate(playerdata_list):
            playerdata[9] = economy_masterlist[i][0]
            playerdata[10] = economy_masterlist[i][1]
            playerdata[11] = economy_masterlist[i][2]
            playerdata[12] = economy_masterlist[i][3]
            playerdata[13] = economy_masterlist[i][4]
            playerdata[14] = economy_masterlist[i][5]
            playerdata[15] = economy_masterlist[i][6]
            playerdata[16] = economy_masterlist[i][7]
            playerdata[17] = economy_masterlist[i][8]
            playerdata[18] = economy_masterlist[i][9]
            playerdata[19] = economy_masterlist[i][10]
        with open(playerdata_filepath, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(core.player_data_header)
            writer.writerows(playerdata_list)
    
    #Update player_action_logs
    return player_action_logs

def resolve_improvement_removals(improvement_remove_list, game_id, player_action_logs):
    '''Resolves all improvement removal actions'''
    
    # Execute Actions
    for remove_action in improvement_remove_list:
        player_id = remove_action[0]
        region_id = remove_action[1][-5:]
        region = Region(region_id, game_id)
        region_improvement = Improvement(region_id, game_id)
        player_action_log = player_action_logs[player_id - 1]

        #ownership check
        if region.owner_id != player_id:
            player_action_log.append(f'Failed to remove improvement in region {region_id}. You do not own or control this region.')
            player_action_logs[player_id - 1] = player_action_log
            continue

        # remove improvement
        region_improvement.clear()
        player_action_log.append(f'Removed improvement in region {region_id}.')
        player_action_logs[player_id - 1] = player_action_log

    return player_action_logs

def resolve_improvement_builds(improvement_build_list, game_id, player_action_logs):
    '''Resolves all improvement build actions.'''

    # define core lists
    playerdata_filepath = f'gamedata/{game_id}/playerdata.csv'
    playerdata_list = core.read_file(playerdata_filepath, 1)

    # get scenario data
    improvement_data_dict = core.get_scenario_dict(game_id, "Improvements")

    # get needed economy information from each player
    nation_info_masterlist = core.get_nation_info(playerdata_list)
    request_list = ['Dollars', 'Basic Materials', 'Common Metals', 'Advanced Metals', 'Rare Earth Elements']
    economy_masterlist = core.get_economy_info(playerdata_list, request_list)
    research_masterlist = []
    improvement_count_masterlist = []
    for player in playerdata_list:
        player_research_list = ast.literal_eval(player[26])
        if player_research_list:
            research_masterlist.append(player_research_list)
        else:
            player_research_list = []
            research_masterlist.append(player_research_list)
        improvement_count_list = ast.literal_eval(player[27])
        improvement_count_masterlist.append(improvement_count_list)


    # Execute Actions
    for build_action in improvement_build_list:
        player_id = build_action[0]
        improvement_name = build_action[1][6:-6]
        region_id = build_action[1][-5:]
        region = Region(region_id, game_id)
        region_improvement = Improvement(region_id, game_id)
        player_government = nation_info_masterlist[player_id - 1][2]
        player_research = research_masterlist[player_id - 1]
        player_action_log = player_action_logs[player_id - 1]

        # get resource stockpiles of player
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
        if region.owner_id != player_id or region.occupier_id != 0:
            player_action_log.append(f'Failed to build {improvement_name} in region {region_id}. You do not own or control this region.')
            player_action_logs[player_id - 1] = player_action_log
            continue
        
        # required research check
        if improvement_data_dict[improvement_name]['Required Research'] is not None:
            if improvement_data_dict[improvement_name]['Required Research'] not in player_research:
                player_action_log.append(f'Failed to build {improvement_name} in region {region_id}. You do not have the required research.')
                player_action_logs[player_id - 1] = player_action_log
                continue

        # required region resource check
        required_resource = improvement_data_dict[improvement_name]['Required Resource']
        if required_resource:
            if required_resource != region.resource:
                player_action_log.append(f'Failed to build {improvement_name} in region {region_id}. The region does not have the resource required for this improvement.')
                player_action_logs[player_id - 1] = player_action_log
                continue

        # ratio check
        improvement_count_list = improvement_count_masterlist[player_id - 1]
        ratio_check = core.verify_ratio(game_id, improvement_count_list, improvement_name)
        if ratio_check == False:
            player_action_log.append(f'Failed to build {improvement_name} in region {region_id}. Refineries must be built in a 1:2 ratio.')
            player_action_logs[player_id - 1] = player_action_log
            continue

        # nuke check
        if region.fallout != 0:
            player_action_log.append(f'Failed to build {improvement_name} in region {region_id}. Region cannot support an improvement due to nuclear missile detonation.')
            player_action_logs[player_id - 1] = player_action_log
            continue

        # calculate build cost
        build_cost_dict = improvement_data_dict[improvement_name]["Build Costs"]
        if player_government == 'Remnant':
            for key in build_cost_dict:
                build_cost_dict[key] *= 0.9

        # build cost check
        cost_check_passed = True
        for key in build_cost_dict:
            cost = build_cost_dict[key]
            stockpile = player_stockpile_dict[key]
            if stockpile - cost < 0:
                cost_check_passed = False
        if not cost_check_passed:
            player_action_log.append(f'Failed to build {improvement_name} in region {region_id}. Insufficient resources.')
            player_action_logs[player_id - 1] = player_action_log

        # pay for improvement
        i = 0
        costs_list = []
        for key in build_cost_dict:
            cost = build_cost_dict[key]
            stockpile = player_stockpile_dict[key]
            economy_masterlist[player_id - 1][i][0] = core.update_stockpile(stockpile, cost)
            if cost > 0:
                costs_list.append(f"{cost} {key.lower()}")
            i += 1
        
        # place improvement
        region_improvement.set_improvement(improvement_name, player_research=player_research)
        if len(costs_list) <= 2:
            costs_str = " and ".join(costs_list)
        else:
            costs_str = ", ".join(costs_list)
            costs_str = " and ".join(costs_str.rsplit(", ", 1))
        player_action_log.append(f"Built {improvement_name} in region {region_id} for {costs_str}.")
        player_action_logs[player_id - 1] = player_action_log


    #Update playerdata.csv
    for economy_list in economy_masterlist:
        for resource_data_list in economy_list:
            resource_data_list = str(resource_data_list)
    i = 0
    for playerdata in playerdata_list:
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

def resolve_market_actions(market_buy_action_list, market_sell_action_list, steal_action_list, game_id, current_turn_num, player_count, player_action_logs):
    '''Resolves all resource market buy and sell actions. Updates resource market prices.'''

    #define core lists
    playerdata_filepath = f'gamedata/{game_id}/playerdata.csv'
    rmdata_filepath = f'gamedata/{game_id}/rmdata.csv'
    playerdata_list = core.read_file(playerdata_filepath, 1)
    with open('active_games.json', 'r') as json_file:
        active_games_dict = json.load(json_file)

    #TO DO: add stealing data to active_games
    steal_tracking_dict = active_games_dict[game_id]["Steal Action Record"]

    #get needed economy information from each player
    nation_info_masterlist = core.get_nation_info(playerdata_list)
    request_list = ['Dollars', 'Technology', 'Coal', 'Oil', 'Basic Materials', 'Common Metals', 'Advanced Metals', 'Uranium', 'Rare Earth Elements']
    economy_masterlist = core.get_economy_info(playerdata_list, request_list)
    nation_info_masterlist = core.get_nation_info(playerdata_list)

    #define important lists
    base_prices = [5, 3, 3, 5, 5, 10, 10, 20]
    current_prices = [5, 3, 3, 5, 5, 10, 10, 20] #aka buy price
    next_prices = [5, 3, 3, 5, 5, 10, 10, 20] #aka sell price
    rmdata_update_list = []
    player_resource_market_incomes = []
    for i in range(player_count):
        player_resource_market_incomes.append([0, 0, 0, 0, 0, 0, 0, 0, 0])


    #Calculate This Turn's Prices
    total_exchanged = [[0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0]]
    rmdata_recent_transaction_list = core.read_rmdata(rmdata_filepath, current_turn_num, 12, False)

    #count bought and sold values for each resource
    for transaction in rmdata_recent_transaction_list: 
        exchange = transaction[2]
        count = transaction[3]
        resource = transaction[4]
        resource_index = request_list.index(resource) - 1
        if exchange == 'Bought':
            total_exchanged[resource_index][0] += count
        elif exchange == 'Sold':
            total_exchanged[resource_index][1] += count

    #calculate new prices using exchange data
    for i in range(len(base_prices)):
        base_price = base_prices[i]
        bought_last_12 = total_exchanged[i][0]
        sold_last_12 = total_exchanged[i][1]
        this_turn_price = base_price * ( (bought_last_12 + 25) / (sold_last_12 + 25) )
        if "Market Inflation" in active_games_dict[game_id]["Active Events"]:
            for resource_name in active_games_dict[game_id]["Active Events"]["Market Inflation"]["Affected Resources"]:
                event_resource_index = request_list.index(resource_name) - 1
                if i == event_resource_index:
                    this_turn_price *= 2
        elif "Market Recession" in active_games_dict[game_id]["Active Events"]:
            for resource_name in active_games_dict[game_id]["Active Events"]["Market Recession"]["Affected Resources"]:
                event_resource_index = request_list.index(resource_name) - 1
                if i == event_resource_index:
                    this_turn_price *= 0.5
        current_prices[i] = round(this_turn_price, 2)

    

    #Process Buy Actions
    for buy_action in market_buy_action_list:
        player_id = buy_action[0]
        buy_action[1] = buy_action[1][4:]
        buy_action_data = buy_action[1].split()
        desired_count = int(buy_action_data[0])
        desired_resource = ' '.join(buy_action_data[1:])
        nation_name = playerdata_list[player_id - 1][1]
        player_gov = nation_info_masterlist[player_id - 1][2]
        player_action_log = player_action_logs[player_id - 1]

        #get resource data
        stockpile_list = []
        stockpile_size_list = []
        for i in range(len(request_list)):
            stockpile_list.append(economy_masterlist[player_id - 1][i][0])
            stockpile_size_list.append(economy_masterlist[player_id - 1][i][1])
        dollars_stockpile = float(stockpile_list[0])
        desired_resource_stockpile = float(stockpile_list[request_list.index(desired_resource)])
        desired_resource_stockpile_size = stockpile_size_list[request_list.index(desired_resource)]

        #affordability check
        discounted_rate = 1
        if player_gov == 'Protectorate':
            discounted_rate -= 0.2
        #event check
        if "Foreign Investment" in active_games_dict[game_id]["Active Events"]:
            chosen_nation_name = active_games_dict[game_id]["Active Events"]["Foreign Investment"]["Chosen Nation Name"]
            if nation_name == chosen_nation_name:
                discounted_rate -= 0.2
        desired_resource_price = current_prices[request_list.index(desired_resource) - 1]
        if discounted_rate != 1:
            desired_resource_price *= discounted_rate
            desired_resource_price = round(desired_resource_price, 2)
        dollars_paid = desired_count * desired_resource_price
        dollars_paid = round(dollars_paid, 2)
        if player_resource_market_incomes[player_id - 1][0] - dollars_paid + dollars_stockpile < 0:
            player_action_log.append(f'Failed to buy {desired_count} {desired_resource}. Not enough dollars.')
            player_action_logs[player_id - 1] = player_action_log
            continue

        #stockpile size check
        if player_resource_market_incomes[player_id - 1][request_list.index(desired_resource)] + desired_count > desired_resource_stockpile_size:
            player_action_log.append(f'Failed to buy {desired_count} {desired_resource}. Not enough room left in stockpile.')
            player_action_logs[player_id - 1] = player_action_log
            continue

        #event check
        if "Embargo" in active_games_dict[game_id]["Active Events"]:
            chosen_nation_name = active_games_dict[game_id]["Active Events"]["Embargo"]["Chosen Nation Name"]
            if nation_name == chosen_nation_name:
                player_action_log.append(f'Failed to buy {desired_count} {desired_resource}. Your nation is currently under an embargo.')
                player_action_logs[player_id - 1] = player_action_log
                continue
        
        #crime syndicate steal
        steal_nation_name = None
        for steal_action in steal_action_list:
            steal_player_id = steal_action[0]
            steal_action_str = steal_action[1]
            if nation_name in steal_action_str:
                steal_nation_name = playerdata_list[steal_player_id - 1][1]
                nation_name_of_last_victim = steal_tracking_dict[steal_nation_name]["Nation Name"]
                streak_of_last_victim = steal_tracking_dict[steal_nation_name]["Streak"]
                modifier = 0.5
                if nation_name == nation_name_of_last_victim:
                    for i in range(streak_of_last_victim):
                        modifier *= 0.5
                    modifier = round(modifier, 2)
                    steal_tracking_dict[steal_nation_name]["Streak"] += 1
                else:
                    steal_tracking_dict[steal_nation_name]["Nation Name"] = nation_name
                    steal_tracking_dict[steal_nation_name]["Streak"] = 1
                stolen_count = int(desired_count * modifier)
                desired_count -= stolen_count
                player_resource_market_incomes[steal_player_id - 1][request_list.index(desired_resource)] += stolen_count
                player_action_log.append(f'{steal_nation_name} stole {stolen_count} {desired_resource} from you! ({int(modifier * 100)}%)')
                steal_player_action_log = player_action_logs[steal_player_id - 1]
                steal_player_action_log.append(f'Stole {stolen_count} {desired_resource} from {nation_name}.')
                player_action_logs[steal_player_id - 1] = steal_player_action_log

        #resolve
        player_resource_market_incomes[player_id - 1][0] -= dollars_paid
        player_resource_market_incomes[player_id - 1][request_list.index(desired_resource)] += desired_count

        #update rmdata
        new_entry = [current_turn_num, nation_info_masterlist[player_id - 1][0], 'Bought', desired_count, desired_resource]
        rmdata_update_list.append(new_entry)

        #update player_action_logs
        player_action_log.append(f'Bought {desired_count} {desired_resource} from the resource market for {dollars_paid} dollars.')
        player_action_logs[player_id - 1] = player_action_log


    #Prune Invalid Sell Actions
    for sell_action in market_sell_action_list:
        player_id = sell_action[0]
        sell_action[1] = sell_action[1][5:]
        sell_action_data = sell_action[1].split()
        desired_count = int(sell_action_data[0])
        desired_resource = ' '.join(sell_action_data[1:])
        player_action_log = player_action_logs[player_id - 1]

        #get resource stockpiles of player
        stockpile_list = []
        for i in range(len(request_list)):
            stockpile_list.append(economy_masterlist[player_id - 1][i][0])
        desired_resource_stockpile = float(stockpile_list[request_list.index(desired_resource)])

        #quantity check
        if desired_count > desired_resource_stockpile:
            player_action_log.append(f'Failed to sell {desired_count} {desired_resource}. You attempted to sell more of that resource than you had stored.')
            player_action_logs[player_id - 1] = player_action_log
            continue

        #event check
        if "Embargo" in active_games_dict[game_id]["Active Events"]:
            chosen_nation_name = active_games_dict[game_id]["Active Events"]["Embargo"]["Chosen Nation Name"]
            if nation_name == chosen_nation_name:
                player_action_log.append(f'Failed to sell {desired_count} {desired_resource}. Your nation is currently under an embargo.')
                player_action_logs[player_id - 1] = player_action_log
                continue
        
        #update rmdata
        new_entry = [current_turn_num, nation_info_masterlist[player_id - 1][0], 'Sold', desired_count, desired_resource]
        rmdata_update_list.append(new_entry)


    #Calculate Next Turn's Prices
    total_exchanged = [[0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0]]
    rmdata_recent_transaction_list = core.read_rmdata(rmdata_filepath, current_turn_num, 11, False)

    #count bought and sold values for each resource
    for transaction in rmdata_recent_transaction_list: 
        exchange = transaction[2]
        count = transaction[3]
        resource = transaction[4]
        resource_index = request_list.index(resource) - 1
        if exchange == 'Bought':    
            total_exchanged[resource_index][0] += count
        elif exchange == 'Sold':
            total_exchanged[resource_index][1] += count
    for transaction in rmdata_update_list: 
        exchange = transaction[2]
        count = transaction[3]
        resource = transaction[4]
        resource_index = request_list.index(resource) - 1
        if exchange == 'Bought':
            total_exchanged[resource_index][0] += count
        elif exchange == 'Sold':
            total_exchanged[resource_index][1] += count

    #calculate new prices using exchange data
    for i in range(len(base_prices)):
        base_price = base_prices[i]
        bought_last_11 = total_exchanged[i][0]
        sold_last_11 = total_exchanged[i][1]
        next_turn_price = base_price * ( (bought_last_11 + 25) / (sold_last_11 + 25) )
        if "Market Inflation" in active_games_dict[game_id]["Active Events"]:
            for resource_name in active_games_dict[game_id]["Active Events"]["Market Inflation"]["Affected Resources"]:
                event_resource_index = request_list.index(resource_name) - 1
                if i == event_resource_index:
                    next_turn_price *= 2
        elif "Market Recession" in active_games_dict[game_id]["Active Events"]:
            for resource_name in active_games_dict[game_id]["Active Events"]["Market Recession"]["Affected Resources"]:
                event_resource_index = request_list.index(resource_name) - 1
                if i == event_resource_index:
                    next_turn_price *= 0.5
        next_prices[i] = round(next_turn_price, 2)


    #Process Sell Actions
    for transaction in rmdata_update_list:
        nation_name = transaction[1]
        player_id = 1
        for nation_info in nation_info_masterlist:
            if nation_info[0] == nation_name:
                break
            player_id += 1
        exchange = transaction[2]
        desired_count = transaction[3]
        desired_resource = transaction[4]
        player_action_log = player_action_logs[player_id - 1]

        if exchange == 'Sold':
            
            #get resource stockpiles
            stockpile_list = []
            for i in range(len(request_list)):
                stockpile_list.append(economy_masterlist[player_id - 1][i][0])
            desired_resource_stockpile = float(stockpile_list[request_list.index(desired_resource)])

            #resolve
            desired_resource_price = next_prices[request_list.index(desired_resource) - 1]
            dollars_earned = desired_resource_price * desired_count
            dollars_earned = round(dollars_earned, 2)
            player_resource_market_incomes[player_id - 1][0] += dollars_earned
            player_resource_market_incomes[player_id - 1][request_list.index(desired_resource)] -= desired_count

            #update player_action_logs
            log_str = f'Sold {desired_count} {desired_resource} to the resource market for {dollars_earned} dollars.'
            player_action_log.append(log_str)
            player_action_logs[player_id - 1] = player_action_log

            #update statistics
            transactions_dict = active_games_dict[game_id]["Transactions Record"]
            transactions_dict[nation_name] += desired_count


    #Process Negative Values
    for i in range(player_count):
        player_id = i + 1
        resource_market_income = player_resource_market_incomes[player_id - 1]

        #get resource stockpile data
        stockpile_list = []
        for j in range(len(request_list)):
            stockpile_list.append(economy_masterlist[player_id - 1][j][0])

        #update stockpiles
        j = 0
        for stockpile in stockpile_list:
            if resource_market_income[j] < 0:
                stockpile = float(stockpile)
                stockpile += resource_market_income[j]
                stockpile = core.round_total_income(stockpile)
                economy_masterlist[player_id - 1][j][0] = stockpile
            j += 1

    #update playerdata.csv
    for economy_list in economy_masterlist:
        for resource_data_list in economy_list:
            resource_data_list = str(resource_data_list)
    for i, playerdata in enumerate(playerdata_list):
        playerdata[9] = economy_masterlist[i][0]
        playerdata[11] = economy_masterlist[i][1]
        playerdata[12] = economy_masterlist[i][2]
        playerdata[13] = economy_masterlist[i][3]
        playerdata[15] = economy_masterlist[i][4]
        playerdata[16] = economy_masterlist[i][5]
        playerdata[17] = economy_masterlist[i][6]
        playerdata[18] = economy_masterlist[i][7]
        playerdata[19] = economy_masterlist[i][8]
    with open(playerdata_filepath, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(core.player_data_header)
        writer.writerows(playerdata_list)


    # Update active_games.json
    with open("active_games.json", 'w') as json_file:
        json.dump(active_games_dict, json_file, indent=4)


    # Update rmdata.csv
    rmdata_all_transaction_list = core.read_rmdata(rmdata_filepath, current_turn_num, False, False)
    with open(rmdata_filepath, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(core.rmdata_header)
        writer.writerows(rmdata_all_transaction_list)
        writer.writerows(rmdata_update_list)
    
    return player_action_logs, player_resource_market_incomes

def resolve_missile_builds(missile_build_list, game_id, player_action_logs):
    '''Resolves Make Standard Missile and Make Nuclear Missile actions.'''

    #define core lists
    playerdata_filepath = f'gamedata/{game_id}/playerdata.csv'
    playerdata_list = core.read_file(playerdata_filepath, 1)

    #get needed information from players
    request_list = ['Common Metals', 'Advanced Metals', 'Uranium', 'Rare Earth Elements']
    economy_masterlist = core.get_economy_info(playerdata_list, request_list)
    missile_data_masterlist = []
    research_masterlist = []
    for player in playerdata_list:
        player_missile_data = ast.literal_eval(player[21])
        missile_data_masterlist.append(player_missile_data)
        player_research_list = ast.literal_eval(player[26])
        research_masterlist.append(player_research_list)

    
    #Execute Actions
    for missile_action in missile_build_list:
        player_id = missile_action[0]
        missile_action_list = missile_action[1].split(' ')
        order_count = int(missile_action_list[1])
        missile_type = ' '.join(missile_action_list[-2:])
        player_missile_data = missile_data_masterlist[player_id - 1]
        player_research = research_masterlist[player_id - 1]
        player_action_log = player_action_logs[player_id - 1]

        #get resource stockpiles of player
        stockpile_list = []
        for i in range(len(request_list)):
            stockpile_list.append(economy_masterlist[player_id - 1][i][0])
        common_stockpile = float(stockpile_list[0])
        advanced_stockpile = float(stockpile_list[1])
        uranium_stockpile = float(stockpile_list[2])
        rare_stockpile = float(stockpile_list[3])

        #required research check
        if missile_type == 'Standard Missile':
            research_check = core.verify_required_research('Missile Technology', player_research)
        else:
            research_check = core.verify_required_research('Nuclear Warhead', player_research)
        if research_check == False:
            player_action_log.append(f'Failed to manufacture {order_count}x {missile_type}. You do not have the required research.')
            player_action_logs[player_id - 1] = player_action_log
            continue

        #calculate costs
        if missile_type == 'Standard Missile':
            common_cost = 5 * order_count
            advanced_cost = 0
            uranium_cost = 0
            rare_cost = 0
        else:
            common_cost = 0
            advanced_cost = 2 * order_count
            uranium_cost = 2 * order_count
            rare_cost = 2 * order_count

        #attempt to pay for missile
        if (common_stockpile - common_cost >= 0) and (advanced_stockpile - advanced_cost >= 0) and (uranium_stockpile - uranium_cost >= 0) and (rare_stockpile - rare_cost >= 0):
            economy_masterlist[player_id - 1][0][0] = core.update_stockpile(common_stockpile, common_cost)
            economy_masterlist[player_id - 1][1][0] = core.update_stockpile(advanced_stockpile, advanced_cost)
            economy_masterlist[player_id - 1][2][0] = core.update_stockpile(uranium_stockpile, uranium_cost)
            economy_masterlist[player_id - 1][3][0] = core.update_stockpile(rare_stockpile, rare_cost)
            if missile_type == 'Standard Missile':
                player_missile_data[0] += 1 * order_count
            else:
                player_missile_data[1] += 1 * order_count
            missile_data_masterlist[player_id - 1] = player_missile_data
            player_action_log.append(f'Manufactured {order_count}x {missile_type}.')
        else:
            player_action_log.append(f'Failed to manufacture {order_count}x {missile_type}. Insufficient resources.')
        player_action_logs[player_id - 1] = player_action_log


    #Update playerdata.csv
    for economy_list in economy_masterlist:
        for resource_data_list in economy_list:
            resource_data_list = str(resource_data_list)
    for player_missile_data in missile_data_masterlist:
        player_missile_data = str(player_missile_data)
    for index, playerdata in enumerate(playerdata_list):
        playerdata[16] = economy_masterlist[index][0]
        playerdata[17] = economy_masterlist[index][1]
        playerdata[18] = economy_masterlist[index][2]
        playerdata[19] = economy_masterlist[index][3]
        playerdata[21] = missile_data_masterlist[index]
    with open(playerdata_filepath, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(core.player_data_header)
        writer.writerows(playerdata_list)

    return player_action_logs

def resolve_peace_actions(peace_action_list, game_id, current_turn_num, player_action_logs):
    '''Process all surrender and white peace actions.'''

    # get core lists
    playerdata_filepath = f'gamedata/{game_id}/playerdata.csv'
    playerdata_list = core.read_file(playerdata_filepath, 1)
    notifications = Notifications(game_id)

    # get needed information from players
    nation_info_masterlist = core.get_nation_info(playerdata_list)
    nation_name_list = []
    for nation_info in nation_info_masterlist:
        nation_name_list.append(nation_info[0])
    diplomatic_relations_masterlist = []
    for player in playerdata_list:
        diplomatic_relations_masterlist.append(ast.literal_eval(player[22]))


    # Execute Actions
    wardata = WarData(game_id)
    white_peace_dict = {}
    for peace_action in peace_action_list:
        
        # decrypt action
        player_id_1 = peace_action[0]
        action_str = peace_action[1]
        nation_name_1 = nation_name_list[player_id_1 - 1]
        player_action_log = player_action_logs[player_id_1 - 1]

        # process for surrender action
        if 'Surrender' in action_str:

            # get player 2 info
            nation_name_2 = action_str[10:]
            player_id_2 = nation_name_list.index(nation_name_2) + 1

            # check if player 1 has the authority to surrender
            war_name = wardata.are_at_war(player_id_1, player_id_2, True)
            if not war_name:
                player_action_log.append(f'Failed to surrender to {nation_name_2}. You are not at war with that nation.')
                player_action_logs[player_id_1 - 1] = player_action_log
                continue
            war_role_1 = wardata.get_war_role(nation_name_1, war_name)
            if 'Main' not in war_role_1:
                player_action_log.append(f'Failed to surrender to {nation_name_2}. You are not the main attacker/defender or {nation_name_2} is not the main attacker/defender.')
                player_action_logs[player_id_1 - 1] = player_action_log
                continue

            # resolve war
            if 'Attacker' in war_role_1:
                outcome = 'Defender Victory'
            else:
                outcome = 'Attacker Victory'
            wardata.end_war(war_name, outcome)
            notifications.append(f'{nation_name_1} surrendered to {nation_name_2}.', 4)
            notifications.append(f'{war_name} has ended.', 4)
            
        # process for white peace action
        elif 'White Peace' in action_str:

            # get player 2 info
            nation_name_2 = action_str[12:]
            player_id_2 = nation_name_list.index(nation_name_2) + 1
            
            # check if player 1 has the authority to white peace
            war_name = wardata.are_at_war(player_id_1, player_id_2, True)
            if not war_name:
                player_action_log.append(f'Failed to white peace with {nation_name_2}. You are not at war with that nation.')
                player_action_logs[player_id_1 - 1] = player_action_log
                continue
            war_role_1 = wardata.get_war_role(nation_name_1, war_name)
            if 'Main' not in war_role_1:
                player_action_log.append(f'Failed to white peace with {nation_name_2}. You are not the main attacker/defender or {nation_name_2} is not the main attacker/defender.')
                player_action_logs[player_id_1 - 1] = player_action_log
                continue
                
            # add white peace request to white_peace_dict
            if war_name in white_peace_dict:
                white_peace_dict[war_name] += 1
            else:
                white_peace_dict[war_name] = 1
    
    # process white peace if both sides agreed
    for war_name in white_peace_dict:
        if white_peace_dict[war_name] == 2:
            outcome = 'White Peace'
            wardata.end_war(war_name, outcome)
            notifications.append(f'{war_name} has ended with a white peace.', 4)

    # update playerdata.csv
    playerdata_list = core.read_file(playerdata_filepath, 1)
    for index, player in enumerate(playerdata_list):
        player[22] = str(diplomatic_relations_masterlist[index])
    with open(playerdata_filepath, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(core.player_data_header)
        writer.writerows(playerdata_list)
    
    return player_action_logs

def resolve_region_purchases(region_purchase_list, game_id, player_action_logs):
    '''Resolves all region purchase actions and region disputes.'''
    
    # get core lists
    playerdata_filepath = f'gamedata/{game_id}/playerdata.csv'
    playerdata_list = core.read_file(playerdata_filepath, 1)
    with open('active_games.json', 'r') as json_file:
        active_games_dict = json.load(json_file)

    # get needed economy information from each player
    request_list = ['Dollars', 'Political Power']
    nation_info_masterlist = core.get_nation_info(playerdata_list)
    economy_masterlist = core.get_economy_info(playerdata_list, request_list)


    # Execute Actions
    region_queue: list[Region] = []
    for region_purchase in region_purchase_list:
        player_id = region_purchase[0]
        region_id = region_purchase[1][-5:]
        player_action_log = player_action_logs[player_id - 1]
        region = Region(region_id, game_id)

        # ownership check
        if region.owner_id != 0:
            player_action_log.append(f'Failed to purchase {region_id}. This region is already claimed by another nation.')
            player_action_logs[player_id - 1] = player_action_log
            continue

        # adjacency check
        # to be added

        # event check
        if "Widespread Civil Disorder" in active_games_dict[game_id]["Active Events"]:
            player_action_log.append(f'Failed to purchase {region_id} due to the Widespread Civil Disorder event.')
            player_action_logs[player_id - 1] = player_action_log
            continue

        # affordability check
        player_government = nation_info_masterlist[player_id - 1][2]
        dollars_stockpile = economy_masterlist[player_id - 1][0][0]
        dollars_stockpile = float(dollars_stockpile)
        pp_stockpile = economy_masterlist[player_id - 1][1][0]
        pp_stockpile = float(pp_stockpile)
        if player_government != 'Remnant':
            pp_cost = 0
        else:
            pp_cost = 0.20
        if (dollars_stockpile - region.purchase_cost) < 0 or (pp_stockpile - pp_cost) < 0:
            player_action_log.append(f'Failed to purchase {region_id}. Insufficient resources.')
            player_action_logs[player_id - 1] = player_action_log
            continue

        # all checks passed add to region_queue
        if region not in region_queue:
            region.add_claim(player_id)
            region_queue.append(region)
        else:
            index = region_queue.index(region)
            existing_region = region_queue[index]
            existing_region.add_claim(player_id)
            region_queue[index] = existing_region
    

    # Process Queue
    for region in region_queue:

        # region purchase successful
        if len(region.claim_list) == 1:
            player_id = region.claim_list[0]
            player_action_log = player_action_logs[player_id - 1]
            pay_for_region(region, economy_masterlist, nation_info_masterlist, player_id)
            region.set_owner_id(player_id)
            player_action_log.append(f'Successfully purchased region {region.region_id} for {region.purchase_cost} dollars.')

        # region dispute
        else:
            region.increase_purchase_cost()
            active_games_dict[game_id]["Statistics"]["Region Disputes"] += 1
            for player_id in region.claim_list:
                player_action_log = player_action_logs[player_id - 1]
                pay_for_region(region, economy_masterlist, nation_info_masterlist, player_id)
                player_action_log.append(f'Failed to purchase {region.region_id} due to a region dispute.')

        player_action_logs[player_id - 1] = player_action_log
    

    #Update playerdata.csv
    for economy_list in economy_masterlist:
        for resource_data_list in economy_list:
            resource_data_list = str(resource_data_list)
    for i, playerdata in enumerate(playerdata_list):
        playerdata[9] = economy_masterlist[i][0]
        playerdata[10] = economy_masterlist[i][1]
    with open(playerdata_filepath, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(core.player_data_header)
        writer.writerows(playerdata_list)

    #Update Active Games
    with open('active_games.json', 'w') as json_file:
        json.dump(active_games_dict, json_file, indent=4)
    
    return player_action_logs

def pay_for_region(region:Region, economy_masterlist, nation_info_masterlist, player_id):
    '''
    Helper function for resolve_region_purchases()
    I intend to remove this once the playerdata class is made.
    '''
    player_government = nation_info_masterlist[player_id - 1][2]
    dollars_stockpile = economy_masterlist[player_id - 1][0][0]
    dollars_stockpile = float(dollars_stockpile)
    pp_stockpile = economy_masterlist[player_id - 1][1][0]
    pp_stockpile = float(pp_stockpile)
    if player_government != 'Remnant':
        pp_cost = 0
    else:
        pp_cost = 0.20
    purchase_cost = region.purchase_cost
    economy_masterlist[player_id - 1][0][0] = core.update_stockpile(dollars_stockpile, purchase_cost)
    economy_masterlist[player_id - 1][1][0] = core.update_stockpile(pp_stockpile, pp_cost)
    return economy_masterlist

def resolve_research_actions(research_action_list, game_id, player_action_logs):
    '''Resolves all research actions.'''
    
    # get game data
    playerdata_filepath = f'gamedata/{game_id}/playerdata.csv'
    playerdata_list = core.read_file(playerdata_filepath, 1)
    regdata_filepath = f'gamedata/{game_id}/regdata.json'
    alliance_table = AllianceTable(game_id)
    agenda_data_dict = core.get_scenario_dict(game_id, "Agendas")
    research_data_dict = core.get_scenario_dict(game_id, "Technologies")
    with open(regdata_filepath, 'r') as json_file:
        regdata_dict = json.load(json_file)

    # get needed economy information from each player
    request_list = ['Political Power', 'Technology']
    economy_masterlist = core.get_economy_info(playerdata_list, request_list)
    nation_info_masterlist = core.get_nation_info(playerdata_list)
    nation_name_list = []
    research_masterlist = []
    for player in playerdata_list:
        nation_name_list.append(player[1])
        player_research_list = ast.literal_eval(player[26])
        research_masterlist.append(player_research_list)


    # Execute Research Actions
    for research_action in research_action_list:
        player_id = research_action[0]
        research_name = research_action[1][9:]
        nation_name = playerdata_list[player_id - 1][1]
        player_research_list = research_masterlist[player_id - 1]
        player_gov = nation_info_masterlist[player_id - 1][2]
        player_fp = nation_info_masterlist[player_id - 1][3]
        player_action_log = player_action_logs[player_id - 1]

        # get resource stockpiles
        stockpile_list = []
        for i in range(len(request_list)):
            stockpile_list.append(economy_masterlist[player_id - 1][i][0])
        political_stockpile = float(stockpile_list[0])
        tech_stockpile = float(stockpile_list[1])

        # duplication check
        if research_name in player_research_list:
            player_action_log.append(f'Failed to research {research_name}. You have already researched this.')
            player_action_logs[player_id - 1] = player_action_log
            continue

        # event check
        with open('active_games.json', 'r') as json_file:
            active_games_dict = json.load(json_file)
        if "Humiliation" in active_games_dict[game_id]["Active Events"]:
            chosen_nation_name = active_games_dict[game_id]["Active Events"]["Humiliation"]["Chosen Nation Name"]
            if nation_name == chosen_nation_name and research_name in agenda_data_dict:
                player_action_log.append(f'Failed to research {research_name} due to Humiliation event.')
                player_action_logs[player_id - 1] = player_action_log
                continue

        # identify research type
        if research_name == 'Ree Mining':
            research_name = 'REE Mining'
        if research_name in agenda_data_dict:
            tech_type = "Agenda"
            tech_dict = agenda_data_dict
            resource = "political power"
            stockpile = political_stockpile
            agenda_type = tech_dict[research_name]['Agenda Type']
        elif research_name in research_data_dict:
            tech_type = "Technology"
            tech_dict = research_data_dict
            resource = "technology"
            stockpile = tech_stockpile
        cost = tech_dict[research_name]['Cost']
        prereq = tech_dict[research_name]['Prerequisite']

        # prereq check
        if prereq not in player_research_list and prereq != None:
            player_action_log.append(f'Failed to research {research_name}. You do not have the prerequisite research.')
            player_action_logs[player_id - 1] = player_action_log
            continue

        # cost check
        if tech_type == "Agenda":
            # agenda cost adjustment
            agenda_cost_adjustment = {
                "Diplomacy": {
                    "Diplomatic": -5,
                    "Commercial": 0,
                    "Isolationist": 5,
                    "Imperialist": 0
                },
                "Economy": {
                    "Diplomatic": 0,
                    "Commercial": -5,
                    "Isolationist": 0,
                    "Imperialist": 5
                },
                "Security": {
                    "Diplomatic": 0,
                    "Commercial": 5,
                    "Isolationist": -5,
                    "Imperialist": 0,
                    
                },
                "Warfare": {
                    "Diplomatic": 5,
                    "Commercial": 0,
                    "Isolationist": 0,
                    "Imperialist": -5,
                }
            }
            cost += agenda_cost_adjustment[agenda_type][player_fp]
        elif tech_type == "Technology":
            # research agreement deductions
            sale_price = 1.0
            for alliance in alliance_table:
                if alliance.is_active and nation_name in alliance.current_members and alliance.type == "Research Agreement":
                    for ally_name in alliance.current_members:
                        if ally_name == nation_name:
                            continue
                        ally_player_id = nation_name_list.index(ally_name) + 1
                        if research_name in research_masterlist[ally_player_id - 1]:
                            sale_price -= 0.2
                            break
            if sale_price < 0:
                sale_price = 0.2
            if sale_price != 1.0:
                cost *= sale_price
                cost = int(cost)
        if (stockpile - cost) < 0:
            player_action_log.append(f'Failed to research {research_name}. Not enough {resource}.')
            player_action_logs[player_id - 1] = player_action_log
            continue

        # pay for and gain tech
        if tech_type == "Agenda":
            economy_masterlist[player_id - 1][0][0] = core.update_stockpile(stockpile, cost)
        else:
            economy_masterlist[player_id - 1][1][0] = core.update_stockpile(stockpile, cost)
            # totalitarian bonus
            totalitarian_discounts = {'Energy', 'Infrastructure'}
            if player_gov == 'Totalitarian' and tech_dict[research_name]["Research Type"] in totalitarian_discounts:
                economy_masterlist[player_id - 1][0][0] = political_stockpile + 2
                player_action_log.append(f'Gained 2 political power for researching {research_name}.')
            # special case for open pit mining
            if research_name == 'Open Pit Mining':
                for region_id in regdata_dict:
                    region = Region(region_id, game_id)
                    region_improvement = Improvement(region_id, game_id)
                    if region_improvement.name == 'Strip Mine' and region.owner_id == player_id:
                        if region_improvement.turn_timer > 4:
                            region_improvement.set_turn_timer()
        player_research_list.append(research_name)
        research_masterlist[player_id - 1] = player_research_list
        player_action_log.append(f'Researched {research_name} for {cost} {resource}.')
        player_action_logs[player_id - 1] = player_action_log

    
    #Update playerdata.csv
    for economy_list in economy_masterlist:
        for resource_data_list in economy_list:
            resource_data_list = str(resource_data_list)
    for player_research_list in research_masterlist:
        player_research_list.sort()
        player_research_list = str(player_research_list)
    i = 0
    for playerdata in playerdata_list:
        playerdata[10] = economy_masterlist[i][0]
        playerdata[11] = economy_masterlist[i][1]
        playerdata[26] = research_masterlist[i] 
        i += 1
    with open(playerdata_filepath, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(core.player_data_header)
        writer.writerows(playerdata_list)
    
    return player_action_logs

def resolve_trades(game_id):
    '''Resolves trade actions between players through the terminial.'''

    notifications = Notifications(game_id)
    trade_action = input("Are there any trade actions this turn? (Y/N) ")
    
    #Action Loop
    while trade_action == 'Y':
        nation1_name = input("Enter 1st nation name: ")
        nation2_name = input("Enter 2nd nation name: ")
        playerdata_filepath = f'gamedata/{game_id}/playerdata.csv'
        playerdata_list = core.read_file(playerdata_filepath, 1)
        nation_info_masterlist = core.get_nation_info(playerdata_list)
        request_list = ['Dollars', 'Technology', 'Coal', 'Oil', 'Green Energy', 'Basic Materials', 'Common Metals', 'Advanced Metals', 'Uranium', 'Rare Earth Elements']
        economy_masterlist = core.get_economy_info(playerdata_list, request_list)
        with open(f'gamedata/{game_id}/regdata.json', 'r') as json_file:
            regdata_dict = json.load(json_file)
        with open('active_games.json', 'r') as json_file:
            active_games_dict = json.load(json_file)
        
        #get player ids
        nation1_id = 0
        nation2_id = 0
        for index, nation_info_list in enumerate(nation_info_masterlist):
            if nation_info_list[0] == nation1_name:
                nation1_id = index + 1
            if nation_info_list[0] == nation2_name:
                nation2_id = index + 1
        
        #ensures nation names are correct
        if nation1_id == 0 or nation2_id == 0:
            print("Invalid nation name(s) were given. Please try again.")
            continue
        
        #print table
        trade_header_str = f'Trade Between {nation1_name} and {nation2_name}'
        print(trade_header_str)
        print("{:<21s}{:<33s}{:<33s}".format('Resource', nation1_name, nation2_name))
        for i in range(len(request_list)):
            print("{:<21s}{:<33s}{:<33s}".format(request_list[i], economy_masterlist[nation1_id-1][i][0], economy_masterlist[nation2_id-1][i][0]))
        

        #Get Trade Deal
        #get resource trades
        trade_difference_list = []
        resource_trade = input("Will any resources be traded in this deal? (Y/N) ")
        if resource_trade == 'Y':
            for resource in core.RESOURCE_LIST:
                if resource == 'Political Power':
                    continue
                resource_count = float(input(f'Enter {resource} amount: '))
                trade_difference_list.append(resource_count)
        #get region trades
        region_trade = input("Will any regions be traded in this deal? (Y/N) ")
        if region_trade == 'Y':
            invalid_region_given = True
            while invalid_region_given:
                nation1_region_trades_str = input(f'Enter regions {nation1_name} is trading away: ')
                nation1_region_trades_list = nation1_region_trades_str.split(',')
                invalid_region_given = False
                for region_id in nation1_region_trades_list:
                    if region_id not in regdata_dict and region_id != 'NONE':
                        invalid_region_given = True
                        print("An invalid region id was provided. Please try again.")
                        break
            invalid_region_given = True
            while invalid_region_given:
                nation2_region_trades_str = input(f'Enter regions {nation2_name} is trading away: ')
                nation2_region_trades_list = nation2_region_trades_str.split(',')
                invalid_region_given = False
                for region_id in nation2_region_trades_list:
                    if region_id not in regdata_dict and region_id != 'NONE':
                        invalid_region_given = True
                        print("An invalid region id was provided. Please try again.")
                        break


        #Calculate Trade Fee and Check if Deal is Honest
        trade_valid = True
        nation1_trade_fee = nation_info_masterlist[nation1_id-1][5]
        nation2_trade_fee = nation_info_masterlist[nation2_id-1][5]
        nation1_trade_fee_owed = 0
        nation2_trade_fee_owed = 0
        if resource_trade == 'Y':
            for index, resource_difference in enumerate(trade_difference_list):
                resource_difference = float(resource_difference)
                #resource is flowing from nation2 to nation 1
                if resource_difference < 0:
                    nation1_resource_stockpile = economy_masterlist[nation1_id-1][index][0]
                    nation2_resource_stockpile = economy_masterlist[nation2_id-1][index][0]
                    nation1_resource_stockpile = float(nation1_resource_stockpile)
                    nation2_resource_stockpile = float(nation2_resource_stockpile)
                    if nation2_resource_stockpile + resource_difference < 0:
                        trade_valid = False
                        print(f'Trade between {nation1_name} and {nation2_name} failed. Insufficient resources.')
                        break
                    nation2_trade_fee_owed += nation2_trade_fee * (resource_difference * -1)
                #resource is flowing from nation1 to nation2
                elif resource_difference > 0:
                    nation1_resource_stockpile = economy_masterlist[nation1_id-1][index][0]
                    nation2_resource_stockpile = economy_masterlist[nation2_id-1][index][0]
                    nation1_resource_stockpile = float(nation1_resource_stockpile)
                    nation2_resource_stockpile = float(nation2_resource_stockpile)
                    if nation1_resource_stockpile - resource_difference < 0:
                        trade_valid = False
                        print(f'Trade between {nation1_name} and {nation2_name} failed. Insufficient resources.')
                        break
                    nation1_trade_fee_owed += nation1_trade_fee * resource_difference
            #check if trade fee can be paid
            if trade_valid == True:
                nation1_dollars_stockpile = economy_masterlist[nation1_id-1][0][0]
                nation2_dollars_stockpile = economy_masterlist[nation2_id-1][0][0]
                nation1_dollars_stockpile = float(nation1_dollars_stockpile)
                nation2_dollars_stockpile = float(nation2_dollars_stockpile)
                dollars_traded = trade_difference_list[0]
                nation1_dollars_stockpile -= float(dollars_traded)
                nation2_dollars_stockpile += float(dollars_traded)
                if nation1_trade_fee_owed > nation1_dollars_stockpile or nation2_trade_fee_owed > nation2_dollars_stockpile:
                    trade_valid = False
                    print(f'Trade between {nation1_name} and {nation2_name} failed. One or both players could not afford the trade fee.')
        

        #Process Traded Resources
        if trade_valid == True and resource_trade == 'Y':
            for index, resource_difference in enumerate(trade_difference_list):
                resource_difference = int(resource_difference)
                if resource_difference != 0:
                    #get stockpile info and convert
                    nation1_resource_stockpile = economy_masterlist[nation1_id-1][index][0]
                    nation2_resource_stockpile = economy_masterlist[nation2_id-1][index][0]
                    nation1_resource_stockpile = float(nation1_resource_stockpile)
                    nation2_resource_stockpile = float(nation2_resource_stockpile)
                    #process traded resources
                    nation1_resource_stockpile -= resource_difference
                    nation2_resource_stockpile += resource_difference
                    nation1_resource_stockpile = core.round_total_income(nation1_resource_stockpile)
                    nation2_resource_stockpile = core.round_total_income(nation2_resource_stockpile)
                    economy_masterlist[nation1_id-1][index][0] = nation1_resource_stockpile
                    economy_masterlist[nation2_id-1][index][0] = nation2_resource_stockpile
                    #update statistics
                    transactions_dict = active_games_dict[game_id]["Transactions Record"]
                    transactions_dict[nation1_name] += abs(resource_difference)
                    transactions_dict[nation2_name] += abs(resource_difference)
        
        #Process Traded Regions
        if trade_valid == True and region_trade == 'Y':
            if nation1_region_trades_list != 'NONE':
                for region_id in nation1_region_trades_list:
                    region = Region(region_id, game_id)
                    region.set_owner_id(nation2_id)
            if nation2_region_trades_list != 'NONE':
                for region_id in nation2_region_trades_list:
                    region = Region(region_id, game_id)
                    region.set_owner_id(nation1_id)
        
        #Process Trade Tax
        if trade_valid == True and resource_trade == 'Y':
            nation1_dollars_stockpile = economy_masterlist[nation1_id-1][0][0]
            nation2_dollars_stockpile = economy_masterlist[nation2_id-1][0][0]
            nation1_dollars_stockpile = float(nation1_dollars_stockpile)
            nation2_dollars_stockpile = float(nation2_dollars_stockpile)
            nation1_dollars_stockpile -= nation1_trade_fee_owed
            nation2_dollars_stockpile -= nation2_trade_fee_owed
            economy_masterlist[nation1_id-1][0][0] = core.round_total_income(nation1_dollars_stockpile)
            economy_masterlist[nation2_id-1][0][0] = core.round_total_income(nation2_dollars_stockpile)
        

        #Update playerdata.csv
        if trade_valid == True:
            for i, playerdata in enumerate(playerdata_list):
                playerdata[9] = economy_masterlist[i][0]
                playerdata[11:20] = economy_masterlist[i][1:10]
            with open(playerdata_filepath, 'w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(core.player_data_header)
                writer.writerows(playerdata_list)

        #Update active games
        with open('active_games.json', 'w') as json_file:
            json.dump(active_games_dict, json_file, indent=4)
        
        notifications.append(f'{nation1_name} traded with {nation2_name}.', 9)
        trade_action = input("Are there any additional trade actions this turn? (Y/N) ")
        print('==================================================')

def resolve_event_actions(event_action_list, game_id, current_turn_num, player_action_logs):
    
    playerdata_filepath = f'gamedata/{game_id}/playerdata.csv'
    trucedata_filepath = f'gamedata/{game_id}/playerdata.csv'
    playerdata_list = core.read_file(playerdata_filepath, 1)
    trucedata_list = core.read_file(trucedata_filepath, 1)
    nation_name_list = []
    for playerdata in playerdata_list:
        nation_name_list.append(playerdata[1])
    with open('active_games.json', 'r') as json_file:
        active_games_dict = json.load(json_file)

    research_data_dict = core.get_scenario_dict(game_id, "Technologies")
    unit_data_dict = core.get_scenario_dict(game_id, "Units")
    
    for event_action in event_action_list:
        player_id = event_action[0]
        event_action_str = event_action[1]
        nation_name = playerdata_list[player_id - 1][1]
        player_action_log = player_action_logs[player_id - 1]

        #Format: "Event Host Peace Talks [ID]"
        if 'Host Peace Talks' in event_action_str:
            #required event check
            if "Nominate Mediator" not in active_games_dict[game_id]["Active Events"]:
                player_action_log.append(f'Failed to Host Peace Talks. Nominate Mediator event is not active.')
                player_action_logs[player_id - 1] = player_action_log
                continue
            #mediator check
            if active_games_dict[game_id]["Active Events"]["Nominate Mediator"]["Chosen Nation Name"] != nation_name:
                player_action_log.append(f'Failed to Host Peace Talks. You are not the Mediator.')
                player_action_logs[player_id - 1] = player_action_log
                continue
            for truce in trucedata_list:
                truce_id = str(truce[0])
                mediator_in_truce = truce[player_id]
                truce_expire_turn = int(truce[11])
                if truce_id in event_action_str and truce_expire_turn >= current_turn_num:
                    #already extended check
                    if truce_id in active_games_dict[game_id]["Active Events"]["Nominate Mediator"]["Extended Truces List"]:
                        player_action_log.append(f'Failed to Host Peace Talks for Truce #{truce[0]}. Truce has already been extended.')
                        player_action_logs[player_id - 1] = player_action_log
                        break
                    #player involved check
                    if mediator_in_truce:
                        player_action_log.append(f'Failed to Host Peace Talks for Truce #{truce[0]}. Mediator is involved in this truce.')
                        player_action_logs[player_id - 1] = player_action_log
                        break
                    #success
                    political_power_economy_data = ast.literal_eval(playerdata_list[player_id - 1][10])
                    political_power_stored = float(political_power_economy_data[0])
                    political_power_stored -= 5
                    political_power_economy_data[0] = core.round_total_income(political_power_stored)
                    playerdata_list[player_id - 1][10] = str(political_power_economy_data)
                    truce[11] = truce_expire_turn + 4
                    active_games_dict[game_id]["Active Events"]["Nominate Mediator"]["Extended Truces List"].append(truce_id)
                    player_action_log.append(f'Used Host Peace Talks on Truce #{truce[0]}.')
                    player_action_logs[player_id - 1] = player_action_log
                    break
                #truce expired check
                elif truce_id in event_action_str and truce_expire_turn < current_turn_num:
                    player_action_log.append(f'Failed to Host Peace Talks for Truce #{truce[0]}. Truce has already expired.')
                    player_action_logs[player_id - 1] = player_action_log
                    break

        #Format: "Event Cure Research [Count]"
        elif "Cure Research" in event_action_str:
            if "Pandemic" not in active_games_dict[game_id]["Active Events"]:
                player_action_log.append(f'Failed to do Cure Research action. Pandemic event is not active.')
                player_action_logs[player_id - 1] = player_action_log
                continue
            event_action_data = event_action_str.split(" ")
            count = int(event_action_data[-1])
            research_amount = count
            technology_economy_data = ast.literal_eval(playerdata_list[player_id - 1][11])
            technology_stored = float(technology_economy_data[0])
            if technology_stored < count:
                player_action_log.append(f'Failed to Cure Research. Insufficient resources.')
                player_action_logs[player_id - 1] = player_action_log
                continue
            technology_stored -= count
            technology_economy_data[0] = core.round_total_income(technology_stored)
            playerdata_list[player_id - 1][11] = str(technology_economy_data)
            active_games_dict[game_id]['Active Events']["Pandemic"]["Completed Cure Research"] += research_amount
            player_action_log.append(f'Used Cure Research to spend {count} technology in exchange for {research_amount} cure progress.')
            player_action_logs[player_id - 1] = player_action_log


        #Format: "Event Fundraise [Count]"
        elif "Fundraise" in event_action_str:
            if "Pandemic" not in active_games_dict[game_id]["Active Events"]:
                player_action_log.append(f'Failed to do Fundraise action . Pandemic event is not active.')
                player_action_logs[player_id - 1] = player_action_log
                continue
            event_action_data = event_action_str.split(" ")
            count = int(event_action_data[-1])
            research_amount = count // 3
            dollars_economy_data = ast.literal_eval(playerdata_list[player_id - 1][9])
            dollars_stored = float(dollars_economy_data[0])
            if dollars_stored < count:
                player_action_log.append(f'Failed to Fundraise. Insufficient resources.')
                player_action_logs[player_id - 1] = player_action_log
                continue
            dollars_stored -= count
            dollars_economy_data[0] = core.round_total_income(dollars_stored)
            playerdata_list[player_id - 1][9] = str(dollars_economy_data)
            active_games_dict[game_id]['Active Events']["Pandemic"]["Completed Cure Research"] += research_amount
            player_action_log.append(f'Used Fundraise to spend {count} dollars in exchange for {research_amount} cure progress.')
            player_action_logs[player_id - 1] = player_action_log

        #Format: "Event Inspect [Region ID]"
        elif "Inspect" in event_action_str:
            if "Pandemic" not in active_games_dict[game_id]["Active Events"]:
                player_action_log.append(f'Failed to do Inspect action. Pandemic event is not active.')
                player_action_logs[player_id - 1] = player_action_log
                continue
            event_action_data = event_action_str.split(" ")
            region_id = event_action_data[-1]
            dollars_economy_data = ast.literal_eval(playerdata_list[player_id - 1][9])
            dollars_stored = float(dollars_economy_data[0])
            if dollars_stored < 5:
                player_action_log.append(f'Failed to do Inspect action. Insufficient resources.')
                player_action_logs[player_id - 1] = player_action_log
                continue
            dollars_stored -= 5
            dollars_economy_data[0] = core.round_total_income(dollars_stored)
            playerdata_list[player_id - 1][9] = str(dollars_economy_data)
            region = Region(region_id, game_id)
            player_action_log.append(f'Used Inspect action for 5 dollars. Region {region_id} has an infection score of {region.infection()}/10.')
            player_action_logs[player_id - 1] = player_action_log

        #Format: "Event Create Quarantine [Region ID]"
        elif "Create Quarantine" in event_action_str:
            if "Pandemic" not in active_games_dict[game_id]["Active Events"]:
                player_action_log.append(f'Failed to do Create Quarantine action. Pandemic event is not active.')
                player_action_logs[player_id - 1] = player_action_log
                continue
            event_action_data = event_action_str.split(" ")
            region_id = event_action_data[-1]
            political_power_economy_data = ast.literal_eval(playerdata_list[player_id - 1][10])
            political_power_stored = float(political_power_economy_data[0])
            if political_power_stored < 1:
                player_action_log.append(f'Failed to do Create Quarantine action. Insufficient resources.')
                player_action_logs[player_id - 1] = player_action_log
                continue
            political_power_stored -= 1
            political_power_economy_data[0] = core.round_total_income(political_power_stored)
            region = Region(region_id, game_id)
            region.set_quarantine()
            player_action_log.append(f'Quarantined {region_id} for 1 political power.')
            player_action_logs[player_id - 1] = player_action_log

        #Format: "Event End Quarantine [Region ID]"
        elif "End Quarantine" in event_action_str:
            if "Pandemic" not in active_games_dict[game_id]["Active Events"]:
                player_action_log.append(f'Failed to do End Quarantine action. Pandemic event is not active.')
                player_action_logs[player_id - 1] = player_action_log
                continue
            event_action_data = event_action_str.split(" ")
            region_id = event_action_data[-1]
            political_power_economy_data = ast.literal_eval(playerdata_list[player_id - 1][10])
            political_power_stored = float(political_power_economy_data[0])
            if political_power_stored < 1:
                player_action_log.append(f'Failed to do End Quarantine action. Insufficient resources.')
                player_action_logs[player_id - 1] = player_action_log
                continue
            political_power_stored -= 1
            political_power_economy_data[0] = core.round_total_income(political_power_stored)
            region = Region(region_id, game_id)
            region.set_quarantine(False)
            player_action_log.append(f'Ended quarantine in {region_id} for 1 political power.')
            player_action_logs[player_id - 1] = player_action_log

        #Format: "Event Open Borders"
        elif "Open Borders" in event_action_str:
            if "Pandemic" not in active_games_dict[game_id]["Active Events"]:
                player_action_log.append(f'Failed to do Open Borders action. Pandemic event is not active.')
                player_action_logs[player_id - 1] = player_action_log
                continue
            political_power_economy_data = ast.literal_eval(playerdata_list[player_id - 1][10])
            political_power_stored = float(political_power_economy_data[0])
            if political_power_stored < 10:
                player_action_log.append(f'Failed to do Open Borders action. Insufficient resources.')
                player_action_logs[player_id - 1] = player_action_log
                continue
            political_power_stored -= 10
            political_power_economy_data[0] = core.round_total_income(political_power_stored)
            active_games_dict[game_id]['Active Events']["Pandemic"]["Closed Borders List"].remove(player_id)
            player_action_log.append('Spent 10 political power to Open Borders.')
            player_action_logs[player_id - 1] = player_action_log

        #Format: "Event Close Borders"
        elif "Close Borders" in event_action_str:
            if "Pandemic" not in active_games_dict[game_id]["Active Events"]:
                player_action_log.append(f'Failed to do Close Borders action. Pandemic event is not active.')
                player_action_logs[player_id - 1] = player_action_log
                continue
            political_power_economy_data = ast.literal_eval(playerdata_list[player_id - 1][10])
            political_power_stored = float(political_power_economy_data[0])
            if political_power_stored < 10:
                player_action_log.append(f'Failed to do Close Borders action. Insufficient resources.')
                player_action_logs[player_id - 1] = player_action_log
                continue
            political_power_stored -= 10
            political_power_economy_data[0] = core.round_total_income(political_power_stored)
            active_games_dict[game_id]['Active Events']["Pandemic"]["Closed Borders List"].append(player_id)
            player_action_log.append('Spent 10 political power to Close Borders.')
            player_action_logs[player_id - 1] = player_action_log
        
        #Format: Event Search For Artifacts [Region ID]
        elif "Search For Artifacts" in event_action_str:
            if "Faustian Bargain" not in active_games_dict[game_id]["Active Events"]:
                player_action_log.append(f'Failed to do Search For Artifacts action. Pandemic event is not active.')
                player_action_logs[player_id - 1] = player_action_log
                continue
            if active_games_dict[game_id]["Active Events"]["Faustian Bargain"]["Chosen Nation Name"] != nation_name:
                player_action_log.append(f'Failed to Search For Artifacts. You are not the collaborator.')
                player_action_logs[player_id - 1] = player_action_log
                continue
            event_action_data = event_action_str.split(" ")
            region_id = event_action_data[-1]
            region = Region(region_id, game_id)
            if region.owner_id != player_id:
                player_action_log.append(f'Failed to do Search For Artifacts action on {region_id}. You do not own that region.')
                player_action_logs[player_id - 1] = player_action_log
                continue
            dollars_economy_data = ast.literal_eval(playerdata_list[player_id - 1][9])
            dollars_stored = float(dollars_economy_data[0])
            if dollars_stored < 3:
                player_action_log.append(f'Failed to do Search For Artifacts action. Insufficient resources.')
                player_action_logs[player_id - 1] = player_action_log
                continue
            dollars_stored -= 3
            dollars_economy_data[0] = core.round_total_income(dollars_stored)
            playerdata_list[player_id - 1][9] = str(dollars_economy_data)
            if random.randint(1, 10) > 5:
                political_power_economy_data = ast.literal_eval(playerdata_list[player_id - 1][10])
                political_power_stored = float(political_power_economy_data[0])
                political_power_stored += 1
                political_power_economy_data[0] = core.round_total_income(political_power_stored)
                player_action_log.append(f'Spent 3 dollars to Search For Artifacts on region {region_id}. Artifacts found! Gained 1 political power.')
            else:
                player_action_log.append(f'Spent 3 dollars to Search For Artifacts on region {region_id}. No artifacts found!')
            player_action_logs[player_id - 1] = player_action_log

        #Format: Event Lease Region [Region ID]
        elif "Lease Region" in event_action_str:
            if "Faustian Bargain" not in active_games_dict[game_id]["Active Events"]:
                player_action_log.append(f'Failed to do Lease Region action. Pandemic event is not active.')
                player_action_logs[player_id - 1] = player_action_log
                continue
            if active_games_dict[game_id]["Active Events"]["Faustian Bargain"]["Chosen Nation Name"] != nation_name:
                player_action_log.append(f'Failed to Lease Region. You are not the collaborator.')
                player_action_logs[player_id - 1] = player_action_log
                continue
            event_action_data = event_action_str.split(" ")
            region_id = event_action_data[-1]
            region = Region(region_id, game_id)
            if region.owner_id != player_id:
                player_action_log.append(f'Failed to do Lease Region action on {region_id}. You do not own that region.')
                player_action_logs[player_id - 1] = player_action_log
                continue
            active_games_dict[game_id]["Active Events"]["Faustian Bargain"]["Leased Regions List"].append(region_id)
            player_action_log.append(f'Leased region {region_id} to the foreign nation.')
            player_action_logs[player_id - 1] = player_action_log

        #Format: Event Outsource Technology [Research Name]
        elif "Outsource Technology" in event_action_str:
            if "Faustian Bargain" not in active_games_dict[game_id]["Active Events"]:
                player_action_log.append(f'Failed to do Outsource Technology action. Pandemic event is not active.')
                player_action_logs[player_id - 1] = player_action_log
                continue
            if active_games_dict[game_id]["Active Events"]["Faustian Bargain"]["Chosen Nation Name"] != nation_name:
                player_action_log.append(f'Failed to Outsource Technology. You are not the collaborator.')
                player_action_logs[player_id - 1] = player_action_log
                continue
            political_power_economy_data = ast.literal_eval(playerdata_list[player_id - 1][10])
            political_power_stored = float(political_power_economy_data[0])
            if political_power_stored < 10:
                player_action_log.append(f'Failed to do Outsource Technology action. Insufficient resources.')
                player_action_logs[player_id - 1] = player_action_log
                continue
            event_action_list = event_action_str.split(" ")
            research_name = event_action_list[3:]
            research_name = " ".join(research_name)
            if research_name not in research_data_dict:
                player_action_log.append(f'Failed to do Outsource Technology action. Research name not recognized.')
                player_action_logs[player_id - 1] = player_action_log
                continue
            playerdata_list, valid_research = events.gain_free_research(game_id, research_name, player_id, playerdata_list)
            political_power_stored -= 10
            political_power_economy_data[0] = core.round_total_income(political_power_stored)
            player_action_log.append(f'Used Outsource Technology to research {research_name}.')
            player_action_logs[player_id - 1] = player_action_log

        #Format: Event Military Reinforcements [Unit Type] [Region ID #1],[Region ID #2]
        elif "Military Reinforcements" in event_action_str:
            if "Faustian Bargain" not in active_games_dict[game_id]["Active Events"]:
                player_action_log.append(f'Failed to do Military Reinforcements action. Pandemic event is not active.')
                player_action_logs[player_id - 1] = player_action_log
                continue
            if active_games_dict[game_id]["Active Events"]["Faustian Bargain"]["Chosen Nation Name"] != nation_name:
                player_action_log.append(f'Failed to Military Reinforcements. You are not the collaborator.')
                player_action_logs[player_id - 1] = player_action_log
                continue
            political_power_economy_data = ast.literal_eval(playerdata_list[player_id - 1][10])
            political_power_stored = float(political_power_economy_data[0])
            if political_power_stored < 10:
                player_action_log.append(f'Failed to do Military Reinforcements action. Insufficient resources.')
                player_action_logs[player_id - 1] = player_action_log
                continue
            event_action_data = event_action_str.split(" ")
            region_id_str = event_action_data[-1]
            unit_type = event_action_data[3:-1]
            unit_type = " ".join(unit_type)
            region_id_list = region_id_str.split(",")
            for region_id in region_id_list:
                region = Region(region_id, game_id)
                region_unit = Unit(region_id, game_id)
                if region.owner_id != player_id:
                    player_action_log.append(f'Failed to use Used Military Reinforcements to deploy {unit_type} {region_id}. You do not own that region.')
                    player_action_logs[player_id - 1] = player_action_log
                    continue
                region_unit.set_unit(unit_type, player_id)
                player_action_log.append(f'Used Military Reinforcements to deploy {unit_type} {region_id}.')
            political_power_stored -= 10
            political_power_economy_data[0] = core.round_total_income(political_power_stored)
            player_action_logs[player_id - 1] = player_action_log


    #Save Files
    with open(playerdata_filepath, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(core.player_data_header)
        writer.writerows(playerdata_list)
    with open(trucedata_filepath, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(core.trucedata_header)
        writer.writerows(trucedata_list)
    with open('active_games.json', 'w') as json_file:
        json.dump(active_games_dict, json_file, indent=4)
    
    return player_action_logs
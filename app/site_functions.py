import csv
import json
import random
import shutil
import os
from datetime import datetime
from operator import itemgetter

from app import core
from app import palette
from app.region import Region
from app.improvement import Improvement
from app.unit import Unit
from app.nationdata import NationTable
from app.alliance import AllianceTable
from app.war import WarTable
from app.notifications import Notifications
from app import actions
from app import checks
from app import map
from app import events


# TURN PROCESSING
################################################################################

def resolve_stage1_processing(game_id: str, contents_dict: dict) -> None:
    """
    Resolves stage one setup for a new game.

    Params:
        game_id (str): Game ID string.
        contents_dict (dict): A dictionary containing the setup data for each player.
    
    Returns:
        None
    """

    # get game files
    nation_table = NationTable(game_id)
    with open(f'gamedata/{game_id}/regdata.json', 'r') as json_file:
        regdata_dict = json.load(json_file)

    # update nation colors
    for nation_id, setup_data in contents_dict.items():
        color_name = setup_data["color"]
        nation = nation_table.get(nation_id)
        player_color = palette.str_to_hex(color_name)
        nation.color = player_color
        nation_table.save(nation)

    # place chosen starts
    random_assignment_list = []
    for nation_id, setup_data in contents_dict.items():
        region_id = setup_data["start"]
        if region_id is None or region_id not in regdata_dict:
            random_assignment_list.append(nation_id)
            continue
        starting_region = Region(region_id, game_id)
        starting_region_improvement = Improvement(region_id, game_id)
        starting_region.set_owner_id(int(nation_id))
        starting_region_improvement.set_improvement("Capital")
        nation = nation_table.get(nation_id)
        nation.improvement_counts["Capital"] += 1
        nation_table.save(nation)

    # place random starts
    random.shuffle(random_assignment_list)
    for random_assignment_player_id in random_assignment_list:
        while True:
            # randomly select a region
            conflict_detected = False
            region_id_list = list(regdata_dict.keys()) 
            random_region_id = random.sample(region_id_list, 1)[0]
            random_region = Region(random_region_id, game_id)
            # if region not allowed restart loop
            if not random_region.is_start:
                continue
            # check if there is a player within three regions
            regions_in_radius = random_region.get_regions_in_radius(3)
            for candidate_region_id in regions_in_radius:
                candidate_region = Region(candidate_region_id, game_id)
                # if player found restart loop
                if candidate_region.owner_id != 0:
                    conflict_detected = True
                    break
            # if no player found place player
            if conflict_detected == False:
                random_region.set_owner_id(int(random_assignment_player_id))
                random_region_improvement = Improvement(random_region_id, game_id)
                random_region_improvement.set_improvement("Capital")
                nation = nation_table.get(nation_id)
                nation.improvement_counts["Capital"] += 1
                nation_table.save(nation)
                break
    
    # update active_games.json
    with open('active_games.json', 'r') as json_file:
        active_games_dict = json.load(json_file)
    active_games_dict[game_id]["Statistics"]["Current Turn"] = "Nation Setup in Progress"
    with open('active_games.json', 'w') as json_file:
        json.dump(active_games_dict, json_file, indent=4)
    
    # generate and update maps
    current_turn_num = core.get_current_turn_num(game_id)
    map_name = core.get_map_name(game_id)
    main_map = map.MainMap(game_id, map_name, current_turn_num)
    resource_map = map.ResourceMap(game_id, map_name)
    control_map = map.ControlMap(game_id, map_name)
    resource_map.create()
    main_map.place_random()
    main_map.update()
    resource_map.update()
    control_map.update()

def resolve_stage2_processing(game_id: str, contents_dict: dict) -> None:
    """
    Resolves stage two setup for a new game.

    Params:
        game_id (str): Game ID string.
        contents_dict (dict): A dictionary containing the setup data for each player.
    
    Returns:
        None
    """

    # get game files
    nation_table = NationTable(game_id)
    research_data_dict = core.get_scenario_dict(game_id, "Technologies")
    five_point_research_list = []
    for key in research_data_dict:
        tech = research_data_dict[key]
        if tech["Cost"] == 5:
            five_point_research_list.append(key)

    # update nation data
    for nation_id, setup_data in contents_dict.items():
        nation = nation_table.get(nation_id)
        nation.name = setup_data["name_choice"]
        nation.gov = setup_data["gov_choice"]
        nation.fp = setup_data["fp_choice"]
        nation.chosen_vc_set = setup_data["vc_choice"]
        nation.reset_income_rates()
        if nation.gov == "Technocracy":
            starting_list = random.sample(five_point_research_list, 3)
            for technology_name in starting_list:
                nation.add_tech(technology_name)
        nation_table.save(nation)

    # update income in playerdata
    checks.update_income(game_id)
    nation_table.reload()
    nation_table.update_records()
    
    with open('active_games.json', 'r') as json_file:
        active_games_dict = json.load(json_file)

    # update game_settings
    active_games_dict[game_id]["Statistics"]["Current Turn"] = "1"
    current_date = datetime.today().date()
    current_date_string = current_date.strftime("%m/%d/%Y")
    active_games_dict[game_id]["Statistics"]["Game Started"] = current_date_string
    active_games_dict[game_id]["Statistics"]["Days Ellapsed"] = 0
    
    # add crime syndicate tracking
    # to do - move this somewhere else
    steal_tracking_dict = {}
    for nation in nation_table:
        if nation.gov == 'Crime Syndicate':
            inner_dict = {
                'Nation Name': None,
                'Streak': 0,
            }
            steal_tracking_dict[nation.name] = inner_dict
    active_games_dict[game_id]["Steal Action Record"] = steal_tracking_dict

    with open('active_games.json', 'w') as json_file:
        json.dump(active_games_dict, json_file, indent=4)
    
    # update visuals
    current_turn_num = 1
    map_name = active_games_dict[game_id]["Information"]["Map"]
    main_map = map.MainMap(game_id, map_name, current_turn_num)
    main_map.update()

def resolve_turn_processing(game_id: str, contents_dict: dict) -> None:
    """
    Resolves a normal turn.

    Params:
        game_id (str): Game ID string.
        contents_dict (dict): A dictionary containing the actions submitted by each player.

    Returns:
        None
    """
    
    notifications = Notifications(game_id)
    notifications.clear()
    current_turn_num = core.get_current_turn_num(game_id)
    
    actions_dict = {
        "AllianceCreateAction": [],
        "AllianceJoinAction": [],
        "AllianceLeaveAction": [],
        "ClaimAction": [],
        "CrimeSyndicateAction": [],
        "EventAction": [],
        "ImprovementBuildAction": [],
        "ImprovementRemoveAction": [],
        "MarketBuyAction": [],
        "MarketSellAction": [],
        "MissileMakeAction": [],
        "MissileLaunchAction": [],
        "RepublicAction": [],
        "ResearchAction": [],
        "SurrenderAction": [],
        "UnitDeployAction": [],
        "UnitDisbandAction": [],
        "UnitMoveAction": [],
        "WarAction": [],
        "WhitePeaceAction": []
    }

    # sort actions
    for nation_id, actions_list in contents_dict.items():
        for action_str in actions_list:
            action = actions.validate_action(game_id, nation_id, action_str)
            if action is not None:
                class_name = type(action).__name__
                actions_dict[class_name].append(action)

    # prompt for missing war justifications
    checks.prompt_for_missing_war_justifications(game_id)
    
    # oppertunity to resolve active events
    events.resolve_active_events(game_id, "Before Actions", actions_dict)
    
    # resolve public actions
    actions.resolve_trade_actions(game_id)
    print("Resolving public actions...")
    actions.resolve_peace_actions(game_id, actions_dict["SurrenderAction"], actions_dict["WhitePeaceAction"])
    actions.resolve_research_actions(game_id, actions_dict["ResearchAction"])
    actions.resolve_alliance_leave_actions(game_id, actions_dict["AllianceLeaveAction"])
    actions.resolve_alliance_create_actions(game_id, actions_dict["AllianceCreateAction"])
    actions.resolve_alliance_join_actions(game_id, actions_dict["AllianceJoinAction"])
    actions.resolve_claim_actions(game_id, actions_dict["ClaimAction"])
    actions.resolve_improvement_remove_actions(game_id, actions_dict["ImprovementRemoveAction"])
    actions.resolve_improvement_build_actions(game_id, actions_dict["ImprovementBuildAction"])
    actions.resolve_missile_make_actions(game_id, actions_dict["MissileMakeAction"])
    actions.resolve_government_actions(game_id, actions_dict["RepublicAction"])
    actions.resolve_event_actions(game_id, actions_dict["EventAction"])
    market_results = actions.resolve_market_actions(game_id, actions_dict["CrimeSyndicateAction"], actions_dict["MarketBuyAction"], actions_dict["MarketSellAction"])

    # resolve private actions
    print("Resolving private actions...")
    actions.resolve_unit_disband_actions(game_id, actions_dict["UnitDisbandAction"])
    actions.resolve_unit_deployment_actions(game_id, actions_dict["UnitDeployAction"])
    actions.resolve_war_actions(game_id, actions_dict["WarAction"])
    actions.resolve_missile_launch_actions(game_id, actions_dict["MissileLaunchAction"])
    actions.resolve_unit_move_actions(game_id, actions_dict["UnitMoveAction"])

    # oppertunity to resolve active events
    events.resolve_active_events(game_id, "After Actions", actions_dict)

    # export logs
    nation_table = NationTable(game_id)
    for nation in nation_table:
        nation.export_action_log()
        nation.action_log = []
        nation_table.save(nation)
    war_table = WarTable(game_id)
    war_table.export_all_logs()

    # end of turn checks
    print("Resolving end of turn updates...")
    war_table.add_warscore_from_occupations()
    war_table.update_totals()
    checks.total_occupation_forced_surrender(game_id)
    checks.war_score_forced_surrender(game_id)
    checks.countdown(game_id)
    run_end_of_turn_checks(game_id)
    checks.gain_income(game_id)
    checks.gain_market_income(game_id, market_results)

    # update victory progress and check if player has won the game
    player_has_won = False
    nation_table.reload()
    for nation in nation_table:
        nation.update_victory_progress()
        if nation.score == 3:
            player_has_won = True
        nation_table.save(nation)

    if player_has_won:
        # game end procedure
        resolve_win(game_id)
    else:
        # bonus phase
        if current_turn_num % 4 == 0:
            checks.bonus_phase_heals(game_id)
            notifications.append('All units and defensive improvements have regained 2 health.', 1)
        if current_turn_num % 8 == 0:
            print("Triggering an event...")
            events.trigger_event(game_id)
            pass

    # update active game records
    core.update_turn_num(game_id)
    with open('active_games.json', 'r') as json_file:
        active_games_dict = json.load(json_file)
    start_date = active_games_dict[game_id]["Statistics"]["Game Started"]
    current_date = datetime.today().date()
    current_date_string = current_date.strftime("%m/%d/%Y")
    current_date_obj = datetime.strptime(current_date_string, "%m/%d/%Y")
    start_date_obj = datetime.strptime(start_date, "%m/%d/%Y")
    date_difference = current_date_obj - start_date_obj
    active_games_dict[game_id]["Statistics"]["Days Ellapsed"] = date_difference.days
    with open('active_games.json', 'w') as json_file:
        json.dump(active_games_dict, json_file, indent=4)

    # update game maps
    current_turn_num = core.get_current_turn_num(game_id)
    map_name = core.get_map_name(game_id)
    main_map = map.MainMap(game_id, map_name, current_turn_num)
    control_map = map.ControlMap(game_id, map_name)
    main_map.update()
    control_map.update()

def run_end_of_turn_checks(game_id: str) -> None:
    """
    Executes end of turn checks and updates.
    """

    nation_table = NationTable(game_id)

    nation_table.check_tags()

    checks.prune_alliances(game_id)
    checks.update_income(game_id)
    checks.resolve_resource_shortages(game_id)
    checks.resolve_military_capacity_shortages(game_id)
    checks.update_income(game_id)
    
    for nation in nation_table:
        nation.update_stockpile_limits()
        nation.update_trade_fee()
        nation_table.save(nation)

    nation_table.update_records()
    nation_table.add_leaderboard_bonuses()

def resolve_win(game_id: str) -> None:
    """
    Updates the game state and game records upon player victory.
    """

    nation_table = NationTable(game_id)
    current_turn_num = core.get_current_turn_num(game_id)
    with open('active_games.json', 'r') as json_file:
        active_games_dict = json.load(json_file)
    with open('game_records.json', 'r') as json_file:
        game_records_dict = json.load(json_file)

    game_name = active_games_dict[game_id]["Game Name"]

    # update active games
    active_games_dict[game_id]["Game Active"] = False
    with open('active_games.json', 'w') as json_file:
        json.dump(active_games_dict, json_file, indent=4)

    # update nation data in archive
    player_data_dict = {}
    for nation in nation_table:
        player_data_entry_dict = {
            "Nation Name": nation.name,
            "Color": nation.color,
            "Government": nation.gov,
            "Foreign Policy": nation.fp,
            "Score": nation.score,
            "Victory": 0
        }
        if nation.score == 3:
            player_data_entry_dict["Victory"] = 1
        player_data_dict[nation.player_id] = player_data_entry_dict
    game_records_dict[game_name]["Player Data"] = player_data_dict

    # update other stuff in archive
    current_date = datetime.today().date()
    current_date_string = current_date.strftime("%m/%d/%Y")
    game_records_dict[game_name]["Statistics"]["Game Ended"] = current_date_string
    game_records_dict[game_name]["Statistics"]["Game End Turn"] = current_turn_num
    game_records_dict[game_name]["Statistics"]["Game Started"] = active_games_dict[game_id]["Statistics"]["Game Started"]
    start_date = game_records_dict[game_name]["Statistics"]["Game Started"]
    current_date_obj = datetime.strptime(current_date_string, "%m/%d/%Y")
    start_date_obj = datetime.strptime(start_date, "%m/%d/%Y")
    date_difference = current_date_obj - start_date_obj
    game_records_dict[game_name]["Statistics"]["Days Ellapsed"] = date_difference.days
    with open('game_records.json', 'w') as json_file:
        json.dump(game_records_dict, json_file, indent=4)

def create_new_game(game_id: str, form_data_dict: dict, user_id_list: list) -> None:
    """
    Backend code for creating the files for a new game.

    Params:
        game_id (str): A valid game_id to be used for the new game.
        form_data_dict (dict): Dictionary of data gathered from the turn resolution HTML form.
        user_id_list (list): A list of all the user ids of players participating in the game.

    Returns:
        None
    """

    # open game record files
    with open('active_games.json', 'r') as json_file:
        active_games_dict = json.load(json_file)
    with open('game_records.json', 'r') as json_file:
        game_records_dict = json.load(json_file)

    # datetime stuff
    current_date = datetime.today().date()
    current_date_string = current_date.strftime("%m/%d/%Y")
    game_version = "Development"

    # generate game id
    # to be added

    # erase old game files
    erase_game(game_id)
    
    # update active_games
    active_games_dict[game_id]["Game Name"] = form_data_dict["Game Name"]
    active_games_dict[game_id]["Statistics"]["Player Count"] = form_data_dict["Player Count"]
    active_games_dict[game_id]["Information"]["Victory Conditions"] = form_data_dict["Victory Conditions"]
    active_games_dict[game_id]["Information"]["Map"] = form_data_dict["Map"]
    active_games_dict[game_id]["Information"]["Accelerated Schedule"] = form_data_dict["Accelerated Schedule"]
    active_games_dict[game_id]["Information"]["Turn Length"] = form_data_dict["Turn Length"]
    active_games_dict[game_id]["Information"]["Fog of War"] = form_data_dict["Fog of War"]
    active_games_dict[game_id]["Information"]["Deadlines on Weekends"] = form_data_dict["Deadlines on Weekends"]
    active_games_dict[game_id]["Information"]["Scenario"] = form_data_dict["Scenario"]
    active_games_dict[game_id]["Statistics"]["Current Turn"] = "Starting Region Selection in Progress"
    active_games_dict[game_id]["Game #"] = len(game_records_dict) + 1
    active_games_dict[game_id]["Information"]["Version"] = game_version
    active_games_dict[game_id]["Statistics"]["Days Ellapsed"] = 0
    active_games_dict[game_id]["Statistics"]["Game Started"] = current_date_string
    active_games_dict[game_id]["Statistics"]["Region Disputes"] = 0
    active_games_dict[game_id]["Inactive Events"] = []
    active_games_dict[game_id]["Active Events"] = {}
    active_games_dict[game_id]["Current Event"] = {}
    active_games_dict[game_id]["Game Active"] = True
    with open('active_games.json', 'w') as json_file:
        json.dump(active_games_dict, json_file, indent=4)
    
    # update game_records
    # to do - game records should not be updated at all until the game is concluded
    # really, active_games.json and game_records.json should be SQL tables
    new_game_entry = {}
    new_game_entry["Game ID"] = "temp"
    new_game_entry["Game #"] = len(game_records_dict) + 1
    new_game_entry["Information"] = {}
    new_game_entry ["Statistics"] = {}
    new_game_entry["Statistics"]["Player Count"] = int(form_data_dict["Player Count"])
    new_game_entry["Information"]["Victory Conditions"] = form_data_dict["Victory Conditions"]
    new_game_entry["Information"]["Map"] = form_data_dict["Map"]
    new_game_entry["Information"]["Accelerated Schedule"] = form_data_dict["Accelerated Schedule"]
    new_game_entry["Information"]["Turn Duration"] = form_data_dict["Turn Length"]
    new_game_entry["Information"]["Fog of War"] = form_data_dict["Fog of War"]
    new_game_entry["Information"]["Version"] = game_version
    new_game_entry["Information"]["Scenario"] = form_data_dict["Scenario"]
    new_game_entry["Statistics"]["Game End Turn"] = 0
    new_game_entry["Statistics"]["Days Ellapsed"] = 0
    new_game_entry["Statistics"]["Game Started"] = current_date_string
    new_game_entry["Statistics"]["Game Ended"] = 'Present'
    game_records_dict[form_data_dict["Game Name"]] = new_game_entry
    with open('game_records.json', 'w') as json_file:
        json.dump(game_records_dict, json_file, indent=4)

    # copy starting map images
    files_destination = f'gamedata/{game_id}'
    map_str = map.get_map_str(new_game_entry["Information"]["Map"])
    starting_map_images = ['resourcemap', 'controlmap']
    for map_filename in starting_map_images:
        shutil.copy(f"app/static/images/map_images/{map_str}/blank.png", f"{files_destination}/images")
        shutil.move(f"{files_destination}/images/blank.png", f"gamedata/{game_id}/images/{map_filename}.png")
    
    # create regdata.json
    shutil.copy(f"maps/{map_str}/regdata.json", files_destination)
    if form_data_dict["Scenario"] == 'Standard':
        with open(f'gamedata/{game_id}/regdata.json', 'r') as json_file:
            regdata_dict = json.load(json_file)
        for region_id in regdata_dict:
            regdata_dict[region_id]["regionData"]["infection"] = 0
            regdata_dict[region_id]["regionData"]["quarantine"] = False
        with open(f'gamedata/{game_id}/regdata.json', 'w') as json_file:
            json.dump(regdata_dict, json_file, indent=4)

    # create rmdata file
    rmdata_filepath = f'{files_destination}/rmdata.csv'
    with open(rmdata_filepath, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(core.rmdata_header)

    # create trucedata.csv
    # to do - store in gamedata.json and create truce class?
    with open(f'gamedata/{game_id}/trucedata.csv', 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(core.trucedata_header)

    # create gamedata.json
    gamedata_filepath = f'gamedata/{game_id}/gamedata.json'
    gamedata_dict = {}
    gamedata_dict["alliances"] = {}
    gamedata_dict["nations"] = {}
    gamedata_dict["notifications"] = {}
    gamedata_dict["victoryConditions"] = {}
    gamedata_dict["wars"] = {}
    with open(gamedata_filepath, 'w') as json_file:
        json.dump(gamedata_dict, json_file, indent=4)

    # create nationdata
    nation_table = NationTable(game_id)
    for i, user_id in enumerate(user_id_list):
        nation_table.create(i + 1, user_id)

def erase_game(game_id: str) -> None:
    """
    Erases all the game files of a given game.
    Note: This does not erase anything from the game_records.json file.
    """
    shutil.rmtree(f'gamedata/{game_id}')
    os.makedirs(f'gamedata/{game_id}/images')
    os.makedirs(f'gamedata/{game_id}/logs')


# MISC SITE FUNCTIONS
################################################################################

def get_data_for_nation_sheet(game_id: str, player_id: str) -> dict:
    '''
    Gathers all the needed data for a player's nation sheet data and spits it as a dict.

    Params:
        game_id (str): Game ID string.
        player_id (int): The integer id of the active player.
        current_turn_num (int): An integer number representing the game's current turn number.

    Returns:
        dict: player_information_dict.
    '''
    
    # get game data
    nation_table = NationTable(game_id)
    nation = nation_table.get(player_id)
    alliance_table = AllianceTable(game_id)
    war_table = WarTable(game_id)
    misc_data_dict = core.get_scenario_dict(game_id, "Misc")

    # build player info dict
    player_information_dict = {
        'Victory Conditions Data': {},
        'Resource Data': {},
        'Misc Info': {},
        'Alliance Data': {},
        'Missile Data': {},
        'Relations Data': {}
    }
    player_information_dict['Nation Name'] = nation.name
    player_information_dict['Color'] = nation.color
    player_information_dict['Government'] = nation.gov
    player_information_dict['Foreign Policy'] = nation.fp
    player_information_dict['Military Capacity'] = f"{nation.get_used_mc()} / {nation.get_max_mc()}"
    player_information_dict['Trade Fee'] = nation.trade_fee
    player_information_dict['Status'] = nation.status
    
    # get victory condition data
    nation.update_victory_progress()
    player_information_dict['Victory Conditions Data']['Conditions List'] = list(nation.victory_conditions.keys())
    vc_colors = []
    for entry in nation.victory_conditions.values():
        if entry:
            vc_colors.append('#00ff00')
        else:
            vc_colors.append('#ff0000')
    player_information_dict['Victory Conditions Data']['Color List'] = vc_colors

    # resource data
    class_list = []
    name_list = []
    stored_list = []
    income_list = []
    rate_list = []
    for resource_name in nation._resources:
        if resource_name in ["Energy", "Military Capacity"]:
            continue
        name_list.append(resource_name)
        class_list.append(resource_name.lower().replace(" ", "-"))
        stored_list.append(f"{nation.get_stockpile(resource_name)} / {nation.get_max(resource_name)}")
        income_list.append(nation.get_income(resource_name))
        rate_list.append(f"{nation.get_rate(resource_name)}%")
    player_information_dict['Resource Data']['Class List'] = class_list
    player_information_dict['Resource Data']['Name List'] = name_list
    player_information_dict['Resource Data']['Stored List'] = stored_list
    player_information_dict['Resource Data']['Income List'] = income_list
    player_information_dict['Resource Data']['Rate List'] = rate_list

    # alliance data
    alliance_count, alliance_capacity = core.get_alliance_count(game_id, nation)
    player_information_dict['Alliance Data']['Name List'] = list(misc_data_dict["allianceTypes"].keys())
    alliance_colors = []
    alliance_data = [False, False, False, False]
    if 'Defensive Agreements' in nation.completed_research:
        alliance_data[0] = True
    if 'Peace Accords' in nation.completed_research:
        alliance_data[1] = True
    if 'Research Exchange' in nation.completed_research:
        alliance_data[2] = True
    if 'Trade Routes' in nation.completed_research:
        alliance_data[3] = True
    for entry in alliance_data:
        if entry:
            alliance_colors.append('#00ff00')
        else:
            alliance_colors.append('#ff0000')
    player_information_dict['Alliance Data']['Header'] = f'Alliances ({alliance_count}/{alliance_capacity})'
    player_information_dict['Alliance Data']['Color List'] = alliance_colors

    # missile data
    player_information_dict['Missile Data']['Standard'] = f'{nation.missile_count}x Standard Missiles'
    player_information_dict['Missile Data']['Nuclear'] = f'{nation.nuke_count}x Nuclear Missiles'

    # relations data
    nation_name_list = ['-'] * 10
    relation_colors = ['#000000'] * 10
    relations_status_list = ['-'] * 10
    for i in range(len(nation_table)):
        temp = nation_table.get(i + 1)
        if temp.name == nation.name:
            continue
        elif war_table.get_war_name(player_id, temp.id) is not None:
            relation_colors[i] = '#ff0000'
            relations_status_list[i] = "At War"
        elif alliance_table.are_allied(nation.name, temp.name):
            relation_colors[i] = '#3c78d8'
            relations_status_list[i] = "Allied"
        else:
            relation_colors[i] = '#00ff00'
            relations_status_list[i] = 'Neutral'
        nation_name_list[i] = temp.name
    while len(nation_name_list) < 10:
        nation_name_list.append('-')
    player_information_dict['Relations Data']['Name List'] = nation_name_list
    player_information_dict['Relations Data']['Color List'] = relation_colors
    player_information_dict['Relations Data']['Status List'] = relations_status_list

    # misc data
    player_information_dict['Misc Info']['Owned Regions'] = f"Total Regions: {nation.regions_owned}"
    player_information_dict['Misc Info']['Occupied Regions'] = f"Occupied Regions: {nation.regions_occupied}"
    if float(nation._records["netIncome"][-1]) >= 0:
        player_information_dict['Misc Info']['Net Income'] = f"Total Net Income: +{nation._records["netIncome"][-1]}"
    else:
        player_information_dict['Misc Info']['Net Income'] = f"Total Net Income: {nation._records["netIncome"][-1]}"
    player_information_dict['Misc Info']['Transaction Total'] = f"Total Transactions: {nation._records["transactionCount"][-1]}"
    player_information_dict['Misc Info']['Technology Count'] = f"Technology Count: {nation._records["researchCount"][-1]}"

    # income details
    income_details = nation.income_details
    for i in range(len(income_details)):
        income_details[i] = income_details[i].replace('&Tab;', '&nbsp;&nbsp;&nbsp;&nbsp;')
    income_str = "<br>".join(income_details)
    player_information_dict['Income Details'] = income_str

    # research details
    research_details = list(nation.completed_research.keys())
    research_str = "<br>".join(research_details)
    player_information_dict['Research Details'] = research_str

    return player_information_dict

def check_color_correction(color):
    if color in palette.BAD_PRIMARY_COLORS:
        color = palette.normal_to_occupied[color]
    return color
        
def generate_refined_player_list_active(game_id: str, current_turn_num: int) -> list:
    """
    Creates list of nations that is shown alongside each game.
    """

    nation_table = NationTable(game_id)
    with open('player_records.json', 'r') as json_file:
        player_records_dict = json.load(json_file)

    data_a = []
    data_b = []
   
    for nation in nation_table:
        gov_fp_str = f"{nation.fp} - {nation.gov}"
        username_str = f"""<a href="profile/{nation.player_id}">{player_records_dict[nation.player_id]["Username"]}</a>"""
        player_color = check_color_correction(nation.color)
        # tba - fix duplicate player color (second one should be redundant)
        if nation.score > 0:
            data_a.append([nation.name, nation.score, gov_fp_str, username_str, player_color, player_color])
        else:
            data_b.append([nation.name, nation.score, gov_fp_str, username_str, player_color, player_color])

    filtered_data_a = sorted(data_a, key=itemgetter(0), reverse=False)
    filtered_data_a = sorted(filtered_data_a, key=itemgetter(1), reverse=True)
    filtered_data_b = sorted(data_b, key=itemgetter(0), reverse=False)
    data = filtered_data_a + filtered_data_b

    return data

def generate_refined_player_list_inactive(game_data):
    
    with open('player_records.json', 'r') as json_file:
        player_records_dict = json.load(json_file)
        
    refined_player_data_a = []
    refined_player_data_b = []
    
    players_who_won = []
    for select_profile_id, player_data in game_data.get("Player Data", {}).items():
        player_data_list = []
        
        player_data_list.append(player_data.get("Nation Name"))
        player_data_list.append(player_data.get("Score"))
        
        gov_fp_string = f"""{player_data.get("Foreign Policy")} - {player_data.get("Government")}"""
        player_data_list.append(gov_fp_string)
        
        username = player_records_dict[select_profile_id]["Username"]
        username_str = f"""<a href="profile/{select_profile_id}">{username}</a>"""
        player_data_list.append(username_str)
        
        player_color = player_data.get("Color")
        player_data_list.append(player_color)
        player_color_occupied_hex = check_color_correction(player_color)
        player_data_list.append(player_color_occupied_hex)
        
        if player_data.get("Victory") == 1:
            players_who_won.append(player_data.get("Nation Name"))
        if player_data.get("Score") > 0:
            refined_player_data_a.append(player_data_list)
        else:
            refined_player_data_b.append(player_data_list)
    
    filtered_player_data_a = sorted(refined_player_data_a, key=itemgetter(0), reverse=False)
    filtered_player_data_a = sorted(filtered_player_data_a, key=itemgetter(1), reverse=True)
    filtered_player_data_b = sorted(refined_player_data_b, key=itemgetter(0), reverse=False)
    refined_player_data = filtered_player_data_a + filtered_player_data_b
    
    return refined_player_data, players_who_won

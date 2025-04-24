import ast
import csv
from datetime import datetime
import json
import os
import random
import shutil
import copy
from typing import Union, Tuple, List

from app import map
from app import public_actions
from app import private_actions
from app import checks
from app import events
from app import palette
from app.region import Region
from app.improvement import Improvement
from app.unit import Unit
from app.wardata import WarData
from app.notifications import Notifications
from app.alliance import Alliance
from app.alliance import AllianceTable
from app.nationdata import Nation
from app.nationdata import NationTable
from app import actions

# TURN PROCESSING PROCEDURE
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
    research_data_dict = get_scenario_dict(game_id, "Technologies")
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
    current_turn_num = get_current_turn_num(game_id)
    
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
    # public_actions_dict, private_actions_dict = events.resolve_active_events("Before Actions", public_actions_dict, private_actions_dict, full_game_id)
    
    # resolve public actions
    actions.resolve_trade_actions(game_id)
    print("Resolving public actions...")
    actions.resolve_peace_actions(game_id, actions_dict["SurrenderAction"] + actions_dict["WhitePeaceAction"])
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
    actions.resolve_market_actions(game_id, actions_dict["CrimeSyndicateAction"] + actions_dict["MarketBuyAction"] + actions_dict["MarketSellAction"])

    # resolve private actions
    print("Resolving private actions...")
    actions.resolve_unit_disband_actions(game_id, actions_dict["UnitDisbandAction"])
    actions.resolve_unit_deployment_actions(game_id, actions_dict["UnitDeployAction"])
    actions.resolve_war_actions(game_id, actions_dict["WarAction"])
    actions.resolve_missile_launch_actions(game_id, actions_dict["MissileLaunchAction"])
    actions.resolve_unit_move_actions(game_id, actions_dict["UnitMoveAction"])

    # oppertunity to resolve active events
    # public_actions_dict, private_actions_dict = events.resolve_active_events("After Actions", public_actions_dict, private_actions_dict, full_game_id)

    # export logs
    nation_table = NationTable(game_id)
    for nation in nation_table:
        nation.export_action_log()
        nation.action_log = []
        nation_table.save(nation)
    wardata = WarData(game_id)
    wardata.export_all_logs()

    # end of turn checks
    print("Resolving end of turn updates...")
    wardata.add_warscore_from_occupations()
    wardata.update_totals()
    checks.total_occupation_forced_surrender(game_id)
    checks.war_score_forced_surrender(game_id)
    checks.countdown(game_id)
    run_end_of_turn_checks(game_id)
    checks.gain_income(game_id)
    checks.gain_market_income(game_id)

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
            # print("Triggering an event...")
            # events.trigger_event(game_id)
            pass

    # update active game records
    update_turn_num(game_id)
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
    current_turn_num = get_current_turn_num(game_id)
    map_name = get_map_name(game_id)
    main_map = map.MainMap(game_id, map_name, current_turn_num)
    control_map = map.ControlMap(game_id, map_name)
    main_map.update()
    control_map.update()


# TURN PROCESSING FUNCTIONS
################################################################################

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
        writer.writerow(rmdata_header)

    # create trucedata.csv
    # to do - store in gamedata.json and create truce class?
    with open(f'gamedata/{game_id}/trucedata.csv', 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(trucedata_header)

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

def resolve_win(game_id: str) -> None:
    """
    Updates the game state and game records upon player victory.
    """

    nation_table = NationTable(game_id)
    game_name = get_game_name(game_id)
    current_turn_num = get_current_turn_num(game_id)

    with open('active_games.json', 'r') as json_file:
        active_games_dict = json.load(json_file)
    with open('game_records.json', 'r') as json_file:
        game_records_dict = json.load(json_file)

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

def run_end_of_turn_checks(game_id: str) -> None:
    """
    Executes end of turn checks and updates.
    """

    checks.prune_alliances(game_id)
    checks.update_income(game_id)
    checks.resolve_resource_shortages(game_id)
    checks.resolve_military_capacity_shortages(game_id)
    checks.update_income(game_id)

    nation_table = NationTable(game_id)
    for nation in nation_table:
        nation.update_stockpile_limits()
        nation.update_trade_fee()
        nation_table.save(nation)

    nation_table.update_records()
    nation_table.add_leaderboard_bonuses()

def get_data_for_nation_sheet(game_id: str, player_id: int) -> dict:
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
    wardata = WarData(game_id)
    misc_data_dict = get_scenario_dict(game_id, "Misc")

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
        stored_list.append(f"{nation.get_stockpile(resource_name)}/{nation.get_max(resource_name)}")
        income_list.append(nation.get_income(resource_name))
        rate_list.append(f"{nation.get_rate(resource_name)}%")
    player_information_dict['Resource Data']['Class List'] = class_list
    player_information_dict['Resource Data']['Name List'] = name_list
    player_information_dict['Resource Data']['Stored List'] = stored_list
    player_information_dict['Resource Data']['Income List'] = income_list
    player_information_dict['Resource Data']['Rate List'] = rate_list

    # alliance data
    alliance_count, alliance_capacity = get_alliance_count(game_id, nation)
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
        elif wardata.are_at_war(player_id, temp.id):
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


# GAMEDATA HELPER FUNCTIONS (TO BE REPLACED WHEN I REWORK GAME MANAGEMENT)
################################################################################

def get_game_name(game_id: str) -> None:
    
    with open('active_games.json', 'r') as json_file:
        active_games_dict = json.load(json_file)
    
    game_name = active_games_dict[game_id]["Game Name"]
    
    return game_name

def get_map_name(game_id: str) -> str:
    """
    Retrieves map name string given a game id.
    """
    
    with open('active_games.json', 'r') as json_file:
        active_games_dict = json.load(json_file)

    map_name = active_games_dict[game_id]["Information"]["Map"]

    return map_name

def get_current_turn_num(game_id: str) -> str | int:
    """
    Gets current turn number given game id.
    """
    
    with open('active_games.json', 'r') as json_file:
        active_games_dict = json.load(json_file)

    try:
        current_turn_num = int(active_games_dict[game_id]["Statistics"]["Current Turn"])
    except:
        current_turn_num = active_games_dict[game_id]["Statistics"]["Current Turn"]

    return current_turn_num

def update_turn_num(game_id: str) -> None:
    """
    Updates the turn number given game id.
    """

    with open('active_games.json', 'r') as json_file:
        active_games_dict = json.load(json_file)

    current_turn_num = int(active_games_dict[game_id]["Statistics"]["Current Turn"])
    current_turn_num += 1
    active_games_dict[game_id]["Statistics"]["Current Turn"] = str(current_turn_num)

    with open('active_games.json', 'w') as json_file:
        json.dump(active_games_dict, json_file, indent=4)


# GENERAL PURPOSE GLOBAL FUNCTIONS
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
    if refine:
        limit = current_turn_num - refine
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


# DIPLOMACY SUB-FUNCTIONS
################################################################################

def get_alliance_count(game_id: str, nation: Nation) -> Tuple[int, int]:
    """
    Gets a count of a player's active alliances and their total alliance capacity.

    Params:
        game_id (str): Game ID string.
        nation (Nation): Nation object.

    Returns:
        Tuple:
            int: Alliance count.
            int: Alliance limit.
    """

    with open('active_games.json', 'r') as json_file:
        active_games_dict = json.load(json_file)
    
    alliance_count = 0
    alliance_table = AllianceTable(game_id)
    alliance_report_dict = alliance_table.report(nation.name)
    alliance_count = alliance_report_dict["Total"] - alliance_report_dict["Non-Aggression Pact"]
    
    alliance_limit = 2
    if nation.gov == 'Republic':
        alliance_limit += 1
    if 'Power Broker' in nation.completed_research:
        alliance_limit += 1
    if 'Improved Logistics' in nation.completed_research:
        alliance_limit += 1
    if "Shared Fate" in active_games_dict[game_id]["Active Events"]:
        if active_games_dict[game_id]["Active Events"]["Shared Fate"]["Effect"] == "Cooperation":
            alliance_limit += 1

    return alliance_count, alliance_limit

def get_subjects(playerdata_list, overlord_nation_name, subject_type):
    '''Returns a list of all player ids that are subjects of the given nation name.'''
    player_id_list = []
    for index, playerdata in enumerate(playerdata_list):
        status = playerdata[28]
        if overlord_nation_name in status and subject_type in status:
            selected_nation_id = index + 1
            player_id_list.append(selected_nation_id)
    return player_id_list


# ECONOMIC SUB-FUNCTIONS
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

def get_unit_count_list(player_id, game_id):
    
    unit_data_dict = get_scenario_dict(game_id, "Units")
    unit_name_list = sorted(unit_data_dict.keys())
    with open(f'gamedata/{game_id}/regdata.json', 'r') as json_file:
        regdata_dict = json.load(json_file)

    count_list = []
    for unit_name in unit_name_list:
        count = 0
        for region_id in regdata_dict:
            region_unit = Unit(region_id, game_id)
            if region_unit.owner_id == player_id and region_unit.name == unit_name:
                count += 1
        count_list.append(count)

    return count_list

def create_player_yield_dict(game_id: str, nation: Nation) -> dict:
    """
    Given a player, this function creates the initial dictionary with the yields of all improvements.

    Params:
        game_id (str): Game ID string.
        nation (Nation): Object representing the nation this yield_dict is for.

    Returns:
        dict: Yield dictionary detailing income and multiplier for every improvement.
    """
    
    # load game info
    improvement_data_dict = get_scenario_dict(game_id, "Improvements")
    technology_data_dict = get_scenario_dict(game_id, "Technologies")
    agenda_data_dict = get_scenario_dict(game_id, "Agendas")

    # build yield dict
    yield_dict = {}
    for improvement_name, improvement_data in improvement_data_dict.items():
        
        # no point in tracking the data for improvements the player does not have any of
        if nation.improvement_counts[improvement_name] == 0:
            continue
        
        yield_dict[improvement_name] = {}
        for resource_name in improvement_data["Income"]:
            inner_dict = {
                "Income": improvement_data["Income"][resource_name],
                "Income Multiplier": 1
            }
            yield_dict[improvement_name][resource_name] = inner_dict
    
    # get modifiers from each technology and agenda
    for tech_name in nation.completed_research:   
        
        if tech_name in technology_data_dict:
            tech_dict = technology_data_dict[tech_name]
        elif tech_name in agenda_data_dict:
            tech_dict = agenda_data_dict[tech_name]
        
        for target in tech_dict["Modifiers"]: 

            # skip over modifiers that are not affecting improvements
            if target not in yield_dict:
                continue
            
            improvement_name = target
            for resource_name, modifier_dict in tech_dict["Modifiers"][improvement_name].items():
                if "Income" in modifier_dict:
                    yield_dict[improvement_name][resource_name]["Income"] += modifier_dict["Income"]
                elif "Income Multiplier" in modifier_dict:
                    yield_dict[improvement_name][resource_name]["Income Multiplier"] += modifier_dict["Income Multiplier"]

    return yield_dict

def create_player_upkeep_dict(game_id: str, nation: Nation) -> dict:
    """
    Given a player, this function creates the initial dictionary with the upkeep of all improvements and units.

    Params:
        game_id (str): Game ID string.
        nation (Nation): Object representing the nation this yield_dict is for.

    Returns:
        dict: Upkeep dictionary detailing upkeep and upkeep multiplier for every improvement.
    """
    
    # load game info
    unit_data_dict = get_scenario_dict(game_id, "Units")
    improvement_data_dict = get_scenario_dict(game_id, "Improvements")
    technology_data_dict = get_scenario_dict(game_id, "Technologies")
    agenda_data_dict = get_scenario_dict(game_id, "Agendas")

    upkeep_dict = {}

    for improvement_name, improvement_data in improvement_data_dict.items():

        # no point in tracking the data for improvements the player does not have any of
        if nation.improvement_counts[improvement_name] == 0:
            continue
        
        upkeep_dict[improvement_name] = {}
        for resource_name in improvement_data["Upkeep"]:
            inner_dict = {
                "Upkeep": improvement_data["Upkeep"][resource_name],
                "Upkeep Multiplier": 1
            }
            upkeep_dict[improvement_name][resource_name] = inner_dict

    for unit_name, unit_data in unit_data_dict.items():

        # no point in tracking the data for units the player does not have any of
        if nation.unit_counts[unit_name] == 0:
            continue
        
        upkeep_dict[unit_name] = {}
        for resource_name in unit_data["Upkeep"]:
            inner_dict = {
                "Upkeep": unit_data["Upkeep"][resource_name],
                "Upkeep Multiplier": 1
            }
            upkeep_dict[unit_name][resource_name] = inner_dict
    
    # get modifiers from each technology and agenda
    for tech_name in nation.completed_research:
        
        if tech_name in technology_data_dict:
            tech_dict = technology_data_dict[tech_name]
        elif tech_name in agenda_data_dict:
            tech_dict = agenda_data_dict[tech_name]

        for target in tech_dict["Modifiers"]: 
            
            # skip over effects that are not improvements or units
            if target not in upkeep_dict:
                continue
            
            for resource_name, modifier_dict in tech_dict["Modifiers"][target].items():
                if "Upkeep" in modifier_dict:
                    upkeep_dict[target][resource_name]["Upkeep"] += modifier_dict["Upkeep"]
                elif "Upkeep Multiplier" in modifier_dict:
                    upkeep_dict[target][resource_name]["Upkeep Multiplier"] += modifier_dict["Upkeep Multiplier"]

    return upkeep_dict

def calculate_upkeep(upkeep_type: str, player_upkeep_dict: dict, player_count_dict: dict) -> float:
    """
    Calculates the total upkeep sum for a player given a specific upkeep type.

    Params:
        upkeep_type (str): Either Dollars, Oil, Uranium, or Energy.
        player_upkeep_dict (dict): Taken from create_player_upkeep_dict().
        player_count_dict (dict): A count of a player's units or improvements.

    Returns:
        float: Upkeep sum.
    """
    
    sum = 0.0

    for target, target_upkeep_dict in player_upkeep_dict.items():
        if upkeep_type in target_upkeep_dict and target in player_count_dict:
            resource_upkeep_dict = player_upkeep_dict[target][upkeep_type]
            target_upkeep = resource_upkeep_dict["Upkeep"] * resource_upkeep_dict["Upkeep Multiplier"]
            sum += target_upkeep * player_count_dict[target]

    return sum


# WAR SUB-FUNCTIONS
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

def check_for_truce(trucedata_list, player_id_1, player_id_2, current_turn_num):
    '''Checks for a truce between two players. Returns True if one is found, otherwise returns False.'''
    for truce in trucedata_list:
        attacker_truce = ast.literal_eval(truce[player_id_1])
        defender_truce = ast.literal_eval(truce[player_id_2])
        if attacker_truce and defender_truce and int(truce[11]) > current_turn_num:
            return True
    return False


# MISC SUB-FUNCTIONS
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
            n = int(player_trade_fee[0])
            d = int(player_trade_fee[2])
            player_trade_fee = float(n / d)
        else:
            player_trade_fee = 0
        nation_info_list = [player_nation_name, player_color, player_government, player_fp, player_military_capacity, player_trade_fee]
        nation_info_masterlist.append(nation_info_list)
    return nation_info_masterlist

def search_and_destroy(game_id: str, player_id: str, target_improvement: str) -> str:
    """
    Searches for a specific improvement and removes it.
    """

    with open(f'gamedata/{game_id}/regdata.json', 'r') as json_file:
        regdata_dict = json.load(json_file)
    
    # find all regions belonging to a player with target improvement
    candidate_region_ids = []
    for region_id in regdata_dict:
        region = Region(region_id, game_id)
        region_improvement = Improvement(region_id, game_id)
        if region_improvement.name == target_improvement and region.owner_id == int(player_id):
            candidate_region_ids.append(region_id)

    # randomly select one of the candidate regions
    random.shuffle(candidate_region_ids)
    chosen_region_id = candidate_region_ids.pop()
    target_region_improvement = Improvement(chosen_region_id, game_id)
    target_region_improvement.clear()
    
    return chosen_region_id

def search_and_destroy_unit(game_id: str, player_id: str, desired_unit_name: str) -> tuple[str, str]:
    """
    Randomly destroys one unit of a given type belonging to a specific player.
    """

    unit_scenario_dict = get_scenario_dict(game_id, "Units")
    with open(f'gamedata/{game_id}/regdata.json', 'r') as json_file:
        regdata_dict = json.load(json_file)

    # get list of regions with desired_unit_name owned by player_id
    candidate_region_ids = []
    if desired_unit_name in unit_scenario_dict:
        for region_id in regdata_dict:
            region_unit = Unit(region_id, game_id)
            if (desired_unit_name == 'ANY' or region_unit.name == desired_unit_name) and region_unit.owner_id == int(player_id):
                candidate_region_ids.append(region_id)

    # randomly select one of the candidate regions
    # there should always be at least one candidate region because we have already checked that the target unit exists
    random.shuffle(candidate_region_ids)
    chosen_region_id = candidate_region_ids.pop()
    target_region_unit = Unit(chosen_region_id, game_id)
    victim = copy.deepcopy(target_region_unit.name)
    target_region_unit.clear()

    return chosen_region_id, victim

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

def has_capital(player_id, game_id):
    '''
    Checks if a player has a capital in their territory.
    '''
    regdata_filepath = f'gamedata/{game_id}/regdata.json'
    with open(regdata_filepath, 'r') as json_file:
        regdata_dict = json.load(json_file)

    for region_id in regdata_dict:
        region = Region(region_id, game_id)
        region_improvement = Improvement(region_id, game_id)
        if region.owner_id == player_id and region_improvement.name == 'Capital':
            return True
        
    return False

def get_scenario_dict(game_id, dictionary_name):
    '''
    Gets a dictionary from the chosen scenario.
    '''

    with open('active_games.json', 'r') as json_file:
        active_games_dict = json.load(json_file)

    if game_id != "TBD":
        scenario_name = active_games_dict[game_id]["Information"]["Scenario"]
        scenario = scenario_name.lower()
    else:
        scenario = "standard"

    filename = f"{dictionary_name.lower()}.json"
    dictionary_filepath = f"scenarios/{scenario}/{filename}"

    with open(dictionary_filepath, 'r') as json_file:
        chosen_dictionary = json.load(json_file)

    return chosen_dictionary

def get_lowest_in_record(game_id, record_name):
    # get core lists
    playerdata_filepath = f'gamedata/{game_id}/playerdata.csv'
    playerdata_list = read_file(playerdata_filepath, 1)

    # get nation names
    nation_name_list = []
    for playerdata in playerdata_list:
        nation_name_list.append(playerdata[1])
    
    #get lowest
    if record_name != "most_transactions":
        record_filepath = f'gamedata/{game_id}/{record_name}.csv'
        record_list = read_file(record_filepath, 0)
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
        sorted_candidates = sorted(candidates, key = lambda x: x[-1], reverse = False)
        return sorted_candidates[0][0]
    else:
        pass

def get_top_three_transactions(game_id):
    """
    Temporary cringe function to read transactions.
    """
    with open('active_games.json', 'r') as json_file:
        active_games_dict = json.load(json_file)
    
    transactions_dict = active_games_dict[game_id]["Transactions Record"]
    sorted_dict = dict(
        sorted(
            transactions_dict.items(),
            key = lambda item: (-item[1], item[0])
        )
    )

    top_three = tuple(sorted_dict.keys())[:3]
    top_three_list = []
    for index, key in enumerate(top_three):
        top_three_list.append(f"{index+1}. {key} ({sorted_dict[key]})")

    return tuple(top_three_list)


# DISGUSTING GLOBAL VARIABLES
################################################################################

# unfortunately like pulling teeth significant refactoring is required to remove some of these - I'm workin' on it!

#file headers
rmdata_header = ["Turn", "Nation", "Bought/Sold", "Count", "Resource Exchanged"]
trucedata_header = ['Truce ID', 'Player #1', 'Player #2', 'Player #3', 'Player #4', 'Player #5', 'Player #6', 'Player #7', 'Player #8', 'Player #9', 'Player #10', 'Expire Turn #']

#color dictionaries
# tba - remove all of these and use palette instead

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
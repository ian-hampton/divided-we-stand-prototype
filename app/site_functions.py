import csv
import json
import random
import shutil
import os
import copy
import importlib
import string
from datetime import datetime
from operator import itemgetter
from collections import defaultdict

from app import core
from app import palette
from app.scenario import ScenarioData as SD
from app.gamedata import Games, GameStatus
from app.alliance.alliances import Alliances
from app.region import Region, Regions
from app.nation.nation import Nation
from app.nation.nations import Nations
from app.notifications import Notifications
from app.truce import Truces
from app.war import Wars
from app.map import GameMaps
from app import actions
from app import checks
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

    # update nation colors
    for nation_id, setup_data in contents_dict.items():
        color_name = setup_data["color"]
        nation = Nations.get(nation_id)
        nation.color = palette.str_to_hex(color_name)

    # place chosen starts
    random_assignment_list = []
    for nation_id, setup_data in contents_dict.items():
        region_id = setup_data["start"]
        if region_id is None or region_id not in Regions:
            random_assignment_list.append(nation_id)
            continue
        starting_region = Regions.load(region_id)
        starting_region.data.owner_id = nation_id
        starting_region.improvement.set("Capital")
        nation = Nations.get(nation_id)
        nation.improvement_counts["Capital"] += 1

    # place random starts
    random.shuffle(random_assignment_list)
    for random_assignment_player_id in random_assignment_list:
        while True:
            # randomly select a region
            conflict_detected = False
            region_id_list = Regions.ids()
            random_region_id = random.sample(region_id_list, 1)[0]
            random_region = Regions.load(random_region_id)
            # if region not allowed restart loop
            if not random_region.graph.is_start:
                continue
            # check if there is a player within three regions
            regions_in_radius = random_region.get_regions_in_radius(3)
            for candidate_region_id in regions_in_radius:
                candidate_region = Regions.load(candidate_region_id)
                # if player found restart loop
                if candidate_region.data.owner_id != "0":
                    conflict_detected = True
                    break
            # if no player found place player
            if conflict_detected == False:
                random_region.data.owner_id = random_assignment_player_id
                random_region.improvement.set("Capital")
                nation = Nations.get(random_assignment_player_id)
                nation.improvement_counts["Capital"] += 1
                break
    
    # update game maps
    maps = GameMaps(game_id)
    maps.populate_resource_map()
    maps.populate_main_map()
    maps.update_all()

def resolve_stage2_processing(game_id: str, contents_dict: dict) -> None:
    """
    Resolves stage two setup for a new game.

    Params:
        game_id (str): Game ID string.
        contents_dict (dict): A dictionary containing the setup data for each player.
    
    Returns:
        None
    """

    game = Games.load(game_id)

    five_point_research_list = []
    for tech_name, tech_data in SD.technologies:
        if tech_data.cost == 5:
            five_point_research_list.append(tech_name)
    if not game.info.fog_of_war:
        five_point_research_list.remove("Surveillance Operations")

    # update nation data
    for nation_id, setup_data in contents_dict.items():
        nation = Nations.get(nation_id)
        
        # add basic data
        nation.name = setup_data["name_choice"]
        nation.gov = setup_data["gov_choice"]
        nation.fp = setup_data["fp_choice"]
        nation.add_gov_tags()
        
        # victory conditions data
        nation.victory_conditions = copy.deepcopy(nation._sets[setup_data["vc_choice"]])
        nation._satisfied = copy.deepcopy(nation._sets[setup_data["vc_choice"]])
        
        # technocracy bonus tech
        if nation.gov == "Technocracy":
            starting_list = random.sample(five_point_research_list, 3)
            for technology_name in starting_list:
                nation.add_tech(technology_name)

    # update income in playerdata
    checks.update_income(game_id)
    Nations.update_records()
        
def resolve_turn_processing(game_id: str, contents_dict: dict) -> None:
    """
    Resolves a normal turn.

    Params:
        game_id (str): Game ID string.
        contents_dict (dict): A dictionary containing the actions submitted by each player.

    Returns:
        None
    """
    
    game = Games.load(game_id)
    scenario_actions = importlib.import_module(f"scenarios.{SD.scenario}.actions")

    # sort and validate actions
    actions_dict = defaultdict(list)
    for nation_id, actions_list in contents_dict.items():
        for action_str in actions_list:
            action = actions.validate_action(game_id, nation_id, action_str)
            if action is None:
                continue
            class_name = type(action).__name__
            actions_dict[class_name].append(action)

    # prompt for missing war justifications
    checks.prompt_for_missing_war_justifications()
    
    # oppertunity to resolve active events
    events.resolve_active_events(game_id, actions_dict)
    
    # resolve public actions
    actions.resolve_trade_actions(game_id)
    print("Resolving public actions...")
    actions.resolve_peace_actions(game_id, actions_dict.get("SurrenderAction", []), actions_dict.get("WhitePeaceAction", []))
    actions.resolve_research_actions(game_id, actions_dict.get("ResearchAction", []))
    actions.resolve_alliance_leave_actions(game_id, actions_dict.get("AllianceLeaveAction", []))
    actions.resolve_alliance_kick_actions(game_id, actions_dict.get("AllianceKickAction", []))
    actions.resolve_alliance_create_actions(game_id, actions_dict.get("AllianceCreateAction", []))
    actions.resolve_alliance_join_actions(game_id, actions_dict.get("AllianceJoinAction", []))
    actions.resolve_claim_actions(game_id, actions_dict.get("ClaimAction", []))
    actions.resolve_improvement_remove_actions(game_id, actions_dict.get("ImprovementRemoveAction", []))
    actions.resolve_improvement_build_actions(game_id, actions_dict.get("ImprovementBuildAction", []))
    actions.resolve_missile_make_actions(game_id, actions_dict.get("MissileMakeAction", []))
    actions.resolve_government_actions(game_id, actions_dict.get("RepublicAction", []))
    market_results = actions.resolve_market_actions(game_id, actions_dict.get("CrimeSyndicateAction", []), actions_dict.get("MarketBuyAction", []), actions_dict.get("MarketSellAction", []))

    # update income step
    checks.update_income(game_id)

    # resolve event actions
    scenario_actions.resolve_event_actions(game_id, actions_dict)

    # resolve private actions
    print("Resolving private actions...")
    actions.resolve_unit_disband_actions(game_id, actions_dict.get("UnitDisbandAction", []))
    actions.resolve_unit_deployment_actions(game_id, actions_dict.get("UnitDeployAction", []))
    actions.resolve_war_actions(game_id, actions_dict.get("WarAction", []))
    actions.resolve_war_join_actions(game_id, actions_dict.get("WarJoinAction", []))
    actions.resolve_missile_launch_actions(game_id, actions_dict.get("MissileLaunchAction", []))
    actions.resolve_unit_move_actions(game_id, actions_dict.get("UnitMoveAction", []))

    # oppertunity to resolve active events
    events.resolve_active_events(game_id)

    # export action logs
    for nation in Nations:
        nation.export_action_log()
        nation.action_log = []
    
    # update wars
    Wars.export_all_logs()
    Wars.add_warscore_from_occupations()
    Wars.update_totals()

    # end of turn checks
    print("Resolving end of turn updates...")
    checks.countdown()    # TODO: replace this function with something better
    run_end_of_turn_checks(game_id)

    # post-turn checks
    run_post_turn_checks(game_id, market_results)

    # update game maps
    maps = GameMaps(game_id)
    maps.update_all()

def run_end_of_turn_checks(game_id: str, *, event_phase = False) -> None:
    """
    Executes end of turn checks and updates.
    """

    if not event_phase:
        checks.total_occupation_forced_surrender()
        checks.war_score_forced_surrender()
        checks.prune_alliances()
    
    checks.update_income(game_id)
    if not event_phase:
        checks.gain_income()
    checks.resolve_resource_shortages()
    checks.resolve_military_capacity_shortages(game_id)
    checks.update_income(game_id)
    
    for nation in Nations:
        nation.update_stockpile_limits()
        nation.update_trade_fee()

    if not event_phase:
        Nations.prune_eliminated_nations()
        Nations.update_records()
        Nations.add_leaderboard_bonuses()

def run_post_turn_checks(game_id: str, market_results: dict) -> None:

    def resolve_win():

        game.status = GameStatus.FINISHED
        game.updated_days_ellapsed()

        with open("game_records.json", 'r') as json_file:
            game_records_dict = json.load(json_file)

        # create game archive entry
        game_records_dict[game_id] = {
            "Name": game.name,
            "Number": game.number,
            "Information": {
                "Version": game.info.version,
                "Scenario": game.info.scenario,
                "Map": game.info.map,
                "Victory Conditions": game.info.victory_conditions,
                "Fog of War": game.info.fog_of_war,
                "Turn Duration": game.info.turn_length,
                "Accelerated Schedule": game.info.accelerated_schedule,
                "Deadlines on Weekends": game.info.weekend_deadlines
            },
            "Statistics": {
                "Player Count": game.info.player_count,
                "Region Disputes": game.stats.region_disputes,
                "Game End Turn": game.turn,
                "Days Ellapsed": game.stats.days_elapsed,
                "Game Started": game.stats.date_started,
                "Game Ended": datetime.today().date().strftime("%m/%d/%Y")
            },
            "Player Data": ()
        }
        
        # add player data to game archive entry
        player_data_dict = {}
        for nation in Nations:
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
        game_records_dict[game_id]["Player Data"] = player_data_dict

        with open("game_records.json", 'w') as json_file:
            json.dump(game_records_dict, json_file, indent=4)
    
    game = Games.load(game_id)

    checks.gain_market_income(market_results)

    player_has_won = False
    for nation in Nations:
        nation.update_victory_progress()
        if nation.score == 3:
            player_has_won = True

    if player_has_won:
        resolve_win(game_id)

    if game.turn % 4 == 0:
        checks.bonus_phase_heals()
        Notifications.add('All units and defensive improvements have regained 2 health.', 2)
    
    if game.turn % 8 == 0 and not player_has_won:
        events.trigger_event(game_id)
        game.updated_days_ellapsed()
        events.filter_events(game_id)
        Nations.check_tags()
        return
    
    game.turn += 1
    game.updated_days_ellapsed()
    events.filter_events(game_id)
    Nations.check_tags()

# MISC SITE FUNCTIONS
################################################################################

def get_data_for_nation_sheet(game_id: str, player_id: str) -> dict:
    """
    Gathers all the needed data for a player's nation sheet data and spits it as a dict.

    Params:
        game_id (str): Game ID string.
        player_id (int): The integer id of the active player.
        current_turn_num (int): An integer number representing the game's current turn number.

    Returns:
        dict: player_information_dict.
    """

    def fetch_color_class(income_str: str, nation: Nation) -> str:
        for resource_name in nation._resources.keys():
            if resource_name in income_str:
                return resource_name.lower().replace(" ", "-")
    
    SD.load(game_id)

    Alliances.load(game_id)
    Nations.load(game_id)
    Wars.load(game_id)
    nation = Nations.get(player_id)

    # build player info dict
    player_information_dict = {
        "Nation Name": nation.name,
        "Color": nation.color,
        "Information": {
            "Status": nation.status,
            "Government": nation.gov,
            "Foreign Policy": nation.fp,
            "Trade Fee": nation.trade_fee
        },
        "Military": {
            "Military Capacity": f"{nation.get_used_mc()} / {nation.get_max_mc()}",
            "Standard Missiles": nation.missile_count,
            "Nuclear Missiles": nation.nuke_count
        },
        "Victory Conditions Data": {},
        "Alliance Data": nation.fetch_alliance_data()
    }
    
    # get victory condition data
    vc_names = list(nation.victory_conditions.keys())
    vc_status = list(nation.victory_conditions.values())
    vc_completed_count = 0
    for i, victory_condition in enumerate(vc_names):
        is_complete = vc_status[i]
        color_hex_str = "#00ff00" if is_complete else "#ff0000"
        player_information_dict["Victory Conditions Data"][victory_condition] = color_hex_str
        vc_completed_count += 1 if is_complete else 0
    player_information_dict["Victory Conditions Data"]["Header"] = f"Victory Conditions ({vc_completed_count}/3)"

    # get resource data
    player_information_dict["Resource Data"] = {}
    for resource_name in nation._resources:
        if resource_name in ["Energy", "Military Capacity"]:
            continue
        resource_data = {
            "Class": resource_name.lower().replace(" ", "-"),
            "Stockpile": f"{nation.get_stockpile(resource_name)} / {nation.get_max(resource_name)}",
            "Gross Income": nation.get_gross_income(resource_name),
            "Net Income": nation.get_income(resource_name),
            "Income Rate": f"{nation.get_rate(resource_name)}%"
        }
        player_information_dict["Resource Data"][resource_name] = resource_data

    # get relations data
    player_information_dict["Relations Data"] = []
    for temp in Nations:
        relation = {"Name": temp.name, "Status": "-", "Color": "#FFFFFF"}
        if temp.name == nation.name:
            pass
        elif Wars.get_war_name(nation.id, temp.id) is not None:
            relation["Color"] = "#ff0000"
            relation["Status"] = "At War"
        elif Alliances.are_allied(nation.name, temp.name):
            relation["Color"] = "#3c78d8"
            relation["Status"] = "Allied"
        else:
            relation["Color"] = "#00ff00"
            relation["Status"] = "Neutral"
        player_information_dict["Relations Data"].append(relation)
    for i in range(10 - len(Nations)):
        relation = {"Name": "-", "Status": "-", "Color": "#FFFFFF"}
        player_information_dict["Relations Data"].append(relation)

    # get misc data
    misc_data = []
    misc_data.append(("Owned Regions", nation.stats.regions_owned))
    misc_data.append(("Occupied Regions", nation.stats.regions_occupied))
    misc_data.append(("Net Income", nation.records.net_income[-1]))
    misc_data.append(("Gross Industrial Income", nation.records.industrial_income[-1]))
    misc_data.append(("Gross Energy Income", nation.records.energy_income[-1]))
    misc_data.append(("Development Score", nation.records.development[-1]))
    misc_data.append(("Unique Improvements", sum(1 for count in nation.improvement_counts.values() if count != 0)))
    misc_data.append(("Net Exports", nation.records.net_exports[-1]))
    misc_data.append(("Military Size", nation.records.military_size[-1]))
    misc_data.append(("Military Strength", nation.records.military_strength[-1]))
    misc_data.append(("Unique Units", sum(1 for count in nation.unit_counts.values() if count != 0)))
    misc_data.append(("Technology Count", nation.records.technology_count[-1]))
    misc_data.append(("Agenda Count", nation.records.agenda_count[-1]))
    player_information_dict["Misc Info"] = misc_data

    # format income details - I am aware this code sucks, however making it better would require updating the income calculation code which I do not want to do right now
    income_details = {}
    income_string_block_text = []
    income_string_block_color = ""
    for income_str in nation.income_details:
        if income_str.startswith("<section> ") and income_string_block_text == []:
            # for loop has just started - start first group
            income_string_block_color = fetch_color_class(income_str, nation)
            income_string_block_text.append(income_str[10:])
        elif income_str.startswith("<section> ") and income_string_block_text != []:
            # group ended - save and start new group
            income_details[income_string_block_color] = income_string_block_text
            income_string_block_text = []
            income_string_block_color = fetch_color_class(income_str, nation)
            income_string_block_text.append(income_str[10:])
        else:
            # add income string to its group
            income_string_block_text.append(income_str)
    income_details[income_string_block_color] = income_string_block_text
    player_information_dict["Income Details"] = income_details

    # get tag data
    player_information_dict["Tag Data"] = {}
    for tag_name, tag_data in nation.tags.items():
        tag_data_filtered = {
            "Expire Turn": tag_data["Expire Turn"],
            "Data": []
        }
        for td_key, td_value in tag_data.items():
            if td_key == "Expire Turn":
                continue
            tag_data_filtered["Data"].append(f"{td_key}: {td_value}")
        player_information_dict["Tag Data"][tag_name] = tag_data_filtered

    # format completed research
    player_information_dict["Research Data"] = defaultdict(list)
    for research_name in nation.completed_research.keys():
        if research_name in SD.agendas:
            player_information_dict["Research Data"]["Agendas"].append(research_name)
        elif research_name in SD.technologies:
            sd_tech = SD.technologies[research_name]
            player_information_dict["Research Data"][sd_tech.type].append(research_name)
    player_information_dict["Research Data"] = {        # sort research names within each category
        key: sorted(value)
        for key, value in player_information_dict["Research Data"].items()
    }
    player_information_dict["Research Data"] = dict(    # sort categories alphabetically
        sorted(player_information_dict["Research Data"].items())
    )

    return player_information_dict

def check_color_correction(color):
    if color in palette.BAD_PRIMARY_COLORS:
        color = palette.normal_to_occupied[color]
    return color

def generate_refined_player_list_inactive(game_data):
    
    with open('playerdata/player_records.json', 'r') as json_file:
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

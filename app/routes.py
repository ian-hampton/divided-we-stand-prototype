import ast
from queue import PriorityQueue 
import csv
from datetime import datetime
import json
import os
import uuid
import string
import random
import shutil
from collections import defaultdict

from app import site_functions
from app import core
from app import events
from app import palette
from app.scenario import ScenarioData as SD

from flask import Flask, Blueprint, render_template, request, redirect, url_for, send_file

app = Flask(__name__)
main = Blueprint('main', __name__)
@main.route('/')
def main_function():
    return render_template('index.html')


# SITE PAGES
################################################################################

#GAMES PAGE
@main.route('/games')
def games():
    
    # read game files
    from app.nation import Nations
    with open('playerdata/player_records.json', 'r') as json_file:
        player_records_dict = json.load(json_file)
    with open('active_games.json', 'r') as json_file:
        active_games_dict = json.load(json_file)

    # read active games
    for game_id, game_data in active_games_dict.items():

        Nations.load(game_id)
        current_turn = game_data["Statistics"]["Current Turn"]
        if current_turn == "Turn N/A":
            continue
        
        match current_turn:

            case "Starting Region Selection in Progress":
                # get title and game link
                game_name = game_data["Name"]
                game_data["Title"] = f"""<a href="/{game_id}">{game_name}</a>"""
                # get status
                game_data["Status"] = current_turn
                # get player information
                refined_player_data = []
                for nation in Nations:
                    username = player_records_dict[nation.player_id]["Username"]
                    username_str = f"""<a href="profile/{nation.player_id}">{username}</a>"""
                    refined_player_data.append([nation.name, 0, 'TBD', username_str, '#ffffff', '#ffffff'])
                # get image
                game_map = game_data["Information"]["Map"]
                if game_map == "United States 2.0":
                    game_map = "united_states"
                image_url = url_for('main.get_mainmap', full_game_id=game_id)

            case "Nation Setup in Progress":
                # get title and game link
                game_name = game_data["Name"]
                game_data["Title"] = f"""<a href="/{game_id}">{game_name}</a>"""
                # get status
                game_data["Status"] = current_turn
                # get player information
                refined_player_data = []
                for nation in Nations:
                    username = player_records_dict[nation.player_id]["Username"]
                    username_str = f"""<a href="profile/{nation.player_id}">{username}</a>"""
                    player_color_2 = site_functions.check_color_correction(nation.color)
                    refined_player_data.append([nation.name, 0, 'TBD', username_str, nation.color, player_color_2])
                # get image
                image_url = url_for('main.get_mainmap', full_game_id=game_id)

            case _:
                # get title and game link
                game_name = game_data["Name"]
                game_data["Title"] = f"""<a href="/{game_id}">{game_name}</a>"""
                # get status
                if game_data["Game Active"]:
                    game_data["Status"] = f"Turn {current_turn}"
                else:
                    game_data["Status"] = "Game Over!"
                # get player information
                refined_player_data = site_functions.generate_refined_player_list_active(game_id, current_turn)
                # get image
                image_url = url_for('main.get_mainmap', full_game_id=game_id)
        
        game_data["Playerdata Masterlist"] = refined_player_data
        game_data["image_url"] = image_url
    
    return render_template('temp_games.html', dict = active_games_dict)

# SETTINGS PAGE
@main.route('/settings')
def settings():

    with open("playerdata/player_records.json", 'r') as json_file:
        player_records_dict = json.load(json_file)
    
    username_list = []
    for profile_id, player_data in player_records_dict.items():
        username_list.append(player_data.get("Username"))

    return render_template('temp_settings.html', username_list = username_list)

# SETTINGS PAGE - Create Game Procedure
@main.route('/create_game', methods=['POST'])
def create_game():
    
    # get game record dictionaries
    with open('active_games.json', 'r') as json_file:
        active_games_dict = json.load(json_file)

    # get username list
    username_list = []
    profile_id_list = []
    with open('playerdata/player_records.json', 'r') as json_file:
        player_records_dict = json.load(json_file)
    for profile_id, player_data in player_records_dict.items():
        username_list.append(player_data.get("Username"))
        profile_id_list.append(profile_id)
    
    # get values from settings form
    form_data_dict = {
        "Game Name": request.form.get('name_input'),
        "Player Count": request.form.get('pc_dropdown'),
        "Victory Conditions": request.form.get('vc_dropdown'),
        "Map": request.form.get('map_dropdown'),
        "Accelerated Schedule": request.form.get('as_dropdown'),
        "Turn Length": request.form.get('td_dropdown'),
        "Fog of War": request.form.get('fow_dropdown'),
        "Deadlines on Weekends": request.form.get('dow_dropdown'),
        "Scenario": request.form.get('scenario_dropdown')
    }
    profile_ids_list = []
    for index, username in enumerate(username_list):
        # if checked, checkbox returns True. Otherwise returns None.
        add_player_value = request.form.get(username)
        if add_player_value:
            profile_ids_list.append(profile_id_list[index])

    # erase all active games override
    if form_data_dict["Game Name"] == "5EQM8Z5VoLxvxqeP1GAu":
        shutil.rmtree(f"gamedata")
        os.makedirs(f"gamedata")
        active_games_dict = {}
        with open("active_games.json", 'w') as json_file:
            json.dump(active_games_dict, json_file, indent=4)
        return redirect(f'/games')

    # create game files
    game_id = ''.join(random.choices(string.ascii_letters, k=20))
    site_functions.create_new_game(game_id, form_data_dict, profile_ids_list)
    
    return redirect(f'/games')

# GAMES ARCHIVE PAGE
@main.route('/archived_games')
def archived_games():
    
    with open("game_records.json", 'r') as json_file:
        game_records_dict = json.load(json_file)
    
    for game_id, game_data in game_records_dict.items():
        
        # get playerdata
        archived_player_data_list, players_who_won_list = site_functions.generate_refined_player_list_inactive(game_data)
        if len(players_who_won_list) == 1:
            victors_str = players_who_won_list[0]
            game_data["Winner String"] = f"{victors_str} Victory!"
        elif len(players_who_won_list) > 1:
            victors_str = " & ".join(players_who_won_list)
            game_data["Winner String"] = f"{victors_str} Victory!"
        elif len(players_who_won_list) == 0:
            game_data["Winner String"] = "Draw!"
        game_data["Playerdata Masterlist"] = archived_player_data_list

        # get game image
        turn_number = game_data["Statistics"]["Game End Turn"]
        game_data["image_url"] = f"{game_id}/{turn_number}.png"
    
    # display games from newest to oldest
    game_records_dict = dict(sorted(game_records_dict.items(), key=lambda item: item[1]["Number"], reverse=True))
    
    return render_template("temp_archive.html", dict = game_records_dict)

# LEADERBOARD PAGE
@main.route('/leaderboard')
def leaderboard():
    
    leaderboard_data = []
    with open("playerdata/leaderboard.csv", 'r') as file:
        reader = csv.reader(file)
        for row in reader:
            if row != []:
                leaderboard_data.append(row)
    
    with open("playerdata/player_records.json", 'r') as json_file:
        player_records_dict = json.load(json_file)
    
    username_list = []
    for profile_id, player_data in player_records_dict.items():
        username_list.append(player_data.get("Username"))
    
    profile_ids = []
    for entry in leaderboard_data:
        username = entry[0]
        profile_id = username_list.index(username)
        profile_id = str(profile_id + 1)
        while len(profile_id) < 3:
            profile_id = f'0{profile_id}'
        profile_ids.append(profile_id)
        entry[0] = f"""<a href="profile/{profile_id}">{entry[0]}</a>"""
    
    with open("playerdata/leaderboard_records.json", 'r') as json_file:
        leaderboard_records_dict = json.load(json_file)
    
    return render_template('temp_leaderboard_new.html', leaderboard_data = leaderboard_data, profile_ids = profile_ids, leaderboard_records_dict = leaderboard_records_dict)

# PROFILE PAGES
@main.route('/profile/<profile_id>')
def profile_route(profile_id):

    with open("playerdata/player_records.json", 'r') as json_file:
        player_records_dict = json.load(json_file)
    with open("game_records.json", 'r') as json_file:
        game_records_dict = json.load(json_file)

    profile = {
        "username": player_records_dict[profile_id]["Username"],
        "dateJoined": player_records_dict[profile_id]["Join Date"],
        "resignations": player_records_dict[profile_id]["Resignations"],
        "firstGame": None,
        "lastGame": None,
        "favoriteGov": None,
        "favoriteFP": None,
        "rank": 0,
        "totalWins": 0,
        "totalDraws": 0,
        "totalLosses": 0,
        "totalScore": 0,
        "averageScore": 0,
        "totalGames": 0,
        "reliability": 0
    }

    with open("playerdata/leaderboard.csv", 'r') as file:
        reader = csv.reader(file)
        for i, row in enumerate(reader):
            if row[0] == profile["username"]:
                profile["rank"] = i + 1
                profile["totalWins"] = row[1]
                profile["totalScore"] = row[2]
                profile["averageScore"] = row[3]
                profile["totalGames"] = int(row[4])
    
    game_starts = defaultdict(int)
    game_ends = defaultdict(int)
    governments_played = defaultdict(int)
    foreign_policies_played = defaultdict(int)
    
    for game_id, game_data in game_records_dict.items():

        if profile_id not in game_data["Player Data"]:
            continue
        
        players_who_lost = set()
        for select_profile_id, player_data in game_data["Player Data"].items():
            if not player_data["Victory"]:
                players_who_lost.add(select_profile_id)
        
        if len(players_who_lost) == len(game_data["Player Data"]):
            profile["totalDraws"] += 1
        elif not game_data["Player Data"][profile_id]["Victory"]:
            profile["totalLosses"] += 1
    
    for game_id, game_data in game_records_dict.items():
        
        if profile_id not in game_data["Player Data"]:
            continue

        game_starts[game_id] = datetime.strptime(game_data["Statistics"]["Game Started"], "%m/%d/%Y")
        game_ends[game_id] = datetime.strptime(game_data["Statistics"]["Game Ended"], "%m/%d/%Y")
        
        government_choice = game_data["Player Data"][profile_id]["Government"]
        foreign_policy_choice = game_data["Player Data"][profile_id]["Foreign Policy"]
        governments_played[government_choice] += 1
        foreign_policies_played[foreign_policy_choice] += 1

    profile["firstGame"] = game_starts[min(game_starts, key=game_starts.get)]
    profile["lastGame"] = game_ends[max(game_ends, key=game_ends.get)]
    profile["favoriteGov"] = governments_played[max(governments_played, key=governments_played.get)]
    profile["favoriteFP"] = foreign_policies_played[max(foreign_policies_played, key=foreign_policies_played.get)]

    profile["reliability"] = int((profile["totalGames"] - profile["resignations"]) / profile["totalGames"] * 100)

    return render_template('temp_profile.html', dict = profile)


# GAME PAGES
################################################################################

# LOAD GAME PAGE
@main.route(f'/<full_game_id>')
def game_load(full_game_id):
    
    #read the contents of active_games.json
    from app.nation import Nations
    Nations.load(full_game_id)
    with open('active_games.json', 'r') as json_file:
        active_games_dict = json.load(json_file)
    game1_title = active_games_dict[full_game_id]["Name"]
    game1_turn = active_games_dict[full_game_id]["Statistics"]["Current Turn"]
    game1_active_bool = active_games_dict[full_game_id]["Game Active"]
    game1_extendedtitle = f"Divided We Stand - {game1_title}" 
    
    #load images
    main_url = url_for('main.get_mainmap', full_game_id=full_game_id)
    resource_url = url_for('main.get_resourcemap', full_game_id=full_game_id)
    control_url = url_for('main.get_controlmap', full_game_id=full_game_id)
    #load inactive state
    if not game1_active_bool:
        with open('game_records.json', 'r') as json_file:
            game_records_dict = json.load(json_file)
        game_data = game_records_dict[game1_title]
        largest_nation_tup = Nations.get_top_three("Largest Nation")
        strongest_economy_tup = Nations.get_top_three("Most Income")
        largest_military_tup = Nations.get_top_three("Largest Military")
        most_research_tup = Nations.get_top_three("Most Technology")
        largest_nation_list = list(largest_nation_tup)
        strongest_economy_list = list(strongest_economy_tup)
        largest_military_list = list(largest_military_tup)
        most_research_list = list(most_research_tup)
        for i in range(len(largest_nation_list)):
            largest_nation_list[i] = palette.color_nation_names(largest_nation_list[i], full_game_id)
            strongest_economy_list[i] = palette.color_nation_names(strongest_economy_list[i], full_game_id)
            largest_military_list[i] = palette.color_nation_names(largest_military_list[i], full_game_id)
            most_research_list[i] = palette.color_nation_names(most_research_list[i], full_game_id)
        archived_player_data_list, players_who_won_list = site_functions.generate_refined_player_list_inactive(game_data)
        if len(players_who_won_list) == 1:
            victors_str = players_who_won_list[0]
            victory_string = (f"""{victors_str} has won the game.""")
        elif len(players_who_won_list) > 1:
            victors_str = ' and '.join(players_who_won_list)
            victory_string = (f'{victors_str} have won the game.')
        elif len(players_who_won_list) == 0:
            victory_string = (f'Game drawn.')
        victory_string = palette.color_nation_names(victory_string, full_game_id)
        return render_template('temp_stage4.html', game1_title = game1_title, game1_extendedtitle = game1_extendedtitle, main_url = main_url, resource_url = resource_url, control_url = control_url, archived_player_data_list = archived_player_data_list, largest_nation_list = largest_nation_list, strongest_economy_list = strongest_economy_list, largest_military_list = largest_military_list, most_research_list = most_research_list, victory_string = victory_string)
    
    # load active state
    # tba - fix this garbage when you get around to redoing the frontend
    match game1_turn:
        
        case "Starting Region Selection in Progress":
            
            form_key = "main.stage1_resolution"
            player_data = []
            
            for nation in Nations:
                p_id = f'p{nation.id}'
                regioninput_id = f'regioninput_{p_id}'
                colordropdown_id = f'colordropdown_{p_id}'
                vc1a, vc2a, vc3a, vc1b, vc2b, vc3b = nation.get_vc_list()
                refined_player_data = [f"Player #{nation.id}", p_id, nation.color, vc1a, vc2a, vc3a, vc1b, vc2b, vc3b, regioninput_id, colordropdown_id]
                player_data.append(refined_player_data)
            active_player_data = player_data.pop(0)
            
            return render_template('temp_stage1.html', active_player_data = active_player_data, player_data = player_data, game1_title = game1_title, game1_extendedtitle = game1_extendedtitle, main_url = main_url, resource_url = resource_url, control_url = control_url, full_game_id = full_game_id, form_key = form_key)
        
        case "Nation Setup in Progress":
            
            form_key = "main.stage2_resolution"
            player_data = []
            
            for nation in Nations:
                p_id = f'p{nation.id}'
                nameinput_id = f"nameinput_{p_id}"
                govinput_id = f"govinput_{p_id}"
                fpinput_id = f"fpinput_{p_id}"
                vcinput_id = f"vcinput_{p_id}"
                vc1a, vc2a, vc3a, vc1b, vc2b, vc3b = nation.get_vc_list()
                refined_player_data = [f"Player #{nation.id}", p_id, nation.color, vc1a, vc2a, vc3a, vc1b, vc2b, vc3b, nameinput_id, govinput_id, fpinput_id, vcinput_id]
                player_data.append(refined_player_data)
            active_player_data = player_data.pop(0)
            
            return render_template('temp_stage2.html', active_player_data = active_player_data, player_data = player_data, game1_title = game1_title, game1_extendedtitle = game1_extendedtitle, main_url = main_url, resource_url = resource_url, control_url = control_url, full_game_id = full_game_id, form_key = form_key)
        
        case _:
            
            form_key = "main.turn_resolution"
            main_url = url_for('main.get_mainmap', full_game_id=full_game_id)
            player_data = []

            for nation in Nations:
                p_id = f'p{nation.id}'
                public_actions_textarea_id = f"public_textarea_{p_id}"
                private_actions_textarea_id = f"private_textarea_{p_id}"
                nation_sheet_url = f'{full_game_id}/player{nation.id}'
                refined_player_data = [f"Player #{nation.id}", p_id, nation.color, nation.name, public_actions_textarea_id, private_actions_textarea_id, nation_sheet_url]
                player_data.append(refined_player_data)
            active_player_data = player_data.pop(0)
            
            with open(f'active_games.json', 'r') as json_file:  
                active_games_dict = json.load(json_file)
            current_event_dict = active_games_dict[full_game_id]["Current Event"]
            if current_event_dict != {}:
                form_key = "main.event_resolution"
            
            return render_template('temp_stage3.html', active_player_data = active_player_data, player_data = player_data, game1_title = game1_title, game1_extendedtitle = game1_extendedtitle, main_url = main_url, resource_url = resource_url, control_url = control_url, full_game_id = full_game_id, form_key = form_key)

# GENERATE NATION SHEET PAGES
@main.route('/<full_game_id>/player<int:player_id>')
def player_route(full_game_id, player_id):
    page_title = f"Player #{player_id} Nation Sheet"
    player_information_dict = site_functions.get_data_for_nation_sheet(full_game_id, str(player_id))
    return render_template("temp_nation_sheet.html", page_title = page_title, player_information_dict = player_information_dict)

# WARS PAGE
@main.route('/<full_game_id>/wars')
def wars(full_game_id):
    
    # get game data
    from app.nation import Nations
    from app.alliance import Alliances
    from app.war import Wars
    Nations.load(full_game_id)
    Alliances.load(full_game_id)
    Wars.load(full_game_id)
    current_turn_num = core.get_current_turn_num(full_game_id)
    with open('active_games.json', 'r') as json_file:
        active_games_dict = json.load(json_file)
    game_name = active_games_dict[full_game_id]["Name"]
    page_title = f'{game_name} Wars List'
    
    # read wars
    results = {}
    for war in Wars:

        inner_dict = {}
        
        # get war timeframe
        season, year = core.date_from_turn_num(war.start)
        start_str = f"{season} {year}"
        if war.end != 0:
            season, year = core.date_from_turn_num(war.end)
            end_str = f"{season} {year}"
        else:
            end_str = "Present"
        inner_dict["timeframe"] = f"{start_str} - {end_str}"

        # get war score information
        attacker_threshold, defender_threshold = war.calculate_score_threshold()
        ma_id, md_id = war.get_main_combatant_ids()
        main_attacker = Nations.get(ma_id)
        main_defender = Nations.get(md_id)

        # implement a score bar using an html table >:)
        inner_dict["outcome"] = war.outcome
        attacker_color = """background-image: linear-gradient(#cc4125, #eb5a3d)"""
        defender_color = """background-image: linear-gradient(#3c78d8, #5793f3)"""
        white_color = """background-image: linear-gradient(#c0c0c0, #b0b0b0)"""
        match war.outcome:
            case "Attacker Victory":
                war_status_bar = [attacker_color] * 1  # set bar entirely red
            case "Defender Victory":
                war_status_bar = [defender_color] * 1  # set bar entirely blue
            case "White Peace":
                war_status_bar = [white_color] * 1     # set bar entirely white
            case "TBD":
                # color bar based on percentage
                if war.attackers.total != 0 and war.defenders.total == 0:
                    war_status_bar = [attacker_color] * 1
                elif war.attackers.total == 0 and war.defenders.total != 0:
                    war_status_bar = [defender_color] * 1
                elif war.attackers.total == 0 and war.defenders.total == 0:
                    war_status_bar = [attacker_color] * 1
                    war_status_bar += [defender_color] * 1
                else:
                    # calculate attacker value
                    attacker_percent = float(war.attackers.total) / float(war.attackers.total + war.defenders.total)
                    attacker_percent = round(attacker_percent, 2)
                    attacker_points = int(attacker_percent * 100)
                    attacker_steps = round(attacker_points / 5)
                    # calculate defender value
                    defender_percent = float(war.defenders.total) / float(war.attackers.total + war.defenders.total)
                    defender_percent = round(defender_percent, 2)
                    defender_points = int(defender_percent * 100)
                    defender_steps = round(defender_points / 5)
                    # add to score bar
                    war_status_bar = [attacker_color] * attacker_steps
                    war_status_bar += [defender_color] * defender_steps
        inner_dict["scoreBar"] = war_status_bar

        # get attacker warscore data
        copy = {
            "Total War Score": war.attackers.total,
            "From Occupation": war.attackers.occupation,
            "From Combat Victories": war.attackers.victories,
            "From Enemy Units Destroyed": war.attackers.destroyed_units,
            "From Enemy Impr. Destroyed": war.attackers.destroyed_improvements,
            "From Capital Captures": war.attackers.captures,
            "From Nuclear Strikes": war.attackers.nuclear_strikes
        }
        inner_dict["attackerWarScore"] = copy
        
        # get defender warscore data
        copy = {
            "Total War Score": war.defenders.total,
            "From Occupation": war.defenders.occupation,
            "From Combat Victories": war.defenders.victories,
            "From Enemy Units Destroyed": war.defenders.destroyed_units,
            "From Enemy Impr. Destroyed": war.defenders.destroyed_improvements,
            "From Capital Captures": war.defenders.captures,
            "From Nuclear Strikes": war.defenders.nuclear_strikes
        }
        inner_dict["defenderWarScore"] = copy

        # create war resolution strings
        match war.outcome:
            
            case "Attacker Victory":
                war_end_str = """This war concluded with an <span class="color-red">attacker victory</span>."""
                inner_dict["warEndStr"] = war_end_str
            
            case "Defender Victory":
                war_end_str = """This war concluded with a <span class="color-blue">defender victory</span>."""
                inner_dict["warEndStr"] = war_end_str
            
            case "White Peace":
                war_end_str = """This war concluded with a white peace."""
                inner_dict["warEndStr"] = war_end_str
            
            case "TBD":
                # calculate negotiation turn
                if current_turn_num - war.start < 4:
                    can_end_str = f"A peace deal may be negotiated by the main combatants in {(war.start + 4) - current_turn_num} turns."
                else:
                    can_end_str = f"A peace deal may be negotiated by the main combatants at any time."
                inner_dict["canEndStr"] = can_end_str
                # calculate forced end score
                if war.attackers.total > war.defenders.total:
                    if attacker_threshold is not None:
                        forced_end_str = f"""The <span class="color-red"> attackers </span> will win this war upon reaching <span class="color-red"> {attacker_threshold} </span> war score."""
                    else:
                        forced_end_str = f"""The <span class="color-red"> attackers </span> cannot win this war using war score since <span class="color-blue"> {main_defender.name} </span> is a Crime Syndicate."""
                else:
                    if defender_threshold is not None:
                        forced_end_str = f"""The <span class="color-blue"> defenders </span> will win this war upon reaching <span class="color-blue"> {defender_threshold} </span> war score."""
                    else:
                        forced_end_str = f"""The <span class="color-blue"> defenders </span> cannot win this war using war score since <span class="color-red"> {main_attacker.name} </span> is a Crime Syndicate."""
                inner_dict["forcedEndStr"] = forced_end_str

        # add combatants
        inner_dict["combatants"] = {}
        for combatant_id in war.combatants:
            combatant = war.get_combatant(combatant_id)
            combatant_data = {
                "role": combatant.role,
                "warJustification": combatant.justification,
                "warClaims": combatant.claims
            }
            inner_dict["combatants"][combatant.name] = combatant_data

        results[war.name] = inner_dict

    return render_template('temp_wars.html', page_title = page_title, dict = results)

# RESEARCH PAGE
@main.route('/<full_game_id>/technologies')
def technologies(full_game_id):
    
    # get game data
    from app.nation import Nations
    Nations.load(full_game_id)
    with open('active_games.json', 'r') as json_file:
        active_games_dict = json.load(json_file)
    game_name = active_games_dict[full_game_id]["Name"]
    page_title = f'{game_name} - Technology Trees'
    scenario = active_games_dict[full_game_id]["Information"]["Scenario"]


    # refine technology dictionary
    refined_dict = {}
    research_data_dict = core.get_scenario_dict(full_game_id, "Technologies")
    if scenario == "Standard":
        categories = ["Energy", "Infrastructure", "Military", "Defense"]
        for category in categories:
            refined_dict[f'{category} Technologies'] = {}
        refined_dict["Energy Technologies"]["Colors"] = ["#5555554D", "#CC58264D", "#106A254D", "NONE"]
        refined_dict["Infrastructure Technologies"]["Colors"] = ["#F9CB304D", "#754C244D", "#5555554D", "#0583C54D"]
        refined_dict["Military Technologies"]["Colors"] = ["#C419194D", "#5F2F8C4D", "#106A254D", "#CC58264D"]
        refined_dict["Defense Technologies"]["Colors"] = ["#0583C54D", "#F9CB304D", "#C419194D", "NONE"]
        color_complements_dict = {
            "#555555": "#636363",
            "#CC5826": "#E0622B",
            "#106A25": "#197B30",
            "#F9CB30": "#FFDF70",
            "#754C24": "#8C6239",
            "#0583C5": "#1591D1",
            "#5F2F8C": "#713BA4",
            "#C41919": "#D43939"
        }
    
    # create research table
    for category in categories:
        table_contents = {
            "A": [None] * 4,
            "B": [None] * 4,
            "C": [None] * 4,
            "D": [None] * 4,
        }
        refined_dict[f'{category} Technologies']["Table"] = table_contents
    
    # hide fow techs if not fog of war
    if active_games_dict[full_game_id]["Information"]["Fog of War"] == "Disabled":
        del research_data_dict["Surveillance Operations"]
        del research_data_dict["Economic Reports"]
        del research_data_dict["Military Intelligence"]

    # add player research data
    for research_name in research_data_dict:
        research_data_dict[research_name]["Player Research"] = [None] * len(Nations)
    for index, nation in enumerate(Nations):
        for research_name in nation.completed_research:
            if research_name in research_data_dict:
                research_data_dict[research_name]["Player Research"][index] = (nation.color[1:], nation.name)

    # load techs to table
    for key, value in research_data_dict.items():
        research_type = value["Research Type"]
        if research_type in categories:
            pos = value["Location"]
            row_pos = pos[0]
            col_pos = int(pos[1])
            value["Name"] = key
            refined_dict[research_type + " Technologies"]["Table"][row_pos][col_pos] = value
    
    return render_template('temp_research.html', page_title = page_title, dict = refined_dict, complement = color_complements_dict)

# AGENDAS PAGE
@main.route('/<full_game_id>/agendas')
def agendas(full_game_id):
    
    # get game data
    from app.nation import Nations
    Nations.load(full_game_id)
    with open('active_games.json', 'r') as json_file:
        active_games_dict = json.load(json_file)
    game_name = active_games_dict[full_game_id]["Name"]
    page_title = f'{game_name} - Political Agendas'
    scenario = active_games_dict[full_game_id]["Information"]["Scenario"]


    # Get Research Information
    refined_dict = {}
    agenda_data_dict = core.get_scenario_dict(full_game_id, "Agendas")
    
    # get scenario data
    if scenario == "Standard":
        categories = ["Agendas"]
        for category in categories:
            refined_dict[category] = {}
        refined_dict["Agendas"]["Colors"] = ["#0583C54D", "#106A254D", "#5F2F8C4D", "#C419194D"]
        color_complements_dict = {
            "#555555": "#636363",
            "#CC5826": "#E0622B",
            "#106A25": "#197B30",
            "#F9CB30": "#FFDF70",
            "#754C24": "#8C6239",
            "#0583C5": "#1591D1",
            "#5F2F8C": "#713BA4",
            "#C41919": "#D43939"
        }
    
    # create research table
    for category in categories:
        table_contents = {
            "A": [None] * 4,
            "B": [None] * 4,
            "C": [None] * 4,
            "D": [None] * 4,
        }
        refined_dict[category]["Table"] = table_contents

    # add player research data
    for research_name in agenda_data_dict:
        agenda_data_dict[research_name]["Player Research"] = [None] * len(Nations)
    for index, nation in enumerate(Nations):
        for research_name in nation.completed_research:
            if research_name in agenda_data_dict:
                agenda_data_dict[research_name]["Player Research"][index] = (nation.color[1:], nation.name)

    # load techs to table
    for key, value in agenda_data_dict.items():
        pos = value["Location"]
        row_pos = pos[0]
        col_pos = int(pos[1])
        value["Name"] = key
        refined_dict["Agendas"]["Table"][row_pos][col_pos] = value
    
    return render_template('temp_agenda.html', page_title = page_title, dict = refined_dict, complement = color_complements_dict)

# UNITS REF PAGE
@main.route('/<full_game_id>/units')
def units_ref(full_game_id):
    
    # read the contents of active_games.json
    with open('active_games.json', 'r') as json_file:
        active_games_dict = json.load(json_file)
    game_name = active_games_dict[full_game_id]["Name"]
    page_title = f'{game_name} - Unit Reference'
    
    # get unit dict
    unit_dict = core.get_scenario_dict(full_game_id, "Units")

    # add reference colors
    for unit_name in unit_dict:
        if "Motorized Infantry" == unit_name:
            unit_dict[unit_name]["stat_color"] = "stat-purple"
            continue
        if "Infantry" in unit_name or "Artillery" in unit_name or "Special Forces" in unit_name:
            unit_dict[unit_name]["stat_color"] = "stat-red"
        elif "Tank" in unit_name:
            unit_dict[unit_name]["stat_color"] = "stat-purple"
        elif "Air" in unit_name:
            unit_dict[unit_name]["stat_color"] = "stat-yellow"

    return render_template('temp_units.html', page_title = page_title, dict = unit_dict)

# IMPROVEMENTS REF PAGE
@main.route('/<full_game_id>/improvements')
def improvements_ref(full_game_id):
    
    # read the contents of active_games.json
    with open('active_games.json', 'r') as json_file:
        active_games_dict = json.load(json_file)
    game_name = active_games_dict[full_game_id]["Name"]
    page_title = f'{game_name} - Improvement Reference'
    
    # get unit dict
    improvement_dict: dict = core.get_scenario_dict(full_game_id, "Improvements")

    # filter improvements
    improvement_dict_filtered = {}
    for improvement_name, improvement_data in improvement_dict.items():

        # assign color
        # to do - make a function that assigns color based on improvement's required tech
        match improvement_name:
            case 'Boot Camp' | 'Military Base' | 'Military Outpost' | 'Missile Defense System' | 'Missile Silo' | 'Trench':
                improvement_data["stat_color"] = "stat-red"
            case 'Coal Mine' | 'Nuclear Power Plant' | 'Oil Well' | 'Solar Farm' | 'Wind Farm':
                improvement_data["stat_color"] = "stat-yellow"
            case 'Advanced Metals Mine' | 'Common Metals Mine' | 'Industrial Zone' | 'Uranium Mine' | 'Rare Earth Elements Mine':
                improvement_data["stat_color"] = "stat-grey"
            case 'Capital' | 'Central Bank' | 'City' | 'Farm' | 'Research Institute' | 'Research Laboratory' | 'Settlement':
                improvement_data["stat_color"] = "stat-blue"
            case _:
                improvement_data["stat_color"] = "stat-grey"

        # hide fog of war improvements
        if active_games_dict[full_game_id]["Information"]["Fog of War"] != "Enabled" and improvement_data.get("Fog of War Improvement", None):
            continue

        # hide event improvements
        if improvement_name == "Colony" and "Faustian Bargain" not in active_games_dict[full_game_id]["Active Events"]:
            continue

        improvement_dict_filtered[improvement_name] = improvement_data

    improvement_dict_filtered = {key: improvement_dict_filtered[key] for key in sorted(improvement_dict_filtered)}
    return render_template('temp_improvements.html', page_title = page_title, dict = improvement_dict_filtered)

# RESOURCE MARKET PAGE
@main.route('/<full_game_id>/resource_market')
def resource_market(full_game_id):

    # get game data
    current_turn_num = core.get_current_turn_num(full_game_id)
    with open('active_games.json', 'r') as json_file:
        active_games_dict = json.load(json_file)
    game_name = active_games_dict[full_game_id]["Name"]
    page_title = f'{game_name} - Resource Market'

    # tba - grab this from scenario files
    data = core.get_scenario_dict(full_game_id, "market")
    
    # get resource market records
    rmdata_filepath = f'gamedata/{full_game_id}/rmdata.csv'
    rmdata_recent_transaction_list = core.read_rmdata(rmdata_filepath, current_turn_num, 12, False)
    if len(rmdata_recent_transaction_list) != 0:
        records_flag = True
        rmdata_recent_transaction_list = rmdata_recent_transaction_list[::-1]
    else:
        records_flag = False

    # sum up recent transactions
    for transaction in rmdata_recent_transaction_list: 
        exchange = transaction[2]
        count = transaction[3]
        resource_name = transaction[4]
        if exchange == "Bought":
            data[resource_name]["Bought"] += count
        elif exchange == "Sold":
            data[resource_name]["Sold"] += count

    # calculate current prices
    for resource_name, resource_info in data.items():
        base_price = resource_info["Base Price"]
        recently_bought_total = resource_info["Bought"]
        recently_sold_total = resource_info["Sold"]
        current_price = base_price * (recently_bought_total + 25) / (recently_sold_total + 25)
        data[resource_name]["Current Price"] = round(current_price, 2)
    
    # factor in impact of events on current prices
    if "Market Inflation" in active_games_dict[full_game_id]["Active Events"]:
        for resource_name in data:
            new_price = data[resource_name]["Current Price"] * 2
            data[resource_name]["Current Price"] = round(new_price, 2)
    elif "Market Recession" in active_games_dict[full_game_id]["Active Events"]:
        for resource_name in data:
            new_price = data[resource_name]["Current Price"] * 0.5
            data[resource_name]["Current Price"] = round(new_price, 2)

    # format price strings
    for resource_name in data:
        data[resource_name]["Base Price"] = f"{data[resource_name]["Base Price"]:.2f}"
        data[resource_name]["Current Price"] = f"{data[resource_name]["Current Price"]:.2f}"

    return render_template('temp_resource_market.html', page_title = page_title, records_list = rmdata_recent_transaction_list, records_flag = records_flag, prices_dict = data)

# ANNOUNCEMENT PAGE
@main.route('/<full_game_id>/announcements')
def announcements(full_game_id):

    from app.alliance import Alliances
    from app.nation import Nations
    from app.notifications import Notifications
    from app.truce import Truces
    from app.war import Wars

    # get game data
    Alliances.load(full_game_id)
    Nations.load(full_game_id)
    Notifications.initialize(full_game_id)
    Truces.load(full_game_id)
    Wars.load(full_game_id)
    with open('active_games.json', 'r') as json_file:
        active_games_dict = json.load(json_file)

    # read the contents of active_games.json
    game_name = active_games_dict[full_game_id]["Name"]
    page_title = f'{game_name} - Announcements Page'
    current_turn_num = int(active_games_dict[full_game_id]["Statistics"]["Current Turn"])
    accelerated_schedule_str = active_games_dict[full_game_id]["Information"]["Accelerated Schedule"]
    current_event_dict = active_games_dict[full_game_id]["Current Event"]
    if current_event_dict != {}:
        event_pending = True
    else:
        event_pending = False

    # calculate date information
    if not event_pending:
        season, year = core.date_from_turn_num(current_turn_num)
        date_output = f'{season} {year} - Turn {current_turn_num}'
    else:
        current_turn_num -= 1
        season, year = core.date_from_turn_num(current_turn_num)
        date_output = f'{season} {year} - Turn {current_turn_num} Bonus Phase'


    # Build Diplomacy String
    diplomacy_list = []
    # expansion rules reminder
    if current_turn_num <= 4:
        diplomacy_list.append('First year expansion rules are in effect.')
    elif current_turn_num == 5:
        diplomacy_list.append('Normal expansion rules are now in effect.')
    # accelerate schedule reminder
    if accelerated_schedule_str == 'Enabled' and current_turn_num <= 10:
        diplomacy_list.append('Accelerated schedule is in effect until turn 11.')
    elif accelerated_schedule_str == 'Enabled' and current_turn_num == 11:
        diplomacy_list.append('Normal turn schedule is now in effect.')
    # get all ongoing wars
    for war in Wars:
        if war.outcome == "TBD":
            diplomacy_list.append(f"{war.name} is ongoing.")
    # get all ongoing truces
    for truce in Truces:
        if truce.end_turn > current_turn_num:
            diplomacy_list.append(f"{str(truce)} truce until turn {truce.end_turn}.")
        elif truce.end_turn == current_turn_num:
            diplomacy_list.append(f"{str(truce)} truce has expired.")
    # format diplomacy string
    diplomacy_string = "<br>".join(diplomacy_list)
    diplomacy_string = palette.color_nation_names(diplomacy_string, full_game_id)

    
    # Build Notifications String
    notifications_list = []
    q = PriorityQueue()
    for notification in Notifications:
        q.put(notification)
    while not q.empty():
        ntf = q.get()
        notifications_list.append(ntf[1])
    notifications_string = "<br>".join(notifications_list)
    notifications_string = palette.color_nation_names(notifications_string, full_game_id)


    # Build Statistics String
    statistics_list = []
    statistics_list.append(f"Total alliances: {len(Alliances)}")
    longest_alliance_name, longest_alliance_duration = Alliances.longest_alliance()
    if longest_alliance_name is not None:
        statistics_list.append(f"Longest alliance: {longest_alliance_name} - {longest_alliance_duration} turns")
    else:
        statistics_list.append(f"Longest alliance: N/A")
    statistics_list.append(f"Total wars: {len(Wars)}")
    statistics_list.append(f"Units lost in war: {Wars.total_units_lost()}")
    statistics_list.append(f"Improvements destroyed in war: {Wars.total_units_lost()}")
    statistics_list.append(f"Nuclear Missiles launched: {Wars.total_missiles_launched()}")
    war_name, war_duration = Wars.find_longest_war()
    if war_name is not None:
        statistics_list.append(f"Longest war: {war_name} - {war_duration} turns")
    else:
        statistics_list.append("Longest war: N/A")
    dispute_count = active_games_dict[full_game_id]["Statistics"]["Region Disputes"]
    statistics_list.append(f"Region disputes: {dispute_count}")
    statistics_string = "<br>".join(statistics_list)
    statistics_string = palette.color_nation_names(statistics_string, full_game_id)


    # get top three standings
    standings_dict = {}
    records = ["nationSize", "netIncome", "transactionCount", "militaryStrength", "researchCount"]
    record_names = ["Largest Nation", "Most Income", "Most Transactions", "Largest Military", "Most Technology"]
    for i, record in enumerate(records):
        standings = Nations.get_top_three(record)
        standings_filtered = []
        for entry in standings:
            # add html span tag
            nation_name = palette.color_nation_names(entry[0], full_game_id)
            # truncate nation name if over 30 chars
            start_index = nation_name.find('>') + 1
            end_index = nation_name.find('</span>')
            if end_index - start_index > 30:
                nation_name = nation_name[0:start_index+31] + nation_name[end_index:]
            # format standing
            if record == "netIncome":
                standings_filtered.append([nation_name, f"{entry[1]:.2f}"])
            else:
                standings_filtered.append([nation_name, entry[1]])
        record_name = record_names[i]
        standings_dict[record_name] = standings_filtered
    
    # update scoreboard
    scoreboard_dict = {}
    for nation in Nations:
        inner_dict = {}
        inner_dict["color"] = nation.color
        inner_dict["score"] = nation.score
        scoreboard_dict[nation.name] = inner_dict
    
    # sort scoreboard
    scoreboard_dict = dict(
        sorted(
            scoreboard_dict.items(),
            key = lambda item: (-item[1]["score"], item[0])
        )
    )

    return render_template('temp_announcements.html', game_name = game_name, page_title = page_title, date_output = date_output, scoreboard_dict = scoreboard_dict, standings_dict = standings_dict, statistics_string = statistics_string, diplomacy_string = diplomacy_string, notifications_string = notifications_string)

# ALLIANCE PAGE
@main.route('/<full_game_id>/alliances')
def alliances(full_game_id):

    from app.alliance import Alliances
    from app.nation import Nations
    from app.scenario import SD_Alliance

    SD.load(full_game_id)

    Alliances.load(full_game_id)
    Nations.load(full_game_id)
    with open('active_games.json', 'r') as json_file:
        active_games_dict = json.load(json_file)
    game_name = active_games_dict[full_game_id]["Name"]
    page_title = f'{game_name} - Alliance Page'

    alliance_dict_filtered = {}
    
    for alliance in Alliances:
        
        if not alliance.is_active:
            continue

        alliance_data = {
            "allianceType": alliance.type,
            "foundingMembers": alliance.founding_members,
            "currentMembersFormatted": {}
        }

        turn_started = alliance_data["turnCreated"]
        season, year = core.date_from_turn_num(turn_started)
        date_str = f"{season} {year} (Turn {turn_started})"
        alliance_data["turnCreated"] = date_str

        for nation_name, turn_joined in alliance.current_members.items():
            nation = Nations.get(nation_name)
            bad_primary_colors_set = {"#603913", "#105500", "#8b2a1a"}
            if nation.color in bad_primary_colors_set:
                color = palette.normal_to_occupied[nation.color]
            else:
                color = nation.color
            alliance_data["currentMembersFormatted"][nation_name] = {
                "turnJoined": turn_joined,
                "nationColor": color
            }

        sd_alliance: SD_Alliance = SD.alliances.get(alliance.type)
        alliance_data["color"] = palette.str_to_hex(sd_alliance.color_theme)
        alliance_data["abilities"] = sd_alliance.description

        alliance_dict_filtered[alliance.name] = alliance_data

    return render_template('temp_alliances.html', alliance_dict = alliance_dict_filtered, page_title = page_title)

# MAP IMAGES
@main.route('/<full_game_id>/mainmap.png')
def get_mainmap(full_game_id):
    with open('active_games.json', 'r') as json_file:
        active_games_dict = json.load(json_file)
    current_turn_num = active_games_dict[full_game_id]["Statistics"]["Current Turn"]
    map_str = core.get_map_str(full_game_id)
    try:
        current_turn_num = int(current_turn_num)
        filepath = f'..\\gamedata\\{full_game_id}\\images\\{current_turn_num - 1}.png'
    except:
        if current_turn_num == "Nation Setup in Progress":
            filepath = f'..\\gamedata\\{full_game_id}\\images\\0.png'
        else:
            filepath = f'..\\app\\static\\images\\map_images\\{map_str}\\blank.png'
    return send_file(filepath, mimetype='image/png')
@main.route('/<full_game_id>/resourcemap.png')
def get_resourcemap(full_game_id):
    filepath = f'../gamedata/{full_game_id}/images/resourcemap.png'
    return send_file(filepath, mimetype='image/png')
@main.route('/<full_game_id>/controlmap.png')
def get_controlmap(full_game_id):
    filepath = f'../gamedata/{full_game_id}/images/controlmap.png'
    return send_file(filepath, mimetype='image/png')


# ACTION PROCESSING
################################################################################

@main.route('/stage1_resolution', methods=['POST'])
def stage1_resolution():
    
    full_game_id = request.form.get('full_game_id')
    from app.nation import Nations
    Nations.load(full_game_id)

    contents_dict = {}
    for nation in Nations:
        contents_dict[nation.id] = {}
        contents_dict[nation.id]["start"] = request.form.get(f"regioninput_p{nation.id}")
        contents_dict[nation.id]["color"] = request.form.get(f"colordropdown_p{nation.id}")
    
    site_functions.resolve_stage1_processing(full_game_id, contents_dict)
    
    return redirect(f'/{full_game_id}')

@main.route('/stage2_resolution', methods=['POST'])
def stage2_resolution():

    full_game_id = request.form.get('full_game_id')
    from app.nation import Nations
    Nations.load(full_game_id)

    contents_dict = {}
    for nation in Nations:
        contents_dict[nation.id] = {}
        contents_dict[nation.id]["name_choice"] = request.form.get(f"nameinput_p{nation.id}")
        contents_dict[nation.id]["gov_choice"] = request.form.get(f"govinput_p{nation.id}")
        contents_dict[nation.id]["fp_choice"] = request.form.get(f"fpinput_p{nation.id}")
        contents_dict[nation.id]["vc_choice"] = request.form.get(f"vcinput_p{nation.id}")

    site_functions.resolve_stage2_processing(full_game_id, contents_dict)
    
    return redirect(f'/{full_game_id}')

@main.route('/turn_resolution', methods=['POST'])
def turn_resolution():

    full_game_id = request.form.get('full_game_id')
    from app.nation import Nations
    Nations.load(full_game_id)

    contents_dict = {}
    for nation in Nations:
        contents_dict[nation.id] = []
        public_str = request.form.get(f"public_textarea_p{nation.id}")
        private_str = request.form.get(f"private_textarea_p{nation.id}")
        if public_str:
            actions_list = public_str.split('\r\n')
            contents_dict[nation.id].extend(actions_list)
        if private_str:
            actions_list = private_str.split('\r\n')
            contents_dict[nation.id].extend(actions_list)

    site_functions.resolve_turn_processing(full_game_id, contents_dict)

    return redirect(f'/{full_game_id}')

@main.route('/event_resolution', methods=['POST'])
def event_resolution():
    """
    Handles current event and runs end of turn checks & updates when activated.
    Redirects back to selected game.
    """

    from app.alliance import Alliances
    from app.region import Regions
    from app.nation import Nations
    from app.notifications import Notifications
    from app.truce import Truces
    from app.war import Wars
    
    game_id = request.form.get("full_game_id")

    SD.load(game_id)
    
    Alliances.load(game_id)
    Regions.load(game_id)
    Nations.load(game_id)
    Notifications.initialize(game_id)
    Truces.load(game_id)
    Wars.load(game_id)
    
    events.resolve_current_event(game_id)
    site_functions.run_end_of_turn_checks(game_id, event_phase=True)

    Alliances.save()
    Regions.save()
    Nations.save()
    Notifications.save()
    Truces.save()
    Wars.save()

    return redirect(f"/{game_id}")
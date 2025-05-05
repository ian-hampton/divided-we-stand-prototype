#STANDARD IMPORTS
import ast
from queue import PriorityQueue 
import csv
from datetime import datetime
import json
from operator import itemgetter
import os
import re
import uuid

#UWS SOURCE IMPORTS
from app import core
from app import checks
from app import events
from app import palette
from app import map
from app.testing import map_tests
from app.notifications import Notifications
from app.alliance import AllianceTable
from app.alliance import Alliance
from app.nationdata import NationTable
from app.war import WarTable

#ENVIROMENT IMPORTS
from flask import Flask, Blueprint, render_template, request, redirect, url_for, send_file
app = Flask(__name__)
main = Blueprint('main', __name__)
@main.route('/')
def main_function():
    return render_template('index.html')

#SITE FUNCTIONS
################################################################################

#COLOR CORRECTION
def check_color_correction(color):
    swap_list = ['#b30000', '#105500', '#003b84', '#603913', '#8b2a1a', '#5bb000'] 
    if color in swap_list:
        player_color_rgb = core.player_colors_conversions[color]
        color = core.player_colors_normal_to_occupied_hex[player_color_rgb]
    return color

#COLOR NATION NAMES
def color_nation_names(string: str, game_id: str) -> str:
    """
    Takes a string of text and colors any nation names inside it.
    """

    temp_dict = {}
    nation_table = NationTable(game_id)

    for nation in nation_table:
        temp_dict[nation.name] = check_color_correction(nation.color)

    for nation_name, nation_color in temp_dict.items():
        if nation_name in string:
            string = string.replace(nation_name, f"""<span style="color:{nation_color}">{nation_name}</span>""")
    
    return string
        
#REFINE PLAYERDATA FUNCTION FOR ACTIVE GAMES
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

#REFINE PLAYERDATA FUNCTION FOR INACTIVE GAMES
def generate_refined_player_list_inactive(game_data):
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


#CORE SITE PAGES
################################################################################

#GAMES PAGE
@main.route('/games')
def games():
    
    # read game files
    with open('player_records.json', 'r') as json_file:
        player_records_dict = json.load(json_file)
    with open('active_games.json', 'r') as json_file:
        active_games_dict = json.load(json_file)

    # read active games
    for game_id, game_data in active_games_dict.items():
        current_turn = game_data["Statistics"]["Current Turn"]
        if current_turn == "Turn N/A":
            continue

        nation_table = NationTable(game_id)
        
        match current_turn:

            case "Starting Region Selection in Progress":
                # get title and game link
                game_name = game_data["Game Name"]
                game_data["Title"] = f"""<a href="/{game_id}">{game_name}</a>"""
                # get status
                game_data["Status"] = current_turn
                # get player information
                refined_player_data = []
                for nation in nation_table:
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
                game_name = game_data["Game Name"]
                game_data["Title"] = f"""<a href="/{game_id}">{game_name}</a>"""
                # get status
                game_data["Status"] = current_turn
                # get player information
                refined_player_data = []
                for nation in nation_table:
                    username = player_records_dict[nation.player_id]["Username"]
                    username_str = f"""<a href="profile/{nation.player_id}">{username}</a>"""
                    player_color_2 = check_color_correction(nation.color)
                    refined_player_data.append([nation.name, 0, 'TBD', username_str, nation.color, player_color_2])
                # get image
                image_url = url_for('main.get_mainmap', full_game_id=game_id)

            case _:
                # get title and game link
                game_name = game_data["Game Name"]
                game_data["Title"] = f"""<a href="/{game_id}">{game_name}</a>"""
                # get status
                if game_data["Game Active"]:
                    game_data["Status"] = f"Turn {current_turn}"
                else:
                    game_data["Status"] = "Game Over!"
                # get player information
                refined_player_data = generate_refined_player_list_active(game_id, current_turn)
                # get image
                image_url = url_for('main.get_mainmap', full_game_id=game_id)
        
        game_data["Playerdata Masterlist"] = refined_player_data
        game_data["image_url"] = image_url
    
    return render_template('temp_games.html', dict = active_games_dict, full_game_id = game_id)

#SETTINGS PAGE
@main.route('/settings')
def settings():
    username_list = []
    for profile_id, player_data in player_records_dict.items():
        username_list.append(player_data.get("Username"))
    return render_template('temp_settings.html', username_list = username_list)

#SETTINGS PAGE - Create Game Procedure
@main.route('/create_game', methods=['POST'])
def create_game():
    
    #get game record dictionaries
    with open('active_games.json', 'r') as json_file:
        active_games_dict = json.load(json_file)
    with open('game_records.json', 'r') as json_file:
        game_records_dict = json.load(json_file)

    #get username list
    username_list = []
    with open('player_records.json', 'r') as json_file:
        player_records_dict = json.load(json_file)
    for profile_id, player_data in player_records_dict.items():
        username_list.append(player_data.get("Username"))
    
    #get values from settings form
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
        #if checked, checkbox returns True. Otherwise returns none.
        add_player_value = request.form.get(username)
        if add_player_value:
            profile_ids_list.append(profile_id_list[index])

    #erase all active games override
    if form_data_dict["Game Name"] == "5EQM8Z5VoLxvxqeP1GAu":
        active_games = [key for key, value in active_games_dict.items() if value.get("Game Active")]
        for active_game_id in active_games:
            active_games_dict[active_game_id] = {
                "Game Name": "Open Game Slot",
                "Game #": 0,
                "Game Active": False,
                "Information": {
                    "Version": "TBD",
                    "Scenario": "TBD",
                    "Map": "TBD",
                    "Victory Conditions": "TBD",
                    "Fog of War": "TBD",
                    "Turn Length": "TBD",
                    "Accelerated Schedule": "TBD",
                    "Deadlines on Weekends": "TBD"
                },
                "Statistics": {
                    "Player Count": "0",
                    "Region Disputes": 0,
                    "Current Turn": "Turn N/A",
                    "Days Ellapsed": 0,
                    "Game Started": "TBD",
                },
                "Inactive Events": [],
                "Active Events": {},
                "Current Event": {}
            }
            core.erase_game(active_game_id)
        active_games = [key for key, value in game_records_dict.items() if value.get("Statistics").get("Game Ended") == "Present"]
        for active_game_name in active_games:
            del game_records_dict[active_game_name]
        with open('active_games.json', 'w') as json_file:
            json.dump(active_games_dict, json_file, indent=4)
        with open('game_records.json', 'w') as json_file:
            json.dump(game_records_dict, json_file, indent=4)
        return redirect(f'/games')

    #check if a game slot is available
    full_game_id = None
    for select_game_id, value in active_games_dict.items():
        if not value.get("Game Active"):
            full_game_id = select_game_id
            break
    if full_game_id != None:
        core.create_new_game(full_game_id, form_data_dict, profile_ids_list)
        return redirect(f'/games')
    else:
        print("Error: No inactive game found to overwrite.")
        quit()

#GAMES ARCHIVE PAGE
@main.route('/archived_games')
def archived_games():
    
    with open('game_records.json', 'r') as json_file:
        game_records_dict = json.load(json_file)
    
    #take information from game_record_dict
    ongoing_list = []
    for game_name, game_data in game_records_dict.items():
        
        if game_data["Statistics"]["Game Ended"] == "Present":
            ongoing_list.append(game_name)
            continue
        
        #get playerdata
        archived_player_data_list, players_who_won_list = generate_refined_player_list_inactive(game_data)
        if len(players_who_won_list) == 1:
            victors_str = players_who_won_list[0]
            game_data["Winner String"] = f'{victors_str} Victory!'
        elif len(players_who_won_list) > 1:
            victors_str = ' & '.join(players_who_won_list)
            game_data["Winner String"] = f'{victors_str} Victory!'
        elif len(players_who_won_list) == 0:
            game_data["Winner String"] = 'Draw!'
        game_data["Playerdata Masterlist"] = archived_player_data_list

        #get game images
        image_name_list = []
        filename = "graphic.png"
        filepath = os.path.join(f"app/static/archive/{game_data["Game ID"]}/", filename)
        if os.path.isfile(filepath):
            image_name_list.append(filename)
        turn_number = game_data["Statistics"]["Turns Ellapsed"]
        if game_data["Statistics"]["Turns Ellapsed"] % 4 != 0:
            filename = f"{turn_number}.png"
            filepath = os.path.join(f"app/static/archive/{game_data["Game ID"]}/", filename)
            if os.path.isfile(filepath):
                image_name_list.append(filename)
            while turn_number % 4 != 0:
                turn_number -= 1
        while turn_number >= 0:
            filename = f"{turn_number}.png"
            filepath = os.path.join(f"app/static/archive/{game_data["Game ID"]}/", filename)
            if os.path.isfile(filepath):
                image_name_list.append(filename)
            turn_number -= 4
        game_data["Slideshow Images"] = image_name_list
    
    #display games from newest to oldest
    game_records_dict = dict(sorted(game_records_dict.items(), key=lambda item: item[1]['Game #'], reverse=True))

    #hide ongoing games
    for game_name in ongoing_list:
        del game_records_dict[game_name]

    #get gameid list (needed for slideshows)
    game_id_list = []
    for game_name, game_data in game_records_dict.items():
        game_id_list.append(game_data["Game ID"])
    game_id_list.reverse()
    slide_index_list = [1] * len(game_id_list)
    
    return render_template('temp_archive.html', dict = game_records_dict, game_id_list = game_id_list, slide_index_list = slide_index_list)

#LEADERBOARD PAGE
@main.route('/leaderboard')
def leaderboard():
    
    leaderboard_data = []
    with open('leaderboard.csv', 'r') as file:
        reader = csv.reader(file)
        for row in reader:
            if row != []:
                leaderboard_data.append(row)
    
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
    
    with open('leaderboard_records.json', 'r') as json_file:
        leaderboard_records_dict = json.load(json_file)
    
    return render_template('temp_leaderboard_new.html', leaderboard_data = leaderboard_data, profile_ids = profile_ids, leaderboard_records_dict = leaderboard_records_dict)

#GENRATE PROFILE PAGES
def generate_profile_route(profile_id):
    route_name = f'profile_route_{uuid.uuid4().hex}'
    @main.route(f'/profile/{profile_id}', endpoint=route_name)
    def load_profile():
        #read needed files
        with open('game_records.json', 'r') as json_file:
            game_records_dict = json.load(json_file)
        leaderboard_list = []
        with open('leaderboard.csv', 'r') as file:
            reader = csv.reader(file)
            for row in reader:
                leaderboard_list.append(row)
        #get data from player_records.json
        username = player_records_dict[profile_id]["Username"]
        joined = player_records_dict[profile_id]["Join Date"]
        resignations = player_records_dict[profile_id]["Resignations"]
        #get data from game_records.json
        game_starts = []
        game_ends = []
        governments_played = {
            'Republic': 0,
            'Technocracy': 0,
            'Oligarchy': 0,
            'Totalitarian': 0,
            'Remnant': 0,
            'Protectorate': 0,
            'Military Junta': 0,
            'Crime Syndicate': 0,
            'Plutocracy': 0,
            'United States Remnant': 0,
        }
        foreign_policies_played = {
            'Diplomatic': 0,
            'Commercial': 0,
            'Isolationist': 0,
            'Imperialist': 0,
        }
        first_game = ''
        latest_game = ''
        draws = 0
        for game_name, game_data in game_records_dict.items():
            if "Test Game" in game_name:
                continue
            players_who_won = []
            players_who_lost = []
            for select_profile_id, player_data in game_data.get("Player Data", {}).items():
                if player_data.get("Victory") == 0:
                    players_who_lost.append(select_profile_id)
                    if profile_id in players_who_lost and len(players_who_lost) == len(game_records_dict[game_name]["Player Data"]):
                        draws += 1
                else:
                    players_who_won.append(select_profile_id)
            if profile_id in players_who_lost or profile_id in players_who_won:
                game_starts.append(game_data['Statistics']["Game Started"])
                game_ends.append(game_data['Statistics']["Game Ended"])
                government_choice = game_records_dict[game_name]["Player Data"][profile_id]["Government"]
                foreign_policy_choice = game_records_dict[game_name]["Player Data"][profile_id]["Foreign Policy"]
                governments_played[government_choice] += 1
                foreign_policies_played[foreign_policy_choice] += 1
        first_game = game_starts.pop(0)
        latest_game = game_ends.pop(0)
        for date_str in game_starts:
            date_obj_leading = datetime.strptime(first_game, "%m/%d/%Y")
            data_obj_contender = datetime.strptime(date_str, "%m/%d/%Y")
            if data_obj_contender < date_obj_leading:
                first_game = date_str
        for date_str in game_ends:
            date_obj_leading = datetime.strptime(latest_game, "%m/%d/%Y")
            data_obj_contender = datetime.strptime(date_str, "%m/%d/%Y")
            if data_obj_contender > date_obj_leading:
                latest_game = date_str
        favorite_gov_score = max(governments_played.values())
        favorite_govs = [key for key, value in governments_played.items() if value == favorite_gov_score]
        favorite_gov = "/".join(favorite_govs)
        favorite_fp_score = max(foreign_policies_played.values())
        favorite_fps = [key for key, value in foreign_policies_played.items() if value == favorite_fp_score]
        favorite_fp = "/".join(favorite_fps)
        #get data from leaderboard.csv
        for index, entry in enumerate(leaderboard_list):
            if entry[0] == username:
                rank = index + 1
                wins = entry[1]
                score = entry[2]
                average = entry[3]
                games = entry[4]
                break
        losses = int(games) - int(wins) - int(draws)
        reliability = (float(games) - float(resignations)) / float(games)
        reliability = round(reliability, 2)
        reliability = reliability * 100
        reliability = int(reliability)
        reliability = f'{reliability}%'
        return render_template('temp_profile.html', username = username, joined = joined, first_game = first_game, latest_game = latest_game, rank = rank, reliability = reliability, wins = wins, draws = draws, losses = losses, score = score, average = average, games = games, favorite_gov = favorite_gov, favorite_fp = favorite_fp)
with open('player_records.json', 'r') as json_file:
    player_records_dict = json.load(json_file)
profile_id_list = list(player_records_dict.keys())
for profile_id in profile_id_list:
    generate_profile_route(profile_id)


#GAME LOADING
################################################################################

#LOAD GAME PAGE
@main.route(f'/<full_game_id>')
def game_load(full_game_id):
    
    #read the contents of active_games.json
    with open('active_games.json', 'r') as json_file:
        active_games_dict = json.load(json_file)
    game1_title = active_games_dict[full_game_id]["Game Name"]
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
        largest_nation_tup = checks.get_top_three(full_game_id, 'largest_nation', True)
        strongest_economy_tup = checks.get_top_three(full_game_id, 'strongest_economy', True)
        largest_military_tup = checks.get_top_three(full_game_id, 'largest_military', True)
        most_research_tup = checks.get_top_three(full_game_id, 'most_research', True)
        largest_nation_list = list(largest_nation_tup)
        strongest_economy_list = list(strongest_economy_tup)
        largest_military_list = list(largest_military_tup)
        most_research_list = list(most_research_tup)
        for i in range(len(largest_nation_list)):
            largest_nation_list[i] = color_nation_names(largest_nation_list[i], full_game_id)
            strongest_economy_list[i] = color_nation_names(strongest_economy_list[i], full_game_id)
            largest_military_list[i] = color_nation_names(largest_military_list[i], full_game_id)
            most_research_list[i] = color_nation_names(most_research_list[i], full_game_id)
        archived_player_data_list, players_who_won_list = generate_refined_player_list_inactive(game_data)
        if len(players_who_won_list) == 1:
            victors_str = players_who_won_list[0]
            victory_string = (f"""{victors_str} has won the game.""")
        elif len(players_who_won_list) > 1:
            victors_str = ' and '.join(players_who_won_list)
            victory_string = (f'{victors_str} have won the game.')
        elif len(players_who_won_list) == 0:
            victory_string = (f'Game drawn.')
        victory_string = color_nation_names(victory_string, full_game_id)
        return render_template('temp_stage4.html', game1_title = game1_title, game1_extendedtitle = game1_extendedtitle, main_url = main_url, resource_url = resource_url, control_url = control_url, archived_player_data_list = archived_player_data_list, largest_nation_list = largest_nation_list, strongest_economy_list = strongest_economy_list, largest_military_list = largest_military_list, most_research_list = most_research_list, victory_string = victory_string)
    
    # load active state
    # tba - fix this garbage when you get around to redoing the frontend
    match game1_turn:
        
        case "Starting Region Selection in Progress":
            
            form_key = "main.stage1_resolution"
            player_data = []
            nation_table = NationTable(full_game_id)
            
            for nation in nation_table:
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
            nation_table = NationTable(full_game_id)
            
            for nation in nation_table:
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
            nation_table = NationTable(full_game_id)
            for nation in nation_table:
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

#GENERATE NATION SHEET PAGES
def generate_player_route(full_game_id, player_id):
    route_name = f'player_route_{uuid.uuid4().hex}'
    @main.route(f'/{full_game_id}/player{player_id}', endpoint=route_name)
    def player_route():
        page_title = f'Player #{player_id} Nation Sheet'
        current_turn_num = core.get_current_turn_num(full_game_id)
        player_information_dict = core.get_data_for_nation_sheet(full_game_id, str(player_id))
        return render_template('temp_nation_sheet.html', page_title=page_title, player_information_dict=player_information_dict)

#GENERATION PROCEDURE
game_ids = ['game1', 'game2']
map_names = ['mainmap', 'resourcemap', 'controlmap']
player_ids = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
for full_game_id in game_ids:
    for player_id in player_ids:
        generate_player_route(full_game_id, player_id)

#WARS PAGE
@main.route('/<full_game_id>/wars')
def wars(full_game_id):
    
    # get game data
    nation_table = NationTable(full_game_id)
    war_table = WarTable(full_game_id)
    current_turn_num = core.get_current_turn_num(full_game_id)
    with open('active_games.json', 'r') as json_file:
        active_games_dict = json.load(json_file)
    game_name = active_games_dict[full_game_id]["Game Name"]
    page_title = f'{game_name} Wars List'
    
    # read wars
    results = {}
    for war in war_table:

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
        main_attacker = nation_table.get(ma_id)
        main_defender = nation_table.get(md_id)

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
                if war.attacker_total != 0 and war.defender_total == 0:
                    war_status_bar = [attacker_color] * 1
                elif war.attacker_total == 0 and war.defender_total != 0:
                    war_status_bar = [defender_color] * 1
                elif war.attacker_total == 0 and war.defender_total == 0:
                    war_status_bar = [attacker_color] * 1
                    war_status_bar += [defender_color] * 1
                else:
                    # calculate attacker value
                    attacker_percent = float(war.attacker_total) / float(war.attacker_total + war.defender_total)
                    attacker_percent = round(attacker_percent, 2)
                    attacker_points = int(attacker_percent * 100)
                    attacker_steps = round(attacker_points / 5)
                    # calculate defender value
                    defender_percent = float(war.defender_total) / float(war.attacker_total + war.defender_total)
                    defender_percent = round(defender_percent, 2)
                    defender_points = int(defender_percent * 100)
                    defender_steps = round(defender_points / 5)
                    # add to score bar
                    war_status_bar = [attacker_color] * attacker_steps
                    war_status_bar += [defender_color] * defender_steps
        inner_dict["scoreBar"] = war_status_bar

        # get attacker warscore data
        copy = {
            "Total War Score": war.attacker_total,
            "From Occupation": war.attacker_occupation,
            "From Combat Victories": war.attacker_victories,
            "From Enemy Units Destroyed": war.attacker_destroyed_units,
            "From Enemy Impr. Destroyed": war.attacker_destroyed_improvements,
            "From Capital Captures": war.attacker_captures,
            "From Nuclear Strikes": war.attacker_nuclear_strikes
        }
        inner_dict["attackerWarScore"] = copy
        
        # get defender warscore data
        copy = {
            "Total War Score": war.defender_total,
            "From Occupation": war.defender_occupation,
            "From Combat Victories": war.defender_victories,
            "From Enemy Units Destroyed": war.defender_destroyed_units,
            "From Enemy Impr. Destroyed": war.defender_destroyed_improvements,
            "From Capital Captures": war.defender_captures,
            "From Nuclear Strikes": war.defender_nuclear_strikes
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
                if war.attacker_total > war.defender_total:
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

#RESEARCH PAGE
@main.route('/<full_game_id>/technologies')
def technologies(full_game_id):
    
    # get game data
    nation_table = NationTable(full_game_id)
    with open('active_games.json', 'r') as json_file:
        active_games_dict = json.load(json_file)
    game_name = active_games_dict[full_game_id]["Game Name"]
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
        research_data_dict[research_name]["Player Research"] = [None] * len(nation_table)
    for index, nation in enumerate(nation_table):
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

#AGENDAS PAGE
@main.route('/<full_game_id>/agendas')
def agendas(full_game_id):
    
    # get game data
    nation_table = NationTable(full_game_id)
    with open('active_games.json', 'r') as json_file:
        active_games_dict = json.load(json_file)
    game_name = active_games_dict[full_game_id]["Game Name"]
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
        agenda_data_dict[research_name]["Player Research"] = [None] * len(nation_table)
    for index, nation in enumerate(nation_table):
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
    game_name = active_games_dict[full_game_id]["Game Name"]
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

    return render_template('temp_units.html', page_title = page_title, dict = unit_dict)

# IMPROVEMENTS REF PAGE
@main.route('/<full_game_id>/improvements')
def improvements_ref(full_game_id):
    
    # read the contents of active_games.json
    with open('active_games.json', 'r') as json_file:
        active_games_dict = json.load(json_file)
    game_name = active_games_dict[full_game_id]["Game Name"]
    page_title = f'{game_name} - Improvement Reference'
    
    # get unit dict
    improvement_dict: dict = core.get_scenario_dict(full_game_id, "Improvements")

    # filter improvements
    improvement_dict_filtered = {}
    for improvement_name, improvement_data in improvement_dict.items():

        # assign color
        # to do - make a function that assigns color based on improvement's required tech
        match improvement_name:
            case 'Boot Camp' | 'Crude Barrier' | 'Military Base' | 'Military Outpost' | 'Missile Defense Network' | 'Missile Defense System' | 'Missile Silo':
                improvement_data["stat_color"] = "stat-red"
            case 'Coal Mine' | 'Nuclear Power Plant' | 'Oil Refinery' | 'Oil Well' | 'Solar Farm' | 'Wind Farm' | 'Strip Mine':
                improvement_data["stat_color"] = "stat-yellow"
            case 'Advanced Metals Mine' | 'Common Metals Mine' | 'Industrial Zone' | 'Uranium Mine' | 'Rare Earth Elements Mine':
                improvement_data["stat_color"] = "stat-grey"
            case 'Capital' | 'Central Bank' | 'City' | 'Research Institute' | 'Research Laboratory':
                improvement_data["stat_color"] = "stat-blue"
            case _:
                improvement_data["stat_color"] = "stat-grey"

        # hide fog of war techs
        if active_games_dict[full_game_id]["Information"]["Fog of War"] != "Enabled" and improvement_data.get("Fog of War Improvement", None):
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
    game_name = active_games_dict[full_game_id]["Game Name"]
    page_title = f'{game_name} - Resource Market'

    # tba - grab this from scenario files
    data = {
        "Technology": {
            "Base Price": 5,
            "Current Price": 0,
            "Bought": 0,
            "Sold": 0
        },
        "Coal": {
            "Base Price": 3,
            "Current Price": 0,
            "Bought": 0,
            "Sold": 0
        },
        "Oil": {
            "Base Price": 3,
            "Current Price": 0,
            "Bought": 0,
            "Sold": 0
        },
        "Basic Materials": {
            "Base Price": 5,
            "Current Price": 0,
            "Bought": 0,
            "Sold": 0
        },
        "Common Metals": {
            "Base Price": 5,
            "Current Price": 0,
            "Bought": 0,
            "Sold": 0
        },
        "Advanced Metals": {
            "Base Price": 10,
            "Current Price": 0,
            "Bought": 0,
            "Sold": 0
        },
        "Uranium": {
            "Base Price": 10,
            "Current Price": 0,
            "Bought": 0,
            "Sold": 0
        },
        "Rare Earth Elements": {
            "Base Price": 20,
            "Current Price": 0,
            "Bought": 0,
            "Sold": 0
        },
    }
    
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
        for affected_resource_name in active_games_dict[full_game_id]["Active Events"]["Market Inflation"]["Affected Resources"]:
            new_price = data[affected_resource_name]["Current Price"] * 2
            data[resource_name]["Current Price"] = round(new_price, 2)
    elif "Market Recession" in active_games_dict[full_game_id]["Active Events"]:
        for affected_resource_name in active_games_dict[full_game_id]["Active Events"]["Market Recession"]["Affected Resources"]:
            new_price = data[affected_resource_name]["Current Price"] * 0.5
            data[resource_name]["Current Price"] = round(new_price, 0.5)

    # format price strings
    for resource_name in data:
        data[resource_name]["Base Price"] = f"{data[resource_name]["Base Price"]:.2f}"
        data[resource_name]["Current Price"] = f"{data[resource_name]["Current Price"]:.2f}"

    return render_template('temp_resource_market.html', page_title = page_title, records_list = rmdata_recent_transaction_list, records_flag = records_flag, prices_dict = data)

# ANNOUNCEMENT PAGE
@main.route('/<full_game_id>/announcements')
def announcements(full_game_id):

    # get game data
    nation_table = NationTable(full_game_id)
    alliance_table = AllianceTable(full_game_id)
    war_table = WarTable(full_game_id)
    notifications = Notifications(full_game_id)
    trucedata_filepath = f'gamedata/{full_game_id}/trucedata.csv'
    trucedata_list = core.read_file(trucedata_filepath, 1)
    with open('active_games.json', 'r') as json_file:
        active_games_dict = json.load(json_file)

    # read the contents of active_games.json
    game_name = active_games_dict[full_game_id]["Game Name"]
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
    for war in war_table:
        if war.outcome == "TBD":
            diplomacy_list.append(f"{war.name} is ongoing.")
    # get all ongoing truces
    for truce in trucedata_list:
        truce_participants_list = []
        for i in range(1, 11):
            truce_status = ast.literal_eval(truce[i])
            if truce_status:
                nation = nation_table.get(i)
                truce_participants_list.append(nation.name)
        truce_name = ' - '.join(truce_participants_list)
        truce_end_turn = int(truce[11])
        if truce_end_turn > current_turn_num:
            diplomacy_list.append(f"{truce_name} truce until turn {truce_end_turn}.")
        if truce_end_turn == current_turn_num:
            diplomacy_list.append(f'{truce_name} truce has expired.')
    # format diplomacy string
    diplomacy_string = "<br>".join(diplomacy_list)
    diplomacy_string = palette.color_nation_names(diplomacy_string, full_game_id)

    
    # Build Notifications String
    notifications_list = []
    q = PriorityQueue()
    for string, priority in notifications:
        q.put((priority, string))
    while not q.empty():
        ntf = q.get()
        notifications_list.append(ntf[1])
    notifications_string = "<br>".join(notifications_list)
    notifications_string = palette.color_nation_names(notifications_string, full_game_id)


    # Build Statistics String
    statistics_list = []
    statistics_list.append(f"Total alliances: {len(alliance_table)}")
    longest_alliance_name, longest_alliance_duration = alliance_table.get_longest_alliance()
    if longest_alliance_name is not None:
        statistics_list.append(f"Longest alliance: {longest_alliance_name} - {longest_alliance_duration} turns")
    else:
        statistics_list.append(f"Longest alliance: N/A")
    statistics_list.append(f"Total wars: {len(war_table)}")
    statistics_list.append(f"Units lost in war: {war_table.total_units_lost()}")
    statistics_list.append(f"Improvements destroyed in war: {war_table.total_units_lost()}")
    statistics_list.append(f"Nuclear Missiles launched: {war_table.total_missiles_launched()}")
    war_name, war_duration = war_table.find_longest_war()
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
        standings = nation_table.get_top_three(record)
        standings_filtered = []
        for entry in standings:
            nation_name = palette.color_nation_names(entry[0], full_game_id)
            if record == "netIncome":
                standings_filtered.append([nation_name, f"{entry[1]:.2f}"])
            else:
                standings_filtered.append([nation_name, entry[1]])
        record_name = record_names[i]
        standings_dict[record_name] = standings_filtered
    
    # update scoreboard
    scoreboard_dict = {}
    for nation in nation_table:
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

    with open('active_games.json', 'r') as json_file:
        active_games_dict = json.load(json_file)
    game_name = active_games_dict[full_game_id]["Game Name"]
    page_title = f'{game_name} - Alliance Page'

    nation_table = NationTable(full_game_id)
    alliance_table = AllianceTable(full_game_id)
    alliance_dict = alliance_table.data
    misc_data_dict = core.get_scenario_dict(full_game_id, "Misc")
    alliance_type_dict = misc_data_dict["allianceTypes"]

    alliance_dict_filtered = {}
    for alliance_name, alliance_data in alliance_dict.items():
        if alliance_data["turnEnded"] == 0:
            
            # adds alliance establishment string
            turn_started = alliance_data["turnCreated"]
            season, year = core.date_from_turn_num(turn_started)
            date_str = f"{season} {year} (Turn {turn_started})"
            alliance_data["turnCreated"] = date_str

            # add color to nation names
            alliance_data["currentMembersFormatted"] = {}
            for nation_name, turn_joined in alliance_data["currentMembers"].items():
                nation = nation_table.get(nation_name)
                bad_primary_colors_set = {"#603913", "#105500", "#8b2a1a"}
                if nation.color in bad_primary_colors_set:
                    color = palette.normal_to_occupied[nation.color]
                else:
                    color = nation.color
                # add to new dict
                alliance_data["currentMembersFormatted"][nation_name] = {}
                alliance_data["currentMembersFormatted"][nation_name]["turnJoined"] = turn_joined
                alliance_data["currentMembersFormatted"][nation_name]["nationColor"] = color
            
            # adds alliance color
            alliance_data["color"] = palette.str_to_hex(alliance_type_dict[alliance_data["allianceType"]]["colorTheme"])

            alliance_dict_filtered[alliance_name] = alliance_data

    return render_template('temp_alliances.html', alliance_dict = alliance_dict_filtered, abilities_dict = alliance_type_dict, page_title = page_title)

#MAP IMAGES
@main.route('/<full_game_id>/mainmap.png')
def get_mainmap(full_game_id):
    with open('active_games.json', 'r') as json_file:
        active_games_dict = json.load(json_file)
    current_turn_num = active_games_dict[full_game_id]["Statistics"]["Current Turn"]
    map_str = map.get_map_str(active_games_dict[full_game_id]["Information"]["Map"])
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


#ACTION PROCESSING
################################################################################

@main.route('/stage1_resolution', methods=['POST'])
def stage1_resolution():
    
    full_game_id = request.form.get('full_game_id')
    nation_table = NationTable(full_game_id)

    contents_dict = {}
    for nation in nation_table:
        contents_dict[nation.id] = {}
        contents_dict[nation.id]["start"] = request.form.get(f"regioninput_p{nation.id}")
        contents_dict[nation.id]["color"] = request.form.get(f"colordropdown_p{nation.id}")
    
    core.resolve_stage1_processing(full_game_id, contents_dict)
    
    return redirect(f'/{full_game_id}')

@main.route('/stage2_resolution', methods=['POST'])
def stage2_resolution():

    full_game_id = request.form.get('full_game_id')
    nation_table = NationTable(full_game_id)

    contents_dict = {}
    for nation in nation_table:
        contents_dict[nation.id] = {}
        contents_dict[nation.id]["name_choice"] = request.form.get(f"nameinput_p{nation.id}")
        contents_dict[nation.id]["gov_choice"] = request.form.get(f"govinput_p{nation.id}")
        contents_dict[nation.id]["fp_choice"] = request.form.get(f"fpinput_p{nation.id}")
        contents_dict[nation.id]["vc_choice"] = request.form.get(f"vcinput_p{nation.id}")

    core.resolve_stage2_processing(full_game_id, contents_dict)
    
    return redirect(f'/{full_game_id}')

@main.route('/turn_resolution', methods=['POST'])
def turn_resolution():

    full_game_id = request.form.get('full_game_id')
    nation_table = NationTable(full_game_id)

    contents_dict = {}
    for nation in nation_table:
        contents_dict[nation.id] = []
        public_str = request.form.get(f"public_textarea_p{nation.id}")
        private_str = request.form.get(f"private_textarea_p{nation.id}")
        if public_str:
            actions_list = public_str.split('\r\n')
            contents_dict[nation.id].extend(actions_list)
        if private_str:
            actions_list = private_str.split('\r\n')
            contents_dict[nation.id].extend(actions_list)

    core.resolve_turn_processing(full_game_id, contents_dict)

    return redirect(f'/{full_game_id}')

@main.route('/event_resolution', methods=['POST'])
def event_resolution():
    '''
    Handles current event and runs end of turn checks & updates when activated.
    Redirects back to selected game.
    '''
    
    full_game_id = request.form.get('full_game_id')
    with open(f'active_games.json', 'r') as json_file:  
        active_games_dict = json.load(json_file)
    
    events.handle_current_event(active_games_dict, full_game_id)
    core.run_end_of_turn_checks(full_game_id)

    return redirect(f'/{full_game_id}')

#map_tests.run()
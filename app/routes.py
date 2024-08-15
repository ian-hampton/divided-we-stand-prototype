#STANDARD IMPORTS
import ast
import csv
from datetime import datetime
import json
from operator import itemgetter
import os
import random
import shutil
import uuid

#UWS SOURCE IMPORTS
import core
import checks
import events
from testing import map_tests

#ENVIROMENT IMPORTS
from flask import Flask, render_template, request, redirect, url_for, send_file
app = Flask(__name__, template_folder='html')


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
def color_nation_names(string, full_game_id):
    playerdata_filepath = f'gamedata/{full_game_id}/playerdata.csv'
    nation_name_list = []
    nation_color_list = []
    with open(playerdata_filepath, 'r') as file:
        reader = csv.reader(file)
        next(reader,None)
        for row in reader:
            if row != []:
                nation_name = row[1]
                nation_color = row[2]
                nation_color = check_color_correction(nation_color)
                nation_name_list.append(nation_name)
                nation_color_list.append(nation_color)
    for index, nation_name in enumerate(nation_name_list):
        if nation_name in string:
            string = string.replace(nation_name, f"""<span style="color:{nation_color_list[index]}">{nation_name}</span>""")
    return string
        
#REFINE PLAYERDATA FUNCTION FOR ACTIVE GAMES
def generate_refined_player_list_active(full_game_id, current_turn_num):
    playerdata_list = core.read_file(f'gamedata/{full_game_id}/playerdata.csv', 1)
    refined_player_data_a = []
    refined_player_data_b = []
    for index, playerdata in enumerate(playerdata_list):
        profile_id = playerdata[29]
        gov_fp_string = f"""{playerdata[4]} - {playerdata[3]}"""
        username = player_records_dict[profile_id]["Username"]
        username_str = f"""<a href="profile/{profile_id}">{username}</a>"""
        player_color = playerdata[2]
        player_color = check_color_correction(player_color)
        player_vc_score = 0
        if current_turn_num != 0:
            vc_results = checks.check_victory_conditions(full_game_id, index + 1, current_turn_num)
            for entry in vc_results:
                if entry:
                    player_vc_score += 1
        if player_vc_score > 0:
            refined_player_data_a.append([playerdata[1], player_vc_score, gov_fp_string, username_str, player_color, player_color])
        else:
            refined_player_data_b.append([playerdata[1], player_vc_score, gov_fp_string, username_str, player_color, player_color])
    filtered_player_data_a = sorted(refined_player_data_a, key=itemgetter(0), reverse=False)
    filtered_player_data_a = sorted(filtered_player_data_a, key=itemgetter(1), reverse=True)
    filtered_player_data_b = sorted(refined_player_data_b, key=itemgetter(0), reverse=False)
    refined_player_data = filtered_player_data_a + filtered_player_data_b
    return refined_player_data

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

#HOMEPAGE
@app.route('/')
def main():
    return render_template('UWS.html')

#GAMES PAGE
@app.route('/games')
def games():
    
    #read json files
    username_list = []
    for profile_id, player_data in player_records_dict.items():
        username_list.append(player_data.get("Username"))
    with open('active_games.json', 'r') as json_file:
        active_games_dict = json.load(json_file)
    
    #generate list of active games by iterating through active_games_dict
    active_game_masterlist = []
    for full_game_id, value in active_games_dict.items():
        active_game_data = []
        game_name = value.get("Game Name")
        current_turn = value.get("Current Turn")
        preview_image_filepath = f'static/{full_game_id}_image.png'

        match current_turn:
            case "Turn N/A":
                active_game_data.append('Open Game Slot')
                active_game_data.append('Turn N/A')
                active_game_data.append('Game #: TBD')
                for i in range(0, 8):
                    active_game_data.append('TBD')
                active_game_data.append('static/UWS-2.png')
                playercount = 10
                refined_player_data = []
                for i in range(playercount):
                    refined_player_data.append(['', '', '', '', '#FFFFFF', '#FFFFFF'])
                active_game_data.append(refined_player_data)

            case "Starting Region Selection in Progress":
                active_game_data.append(f"""<a href="/{full_game_id}">{game_name}</a>""")
                active_game_data.append(current_turn)
                active_game_data.append(f"""Game #{value.get("Game #")}""")
                active_game_data.append(value.get("Version"))
                active_game_data.append(value.get("Map"))
                active_game_data.append(value.get("Victory Conditions"))
                active_game_data.append(value.get("Fog of War"))
                active_game_data.append(value.get("Turn Length"))
                active_game_data.append(value.get("Accelerated Schedule"))
                active_game_data.append(value.get("Days Ellapsed"))
                active_game_data.append('TBD')
                active_game_data.append(preview_image_filepath)
                refined_player_data = []
                playerdata_list = core.read_file(f'gamedata/{full_game_id}/playerdata.csv', 1)
                for playerdata in playerdata_list:
                    profile_id = playerdata[30]
                    username = player_records_dict[profile_id]["Username"]
                    username_str = f"""<a href="profile/{profile_id}">{username}</a>"""
                    refined_player_data.append([playerdata[1], 0, 'TBD', username_str, '#ffffff', '#ffffff'])
                active_game_data.append(refined_player_data)

            case "Nation Setup in Progress":
                active_game_data.append(f"""<a href="/{full_game_id}">{game_name}</a>""")
                active_game_data.append(current_turn)
                active_game_data.append(f"""Game #{value.get("Game #")}""")
                active_game_data.append(value.get("Version"))
                active_game_data.append(value.get("Map"))
                active_game_data.append(value.get("Victory Conditions"))
                active_game_data.append(value.get("Fog of War"))
                active_game_data.append(value.get("Turn Length"))
                active_game_data.append(value.get("Accelerated Schedule"))
                active_game_data.append(value.get("Days Ellapsed"))
                active_game_data.append('TBD')
                active_game_data.append(preview_image_filepath)
                refined_player_data = []
                playerdata_list = core.read_file(f'gamedata/{full_game_id}/playerdata.csv', 1)
                for playerdata in playerdata_list:
                    profile_id = playerdata[30]
                    username = player_records_dict[profile_id]["Username"]
                    username_str = f"""<a href="profile/{profile_id}">{username}</a>"""
                    player_color = playerdata[2]
                    player_color_2 = check_color_correction(player_color)
                    refined_player_data.append([playerdata[1], 0, 'TBD', username_str, player_color, player_color_2])
                active_game_data.append(refined_player_data)

            case _:
                active_game_data.append(f"""<a href="/{full_game_id}">{game_name}</a>""")
                if value.get("Game Active"):
                    active_game_data.append(f"Turn {current_turn}")
                else:
                    active_game_data.append("Game Completed")
                active_game_data.append(f"""Game #{value.get("Game #")}""")
                active_game_data.append(value.get("Version"))
                active_game_data.append(value.get("Map"))
                active_game_data.append(value.get("Victory Conditions"))
                active_game_data.append(value.get("Fog of War"))
                active_game_data.append(value.get("Turn Length"))
                active_game_data.append(value.get("Accelerated Schedule"))
                active_game_data.append(value.get("Days Ellapsed"))
                active_game_data.append(value.get("Game Started"))
                active_game_data.append(preview_image_filepath)
                refined_player_data = generate_refined_player_list_active(full_game_id, current_turn)
                active_game_data.append(refined_player_data)
        active_game_masterlist.append(active_game_data)
    return render_template('Games.html', active_game_masterlist = active_game_masterlist, full_game_id = full_game_id)

#SETTINGS PAGE
@app.route('/settings')
def settings():
    username_list = []
    for profile_id, player_data in player_records_dict.items():
        username_list.append(player_data.get("Username"))
    return render_template('Settings.html', username_list = username_list)

#SETTINGS PAGE - Create Game Procedure
@app.route('/create_game', methods=['POST'])
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
        "Fog of War": request.form.get('fow_dropdown')
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
                "Current Turn": "Turn N/A",
                "Game #": 0,
                "Version": "TBD",
                "Player Count": "0",
                "Map": "TBD",
                "Victory Conditions": "TBD",
                "Fog of War": "TBD",
                "Turn Length": "TBD",
                "Accelerated Schedule": "TBD",
                "Days Ellapsed": 0,
                "Game Started": "TBD",
                "Inactive Events": [],
                "Active Events": {},
                "Current Event": {},
                "Game Active": False
            }
            core.erase_game(active_game_id)
        active_games = [key for key, value in game_records_dict.items() if value.get("Game Ended") == "Present"]
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

#GAME CREATED
@app.route('/game_created')
def game_created():
    return render_template('Game Created.html')

#GAMES ARCHIVE PAGE
@app.route('/archived_games')
def archived_games():
    with open('game_records.json', 'r') as json_file:
        game_records_dict = json.load(json_file)
    archived_game_masterlist = []
    for game, game_data in game_records_dict.items():
        if game_records_dict[game]["Game Ended"] == "Present":
            continue
        archived_game_data = []
        archived_game_data.append(game)
        archived_game_data.append(game_records_dict[game]["Version"])
        archived_game_data.append(game_records_dict[game]["Map"])
        archived_game_data.append(game_records_dict[game]["Victory Conditions"])
        archived_game_data.append(game_records_dict[game]["Fog of War"])
        archived_game_data.append(game_records_dict[game]["Turn Duration"])
        archived_game_data.append(game_records_dict[game]["Accelerated Schedule"])
        archived_game_data.append(game_records_dict[game]["Game End Turn"])
        archived_game_data.append(game_records_dict[game]["Days Ellapsed"])
        date_string = f"""{game_records_dict[game]["Game Started"]} - {game_records_dict[game]["Game Ended"]}"""
        archived_game_data.append(date_string)
        game_title_str = game.replace(' ', '-')
        archived_game_data.append(f'static/archive/{game_title_str}.png')
        archived_player_data_list, players_who_won_list = generate_refined_player_list_inactive(game_data)
        if len(players_who_won_list) == 1:
            victors_str = players_who_won_list[0]
            archived_game_data.append(f'{victors_str} Victory!')
        elif len(players_who_won_list) > 1:
            victors_str = ' & '.join(players_who_won_list)
            archived_game_data.append(f'{victors_str} Victory!')
        elif len(players_who_won_list) == 0:
            archived_game_data.append(f'Draw!')
        archived_game_data.append(archived_player_data_list)
        archived_game_data.append(game_records_dict[game]["Game #"])
        archived_game_masterlist.append(archived_game_data)
    archived_game_masterlist.reverse()
    return render_template('Games Archive.html', archived_game_masterlist = archived_game_masterlist)

#LEADERBOARD PAGE
@app.route('/leaderboard')
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
    leaderboard_height = f'{(len(leaderboard_data) * 15) + 50}px'
    with open('leaderboard_records.json', 'r') as json_file:
        leaderboard_records_dict = json.load(json_file)
    return render_template('Leaderboard.html', leaderboard_data = leaderboard_data, profile_ids = profile_ids, leaderboard_height = leaderboard_height, leaderboard_records_dict = leaderboard_records_dict)

#GENRATE PROFILE PAGES
def generate_profile_route(profile_id):
    route_name = f'profile_route_{uuid.uuid4().hex}'
    @app.route(f'/profile/{profile_id}', endpoint=route_name)
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
            'Democracy': 0,
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
                game_starts.append(game_data.get("Game Started"))
                game_ends.append(game_data.get("Game Ended"))
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
        return render_template('Profile.html', username = username, joined = joined, first_game = first_game, latest_game = latest_game, rank = rank, reliability = reliability, wins = wins, draws = draws, losses = losses, score = score, average = average, games = games, favorite_gov = favorite_gov, favorite_fp = favorite_fp)
with open('player_records.json', 'r') as json_file:
    player_records_dict = json.load(json_file)
profile_id_list = list(player_records_dict.keys())
for profile_id in profile_id_list:
    generate_profile_route(profile_id)


#GAME LOADING
################################################################################

#LOAD GAME PAGE
@app.route(f'/<full_game_id>')
def game_load(full_game_id):
    
    #define additional functions
    def define_victory_conditions(row8, row9):
        vc_set1 = ast.literal_eval(row8)
        vc1a = vc_set1[0]
        vc2a = vc_set1[1]
        vc3a = vc_set1[2]
        vc_set2 = ast.literal_eval(row9)
        vc1b = vc_set2[0]
        vc2b = vc_set2[1]
        vc3b = vc_set2[2]
        return vc1a, vc2a, vc3a, vc1b, vc2b, vc3b
    
    #read the contents of active_games.json
    with open('active_games.json', 'r') as json_file:
        active_games_dict = json.load(json_file)
    game1_title = active_games_dict[full_game_id]["Game Name"]
    game1_turn = active_games_dict[full_game_id]["Current Turn"]
    game1_active_bool = active_games_dict[full_game_id]["Game Active"]
    game1_extendedtitle = f"United We Stood - {game1_title}" 
    
    #load images
    main_url = url_for('get_mainmap', full_game_id=full_game_id)
    resource_url = url_for('get_resourcemap', full_game_id=full_game_id)
    control_url = url_for('get_controlmap', full_game_id=full_game_id)
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
        return render_template('stage4.html', game1_title = game1_title, game1_extendedtitle = game1_extendedtitle, main_url = main_url, resource_url = resource_url, control_url = control_url, archived_player_data_list = archived_player_data_list, largest_nation_list = largest_nation_list, strongest_economy_list = strongest_economy_list, largest_military_list = largest_military_list, most_research_list = most_research_list, victory_string = victory_string)
    
    #load active state
    match game1_turn:
        
        case "Starting Region Selection in Progress":
            form_key = "stage1_resolution"
            player_data = []
            with open(f'gamedata/{full_game_id}/playerdata.csv', 'r') as file:
                reader = csv.reader(file)
                next(reader,None)
                for index, row in enumerate(reader):
                    if row != []:
                        player_number = row[0]
                        player_color = row[2]
                        player_id = f'p{index + 1}'
                        regioninput_id = f'regioninput_{player_id}'
                        colordropdown_id = f'colordropdown_{player_id}'
                        vc1a, vc2a, vc3a, vc1b, vc2b, vc3b = define_victory_conditions(row[8], row[9])
                        refined_player_data = [player_number, player_id, player_color, vc1a, vc2a, vc3a, vc1b, vc2b, vc3b, regioninput_id, colordropdown_id]
                        player_data.append(refined_player_data)
                active_player_data = player_data.pop(0)
            return render_template('stage1.html', active_player_data = active_player_data, player_data = player_data, game1_title = game1_title, game1_extendedtitle = game1_extendedtitle, main_url = main_url, resource_url = resource_url, control_url = control_url, full_game_id = full_game_id, form_key = form_key)
        
        case "Nation Setup in Progress":
            form_key = "stage2_resolution"
            player_data = []
            with open(f'gamedata/{full_game_id}/playerdata.csv', 'r') as file:
                reader = csv.reader(file)
                next(reader,None)
                for index, row in enumerate(reader):
                    if row != []:
                        player_number = row[0]
                        player_color = row[2]
                        player_id = f'p{index + 1}'
                        nameinput_id = f"nameinput_{player_id}"
                        govinput_id = f"govinput_{player_id}"
                        fpinput_id = f"fpinput_{player_id}"
                        vcinput_id = f"vcinput_{player_id}"
                        vc1a, vc2a, vc3a, vc1b, vc2b, vc3b = define_victory_conditions(row[8], row[9])
                        refined_player_data = [player_number, player_id, player_color, vc1a, vc2a, vc3a, vc1b, vc2b, vc3b, nameinput_id, govinput_id, fpinput_id, vcinput_id]
                        player_data.append(refined_player_data)
                active_player_data = player_data.pop(0)
            return render_template('stage2.html', active_player_data = active_player_data, player_data = player_data, game1_title = game1_title, game1_extendedtitle = game1_extendedtitle, main_url = main_url, resource_url = resource_url, control_url = control_url, full_game_id = full_game_id, form_key = form_key)
        
        case _:
            form_key = "turn_resolution"
            main_url = url_for('get_mainmap', full_game_id=full_game_id)
            player_data = []
            with open(f'gamedata/{full_game_id}/playerdata.csv', 'r') as file:
                reader = csv.reader(file)
                next(reader,None)
                for index, row in enumerate(reader):
                    if row != []:
                        player_number = row[0]
                        nation_name = row[1]
                        player_color = row[2]
                        player_id = f'p{index + 1}' 
                        public_actions_textarea_id = f"public_textarea_{player_id}"
                        private_actions_textarea_id = f"private_textarea_{player_id}"
                        nation_sheet_url = f'{full_game_id}/player{index + 1}'
                        refined_player_data = [player_number, player_id, player_color, nation_name, public_actions_textarea_id, private_actions_textarea_id, nation_sheet_url]
                        player_data.append(refined_player_data)
                active_player_data = player_data.pop(0)
            with open(f'active_games.json', 'r') as json_file:  
                active_games_dict = json.load(json_file)
            current_event_dict = active_games_dict[full_game_id]["Current Event"]
            if current_event_dict != {}:
                form_key = "event_resolution"
            return render_template('stage3.html', active_player_data = active_player_data, player_data = player_data, game1_title = game1_title, game1_extendedtitle = game1_extendedtitle, main_url = main_url, resource_url = resource_url, control_url = control_url, full_game_id = full_game_id, form_key = form_key)

#GENERATE NATION SHEET PAGES
def generate_player_route(full_game_id, player_id):
    route_name = f'player_route_{uuid.uuid4().hex}'
    @app.route(f'/{full_game_id}/player{player_id}', endpoint=route_name)
    def player_route():
        page_title = f'Player #{player_id} Nation Sheet'
        game_id = int(full_game_id[-1])
        current_turn_num = core.get_current_turn_num(game_id)
        player_information_dict = core.get_data_for_nation_sheet(full_game_id, player_id, current_turn_num)
        return render_template('nation_sheet.html', page_title=page_title, player_information_dict=player_information_dict)

#GENERATION PROCEDURE
game_ids = ['game1', 'game2']
map_names = ['mainmap', 'resourcemap', 'controlmap']
player_ids = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
for full_game_id in game_ids:
    for player_id in player_ids:
        generate_player_route(full_game_id, player_id)

#WARS PAGE
@app.route('/<full_game_id>/wars')
def wars(full_game_id):
    
    #function defs
    def process_wardata(output_list, war_data, i):
        nation_name = playerdata_list[i][1]
        output_list.append(nation_name)
        if len(war_data) == 6:
            war_data.insert(2, "None")
        else:
            war_data.insert(2, war_data.pop(6))
        war_data.pop(0)
        output_list += war_data
        return output_list
    def calculate_war_score(main_nation_data, secondary_nation_list):
        war_score = 0
        war_score += int(main_nation_data[3])
        for secondary_nation_data in secondary_nation_list:
            war_score += int(secondary_nation_data[3])
        return war_score
    
    #read the contents of active_games.json
    with open('active_games.json', 'r') as json_file:
        active_games_dict = json.load(json_file)
    game_id = int(full_game_id[-1])
    game_name = active_games_dict[full_game_id]["Game Name"]
    page_title = f'{game_name} Wars List'
    
    #read playerdata.csv
    playerdata_filepath = f'gamedata/{full_game_id}/playerdata.csv'
    playerdata_list = core.read_file(playerdata_filepath, 0)
    
    #read wardata.csv
    wardata_filepath = f'gamedata/{full_game_id}/wardata.csv'
    wardata_list = core.read_file(wardata_filepath, 2)
    war_masterlist = []
    for war in wardata_list:
        war_entry = []
        #get war title
        war_entry.append(war[11])
        #get war timeframe
        war_start = int(war[12])
        season, year = core.date_from_turn_num(war_start)
        war_start = f'{season} {year}'
        war_end = war[15]
        if war_end.isdigit():
            war_end = int(war_end)
            season, year = core.date_from_turn_num(war_end)
            war_end = f'{season} {year}'
        else:
            war_end = "Present"
        war_entry.append(f'{war_start} - {war_end}')
        #get main attacker and defender
        main_attacker_data = []
        main_defender_data = []
        for i in range(1, 11):
            if war[i] != '-':
                war_data = ast.literal_eval(war[i])
                if war_data[0] == 'Main Attacker':
                    main_attacker_data = process_wardata(main_attacker_data, war_data, i)
                elif war_data[0] == 'Main Defender':
                    main_defender_data = process_wardata(main_defender_data, war_data, i)
            if main_attacker_data != [] and main_defender_data != []:
                break
        war_entry.append(main_attacker_data)
        war_entry.append(main_defender_data)
        #get secondary attackers/defenders
        supporting_attackers = []
        supporting_defenders = []
        for i in range(1, 11):
            secondary_data = []
            if war[i] != '-':
                war_data = ast.literal_eval(war[i])
                if war_data[0] == 'Secondary Attacker':
                    secondary_data = process_wardata(secondary_data, war_data, i)
                    supporting_attackers.append(secondary_data)
                elif war_data[0] == 'Secondary Defender':
                    secondary_data = process_wardata(secondary_data, war_data, i)
                    supporting_defenders.append(secondary_data)
        if supporting_attackers != []:
            war_entry.append("visibility: visible")
        else:
            war_entry.append("display: none")
        if supporting_defenders != []:
            war_entry.append("visibility: visible")
        else:
            war_entry.append("display: none")
        war_entry.append(supporting_attackers)
        war_entry.append(supporting_defenders)
        #get war status
        war_status = war[13]
        attacker_color = ["""background-image: linear-gradient(#cc4125, #eb5a3d)"""]
        defender_color = ["""background-image: linear-gradient(#3c78d8, #5793f3)"""]
        white_color = ["""background-image: linear-gradient(#c0c0c0, #b0b0b0)"""]
        match war_status:
            case "Attacker Victory":
                war_status_bar = attacker_color * 1
            case "Defender Victory":
                war_status_bar = defender_color * 1
            case "White Peace":
                war_status_bar = white_color * 1
            case "Ongoing":
                attacker_score = calculate_war_score(main_attacker_data, supporting_attackers)
                defender_score = calculate_war_score(main_defender_data, supporting_defenders)
                if attacker_score != 0 and defender_score == 0:
                    war_status_bar = attacker_color * 1
                elif attacker_score == 0 and defender_score != 0:
                    war_status_bar = defender_color * 1
                elif attacker_score == 0 and defender_score == 0:
                    war_status_bar = attacker_color * 1
                    war_status_bar += defender_color * 1
                else:
                    attacker_percent = float(attacker_score) / float(attacker_score + defender_score)
                    attacker_percent = round(attacker_percent, 1)
                    attacker_value = int(attacker_percent * 10)
                    defender_percent = float(defender_score) / float(attacker_score + defender_score)
                    defender_percent = round(defender_percent, 1)
                    defender_value = int(defender_percent * 10)
                    war_status_bar = attacker_color * attacker_value
                    war_status_bar += defender_color * defender_value
        war_entry.append(war_status_bar)
        #add war to list
        war_masterlist.append(war_entry)
    return render_template('wars.html', page_title = page_title, war_masterlist = war_masterlist)

#MAP IMAGES
@app.route('/<full_game_id>/mainmap.png')
def get_mainmap(full_game_id):
    with open('active_games.json', 'r') as json_file:
        active_games_dict = json.load(json_file)
    try:
        current_turn_num = int(active_games_dict[full_game_id]["Current Turn"])
        filepath = f'gamedata/{full_game_id}/images/{current_turn_num - 1}.png'
    except:
        filepath = f'gamedata/{full_game_id}/images/mainmap.png'
    return send_file(filepath, mimetype='image/png')
@app.route('/<full_game_id>/resourcemap.png')
def get_resourcemap(full_game_id):
    filepath = f'gamedata/{full_game_id}/images/resourcemap.png'
    return send_file(filepath, mimetype='image/png')
@app.route('/<full_game_id>/controlmap.png')
def get_controlmap(full_game_id):
    filepath = f'gamedata/{full_game_id}/images/controlmap.png'
    return send_file(filepath, mimetype='image/png')


#ACTION PROCESSING
################################################################################
@app.route('/stage1_resolution', methods=['POST'])
def stage1_resolution():
    #process form data
    full_game_id = request.form.get('full_game_id')
    starting_region_list  = []
    player_color_list = []
    for i in range(1, 11):
        starting_region_str = request.form.get(f'regioninput_p{i}')
        if starting_region_str:
            starting_region_list.append(starting_region_str)
        player_color_str = request.form.get(f'colordropdown_p{i}')
        if player_color_str:
            player_color_list.append(player_color_str)
    core.resolve_stage1_processing(full_game_id, starting_region_list, player_color_list)
    return redirect(f'/{full_game_id}')

@app.route('/stage2_resolution', methods=['POST'])
def stage2_resolution():
    #process form data
    full_game_id = request.form.get('full_game_id')
    player_nation_name_list = []
    player_government_list = []
    player_foreign_policy_list = []
    player_victory_condition_set_list = []
    for i in range(1, 11):
        player_nation_name = request.form.get(f'nameinput_p{i}')
        if player_nation_name:
            player_nation_name_list.append(player_nation_name)
        player_government = request.form.get(f'govinput_p{i}')
        if player_government:
            player_government_list.append(player_government)
        player_foreign_policy = request.form.get(f'fpinput_p{i}')
        if player_foreign_policy:
            player_foreign_policy_list.append(player_foreign_policy)
        player_vc_set = request.form.get(f'vcinput_p{i}')
        if player_vc_set:
            player_victory_condition_set_list.append(player_vc_set)
    core.resolve_stage2_processing(full_game_id, player_nation_name_list, player_government_list, player_foreign_policy_list, player_victory_condition_set_list)
    return redirect(f'/{full_game_id}')

@app.route('/turn_resolution', methods=['POST'])
def turn_resolution():
    #process form data
    full_game_id = request.form.get('full_game_id')
    public_actions_list = []
    private_actions_list = []
    for i in range(1, 11):
        public_str = request.form.get('public_textarea_p' + str(i))
        if public_str:
            #if this player submitted public actions, convert actions into a list
            player_public_list = public_str.split('\r\n')
            public_actions_list.append(player_public_list)
        else:
            public_actions_list.append([])
        private_str = request.form.get('private_textarea_p' + str(i))
        if private_str:
            #if this player submitted private actions, convert actions into a list
            player_private_list = private_str.split('\r\n')
            private_actions_list.append(player_private_list)
        else:
            private_actions_list.append([])
    core.resolve_turn_processing(full_game_id, public_actions_list, private_actions_list)
    return redirect(f'/{full_game_id}')

@app.route('/event_resolution', methods=['POST'])
def event_resolution():
    '''
    Handles current event and runs end of turn checks & updates when activated.
    
    Redirects back to selected game.
    '''
    
    full_game_id = request.form.get('full_game_id')
    game_id = int(full_game_id[-1])
    playerdata_filepath = f'gamedata/{full_game_id}/playerdata.csv'
    playerdata_list = core.read_file(playerdata_filepath, 1)
    with open(f'active_games.json', 'r') as json_file:  
        active_games_dict = json.load(json_file)
    
    diplomacy_log = []
    current_turn_num = core.get_current_turn_num(game_id)
    player_count = len(playerdata_list)
    
    diplomacy_log = events.handle_current_event(active_games_dict, full_game_id, diplomacy_log)
    diplomacy_log = core.run_end_of_turn_checks(full_game_id, current_turn_num, player_count, diplomacy_log)
    core.update_announcements_sheet(full_game_id, False, diplomacy_log, [])

    return redirect(f'/{full_game_id}')

#map_tests.run()

if __name__ == '__main__':
    app.run()

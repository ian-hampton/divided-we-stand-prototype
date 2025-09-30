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
from operator import itemgetter
from collections import defaultdict

from app import site_functions
from app import core
from app import events
from app import palette
from app.scenario import ScenarioData as SD
from app.gamedata import Games, GameStatus

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

    def generate_refined_player_list_active():
        """
        Creates list of nations that is shown alongside each game.
        """

        with open('playerdata/player_records.json', 'r') as json_file:
            player_records_dict = json.load(json_file)

        data_a = []
        data_b = []
    
        for nation in Nations:
            gov_fp_str = f"{nation.fp} - {nation.gov}"
            username_str = f"""<a href="profile/{nation.player_id}">{player_records_dict[nation.player_id]["Username"]}</a>"""
            player_color = site_functions.check_color_correction(nation.color)
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
    
    from app.nation import Nations
    with open("playerdata/player_records.json", 'r') as json_file:
        player_records_dict = json.load(json_file)

    active_games = {}

    for game in Games:

        Nations.load(game.id)
        active_games[game.id] = {
            "title": None,
            "status": None,
            "image_url": None,
            "playerdata": None,
            "information": {
                "Scenario": game.info.scenario,
                "Map": game.info.map,
                "Players": game.info.player_count,
                "Turn Length": game.info.turn_length,
                "Victory Conditions": game.info.victory_conditions,
                "Accelerated Schedule": game.info.accelerated_schedule,
                "Weekend Deadlines": game.info.weekend_deadlines,
                "Fog of War": game.info.fog_of_war
            },
            "statistics": {
                "Date Started": game.stats.date_started,
                "Days Ellapsed": game.stats.days_elapsed,
                "Region Disputes": game.stats.region_disputes,
            }
        }
        
        match game.status:

            case GameStatus.REGION_SELECTION:
                active_games[game.id]["title"] = f"""<a href="/{game.id}">{game.name}</a>"""
                active_games[game.id]["status"] = "Starting Region Selection in Progress"
                refined_player_data = []
                for nation in Nations:
                    username = player_records_dict[nation.player_id]["Username"]
                    username_str = f"""<a href="profile/{nation.player_id}">{username}</a>"""
                    refined_player_data.append([nation.name, 0, 'TBD', username_str, '#ffffff', '#ffffff'])
                active_games[game.id]["playerdata"] = refined_player_data
                active_games[game.id]["image_url"] = url_for('main.get_mainmap', full_game_id=game.id)

            case GameStatus.NATION_SETUP:
                active_games[game.id]["title"] = f"""<a href="/{game.id}">{game.name}</a>"""
                active_games[game.id]["status"] = "Nation Setup in Progress"
                refined_player_data = []
                for nation in Nations:
                    username = player_records_dict[nation.player_id]["Username"]
                    username_str = f"""<a href="profile/{nation.player_id}">{username}</a>"""
                    player_color_2 = site_functions.check_color_correction(nation.color)
                    refined_player_data.append([nation.name, 0, 'TBD', username_str, nation.color, player_color_2])
                active_games[game.id]["playerdata"] = refined_player_data
                active_games[game.id]["image_url"] = url_for('main.get_mainmap', full_game_id=game.id)

            case _:
                active_games[game.id]["title"] = f"""<a href="/{game.id}">{game.name}</a>"""
                if not GameStatus.FINISHED:
                    active_games[game.id]["status"] = "Game Over!"
                else:
                    active_games[game.id]["status"] = f"Turn {game.turn}"
                active_games[game.id]["playerdata"] = generate_refined_player_list_active()
                active_games[game.id]["image_url"] = url_for('main.get_mainmap', full_game_id=game.id)
    
    return render_template('temp_games.html', dict = active_games)

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

    def create_new_game() -> None:

        from app.nation import Nations

        game_id = ''.join(random.choices(string.ascii_letters, k=20))

        Games.create(game_id, form_data_dict)
        game = Games.load(game_id)
        SD.load(game_id)
        map_str = game.get_map_string()
        with open(f"maps/{map_str}/graph.json", 'r') as json_file:
            graph_dict = json.load(json_file)

        # create directories
        os.makedirs(f"gamedata/{game_id}/images")
        os.makedirs(f"gamedata/{game_id}/logs")

        # copy starting map images
        files_destination = f"gamedata/{game_id}"
        shutil.copy(f"app/static/images/map_images/{map_str}/blank.png", f"{files_destination}/images")
        shutil.move(f"{files_destination}/images/blank.png", f"gamedata/{game_id}/images/resourcemap.png")
        shutil.copy(f"app/static/images/map_images/{map_str}/{map_str}.png", f"{files_destination}/images")
        shutil.move(f"{files_destination}/images/{map_str}.png", f"gamedata/{game_id}/images/controlmap.png")
        
        # create regdata.json
        regdata_dict = {}
        for region_id in graph_dict:
            regdata_dict[region_id] = {
                "regionData": {
                    "ownerID": "0",
                    "occupierID": "0",
                    "purchaseCost": 5,
                    "regionResource": "Empty",
                    "nukeTurns": 0,
                },
                "improvementData": {
                    "name": None,
                    "health": 99,
                    "turnTimer": 99
                },
                "unitData": {
                    "name": None,
                    "health": 99,
                    "ownerID": "0"
                }
            }
            if form_data_dict["Scenario"] == "Standard":
                regdata_dict[region_id]["regionData"]["infection"] = 0
                regdata_dict[region_id]["regionData"]["quarantine"] = False
        with open(f"gamedata/{game_id}/regdata.json", 'w') as json_file:
            json.dump(regdata_dict, json_file, indent=4)

        # create gamedata.json
        gamedata_filepath = f"gamedata/{game_id}/gamedata.json"
        gamedata_dict = {
            "alliances": {},
            "nations": {},
            "notifications": [],
            "truces": {},
            "wars": {}
        }
        with open(gamedata_filepath, 'w') as json_file:
            json.dump(gamedata_dict, json_file, indent=4)

        # create nationdata
        Nations.load(game_id)
        for i, user_id in enumerate(profile_ids_list):
            Nations.create(str(i + 1), user_id)
        Nations.save()

        # create rmdata file
        rmdata_filepath = f'{files_destination}/rmdata.csv'
        with open(rmdata_filepath, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(["Turn", "Nation", "Bought/Sold", "Count", "Resource Exchanged"])

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
        active_game_ids = []
        for game in Games:
            active_game_ids.append(game.id)
        for game_id in active_game_ids:
            Games.delete(game_id)
        Games.save()
        return redirect(f'/games')

    # create game files
    create_new_game()
    Games.save()
    
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
    
    from app.nation import Nations

    game = Games.load(full_game_id)
    Nations.load(full_game_id)

    full_title = f"Divided We Stand - {game.name}" 
    main_url = url_for('main.get_mainmap', full_game_id=full_game_id)
    resource_url = url_for('main.get_resourcemap', full_game_id=full_game_id)
    control_url = url_for('main.get_controlmap', full_game_id=full_game_id)

    match game.status:

        case GameStatus.REGION_SELECTION:
            
            player_data = []
            for nation in Nations:
                p_id = f'p{nation.id}'
                regioninput_id = f'regioninput_{p_id}'
                colordropdown_id = f'colordropdown_{p_id}'
                vc1a, vc2a, vc3a, vc1b, vc2b, vc3b = nation.get_vc_list()
                refined_player_data = [f"Player #{nation.id}", p_id, nation.color, vc1a, vc2a, vc3a, vc1b, vc2b, vc3b, regioninput_id, colordropdown_id]
                player_data.append(refined_player_data)
            active_player_data = player_data.pop(0)

            return render_template('temp_stage1.html', active_player_data = active_player_data, player_data = player_data, game_title = game.name, full_title = full_title, main_url = main_url, resource_url = resource_url, control_url = control_url, full_game_id = full_game_id)

        case GameStatus.NATION_SETUP:
            
            player_data = []
            for nation in Nations:
                p_id = f"p{nation.id}"
                nameinput_id = f"nameinput_{p_id}"
                govinput_id = f"govinput_{p_id}"
                fpinput_id = f"fpinput_{p_id}"
                vcinput_id = f"vcinput_{p_id}"
                vc1a, vc2a, vc3a, vc1b, vc2b, vc3b = nation.get_vc_list()
                refined_player_data = [f"Player #{nation.id}", p_id, nation.color, vc1a, vc2a, vc3a, vc1b, vc2b, vc3b, nameinput_id, govinput_id, fpinput_id, vcinput_id]
                player_data.append(refined_player_data)
            active_player_data = player_data.pop(0)
            
            return render_template('temp_stage2.html', active_player_data = active_player_data, player_data = player_data, game_title = game.name, full_title = full_title, main_url = main_url, resource_url = resource_url, control_url = control_url, full_game_id = full_game_id)

        case GameStatus.FINISHED:
            # TODO - fix stage 4 rendering, currently broken
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
        
        case _:

            player_data = []
            for nation in Nations:
                p_id = f'p{nation.id}'
                public_actions_textarea_id = f"public_textarea_{p_id}"
                private_actions_textarea_id = f"private_textarea_{p_id}"
                nation_sheet_url = f'{full_game_id}/player{nation.id}'
                refined_player_data = [f"Player #{nation.id}", p_id, nation.color, nation.name, public_actions_textarea_id, private_actions_textarea_id, nation_sheet_url]
                player_data.append(refined_player_data)
            active_player_data = player_data.pop(0)
            
            return render_template('temp_stage3.html', active_player_data = active_player_data, player_data = player_data, game_title = game.name, full_title = full_title, main_url = main_url, resource_url = resource_url, control_url = control_url, full_game_id = full_game_id)

# GENERATE NATION SHEET PAGES
@main.route('/<full_game_id>/player<int:player_id>')
def player_route(full_game_id, player_id):
    page_title = f"Player #{player_id} Nation Sheet"
    player_information_dict = site_functions.get_data_for_nation_sheet(full_game_id, str(player_id))
    return render_template("temp_nation_sheet.html", page_title = page_title, player_information_dict = player_information_dict)

# WARS PAGE
@main.route('/<full_game_id>/wars')
def wars(full_game_id):
    
    from app.nation import Nations
    from app.alliance import Alliances
    from app.war import Wars

    game = Games.load(full_game_id)
    
    Nations.load(full_game_id)
    Alliances.load(full_game_id)
    Wars.load(full_game_id)
    
    page_title = f"{game.name} Wars List"
    
    # read wars
    results = {}
    for war in Wars:

        inner_dict = {}
        
        # get war timeframe
        season, year = game.get_season_and_year(war.start)
        start_str = f"{season} {year}"
        if war.end != 0:
            season, year = game.get_season_and_year(war.end)
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
                if game.turn - war.start < 4:
                    can_end_str = f"A peace deal may be negotiated by the main combatants in {(war.start + 4) - game.turn} turns."
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

    from app.nation import Nations

    SD.load(full_game_id)
    game = Games.load(full_game_id)

    Nations.load(full_game_id)

    page_title = f"{game.name} - Technology Trees"
    data = {}

    # create technology dictionary
    if SD.scenario == "standard":
        categories = ["Energy", "Infrastructure", "Military", "Defense"]
        for category in categories:
            data[f"{category} Technologies"] = {}
        data["Energy Technologies"]["Colors"] = ["#5555554D", "#CC58264D", "#106A254D", "NONE"]
        data["Infrastructure Technologies"]["Colors"] = ["#F9CB304D", "#754C244D", "#5555554D", "#0583C54D"]
        data["Military Technologies"]["Colors"] = ["#C419194D", "#5F2F8C4D", "#106A254D", "#CC58264D"]
        data["Defense Technologies"]["Colors"] = ["#0583C54D", "#F9CB304D", "#C419194D", "NONE"]
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
    
    # create technology table
    for category in categories:
        table_contents = {
            "A": [None] * 4,
            "B": [None] * 4,
            "C": [None] * 4,
            "D": [None] * 4,
        }
        data[f"{category} Technologies"]["Table"] = table_contents

    # fetch technology data
    temp_technology_data = {}
    for research_name, research_data in SD.technologies:

        # TODO - make an attribute for technologies to handle this
        if not game.info.fog_of_war and research_name in ["Surveillance Operations", "Economic Reports", "Military Intelligence"]:
            continue

        temp_technology_data[research_name] = {
            "Name": research_name,
            "Research Type": research_data.type,
            "Cost": research_data.cost,
            "Description": research_data.description,
            "Location": research_data.location,
            "Player Research": [None] * len(Nations)
        }
    
    # fetch player research data
    for index, nation in enumerate(Nations):
        for research_name in nation.completed_research:
            if research_name in SD.technologies:
                data[research_name]["Player Research"][index] = (nation.color[1:], nation.name)

    # load techs to table
    for key, value in temp_technology_data.items():
        research_type = value["Research Type"]
        if research_type in categories:
            pos = value["Location"]
            row_pos = pos[0]
            col_pos = int(pos[1])
            value["Name"] = key
            data[research_type + " Technologies"]["Table"][row_pos][col_pos] = value
    
    return render_template('temp_research.html', page_title = page_title, dict = data, complement = color_complements_dict)

# AGENDAS PAGE
@main.route('/<full_game_id>/agendas')
def agendas(full_game_id):
    
    from app.nation import Nations

    SD.load(full_game_id)
    game = Games.load(full_game_id)
    
    Nations.load(full_game_id)

    page_title = f"{game.name} - Political Agendas"
    data = {}

    # create dictionary
    if SD.scenario == "standard":
        categories = ["Agendas"]
        for category in categories:
            data[category] = {}
        data["Agendas"]["Colors"] = ["#0583C54D", "#106A254D", "#5F2F8C4D", "#C419194D"]
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
    
    # create table
    for category in categories:
        table_contents = {
            "A": [None] * 4,
            "B": [None] * 4,
            "C": [None] * 4,
            "D": [None] * 4,
        }
        data[category]["Table"] = table_contents

    # fetch agenda data
    temp_agenda_data = {}
    for agenda_name, agenda_data in SD.agendas:
        
        temp_agenda_data[agenda_name] = {
            "Name": agenda_name,
            "Agenda Type": agenda_data.type,
            "Cost": agenda_data.cost,
            "Description": agenda_data.description,
            "Location": agenda_data.location,
            "Player Research": [None] * len(Nations)
        }
    
    # fetch player research data
    for index, nation in enumerate(Nations):
        for research_name in nation.completed_research:
            if research_name in SD.agendas:
                data[research_name]["Player Research"][index] = (nation.color[1:], nation.name)

    # load techs to table
    for key, value in temp_agenda_data.items():
        pos = value["Location"]
        row_pos = pos[0]
        col_pos = int(pos[1])
        value["Name"] = key
        data["Agendas"]["Table"][row_pos][col_pos] = value
    
    return render_template('temp_agenda.html', page_title = page_title, dict = data, complement = color_complements_dict)

# UNITS REF PAGE
@main.route('/<full_game_id>/units')
def units_ref(full_game_id):

    SD.load(full_game_id)
    game = Games.load(full_game_id)

    page_title = f"{game.name} - Unit Reference"

    data = {}
    for unit_name, unit_data in SD.units:
        data[unit_name] = {
            "Required Research": unit_data.required_research,
            "Unit Type": unit_data.type,
            "Abbreviation": unit_data.abbreviation,
            "Reference Color": unit_data.color,
            "Health": unit_data.health,
            "Victory Damage": unit_data.victory_damage,
            "Draw Damage": unit_data.draw_damage,
            "Combat Value": unit_data.hit_value,
            "Movement": unit_data.movement,
            "Standard Missile Defense": unit_data.missile_defense,
            "Nuclear Missile Defense": unit_data.nuclear_defense,
            "Abilities": unit_data.abilities,
            "Upkeep": unit_data.upkeep,
            "Build Costs": unit_data.cost
        }

    return render_template('temp_units.html', page_title = page_title, dict = data)

# IMPROVEMENTS REF PAGE
@main.route('/<full_game_id>/improvements')
def improvements_ref(full_game_id):

    # Improvement Colors:
    # red - military
    # yellow - energy
    # blue - civilian
    # grey - everything else (default)

    SD.load(full_game_id)
    game = Games.load(full_game_id)

    page_title = f"{game.name} - Improvement Reference"

    data = {}
    for improvement_name, improvement_data in SD.improvements:

        # hide event specific improvements
        if improvement_name == "Colony" and "Faustian Bargain" not in game.active_events:
            continue

        # hide fog of war improvements
        if not game.info.fog_of_war and improvement_data.is_fog_of_war:
            continue

        data[improvement_name] = {
            "Required Research": improvement_data.required_research,
            "Required Resource": improvement_data.required_resource,
            "Reference Color": improvement_data.color,
            "Income": improvement_data.income,
            "Health": improvement_data.health,
            "Victory Damage": improvement_data.victory_damage,
            "Draw Damage": improvement_data.draw_damage,
            "Combat Value": improvement_data.hit_value,
            "Standard Missile Defense": improvement_data.missile_defense,
            "Nuclear Missile Defense": improvement_data.nuclear_defense,
            "Abilities": improvement_data.abilities,
            "Upkeep": improvement_data.upkeep,
            "Build Costs": improvement_data.cost
        }

    data = {key: data[key] for key in sorted(data)}
    
    return render_template('temp_improvements.html', page_title = page_title, dict = data)

# RESOURCE MARKET PAGE
@main.route('/<full_game_id>/resource_market')
def resource_market(full_game_id):

    SD.load(full_game_id)
    game = Games.load(full_game_id)

    page_title = f"{game.name} - Resource Market"

    # generate market data
    data = {}
    for resource_name, market_data in SD.market:
        data[resource_name] = {
        "Base Price": market_data.base_price,
        "Current Price": 0,
        "Bought": 0,
        "Sold": 0
    }
    
    # get resource market records
    rmdata_recent_transaction_list = game.get_market_data()
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
    if "Market Inflation" in game.active_events:
        for resource_name in data:
            new_price = data[resource_name]["Current Price"] * 2
            data[resource_name]["Current Price"] = round(new_price, 2)
    elif "Market Recession" in game.active_events:
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

    def build_diplomacy_string() -> str:
        
        diplomacy_list = []

        if game.turn <= 4:
            diplomacy_list.append("First year expansion rules are in effect.")
        elif game.turn == 5:
            diplomacy_list.append("Normal expansion rules are now in effect.")

        if game.info.accelerated_schedule:
            if game.turn <= 10:
                diplomacy_list.append("Accelerated schedule is in effect until turn 11.")
            elif game.turn == 11:
                diplomacy_list.append("Normal turn schedule is now in effect.")

        for war in Wars:
            if war.outcome == "TBD":
                diplomacy_list.append(f"{war.name} is ongoing.")

        for truce in Truces:
            if truce.end_turn > game.turn:
                diplomacy_list.append(f"{str(truce)} truce until turn {truce.end_turn}.")
            elif truce.end_turn == game.turn:
                diplomacy_list.append(f"{str(truce)} truce has expired.")

        diplomacy_string = "<br>".join(diplomacy_list)
        diplomacy_string = palette.color_nation_names(diplomacy_string, full_game_id)
        return diplomacy_string

    def build_notifications_string() -> str:
        
        notifications_list = []
        q = PriorityQueue()
        for notification in Notifications:
            q.put(notification)
        while not q.empty():
            ntf = q.get()
            notifications_list.append(ntf[1])
        
        notifications_string = "<br>".join(notifications_list)
        notifications_string = palette.color_nation_names(notifications_string, full_game_id)
        return notifications_string

    def build_statistics_string() -> str:
        
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
        
        statistics_list.append(f"Region disputes: {game.stats.region_disputes}")
        
        statistics_string = "<br>".join(statistics_list)
        statistics_string = palette.color_nation_names(statistics_string, full_game_id)
        return statistics_string

    game = Games.load(full_game_id)
    Alliances.load(full_game_id)
    Nations.load(full_game_id)
    Notifications.initialize(full_game_id)
    Truces.load(full_game_id)
    Wars.load(full_game_id)

    # page title and date
    page_title = f"{game.name} - Announcements Page"
    season, year = game.get_season_and_year()
    date_str = f"{season} {year} - Turn {game.turn}"
    if game.status == GameStatus.ACTIVE_PENDING_EVENT:
        date_str += " Bonus Phase"

    # build announcements strings
    diplomacy_string = build_diplomacy_string()
    notifications_string = build_notifications_string()
    statistics_string = build_statistics_string()

    # get top three standings
    standings_dict = {}
    for record_name in Nations.LEADERBOARD_RECORD_NAMES:
        standings = Nations.get_top_three(record_name)
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
            if record_name == "net_income":
                standings_filtered.append([nation_name, f"{entry[1]:.2f}"])
            else:
                standings_filtered.append([nation_name, entry[1]])
        title = Nations.attribute_to_title(record_name)
        standings_dict[title] = standings_filtered
    
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

    return render_template('temp_announcements.html', game_name = game.name, page_title = page_title, date_output = date_str, scoreboard_dict = scoreboard_dict, standings_dict = standings_dict, statistics_string = statistics_string, diplomacy_string = diplomacy_string, notifications_string = notifications_string)

# ALLIANCE PAGE
@main.route('/<full_game_id>/alliances')
def alliances(full_game_id):

    from app.alliance import Alliances
    from app.nation import Nations

    SD.load(full_game_id)
    game = Games.load(full_game_id)

    Alliances.load(full_game_id)
    Nations.load(full_game_id)
    page_title = f"{game.name} - Alliance Page"

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

        sd_alliance = SD.alliances[alliance.type]
        alliance_data["color"] = palette.str_to_hex(sd_alliance.color_theme)
        alliance_data["abilities"] = sd_alliance.description

        alliance_dict_filtered[alliance.name] = alliance_data

    return render_template('temp_alliances.html', alliance_dict = alliance_dict_filtered, page_title = page_title)

# MAP IMAGES
@main.route('/<full_game_id>/mainmap.png')
def get_mainmap(full_game_id):
    game = Games.load(full_game_id)
    map_str = game.get_map_string()
    if game.status == GameStatus.REGION_SELECTION:
        filepath = f"..\\app\\static\\images\\map_images\\{map_str}\\blank.png"
    elif game.status == GameStatus.NATION_SETUP:
        filepath = f"..\\gamedata\\{full_game_id}\\images\\0.png"
    else:
        filepath = f"..\\gamedata\\{full_game_id}\\images\\{game.turn - 1}.png"
    return send_file(filepath, mimetype='image/png')
@main.route('/<full_game_id>/resourcemap.png')
def get_resourcemap(full_game_id):
    filepath = f'../gamedata/{full_game_id}/images/resourcemap.png'
    return send_file(filepath, mimetype='image/png')
@main.route('/<full_game_id>/controlmap.png')
def get_controlmap(full_game_id):
    filepath = f'../gamedata/{full_game_id}/images/controlmap.png'
    return send_file(filepath, mimetype='image/png')

# TURN RESOLUTION
@main.route('/<full_game_id>/resolve', methods=['POST'])
def turn_resolution_new(full_game_id):

    from app.alliance import Alliances
    from app.region import Regions
    from app.nation import Nations
    from app.notifications import Notifications
    from app.truce import Truces
    from app.war import Wars

    game = Games.load(full_game_id)
    SD.load(full_game_id)

    match game.status:

        case GameStatus.REGION_SELECTION:
            
            Nations.load(full_game_id)
            Regions.load(full_game_id)

            contents_dict = {}
            for nation in Nations:
                contents_dict[nation.id] = {}
                contents_dict[nation.id]["start"] = request.form.get(f"regioninput_p{nation.id}")
                contents_dict[nation.id]["color"] = request.form.get(f"colordropdown_p{nation.id}")
            
            site_functions.resolve_stage1_processing(full_game_id, contents_dict)
            Nations.save()
            Regions.save()
            
            game.status = GameStatus.NATION_SETUP
            
        case GameStatus.NATION_SETUP:
            
            Alliances.load(full_game_id)
            Nations.load(full_game_id)
            Regions.load(full_game_id)

            contents_dict = {}
            for nation in Nations:
                contents_dict[nation.id] = {}
                contents_dict[nation.id]["name_choice"] = request.form.get(f"nameinput_p{nation.id}")
                contents_dict[nation.id]["gov_choice"] = request.form.get(f"govinput_p{nation.id}")
                contents_dict[nation.id]["fp_choice"] = request.form.get(f"fpinput_p{nation.id}")
                contents_dict[nation.id]["vc_choice"] = request.form.get(f"vcinput_p{nation.id}")

            site_functions.resolve_stage2_processing(full_game_id, contents_dict)
            Nations.save()
            
            game.set_startdate()
            game.turn += 1
            game.status = GameStatus.ACTIVE

        case GameStatus.ACTIVE:
            
            Alliances.load(full_game_id)
            Regions.load(full_game_id)
            Nations.load(full_game_id)
            Notifications.initialize(full_game_id)
            Truces.load(full_game_id)
            Wars.load(full_game_id)

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
            Alliances.save()
            Regions.save()
            Nations.save()
            Notifications.save()
            Truces.save()
            Wars.save()

        case GameStatus.ACTIVE_PENDING_EVENT:
            
            Alliances.load(full_game_id)
            Regions.load(full_game_id)
            Nations.load(full_game_id)
            Notifications.initialize(full_game_id)
            Truces.load(full_game_id)
            Wars.load(full_game_id)

            events.resolve_current_event(full_game_id)
            site_functions.run_end_of_turn_checks(full_game_id, event_phase=True)
            Alliances.save()
            Regions.save()
            Nations.save()
            Notifications.save()
            Truces.save()
            Wars.save()
            
            game.turn += 1
            game.status = GameStatus.ACTIVE
    
    Games.save()

    return redirect(f"/{full_game_id}")
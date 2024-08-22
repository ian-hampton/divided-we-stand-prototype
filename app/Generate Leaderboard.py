#IMPORTOIDS
import csv
from operator import itemgetter
import json


def calculate_totals(game_records_dict):
    '''
    Reads game records and retrieves useful data for leaderboard.

    Parameters:
    - game_records_dict: Game records file stored as a dictionary.

    Returns:
    - player_totals_dict: The dictionary of player leaderboard data.
    '''
    player_totals_dict = {}
    for game, game_data in game_records_dict.items():
        if "Test Game" in game:
            continue
        player_data = game_data.get("Player Data", {})
        for player_id, player_info in player_data.items():
            score = player_info.get("Score", 0)
            victory = player_info.get("Victory", 0)
            if player_id in player_totals_dict:
                player_totals_dict[player_id]['Victory'] += victory
                player_totals_dict[player_id]['Score'] += score
                player_totals_dict[player_id]['Games'] += 1
            else:
                player_totals_dict[player_id] = {'Victory': victory, 'Score': score, 'Games': 1}
    return player_totals_dict

def update_leaderboard(player_totals_dict, player_records_dict):
    '''
    Updates leaderboard.csv

    Parameters:
    - player_totals_dict: The dictionary of player leaderboard data.
    - player_records_dict: The dictionary of player ids and usernames.
    '''
    leaderboard_list = []
    for player_id, player_info in player_totals_dict.items():
        score = player_info.get("Score")
        victory = player_info.get("Victory")
        games = player_info.get("Games")
        username = player_records_dict[player_id]["Username"]
        score_avg = round(score/games, 2)
        player_record_entry = [username, victory, score, score_avg, games]
        leaderboard_list.append(player_record_entry)
    filtered_leaderboard_list = sorted(leaderboard_list, key=itemgetter(1, 2, 3, 4), reverse=True)
    with open("../leaderboard.csv", "w", newline='') as file:
        writer = csv.writer(file)
        writer.writerows(filtered_leaderboard_list)

with open('../game_records.json', 'r') as json_file:
    game_records_dict = json.load(json_file)

with open('../player_records.json', 'r') as json_file:
    player_records_dict = json.load(json_file)

player_totals_dict = calculate_totals(game_records_dict)
update_leaderboard(player_totals_dict, player_records_dict)




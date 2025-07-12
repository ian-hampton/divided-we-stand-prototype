import csv
from operator import itemgetter
import json
from collections import defaultdict


def player_totals():
    return {"Victory": 0, "Score": 0, "Games": 0}

def calculate_totals(game_records_dict):

    player_totals_dict = defaultdict(player_totals)
    
    for game_data in game_records_dict.values():
        
        player_data = game_data.get("Player Data", {})
        for player_id, player_info in player_data.items():
            player_totals_dict[player_id]["Victory"] += player_info.get("Victory", 0)
            player_totals_dict[player_id]["Score"] += player_info.get("Score", 0)
            player_totals_dict[player_id]["Games"] += 1
    
    return player_totals_dict

def update_leaderboard(player_totals_dict, player_records_dict):

    leaderboard_list = []
    for player_id, player_info in player_totals_dict.items():
        
        victory = player_info["Victory"]
        score = player_info["Score"]
        games = player_info["Games"]
        username = player_records_dict[player_id]["Username"]

        score_avg = round(score/games, 2)
        player_record_entry = [username, victory, score, score_avg, games]
        leaderboard_list.append(player_record_entry)
    
    filtered_leaderboard_list = sorted(leaderboard_list, key=itemgetter(1, 2, 3, 4), reverse=True)
    
    with open("leaderboard.csv", "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerows(filtered_leaderboard_list)

def main():
    
    with open("../game_records.json", "r") as json_file:
        game_records_dict = json.load(json_file)

    with open("player_records.json", "r") as json_file:
        player_records_dict = json.load(json_file)

    player_totals_dict = calculate_totals(game_records_dict)
    update_leaderboard(player_totals_dict, player_records_dict)

main()




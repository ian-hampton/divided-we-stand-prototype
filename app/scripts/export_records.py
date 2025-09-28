import csv
import json
import os
import sys

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
sys.path.append(parent_dir)
os.chdir(parent_dir)

from app.nation import Nations

GAME_ID = "game1"
Nations.load(GAME_ID)

def create_record_table(attribute_name):

    with open('active_games.json', 'r') as json_file:
        active_games_dict = json.load(json_file)

    data = []

    header = ["-"]
    end_turn = int(active_games_dict[GAME_ID]["turn"])
    for i in range(end_turn + 1):
        header.append(i)
    data.append(header)

    for nation in Nations:
        record_data: list = getattr(nation.records, attribute_name)
        record_data = [nation.name] + record_data
        data.append(record_data)

    os.makedirs(f"export", exist_ok=True)
    with open(f"export/{attribute_name}.csv", "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerows(data)

def main():
    for attribute_name in Nations.LEADERBOARD_RECORD_NAMES:
        create_record_table(attribute_name)

main()
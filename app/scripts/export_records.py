import csv
import json
import os
import sys

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
sys.path.append(parent_dir)
os.chdir(parent_dir)

from app.game.games import Games
from app.nation.nations import Nations, LeaderboardRecordNames

GAME_ID = "game1"

def create_record_table(record: LeaderboardRecordNames):

    game = Games.load(GAME_ID)
    Nations.load(GAME_ID)

    data = []

    header = ["-"]
    for i in range(game.turn + 1):
        header.append(i)
    data.append(header)

    for nation in Nations:
        record_data: list = getattr(nation.records, record.value)
        record_data = [nation.name] + record_data
        data.append(record_data)

    os.makedirs(f"export", exist_ok=True)
    with open(f"export/{record.value}.csv", "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerows(data)

def main():
    for record in LeaderboardRecordNames:
        create_record_table(record)

main()
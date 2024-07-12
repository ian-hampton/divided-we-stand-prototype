import ast
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import core

def detect_bad_region_ids(regdata_list):
    region_ids_list = []
    bad_count = 0
    for region in regdata_list:
        region_ids_list.append(region[0])
    for region in regdata_list:
        adjacency_list = ast.literal_eval(region[8])
        for select_region in adjacency_list:
            if select_region not in region_ids_list:
                print(f"BAD REGION FOUND: {select_region} in adjacency list for {region[0]}.")
                bad_count += 1
    print(f"""Scan completed! {bad_count} bad region ids found.""")

map_name = input("Enter map name: ")
regdata_filepath = f'../maps/{map_name}/regdata.csv'
regdata_list = core.read_file(regdata_filepath, 2)
detect_bad_region_ids(regdata_list)
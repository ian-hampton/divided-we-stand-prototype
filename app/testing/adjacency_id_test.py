import ast
import json
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# This script tests the map graph, looking for any invalid ids in the adjacency list/map.
# Last updated 1/29/2025

MAP_STR = "china"
REGDATA_FILEPATH = f"../../maps/{MAP_STR}/regdata.json"

def detect_bad_region_ids():

    with open(REGDATA_FILEPATH, 'r') as json_file:
        regdata_dict = json.load(json_file)

    bad_count = 0
    for region_id in regdata_dict:
        adjacency_list = regdata_dict[region_id]["regionData"]["adjacencyList"]
        for adj_region_id in adjacency_list:
            if adj_region_id not in regdata_dict or adj_region_id == region_id:
                print(f"BAD REGION FOUND: {adj_region_id} in adjacency list for {region_id}.")
                bad_count += 1
    
    print(f"""Scan completed! {bad_count} bad region ids found.""")

detect_bad_region_ids()
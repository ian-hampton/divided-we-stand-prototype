"""
File: base.py
Author: Ian Hampton
Created Date: 29th January 2025

This script tests the map graph, looking for any invalid ids.
"""

import json
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

MAP_STR = "china"
GRAPH_FILEPATH = f"../../maps/{MAP_STR}/graph.json"

def detect_bad_region_ids():

    with open(GRAPH_FILEPATH, 'r') as json_file:
        graph = json.load(json_file)

    bad_count = 0
    for region_id in graph:
        adjacency_map= graph[region_id]["adjacencyMap"]
        for adj_region_id in adjacency_map:
            if adj_region_id not in graph or adj_region_id == region_id:
                print(f"BAD REGION FOUND: {adj_region_id} in adjacency list for {region_id}.")
                bad_count += 1
    
    print(f"""Scan completed! {bad_count} bad region ids found.""")

detect_bad_region_ids()
import json

# This script generates a graph file for a map using the graph.json file outputted from the image-to-graph step.
# Last updated 6/1/2025

# STEPS TO USE
# 1. Generate graph.json using the image-to-graph-dws script.
# 2. Copy graph.json to the map directory in this repo.
# 3. Run this script. Note that it will overwrite graph.json.
# 4. Manually fill the following region data:
#   - fullName
#   - isEdgeOfMap
#   - hasRegionalCapital
#   - isMagnified
#   - randomStartAllowed
#   - additionalRegionCords
#   - improvementCords and unitCords for magnified regions
#   - sea routes

MAP_STR = "united_states"
GRAPH_FILEPATH = f"../../maps/{MAP_STR}/graph.json"

# open files
with open(GRAPH_FILEPATH, 'r') as json_file:
    graph_dict = json.load(json_file)

print(len(graph_dict))

# create new graph.json
new_graph = {}
for region_id in graph_dict:
    new_graph[region_id] = {
        "fullName": None,
        "isEdgeOfMap": False,
        "hasRegionalCapital": None,
        "isMagnified": None,
        "randomStartAllowed": True,
        "additionalRegionCords": [],
        "improvementCords": graph_dict[region_id]["improvementCords"],
        "unitCords": graph_dict[region_id]["unitCords"],
        "adjacencyMap": graph_dict[region_id]["adjacencyMap"]
    }

with open(GRAPH_FILEPATH, 'w') as json_file:
    json.dump(new_graph, json_file, indent=4)
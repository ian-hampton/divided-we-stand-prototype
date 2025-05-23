# from regdata:
# "fullName"
# "edgeOfMap"
# "containsRegionalCapital"
# "randomStartAllowed"

# new
# "magnified"
# "additionalRegionCoords"

# from graph:
# "improvementCoords"
# "unitCoords"
# "adjacencyMap"

import json

MAP_STR = "china"
REGDATA_FILEPATH = f"../../maps/{MAP_STR}/regdata.json"
GRAPH_FILEPATH = f"../../maps/{MAP_STR}/graph.json"

# open files
with open(REGDATA_FILEPATH, 'r') as json_file:
    regdata_dict = json.load(json_file)
with open(GRAPH_FILEPATH, 'r') as json_file:
    graph_dict = json.load(json_file)

# create new graph.json
new_graph = {}
for region_id in graph_dict:
    new_graph[region_id] = {
        "fullName": regdata_dict[region_id]["regionData"]["fullName"],
        "isEdgeOfMap": regdata_dict[region_id]["regionData"]["edgeOfMap"],
        "hasRegionalCapital": regdata_dict[region_id]["regionData"]["containsRegionalCapital"],
        "isMagnified": None,
        "randomStartAllowed": regdata_dict[region_id]["regionData"]["randomStartAllowed"],
        "additionalRegionCords": [],
        "improvementCords": graph_dict[region_id]["improvementCords"],
        "unitCords": graph_dict[region_id]["unitCords"],
        "adjacencyMap": graph_dict[region_id]["adjacencyMap"]
    }

with open(GRAPH_FILEPATH, 'w') as json_file:
    json.dump(new_graph, json_file, indent=4)
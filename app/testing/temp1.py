import json

MAP_STR = "china"
REGDATA_FILEPATH = f"../../maps/{MAP_STR}/regdata.json"
GRAPH_FILEPATH = f"../../maps/{MAP_STR}/graph.json"

with open(REGDATA_FILEPATH, 'r') as json_file:
    regdata_dict = json.load(json_file)

with open(GRAPH_FILEPATH, 'r') as json_file:
    graph_dict = json.load(json_file)

set1 = set(regdata_dict.keys())
set2 = set(graph_dict.keys())
print(set1.difference(set2))
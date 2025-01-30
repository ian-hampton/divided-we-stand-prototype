import json
from copy import deepcopy

# This script generates regdata given a dictionary of region ids.

regdata_filepath = f"../../maps/china/regdata.json"

def create_regdata():
    """
    Note: Once regdata is generated, the following parameters must be manually filled in:
    - "edgeOfMap"
    - "containsRegionalCapital"
    - "adjacencyList"
    - "randomStartAllowed"
    - improvementData -> "coordinates"
    - unitData -> "coordinates" (if non-standard unit placement)
    - regdataData -> "coordinates" (if region is split in two)
    """

    regdata_dict = {}

    for region_id, full_name in region_ids.items():
        regdata_dict[region_id.upper()] = deepcopy(template)
        regdata_dict[region_id.upper()]["regionData"]["fullName"] = full_name

    with open(regdata_filepath, 'w') as json_file:
        json.dump(regdata_dict, json_file, indent=4)
    
    f"Done. Region count: {len(region_ids)}"

region_ids = {
    "HONGK": "Hong Kong"
}

template = {
    "regionData": {
        "fullName": "???",
        "ownerID": 0,
        "occupierID": 0,
        "purchaseCost": 5,
        "regionResource": "Empty",
        "nukeTurns": 0,
        "edgeOfMap": False,
        "containsRegionalCapital": False,
        "adjacencyList": [],
        "randomStartAllowed": True
    },
    "improvementData": {
        "name": None,
        "health": 99,
        "turnTimer": 99,
        "coordinates": []
    },
    "unitData": {
        "name": None,
        "health": 99,
        "ownerID": 99,
    }
}

create_regdata()
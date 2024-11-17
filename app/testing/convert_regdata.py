import json
import csv
import copy
import ast

def convert_regdata():
    '''
    Converts old regdata.csv to regdata.json
    '''

    regdata_dict = {}
    old_filepath = '../../maps/united_states/regdata.csv'
    new_filepath = f'../../maps/united_states/regdata.json'

    regdata_list = []
    with open(old_filepath, 'r') as file:
        reader = csv.reader(file)
        for i in range(0, 2):
            next(reader, None)
        for row in reader:
            if row != []:
                regdata_list.append(row)

    for region in regdata_list:
        
        new_entry = copy.deepcopy(template)

        region_data = new_entry["regionData"]
        region_data["fullName"] = region[1]
        region_data["edgeOfMap"] = region[9]
        region_data["containsRegionalCapital"] = region[10]
        region_data["adjacencyList"] = ast.literal_eval(region[8])
        
        region_id = region[0]
        regdata_dict[region_id] = new_entry
    
    with open(new_filepath, 'w') as json_file:
        json.dump(regdata_dict, json_file, indent=4)
    
    print("Done!")

template = {
    "regionData": {
        "fullName": "",
        "ownerID": 0,
        "occupierID": 0,
        "purchaseCost": 5,
        "regionResource": "Empty",
        "nukeTurns": 0,
        "edgeOfMap": False,
        "containsRegionalCapital": False,
        "adjacencyList": []
    },
    "improvementData": {
        "name": None,
        "health": 99
    },
    "unitData": {
        "name": None,
        "health": 99,
        "ownerID": 99
    }
}

convert_regdata()
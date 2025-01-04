import json

with open(f'maps/united_states/regdata.json', 'r') as json_file:
    regdata_dict: dict = json.load(json_file)

for region_id in regdata_dict:
    if region_id in ["LOSAN", "FIRCT", "TAMPA", "GACST", "HAMPT", "EASMD", "DELAW", "RHODE", "NTHMA", "STHMA"]:
        regdata_dict[region_id]["regionData"]["magnified"] = True
    else:
        regdata_dict[region_id]["regionData"]["magnified"] = False

with open(f'maps/united_states/regdata.json', 'w') as json_file:
    json.dump(regdata_dict, json_file, indent=4)
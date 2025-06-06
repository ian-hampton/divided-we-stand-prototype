import ast
import csv
import json
import random
import copy
from typing import Union, Tuple, List

from app.region import Region
from app.improvement import Improvement
from app.unit import Unit
from app.alliance import AllianceTable
from app.nationdata import Nation
from app.nationdata import NationTable


# GAMEDATA HELPER FUNCTIONS
################################################################################

def get_current_turn_num(game_id: str) -> str | int:
    """
    Gets current turn number given game id.
    """
    
    with open('active_games.json', 'r') as json_file:
        active_games_dict = json.load(json_file)

    try:
        current_turn_num = int(active_games_dict[game_id]["Statistics"]["Current Turn"])
    except:
        current_turn_num = active_games_dict[game_id]["Statistics"]["Current Turn"]

    return current_turn_num

def update_turn_num(game_id: str) -> None:
    """
    Updates the turn number given game id.
    """

    with open('active_games.json', 'r') as json_file:
        active_games_dict = json.load(json_file)

    current_turn_num = int(active_games_dict[game_id]["Statistics"]["Current Turn"])
    current_turn_num += 1
    active_games_dict[game_id]["Statistics"]["Current Turn"] = str(current_turn_num)

    with open('active_games.json', 'w') as json_file:
        json.dump(active_games_dict, json_file, indent=4)

def get_map_str(game_id: str) -> str:
    """
    Takes a map name and returns its filepath
    """

    with open('active_games.json', 'r') as json_file:
        active_games_dict = json.load(json_file)

    map_name: str = active_games_dict[game_id]["Information"]["Map"]

    map_name_actual = ""
    for index, char in enumerate(map_name):
        if char.isalpha():
            map_name_actual += char.lower()
        elif char == " ":
            map_name_actual += "_"

    return map_name_actual.strip("_")

# DIPLOMACY SUB-FUNCTIONS
################################################################################

def get_alliance_count(game_id: str, nation: Nation) -> Tuple[int, int]:
    """
    Gets a count of a player's active alliances and their total alliance capacity.

    Params:
        game_id (str): Game ID string.
        nation (Nation): Nation object.

    Returns:
        Tuple:
            int: Alliance count.
            int: Alliance limit.
    """
    
    # get alliance data
    alliance_count = 0
    alliance_table = AllianceTable(game_id)
    alliance_report_dict = alliance_table.report(nation.name)

    # get alliance count
    alliance_count = alliance_report_dict["Total"] - alliance_report_dict["Non-Aggression Pact"]
    
    # get alliance limit
    alliance_limit = 2
    if 'Power Broker' in nation.completed_research:
        alliance_limit += 1
    if 'Improved Logistics' in nation.completed_research:
        alliance_limit += 1
    for tag_data in nation.tags.values():
        alliance_limit += tag_data.get("Alliance Limit Modifier", 0)

    return alliance_count, alliance_limit

def get_subjects(game_id: str, overlord_name: str, subject_type: str) -> list:

    nation_id_list = []
    nation_table = NationTable(game_id)

    for nation in nation_table:
        if overlord_name in nation.status and subject_type in nation.status:
            nation_id_list.append(nation.id)
    
    return nation_id_list


# ECONOMIC SUB-FUNCTIONS
################################################################################

def create_player_yield_dict(game_id: str, nation: Nation) -> dict:
    """
    Given a player, this function creates the initial dictionary with the yields of all improvements.

    Params:
        game_id (str): Game ID string.
        nation (Nation): Object representing the nation this yield_dict is for.

    Returns:
        dict: Yield dictionary detailing income and multiplier for every improvement.
    """
    
    # load game info
    improvement_data_dict = get_scenario_dict(game_id, "Improvements")
    technology_data_dict = get_scenario_dict(game_id, "Technologies")
    agenda_data_dict = get_scenario_dict(game_id, "Agendas")

    # build yield dict
    yield_dict = {}
    for improvement_name, improvement_data in improvement_data_dict.items():
        
        # no point in tracking the data for improvements the player does not have any of
        if nation.improvement_counts[improvement_name] == 0:
            continue
        
        yield_dict[improvement_name] = {}
        for resource_name in nation._resources:
            yield_dict[improvement_name][resource_name] = {
                "Income": 0,
                "Income Multiplier": 1
            }

        for resource_name in improvement_data["Income"]:
            yield_dict[improvement_name][resource_name]["Income"] = improvement_data["Income"][resource_name]
    
    # get modifiers from each technology and agenda
    for tech_name in nation.completed_research:   
        
        if tech_name in technology_data_dict:
            tech_dict = technology_data_dict[tech_name]
        elif tech_name in agenda_data_dict:
            tech_dict = agenda_data_dict[tech_name]
        
        for target in tech_dict["Modifiers"]: 

            # skip over modifiers that are not affecting improvements
            if target not in yield_dict:
                continue
            
            improvement_name = target
            for resource_name, modifier_dict in tech_dict["Modifiers"][improvement_name].items():
                if "Income" in modifier_dict:
                    yield_dict[improvement_name][resource_name]["Income"] += modifier_dict["Income"]
                elif "Income Multiplier" in modifier_dict:
                    yield_dict[improvement_name][resource_name]["Income Multiplier"] += modifier_dict["Income Multiplier"]

    return yield_dict

def create_player_upkeep_dict(game_id: str, nation: Nation) -> dict:
    """
    Given a player, this function creates the initial dictionary with the upkeep of all improvements and units.

    Params:
        game_id (str): Game ID string.
        nation (Nation): Object representing the nation this yield_dict is for.

    Returns:
        dict: Upkeep dictionary detailing upkeep and upkeep multiplier for every improvement.
    """
    
    # load game info
    unit_data_dict = get_scenario_dict(game_id, "Units")
    improvement_data_dict = get_scenario_dict(game_id, "Improvements")
    technology_data_dict = get_scenario_dict(game_id, "Technologies")
    agenda_data_dict = get_scenario_dict(game_id, "Agendas")

    upkeep_dict = {}

    for improvement_name, improvement_data in improvement_data_dict.items():

        # no point in tracking the data for improvements the player does not have any of
        if nation.improvement_counts[improvement_name] == 0:
            continue
        
        upkeep_dict[improvement_name] = {}
        for resource_name in ["Dollars", "Energy", "Coal", "Oil", "Uranium"]:  # tba - pull list from scenario files
            upkeep_dict[improvement_name][resource_name] = {
                "Upkeep": 0,
                "Upkeep Multiplier": 1
            }

        for resource_name in improvement_data["Upkeep"]:
            upkeep_dict[improvement_name][resource_name]["Upkeep"] = improvement_data["Upkeep"][resource_name]

    for unit_name, unit_data in unit_data_dict.items():

        # no point in tracking the data for units the player does not have any of
        if nation.unit_counts[unit_name] == 0:
            continue
        
        upkeep_dict[unit_name] = {
            "Dollars": {
                "Upkeep": 0,
                "Upkeep Multiplier": 1
            },
            "Food": {
                "Upkeep": 0,
                "Upkeep Multiplier": 1
            },
            "Energy": {
                "Upkeep": 0,
                "Upkeep Multiplier": 1
            },
            "Coal": {
                "Upkeep": 0,
                "Upkeep Multiplier": 1
            },
            "Oil": {
                "Upkeep": 0,
                "Upkeep Multiplier": 1
            },
            "Uranium": {
                "Upkeep": 0,
                "Upkeep Multiplier": 1
            }
        }

        for resource_name in unit_data["Upkeep"]:
            upkeep_dict[unit_name][resource_name]["Upkeep"] = unit_data["Upkeep"][resource_name]
    
    # get modifiers from each technology and agenda
    for tech_name in nation.completed_research:
        
        if tech_name in technology_data_dict:
            tech_dict = technology_data_dict[tech_name]
        elif tech_name in agenda_data_dict:
            tech_dict = agenda_data_dict[tech_name]

        for target in tech_dict["Modifiers"]: 
            
            # skip over effects that are not improvements or units
            if target not in upkeep_dict:
                continue
            
            for resource_name, modifier_dict in tech_dict["Modifiers"][target].items():
                if "Upkeep" in modifier_dict:
                    upkeep_dict[target][resource_name]["Upkeep"] += modifier_dict["Upkeep"]
                elif "Upkeep Multiplier" in modifier_dict:
                    upkeep_dict[target][resource_name]["Upkeep Multiplier"] += modifier_dict["Upkeep Multiplier"]

    return upkeep_dict

def calculate_upkeep(upkeep_type: str, player_upkeep_dict: dict, player_count_dict: dict) -> float:
    """
    Calculates the total upkeep sum for a player given a specific upkeep type.

    Params:
        upkeep_type (str): Either Dollars, Oil, Uranium, or Energy.
        player_upkeep_dict (dict): Taken from create_player_upkeep_dict().
        player_count_dict (dict): A count of a player's units or improvements.

    Returns:
        float: Upkeep sum.
    """
    
    sum = 0.0

    for target, target_upkeep_dict in player_upkeep_dict.items():
        if upkeep_type in target_upkeep_dict and target in player_count_dict:
            resource_upkeep_dict = player_upkeep_dict[target][upkeep_type]
            target_upkeep = resource_upkeep_dict["Upkeep"] * resource_upkeep_dict["Upkeep Multiplier"]
            sum += target_upkeep * player_count_dict[target]

    return sum


# WAR SUB-FUNCTIONS
################################################################################

def add_truce_period(game_id: str, signatories_list: list, truce_length: int) -> None:

    # get game data
    trucedata_filepath = f'gamedata/{game_id}/trucedata.csv'
    trucedata_list = read_file(trucedata_filepath, 0)
    current_turn_num = get_current_turn_num(game_id)

    # add truce
    truce_id = len(trucedata_list)
    signatories_list.insert(0, truce_id)
    signatories_list.append(current_turn_num + truce_length + 1)
    trucedata_list.append(signatories_list)

    # update trucedata.csv
    with open(trucedata_filepath, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerows(trucedata_list)

def check_for_truce(game_id: str, nation1_id: str, nation2_id: str) -> bool:
    
    trucedata_filepath = f'gamedata/{game_id}/trucedata.csv'
    trucedata_list = read_file(trucedata_filepath, 1)
    current_turn_num = get_current_turn_num(game_id)

    for truce in trucedata_list:
        
        attacker_truce = ast.literal_eval(truce[int(nation1_id)])
        defender_truce = ast.literal_eval(truce[int(nation2_id)])
        
        if attacker_truce and defender_truce and int(len(truce)) > current_turn_num:
            return True
        
    return False

def validate_war_claims(game_id: str, war_justification: str, region_claims_list: list) -> bool:

    with open(f'gamedata/{game_id}/regdata.json', 'r') as json_file:
        regdata_dict = json.load(json_file)

    # get war justification info
    if war_justification == 'Border Skirmish':
        free_claims = 3
        max_claims = 6
        claim_cost = 5
    elif war_justification == 'Conquest':
        free_claims = 5
        max_claims = 10
        claim_cost = 3
    
    # check that all claims are valid
    total = 0
    for i, region_id in enumerate(region_claims_list):
        
        if region_id not in regdata_dict:
            return -1
        
        if i + 1 > max_claims:
            return -1
        
        if i + 1 > free_claims:
            total += claim_cost

    return total

def locate_best_missile_defense(game_id: str, target_nation: Nation, missile_type: str, target_region_id: str) -> str | None:
    """
    Identifies best missile defense to counter incoming missile. Returns None if not found.
    """
    
    # get game data
    improvement_data_dict = get_scenario_dict(game_id, "Improvements")
    target_region = Region(target_region_id, game_id)
    target_region_improvement = Improvement(target_region_id, game_id)

    defender_name = None
    # tba - get priority for missile defense from game files
    # tba - get defensive capabilities from game files

    # check for MDS
    if target_region_improvement.name == "Missile Defense System":
        defender_name = "Missile Defense System"
    else:
        missile_defense_network_candidates_list = target_region.get_regions_in_radius(2)
        for select_region_id in missile_defense_network_candidates_list:
            select_region = Region(select_region_id, game_id)
            select_region_improvement = Improvement(select_region_id, game_id)
            if select_region_improvement.name == "Missile Defense System" and select_region.owner_id == target_region.owner_id:
                defender_name = "Missile Defense System"
                break

    # check for anti-air unit
    # tba

    # last resort - check for local defense
    if defender_name is None and "Local Missile Defense" in target_nation.completed_research:
        if target_region_improvement is not None and target_region_improvement.health != 0:
            if target_region_improvement.missile_defense != 99:
                defender_name = target_region_improvement.name

    return defender_name

def withdraw_units(game_id: str):

    nation_table = NationTable(game_id)
    with open(f'gamedata/{game_id}/regdata.json', 'r') as json_file:
        regdata_dict = json.load(json_file)

    for region_id in regdata_dict:
        region = Region(region_id, game_id)
        region_unit = Unit(region_id, game_id)
        
        # a unit can only be present in another nation without occupation if a war just ended 
        if region_unit.name is not None and region_unit.owner_id != region.owner_id and region.occupier_id == 0:
            
            nation = nation_table.get(str(region_unit.owner_id))
            target_id = region.find_suitable_region()
            
            if target_id is not None:
                nation.action_log.append(f"Withdrew {region_unit.name} {region_unit.region_id} to {target_id}.")
                region_unit.move(Region(target_id, game_id), withdraw=True)
            else:
                nation.action_log.append(f"Failed to withdraw {region_unit.name} {region_unit.region_id}. Unit disbanded!")
                nation.unit_counts[region_unit.name] -= 1
                region_unit.clear()
            
            nation_table.save(nation)


# MISC SUB-FUNCTIONS
################################################################################

def read_file(filepath, skip_value):

    '''
    Reads a csv file given a filepath and returns it as a list of lists.

    Parameters:
    - filepath: The full filepath to the desired file relative to core.py.
    - skip_value: A positive integer value representing how many of the first rows to skip. Usually 0-2.
    '''
    output = []
    with open(filepath, 'r') as file:
        reader = csv.reader(file)
        for i in range(0, skip_value):
            next(reader, None)
        for row in reader:
            if row != []:
                output.append(row)
    return output

def read_rmdata(rmdata_filepath, current_turn_num, refine, keep_header):
    '''
    Reads rmdata.csv and generates a list of all currently relevant transactions.

    Parameters:
    - rmdata_filepath: The full relative filepath to rmdata.csv.
    - current_turn_num: An integer number representing the game's current turn number.
    - refine: A count representing how many turns back you want of resource market data. Define as a positive integer or False if you want all records.
    - keep_header: A boolean value. Enter as True if you don't care about the header rows being in your data.
    '''

    #Get list of all transactions
    rmdata_list = []
    if keep_header == True:
        with open(rmdata_filepath, 'r') as file:
            reader = csv.reader(file)
            for row in reader:
                if row != []:
                    rmdata_list.append(row)
    if keep_header == False:
        with open(rmdata_filepath, 'r') as file:
                reader = csv.reader(file)
                next(reader,None)
                for row in reader:
                    if row != []:
                        rmdata_list.append(row)
    #Refine list as needed
    rmdata_refined_list = []
    if refine:
        limit = current_turn_num - refine
        for transaction in rmdata_list:
            transaction[0] = int(transaction[0])
            transaction[3] = int(transaction[3])
            if transaction[0] >= limit:
                rmdata_refined_list.append(transaction)
    elif refine == False:
        for transaction in rmdata_list:
            transaction[0] = int(transaction[0])
            transaction[3] = int(transaction[3])
            rmdata_refined_list.append(transaction)
    return rmdata_refined_list

def date_from_turn_num(current_turn_num):
    remainder = current_turn_num % 4
    if remainder == 0:
        season = 'Winter'
    elif remainder == 1:
        season = 'Spring'
    elif remainder == 2:
        season = 'Summer'
    elif remainder == 3:
        season = 'Fall'
    quotient = current_turn_num // 4
    year = 2021 + quotient
    if season == 'Winter':
        year -= 1
    return season, year

def search_and_destroy(game_id: str, player_id: str, target_improvement: str) -> str:
    """
    Searches for a specific improvement and removes it.
    """

    with open(f'gamedata/{game_id}/regdata.json', 'r') as json_file:
        regdata_dict = json.load(json_file)
    
    # find all regions belonging to a player with target improvement
    candidate_region_ids = []
    for region_id in regdata_dict:
        region = Region(region_id, game_id)
        region_improvement = Improvement(region_id, game_id)
        if region_improvement.name == target_improvement and region.owner_id == int(player_id):
            candidate_region_ids.append(region_id)

    # randomly select one of the candidate regions
    random.shuffle(candidate_region_ids)
    chosen_region_id = candidate_region_ids.pop()
    target_region_improvement = Improvement(chosen_region_id, game_id)
    target_region_improvement.clear()
    
    return chosen_region_id

def search_and_destroy_unit(game_id: str, player_id: str, desired_unit_name: str) -> tuple[str, str]:
    """
    Randomly destroys one unit of a given type belonging to a specific player.
    """

    unit_scenario_dict = get_scenario_dict(game_id, "Units")
    with open(f'gamedata/{game_id}/regdata.json', 'r') as json_file:
        regdata_dict = json.load(json_file)

    # get list of regions with desired_unit_name owned by player_id
    candidate_region_ids = []
    if desired_unit_name in unit_scenario_dict:
        for region_id in regdata_dict:
            region_unit = Unit(region_id, game_id)
            if (desired_unit_name == 'ANY' or region_unit.name == desired_unit_name) and region_unit.owner_id == int(player_id):
                candidate_region_ids.append(region_id)

    # randomly select one of the candidate regions
    # there should always be at least one candidate region because we have already checked that the target unit exists
    random.shuffle(candidate_region_ids)
    chosen_region_id = candidate_region_ids.pop()
    target_region_unit = Unit(chosen_region_id, game_id)
    victim = copy.deepcopy(target_region_unit.name)
    target_region_unit.clear()

    return chosen_region_id, victim

def get_scenario_dict(game_id, dictionary_name):
    '''
    Gets a dictionary from the chosen scenario.
    '''

    with open('active_games.json', 'r') as json_file:
        active_games_dict = json.load(json_file)

    if game_id != "TBD":
        scenario_name = active_games_dict[game_id]["Information"]["Scenario"]
        scenario = scenario_name.lower()
    else:
        scenario = "standard"

    filename = f"{dictionary_name.lower()}.json"
    dictionary_filepath = f"scenarios/{scenario}/{filename}"

    with open(dictionary_filepath, 'r') as json_file:
        chosen_dictionary = json.load(json_file)

    return chosen_dictionary


# CSV File Headers
################################################################################

rmdata_header = ["Turn", "Nation", "Bought/Sold", "Count", "Resource Exchanged"]
trucedata_header = ['Truce ID', 'Player #1', 'Player #2', 'Player #3', 'Player #4', 'Player #5', 'Player #6', 'Player #7', 'Player #8', 'Player #9', 'Player #10', 'Expire Turn #']    # not actually needed anymore
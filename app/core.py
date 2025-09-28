import ast
import csv
import json
import random
import copy
from collections import defaultdict
from typing import Union, Tuple, List

from app.nation import Nation, Nations


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
    
    from app.scenario import ScenarioData as SD

    # build yield dict
    yield_dict = {}
    for improvement_name, improvement_data in SD.improvements:
        
        # no point in tracking the data for improvements the player does not have any of
        if nation.improvement_counts[improvement_name] == 0:
            continue
        
        yield_dict[improvement_name] = {}
        for resource_name in nation._resources:
            yield_dict[improvement_name][resource_name] = {
                "Income": 0,
                "Income Multiplier": 1
            }

        for resource_name, amount in improvement_data.income.items():
            yield_dict[improvement_name][resource_name]["Income"] = amount
    
    # get modifiers from each technology and agenda
    for tech_name in nation.completed_research:   

        if tech_name in SD.agendas:
            tech_dict = SD.agendas[tech_name]
        else:
            tech_dict = SD.technologies[tech_name]
        
        for target in tech_dict.modifiers: 

            # skip over modifiers that are not affecting improvements
            if target not in yield_dict:
                continue
            
            improvement_name = target
            for resource_name, modifier_dict in tech_dict.modifiers[improvement_name].items():
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
    
    from app.scenario import ScenarioData as SD

    upkeep_dict = {}

    for improvement_name, improvement_data in SD.improvements:

        # no point in tracking the data for improvements the player does not have any of
        if nation.improvement_counts[improvement_name] == 0:
            continue
        
        upkeep_dict[improvement_name] = {}
        for resource_name in ["Dollars", "Food", "Energy", "Coal", "Oil", "Uranium"]:  # tba - pull list from scenario files
            upkeep_dict[improvement_name][resource_name] = {
                "Upkeep": 0,
                "Upkeep Multiplier": 1
            }

        for resource_name, amount in improvement_data.upkeep.items():
            upkeep_dict[improvement_name][resource_name]["Upkeep"] = amount

    for unit_name, unit_data in SD.units:

        # no point in tracking the data for units the player does not have any of
        if nation.unit_counts[unit_name] == 0:
            continue
        
        upkeep_dict[unit_name] = {}
        for resource_name in ["Dollars", "Food", "Energy", "Coal", "Oil", "Uranium"]:  # tba - pull list from scenario files
            upkeep_dict[unit_name][resource_name] = {
                "Upkeep": 0,
                "Upkeep Multiplier": 1
            }

        for resource_name, amount in unit_data.upkeep.items():
            upkeep_dict[unit_name][resource_name]["Upkeep"] = amount
    
    # get modifiers from each technology and agenda
    for tech_name in nation.completed_research:
        
        if tech_name in SD.agendas:
            tech_dict = SD.agendas[tech_name]
        else:
            tech_dict = SD.technologies[tech_name]

        for target in tech_dict.modifiers: 
            
            # skip over effects that are not improvements or units
            if target not in upkeep_dict:
                continue
            
            for resource_name, modifier_dict in tech_dict.modifiers[target].items():
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

def locate_best_missile_defense(game_id: str, target_nation: Nation, missile_type: str, target_region_id: str) -> str | None:
    """
    Identifies best missile defense to counter incoming missile. Returns None if not found.
    """
    
    # get game data
    from app.region import Region
    target_region = Region(target_region_id)

    defender_name = None
    # TODO - rewrite, no hardcoding the names

    # check for MDS
    if target_region.improvement.name == "Missile Defense System":
        defender_name = "Missile Defense System"
    else:
        missile_defense_network_candidates_list = target_region.get_regions_in_radius(2)
        for select_region_id in missile_defense_network_candidates_list:
            select_region = Region(select_region_id)
            if select_region.improvement.name == "Missile Defense System" and select_region.data.owner_id == target_region.data.owner_id:
                defender_name = "Missile Defense System"
                break
    
    if missile_type != "Standard Missile":
        return defender_name

    # check for anti-air unit
    if target_region.unit.name == "Anti-Air":
        defender_name = "Anti-Air"
    else:
        if target_region.check_for_adjacent_unit({"Anti-Air"}, target_region.data.owner_id):
            defender_name = "Anti-Air"

    # last resort - check for local defense
    if defender_name is None and "Local Missile Defense" in target_nation.completed_research:
        if target_region.improvement is not None and target_region.improvement.health != 0:
            if target_region.improvement.missile_defense != "99":
                defender_name = target_region.improvement.name

    return defender_name

def withdraw_units(game_id: str):

    from app.region import Region, Regions

    for region in Regions:
        
        # a unit can only be present in another nation without occupation if a war just ended 
        if region.unit.name is not None and region.unit.owner_id != region.data.owner_id and region.data.occupier_id == "0":
            
            nation = Nations.get(region.unit.owner_id)
            target_id = region.find_suitable_region()
            
            if target_id is not None:
                nation.action_log.append(f"Withdrew {region.unit.name} {region.region_id} to {target_id}.")
                region.move_unit(Region(target_id), withdraw=True)
            else:
                nation.action_log.append(f"Failed to withdraw {region.unit.name} {region.region_id}. Unit disbanded!")
                nation.unit_counts[region.unit.name] -= 1
                region.unit.clear()


# MISC SUB-FUNCTIONS
################################################################################

def search_and_destroy(game_id: str, player_id: str, target_improvement: str) -> str:
    """
    Searches for a specific improvement and removes it.
    """

    from app.region import Region, Regions
    
    # find all regions belonging to a player with target improvement
    candidate_region_ids = []
    for region in Regions:
        if region.improvement.name == target_improvement and region.data.owner_id == int(player_id):
            candidate_region_ids.append(region.region_id)

    # randomly select one of the candidate regions
    random.shuffle(candidate_region_ids)
    chosen_region_id = candidate_region_ids.pop()
    target_region = Region(chosen_region_id)
    target_region.improvement.clear()
    
    return chosen_region_id

def search_and_destroy_unit(game_id: str, player_id: str, desired_unit_name: str) -> tuple[str, str]:
    """
    Randomly destroys one unit of a given type belonging to a specific player.
    """

    from app.scenario import ScenarioData as SD
    from app.region import Region, Regions

    # get list of regions with desired_unit_name owned by player_id
    candidate_region_ids = []
    if desired_unit_name in SD.units:
        for region in Regions:
            if (desired_unit_name == 'ANY' or region.unit.name == desired_unit_name) and region.unit.owner_id == player_id:
                candidate_region_ids.append(region.region_id)

    # randomly select one of the candidate regions
    # there should always be at least one candidate region because we have already checked that the target unit exists
    random.shuffle(candidate_region_ids)
    chosen_region_id = candidate_region_ids.pop()
    target_region = Region(chosen_region_id)
    victim = copy.deepcopy(target_region.unit.name)
    target_region.unit.clear()

    return chosen_region_id, victim
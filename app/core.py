import random
import copy

from app.scenario.scenario import ScenarioInterface as SD
from app.nation.nation import Nation
from app.nation.nations import Nations
from app.region.region import Region
from app.region.regions import Regions

# ECONOMIC HELPER FUNCTIONS
################################################################################

def create_player_yield_dict(nation: Nation) -> dict:
    """
    Given a player, this function creates the initial dictionary with the yields of all improvements.

    Params:
        game_id (str): Game ID string.
        nation (Nation): Object representing the nation this yield_dict is for.

    Returns:
        dict: Yield dictionary detailing income and multiplier for every improvement.
    """
    
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

def create_player_upkeep_dict(nation: Nation) -> dict:
    """
    Given a player, this function creates the initial dictionary with the upkeep of all improvements and units.

    Params:
        game_id (str): Game ID string.
        nation (Nation): Object representing the nation this yield_dict is for.

    Returns:
        dict: Upkeep dictionary detailing upkeep and upkeep multiplier for every improvement.
    """

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


# WAR HELPRR FUNCTIONS
################################################################################

def withdraw_units():

    for region in Regions:
        
        # a unit can only be present in another nation without occupation if a war just ended 
        if region.unit.name is not None and region.unit.owner_id != region.data.owner_id and region.data.occupier_id == "0":
            
            nation = Nations.get(region.unit.owner_id)
            target_id = region.find_suitable_region()
            
            if target_id is not None:
                nation.action_log.append(f"Withdrew {region.unit.name} {region.id} to {target_id}.")
                region.move_unit(Region(target_id), withdraw=True)
            else:
                nation.action_log.append(f"Failed to withdraw {region.unit.name} {region.id}. Unit disbanded!")
                nation.unit_counts[region.unit.name] -= 1
                region.unit.clear()


# MISC HELPER FUNCTIONS
################################################################################

def search_and_destroy(player_id: str, target_improvement: str) -> str:
    """
    Searches for a specific improvement and removes it.
    """
    
    # find all regions belonging to a player with target improvement
    candidate_region_ids = []
    for region in Regions:
        if region.improvement.name == target_improvement and region.data.owner_id == int(player_id):
            candidate_region_ids.append(region.id)

    # randomly select one of the candidate regions
    random.shuffle(candidate_region_ids)
    chosen_region_id = candidate_region_ids.pop()
    target_region = Regions.load(chosen_region_id)
    target_region.improvement.clear()
    
    return chosen_region_id

def search_and_destroy_unit(player_id: str, desired_unit_name: str) -> tuple[str, str]:
    """
    Randomly destroys one unit of a given type belonging to a specific player.
    """

    # get list of regions with desired_unit_name owned by player_id
    candidate_region_ids = []
    for region in Regions:
        if (desired_unit_name == 'ANY' or region.unit.name == desired_unit_name) and region.unit.owner_id == player_id:
            candidate_region_ids.append(region.id)

    # randomly select one of the candidate regions
    # there should always be at least one candidate region because we have already checked that the target unit exists
    random.shuffle(candidate_region_ids)
    chosen_region_id = candidate_region_ids.pop()
    target_region = Regions.load(chosen_region_id)
    victim = copy.deepcopy(target_region.unit.name)
    target_region.unit.clear()

    return chosen_region_id, victim
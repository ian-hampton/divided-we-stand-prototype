
from app.scenario.scenario import ScenarioInterface as SD
from app.nation.nation import Nation

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
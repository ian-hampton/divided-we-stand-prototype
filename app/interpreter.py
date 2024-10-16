from app import core
import re
import json

def check_action(action, library, game_id):
    '''
    Takes an action string and checks it for errors. Returns properly formatted action string.

    Parameters:
    - action: A player action string.
    - game_id: The full game_id of the active game.
    '''
    with open(f'gamedata/{game_id}/regdata.json', 'r') as json_file:
        regdata_dict = json.load(json_file)
    
    #get action type and strip action
    action_type = core.identify(action)
    action = action.lower().strip()

    #catch mistaken use of buy instead of purchase
    if "buy" in action and "oil" not in action:
        if len(action) == 9:
            action = f'purchase {action[-5:]}'

    #catch common errors and abbreviations
    action = catch_errors_and_abbreviations(action, action_type)

    #capitalize the start of every word
    action = action.title()

    #make all region ids all caps
    if action_type not in ['Surrender', 'White Peace', 'Research', 'Alliance', 'Republic', 'Steal', 'Make', 'Buy', 'Sell', 'War']:
        for region_id in regdata_dict:
            if region_id.title() in action:
                action = replace_target(action, region_id.title(), region_id.upper())
            elif region_id.lower() in action:
                action = replace_target(action, region_id.lower(), region_id.upper())
    
    #replace all unit abbreviations
    unit_data_dict = core.get_scenario_dict(game_id, "Units")
    if action_type == 'Deploy':
        unit_input = action[7:-6].title()
        print(unit_input)
        if unit_input in library['Unit Name List']:
            unit_name = unit_input
            action = replace_target(action, action[7:-6], unit_name)
        elif unit_input.upper() in library['Unit Abbreviation List']:
            unit_abbrev = unit_input.upper()
            for unit_name in unit_data_dict:
                if unit_data_dict[unit_name]["Abbreviation"] == unit_abbrev:
                    action = replace_target(action, action[7:-6], unit_name)
                    break

    #validate action
    action_valid = validate(action, action_type, library, regdata_dict)
    if not action_valid:
        print(f'The action: "{action}" of type {action_type} is not valid.')
        new_action = input("Please re-enter the action: ")
        action = check_action(new_action, library)

    return action

def catch_errors_and_abbreviations(action, action_type):
    match action_type:
        case "Build":
            for error in resource_errors_dict:
                correction = resource_errors_dict[error]
                if error in action and correction.lower() not in action:
                    action = replace_target(action, error, correction)
                    break
            for error in improvement_errors_dict:
                correction = improvement_errors_dict[error]
                if error in action and correction.lower() not in action:
                    action = replace_target(action, error, correction)
                    break
            for abbreviation in improvement_abbreviations_dict:
                correction = improvement_abbreviations_dict[abbreviation]
                if abbreviation in action and correction.lower() not in action:
                    action = replace_target(action, abbreviation, correction)
                    break
        case "Buy" | "Sell" | "Republic":
            action = action.replace(":", "")
            for error in resource_errors_dict:
                correction = resource_errors_dict[error]
                if error in action and correction.lower() not in action:
                    action = replace_target(action, error, correction)
                    break
        case "Research":
            for error in research_errors_dict:
                correction = research_errors_dict[error]
                if error in action and correction.lower() not in action:
                    action = replace_target(action, error, correction)
                    break
    return action

def replace_target(string, target, replacement):
    '''
    From my good friend ChatGPT. Uses regex to only replace strings that are not parts of another word.
    '''

    pattern = r'(?<![a-zA-Z0-9])' + re.escape(target) + r'(?![a-zA-Z0-9])'
    new_string = re.sub(pattern, replacement, string)

    return new_string

def validate(action, action_type, library, regdata_dict):
    '''
    Compares an action to the library of game terms. Gives oppertunity to correct an action if error found.
    '''
        
    move_regions_list = []
    if action_type == 'Move' or action_type == 'Withdraw':
        action_data_list = action.split(' ')
        move_regions_list = action_data_list[-1].split('-')

    validate_resolution_dict = {
        'Surrender': [check_nation_name(action, library)],
        'White Peace': [check_nation_name(action, library)],
        'Purchase': [check_region_id(action, regdata_dict)],
        'Research': [check_research_name(action, library)],
        'Remove': [check_region_id(action, regdata_dict)],
        'Build': [check_improvement_name(action, library), check_region_id(action, regdata_dict)],
        'Alliance': [check_alliance_name(action, library), check_nation_name(action, library)],
        'Republic': [check_resource_name(action, library)],
        'Steal': [check_nation_name(action, library)],
        'Make': [check_missile_name(action, library)],
        'Buy': [check_resource_name(action, library)],
        'Sell': [check_resource_name(action, library)],
        'Withdraw': [check_region_id(region_id, library) for region_id in move_regions_list],
        'Disband': [check_region_id(action, regdata_dict)],
        'Deploy': [check_unit_name(action, library), check_region_id(action, regdata_dict)],
        'War': [check_justification_name(action, library), check_nation_name(action, library)],
        'Launch': [check_missile_name(action, library), check_region_id(action, regdata_dict)],
        'Move': [check_region_id(region_id, library) for region_id in move_regions_list],
        'Event': [],
    }

    if action_type not in validate_resolution_dict:
        return False
    
    for i in range(len(validate_resolution_dict[action_type])):
        check = validate_resolution_dict[action_type][i]
        if not check:
            return False
    return True

improvement_abbreviations_dict = {
    "amm":"Advanced Metals Mine",
    "amr":"Advanced Metals Refinery",
    "bank":"Central Bank",
    "cmm":"Common Metals Mine",
    "barrier":"Crude Barrier",
    "iz":"Industrial Zone",
    "inz":"Industrial Zone",
    "idz":"Industrial Zone",
    "indz":"Industrial Zone",
    "base":"Military Base",
    "outpost":"Military Outpost",
    "mdn":"Missile Defense Network",
    "defense network":"Missile Defense Network",
    "mds":"Missile Defense System",
    "defense system":"Missile Defense System",
    "npp":"Nuclear Power Plant",
    "power plant":"Nuclear Power Plant",
    "ree":"Rare Earth Elements Mine",
    "reem":"Rare Earth Elements Mine",
    "ree mine":"Rare Earth Elements Mine",
    "inst":"Research Institute",
    "institute":"Research Institute",
    "research lab":"Research Laboratory",
    "lab":"Research Laboratory",
    "laboratory":"Research Laboratory",
    "silo":"Missile Silo",
    "sfarm":"Solar Farm",
    "solar":"Solar Farm",
    "surv":"Surveillance Center",
    "surveillance":"Surveillance Center",
    "wfarm":"Wind Farm",
    "wind":"Wind Farm"
}

improvement_errors_dict = {
    "barracks":"Boot Camp",
    "rare elements mine ": "Rare Earth Elements Mine",
    "rare earth mine ": "Rare Earth Elements Mine",
    "solar panels ": "Solar Farm",   
    "radioactive element mine ": "Uranium Mine",
    "radioactive elements mine ": "Uranium Mine",
    "radioactive element refinery ": "Uranium Refinery",
    "radioactive elements refinery ": "Uranium Refinery",
    "wind turbines ": "Wind Farm",
}

research_errors_dict = {
    "research coal mines": "Research Coal Mining",
    "research strip mines": "Research Strip Mining",
    "research oil wells": "Research Oil Drilling",
    "research oil refining": "Research Oil Refinement",
    "research central banking": "Research Central Banking System",
    "research surface mines": "Research Surface Mining",
    "research underground mines": "Research Underground Mining",
    "research metal refining": "Research Metal Refinement",
    "research labs": "Research Laboratories",
    "research special forces": "Research Special Operations",
    "research light tank": "Research Light Tanks",
    "research heavy tank": "Heavy Tank",
    "research main battle tank": "Main Battle Tank",
    "research missiles": "Research Missile Technology",
    "research standard missiles": "Research Missile Technology",
    "research nukes": "Research Nuclear Warhead",
    "research uranium refining": "Research Uranium Refinement",
    "research boot camps": "Research Standing Army",
    "research crude barrier": "Research Basic Defenses",
    "research crude barriers": "Research Basic Defenses",
    "research military outpost": "Research Military Outposts",
    "research military base": "Research Military Bases"
}

resource_errors_dict = {
    "basic material": "Basic Materials",
    "common metal": "Common Metals",
    "advanced metal": "Advanced Metals",
    "rare earth element": "Rare Earth Elements",
    "rareearthelements": "Rare Earth Elements",
    "politicalpower": "Political Power",
    "commonmetals": "Common Metals",
    "advancedmetals": "Advanced Metals",
    "basicmaterials": "Basic Materials",
    "greenenergy": "Green Energy",
}

def check_nation_name(action, library):
    for nation_name in library['Nation Name List']:
        if nation_name in action:
            return True
    return False

def check_region_id(action, regdata_dict):
    for region_id in regdata_dict:
        if region_id in action:
            return True
    return False

def check_research_name(action, library):
    for research_name in library['Research Name List']:
        if research_name in action:
            return True
    return False

def check_improvement_name(action, library):
    for improvement_name in library['Improvement List']:
        if improvement_name in action:
            return True
    return False

def check_alliance_name(action, library):
    for alliance_type in library['Alliance Type List']:
        if alliance_type in action:
            return True
    return False

def check_resource_name(action, library):
    for resource_name in library['Resource Name List']:
        if resource_name in action:
            return True
    return False

def check_missile_name(action, library):
    for missile_type in library['Missile Type List']:
        if missile_type in action:
            return True
    return False

def check_unit_name(action, library):
    for unit_name in library['Unit Name List']:
        if unit_name in action:
            return True
    return False

def check_justification_name(action, library):
    for war_justification_name in library['War Justification Name List']:
        if war_justification_name in action:
            return True
    return False


import json
import random
import importlib

from app import core

def trigger_event(game_id: str) -> None:
    """
    Triggers a random event.

    Params:
        game_id (str): Game ID string.
    
    Returns:
        None
    """

    with open("active_games.json", 'r') as json_file:
        active_games_dict = json.load(json_file)
    
    # load event data and events module based on scenario
    event_scenario_dict = core.get_scenario_dict(game_id, "events")
    scenario = active_games_dict[game_id]["Information"]["Scenario"].lower()
    events = importlib.import_module(f"scenarios.{scenario}.events")

    # create list of eligible events
    event_list = list(event_scenario_dict.keys())
    already_chosen_events = set(active_games_dict[game_id]["Inactive Events"]) | set(key for key in active_games_dict[game_id]["Active Events"])
    event_list_filtered = []
    for event_name in event_list:
        event = events.load_event(game_id, event_name, event_data=None, temp=True)
        if event_name in already_chosen_events or not event.has_conditions_met():
            continue
        event_list_filtered.append(event_name)

    # initiate random event
    event_name = random.choice(event_list)
    print(f"Triggering {event_name} event...")
    event = events.load_event(game_id, event_name, event_data=None)
    event.activate()

    # save event
    match event.state:
        case 2:
            active_games_dict["Current Event"] = event.export()
        case 1:
            active_games_dict["Active Events"][event_name] = event.export()
        case 0:
            active_games_dict["Inactive Events"].append(event_name)

    with open("active_games.json", 'w') as json_file:
        json.dump(active_games_dict, json_file, indent=4)

def resolve_current_event(game_id: str) -> None:
    
    with open("active_games.json", 'r') as json_file:
        active_games_dict = json.load(json_file)
    
    # load events module based on scenario
    scenario = active_games_dict[game_id]["Information"]["Scenario"].lower()
    events = importlib.import_module(f"scenarios.{scenario}.events")

    # load event
    event_data = active_games_dict["Current Event"]
    event_name = event_data["Name"]
    event = events.load_event(game_id, event_name, event_data)

    # resolve current event
    event.resolve()
    active_games_dict["Current Event"] = {}

    # save event
    match event.state:
        case 1:
            active_games_dict["Active Events"][event_name] = event.export()
        case 0:
            active_games_dict["Inactive Events"].append(event_name)

    with open("active_games.json", 'w') as json_file:
        json.dump(active_games_dict, json_file, indent=4)

def resolve_active_events(game_id: str, run_before_actions: bool):
    
    with open("active_games.json", 'r') as json_file:
        active_games_dict = json.load(json_file)

    scenario = active_games_dict[game_id]["Information"]["Scenario"].lower()
    events = importlib.import_module(f"scenarios.{scenario}.events")

    for event_name, event_data in active_games_dict["Active Events"].items():

        event = events.load_event(game_id, event_name, event_data, temp = True)

        if run_before_actions and hasattr(event, 'run_before') and callable(event.run_before):
            event.run_before()
        
        if run_before_actions and hasattr(event, 'run_after') and callable(event.run_after):
            event.run_after()

        match event.state:
            case 1:
                active_games_dict["Active Events"][event_name] = event.export()
            case 0:
                active_games_dict["Inactive Events"].append(event_name)

    with open("active_games.json", 'w') as json_file:
        json.dump(active_games_dict, json_file, indent=4)

def filter_events():
    pass

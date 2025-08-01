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

    # load event data and events module based on scenario
    with open("active_games.json", 'r') as json_file:
        active_games_dict = json.load(json_file)
    event_scenario_dict = core.get_scenario_dict(game_id, "events")
    scenario = active_games_dict[game_id]["Information"]["Scenario"].lower()
    events = importlib.import_module(f"scenarios.{scenario}.events")

    # create list of eligible events
    event_list = list(event_scenario_dict.keys())
    already_chosen_events = set(active_games_dict[game_id]["Inactive Events"]) | set(key for key in active_games_dict[game_id]["Active Events"])
    event_list_filtered = []
    for event_name in event_list:
        event = events.load_event(game_id, event_name, temp = True)
        if event_name in already_chosen_events or not event.has_conditions_met():
            continue
        event_list_filtered.append(event_name)

    # initiate random event
    event_name = random.choice(event_list)
    print(f"Triggering {event_name} event...")
    event = events.load_event(game_id, event_name, new=True)
    event.activate()

    # save event
    match event.state:
        case "Current":
            active_games_dict["Current Event"] = event.export()
        case "Active":
            active_games_dict["Active Events"][event_name] = event.export()
        case "Inactive":
            active_games_dict["Inactive Events"].append(event_name)

    # save changes to active games    
    with open("active_games.json", 'w') as json_file:
        json.dump(active_games_dict, json_file, indent=4)

def resolve_active_events():
    pass

def filter_events():
    pass

import json
import random
import importlib

from app import core
from app.notifications import Notifications

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
    event_name = random.choice(event_list_filtered)
    print(f"Triggering {event_name} event...")
    event = events.load_event(game_id, event_name, event_data=None)
    event.activate()

    # save event
    match event.state:
        case 2:
            active_games_dict[game_id]["Current Event"] = event.export()
        case 1:
            active_games_dict[game_id]["Active Events"][event_name] = event.export()
        case 0:
            active_games_dict[game_id]["Inactive Events"].append(event_name)

    with open("active_games.json", 'w') as json_file:
        json.dump(active_games_dict, json_file, indent=4)

def resolve_current_event(game_id: str) -> None:
    
    with open("active_games.json", 'r') as json_file:
        active_games_dict = json.load(json_file)
    
    # load events module based on scenario
    scenario = active_games_dict[game_id]["Information"]["Scenario"].lower()
    events = importlib.import_module(f"scenarios.{scenario}.events")

    # load event
    event_data = active_games_dict[game_id]["Current Event"]
    event_name = event_data["Name"]
    event = events.load_event(game_id, event_name, event_data)

    # resolve current event
    event.resolve()
    active_games_dict[game_id]["Current Event"] = {}

    # save event
    match event.state:
        case 1:
            active_games_dict[game_id]["Active Events"][event_name] = event.export()
        case 0:
            active_games_dict[game_id]["Inactive Events"].append(event_name)

    with open("active_games.json", 'w') as json_file:
        json.dump(active_games_dict, json_file, indent=4)

def resolve_active_events(game_id: str, actions_dict=None):
    
    with open("active_games.json", 'r') as json_file:
        active_games_dict = json.load(json_file)

    scenario = active_games_dict[game_id]["Information"]["Scenario"].lower()
    events = importlib.import_module(f"scenarios.{scenario}.events")

    active_events_filtered = {}

    for event_name, event_data in active_games_dict[game_id]["Active Events"].items():

        event = events.load_event(game_id, event_name, event_data)

        if actions_dict is not None:
            event.run_before(actions_dict)
        else:
            event.run_after()

        match event.state:
            case 1:
                active_events_filtered[event_name] = event.export()
            case 0:
                active_games_dict[game_id]["Inactive Events"].append(event_name)

    active_games_dict[game_id]["Active Events"] = active_events_filtered
    with open("active_games.json", 'w') as json_file:
        json.dump(active_games_dict, json_file, indent=4)

def filter_events(game_id: str):
    
    current_turn_num = core.get_current_turn_num(game_id)
    notifications = Notifications(game_id)
    with open("active_games.json", 'r') as json_file:
        active_games_dict = json.load(json_file)

    scenario = active_games_dict[game_id]["Information"]["Scenario"].lower()
    events = importlib.import_module(f"scenarios.{scenario}.events")

    active_events_filtered = {}

    for event_name, event_data in active_games_dict[game_id]["Active Events"].items():

        event = events.load_event(game_id, event_name, event_data)

        if current_turn_num >= event.expire_turn:
            notifications.append(f"{event.name} event has ended.", 2)
            if event.name == "Foreign Invasion":
                event._foreign_invasion_end()
            continue

        active_events_filtered[event.name] = event.export()
        if event.expire_turn != 99999:
            notifications.append(f"{event.name} will end on turn {event.expire_turn}.", 2)
        else:
            notifications.append(f"{event.name} event is active.", 2)

    active_games_dict[game_id]["Active Events"] = active_events_filtered
    with open("active_games.json", 'w') as json_file:
        json.dump(active_games_dict, json_file, indent=4)

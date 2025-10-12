import copy
import random
import importlib

from app.gamedata import Games, GameStatus
from app.notifications import Notifications

def trigger_event(game_id: str) -> None:
    """
    Triggers a random event.

    Params:
        game_id (str): Game ID string.
    
    Returns:
        None
    """

    from app.scenario import ScenarioData as SD
    
    game = Games.load(game_id)
    events = importlib.import_module(f"scenarios.{SD.scenario}.events")

    # create list of eligible events
    event_list = list(SD.events.names())
    already_chosen_events = set(game.inactive_events) | set(key for key in game.active_events)
    event_list_filtered = []
    for event_name in event_list:
        event = events.load_event(game_id, event_name, event_data=None)
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
            game.current_event = event.export()
            game.status = GameStatus.ACTIVE_PENDING_EVENT
        case 1:
            game.active_events[event_name] = event.export()
        case 0:
            game.inactive_events.append(event_name)

def resolve_current_event(game_id: str) -> None:
    
    from app.scenario import ScenarioData as SD
    
    game = Games.load(game_id)
    events = importlib.import_module(f"scenarios.{SD.scenario}.events")

    # load event
    event_data = copy.deepcopy(game.current_event)
    event_name = event_data["Name"]
    event = events.load_event(game_id, event_name, event_data)

    # resolve current event
    event.resolve()
    game.current_event = {}

    # save event
    match event.state:
        case 1:
            game.active_events[event_name] = event.export()
        case 0:
            game.inactive_events.append(event_name)

def resolve_active_events(game_id: str, actions_dict=None):
    
    from app.scenario import ScenarioData as SD
    
    game = Games.load(game_id)
    events = importlib.import_module(f"scenarios.{SD.scenario}.events")

    active_events_filtered = {}

    for event_name, event_data in game.active_events.items():

        event = events.load_event(game_id, event_name, event_data)

        if actions_dict is not None:
            event.run_before(actions_dict)
        else:
            event.run_after()

        match event.state:
            case 1:
                active_events_filtered[event_name] = event.export()
            case 0:
                game.inactive_events.append(event_name)

    game.active_events = active_events_filtered

def filter_events(game_id: str):
    
    from app.scenario import ScenarioData as SD

    game = Games.load(game_id)
    events = importlib.import_module(f"scenarios.{SD.scenario}.events")

    active_events_filtered = {}

    for event_name, event_data in game.active_events.items():

        event = events.load_event(game_id, event_name, event_data)

        if game.turn >= event.expire_turn:
            Notifications.add(f"{event.name} event has ended.", 3)
            if event.name == "Foreign Invasion":
                event._foreign_invasion_end()
            continue

        active_events_filtered[event.name] = event.export()
        if event.expire_turn != 99999:
            Notifications.add(f"{event.name} will end on turn {event.expire_turn}.", 3)
        else:
            Notifications.add(f"{event.name} event is active.", 3)

    game.active_events = active_events_filtered
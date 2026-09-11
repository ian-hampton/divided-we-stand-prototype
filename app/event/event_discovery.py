import importlib
import pkgutil
import inspect
from typing import Dict, Type

from app.scenario.scenario import ScenarioInterface as SD
from app.event.event import Event

EVENT_REGISTRY: Dict[str, Type[Event]] = {}

def discover_events():
    """
    Dynamically import all modules in the events package from the chosen scenario.

    Must be called before load_event() is used!
    ScenarioInterface will call this function so we do not have to think about it.
    """
    if EVENT_REGISTRY:
        return
    
    event_src = f"scenarios.{SD.scenario}.events"
    events = importlib.import_module(event_src)

    for loader, module_name, is_pkg in pkgutil.iter_modules(events.__path__):
        full_module_name = f"{event_src}.{module_name}"
        module = importlib.import_module(full_module_name)
        
        for name, obj in inspect.getmembers(module, inspect.isclass):
            if (
                obj.__module__ == module.__name__
                and issubclass(obj, Event)
                and obj is not Event
            ):
                key = getattr(module, "EVENT_NAME", name)
                EVENT_REGISTRY[key] = obj

def load_event(game_id: str, event_name: str, event_data: dict | None) -> Event:
    """
    Create an event object using the event name and event information.
    """
    if event_name not in EVENT_REGISTRY:
        raise Exception(f"Error: {event_name} event not recognized.")
    return EVENT_REGISTRY[event_name](game_id, event_name, event_data)

def get_event_list() -> list:
    return list(EVENT_REGISTRY.keys())
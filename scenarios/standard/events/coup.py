import random

from scenarios.standard import event_tools
from app.event.event import Event, EventState
from app.nation.nations import Nations
from app.notifications import Notifications

EVENT_NAME = "Coup"

class Coup(Event):
    
    def __init__(self, game_id: str, event_name: str, event_data: dict):
        Event.__init__(self, game_id, event_name)
        self.type = "Standard Event"
        self.duration = 0
        self.targets: list = event_data.get("Targets", [])
        self.expire_turn: int = event_data.get("Expiration", -1)

    def activate(self):
        
        lowest_economy = Nations.get_lowest_in_record("net_income")
        victim_nation_name = lowest_economy[0]
        victim_nation = Nations.get(victim_nation_name)

        old_government = victim_nation.gov
        gov_list = ["Republic", "Technocracy", "Oligarchy", "Totalitarian", "Remnant", "Protectorate", "Military Junta", "Crime Syndicate"]
        gov_list.remove(old_government)
        random.shuffle(gov_list)
        new_government = gov_list.pop()
        
        victim_nation.gov = new_government
        victim_nation.update_stockpile("Political Power", 0, overwrite=True)
        Notifications.add(f"{victim_nation_name}'s {old_government} government has been defeated by a coup. A new {new_government} government has taken power.", 3)

        self.state = EventState.FINISHED

    def has_conditions_met(self) -> bool:

        if event_tools._is_first_event(self.game_id):
            return False
        
        return True
from scenarios.standard import event_tools
from app.event.event import Event, EventState
from app.nation.nations import Nations
from app.notifications import Notifications

EVENT_NAME = "Widespread Civil Disorder"

class WidespreadCivilDisorder(Event):
    
    def __init__(self, game_id: str, event_name: str, event_data: dict):
        Event.__init__(self, game_id, event_name)
        self.type = "Standard Event"
        self.duration = 8
        self.targets: list = event_data.get("Targets", [])
        self.expire_turn: int = event_data.get("Expiration", -1)

    def activate(self):

        Notifications.add(f"New Event: {self.name}!", 3)

        for nation in Nations:
            new_tag = {
                "Expire Turn": self.game.turn + self.duration + 1
            }
            nation.tags["Civil Disorder"] = new_tag

        self.state = EventState.ACTIVE
        self.expire_turn = self.game.turn + self.duration + 1

    def has_conditions_met(self) -> bool:

        if event_tools._is_first_event(self.game_id):
            return False
        
        return True

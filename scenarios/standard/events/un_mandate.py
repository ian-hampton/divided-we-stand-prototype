from scenarios.standard import event_tools
from app.event.event import Event, EventState
from app.notifications import Notifications
from app.war.wars import Wars

EVENT_NAME = "United Nations Peacekeeping Mandate"

class UnitedNationsPeacekeepingMandate(Event):
    
    def __init__(self, game_id: str, event_name: str, event_data: dict):
        Event.__init__(self, game_id, event_name)
        self.type = "Standard Event"
        self.duration = 0
        self.targets: list = event_data.get("Targets", [])
        self.expire_turn: int = event_data.get("Expiration", -1)

    def activate(self):

        for war in Wars:
            if war.outcome == "TBD":
                war.end_conflict("White Peace")
                Notifications.add(f"{war.name} has ended with a white peace due to United Nations Peacekeeping Mandate.", 3)

        self.state = EventState.FINISHED

    def has_conditions_met(self) -> bool:

        if not event_tools._at_least_x_ongoing_wars(self.game_id, 3):
            return False
        
        return True
from app.event.event import Event, EventState
from app.nation.nations import Nations
from app.notifications import Notifications

EVENT_NAME = "Observer Status Invitation"

class ObserverStatusInvitation(Event):
    
    def __init__(self, game_id: str, event_name: str, event_data: dict):
        Event.__init__(self, game_id, event_name)
        self.type = "Standard Event"
        self.duration = 0
        self.targets: list = event_data.get("Targets", [])
        self.expire_turn: int = event_data.get("Expiration", -1)

    def activate(self):
        
        Notifications.add(f"New Event: {self.name}!", 3)
        for nation in Nations:
            self.targets.append(nation.id)
        
        self.state = EventState.PENDING

    def resolve(self):
        
        self.choices = ["Accept", "Decline"]
        print(f"Available Options: {" or ".join(self.choices)}")
        decision_dict = self._collect_basic_decisions()

        for nation_id, decision in decision_dict.items():
            
            nation = Nations.get(nation_id)
            
            if decision == "Accept":
                new_tag = {
                    "Political Power Income": 0.5,
                    "Expire Turn": 99999
                }
                nation.tags["Observer Status"] = new_tag
            
            elif decision == "Decline":
                valid_research = False
                while not valid_research:
                    research_name = input(f"Enter {nation.name} military technology decision: ")
                    valid_research = self._gain_free_research(research_name, nation)
        
        self.state = EventState.FINISHED

    def has_conditions_met(self) -> bool:
        return True
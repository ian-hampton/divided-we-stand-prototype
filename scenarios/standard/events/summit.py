from app.event.event import Event, EventState
from app.nation.nations import Nations
from app.notifications import Notifications

EVENT_NAME = "Diplomatic Summit"

class DiplomaticSummit(Event):
    
    def __init__(self, game_id: str, event_name: str, event_data: dict):
        Event.__init__(self, game_id, event_name, event_data)

    def activate(self):
        
        Notifications.add(f"New Event: {self.name}!", 3)
        for nation in Nations:
            self.targets.append(nation.id)
        
        self.state = EventState.PENDING

    def resolve(self):

        summit_attendance_list = []
        
        self.choices = ["Attend", "Decline"]
        print(f"Available Options: {" or ".join(self.choices)}")
        decision_dict = self._collect_basic_decisions()

        for nation_id, decision in decision_dict.items():
            
            nation = Nations.get(nation_id)
            
            if decision == "Attend":
                nation.update_stockpile("Political Power", 5)
                summit_attendance_list.append(nation.id)
            
            elif decision == "Decline":
                valid_research = False
                while not valid_research:
                    research_name = input(f"Enter {nation.name} military technology decision: ")
                    valid_research = self._gain_free_research(research_name, nation)
        
        if len(summit_attendance_list) < 2:
            self.state = EventState.FINISHED
            return

        for nation_id in summit_attendance_list:
            nation = Nations.get(nation_id)
            new_tag = {
                "Expire Turn": self.game.turn + self.duration + 1
            }
            for attendee_id in summit_attendance_list:
                new_tag[f"Cannot Declare War On #{attendee_id}"] = True
            nation.tags["Summit"] = new_tag
        
        self.state = EventState.ACTIVE
        self.expire_turn = self.game.turn + self.duration + 1

    def has_conditions_met(self) -> bool:
        return True

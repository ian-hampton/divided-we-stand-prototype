import random

from scenarios.standard import event_tools
from app.event.event import Event, EventState
from app.alliance.alliances import Alliances
from app.nation.nations import Nations
from app.notifications import Notifications

EVENT_NAME = "Faustian Bargain"

class FaustianBargain(Event):
    
    def __init__(self, game_id: str, event_name: str, event_data: dict):
        Event.__init__(self, game_id, event_name)
        self.type = "Major Event"
        self.duration = 99999
        self.targets: list = event_data.get("Targets", [])
        self.expire_turn: int = event_data.get("Expiration", -1)

    def activate(self):
        
        Notifications.add(f"New Event: {self.name}!", 3)
        for nation in Nations:
            self.targets.append(nation.id)
        
        self.state = EventState.PENDING

    def resolve(self):

        candidates_list = []
        
        self.choices = ["Accept", "Decline"]
        print(f"Available Options: {" or ".join(self.choices)}")
        decision_dict = self._collect_basic_decisions()

        for player_id, choice in decision_dict.items():
            nation = Nations.get(player_id)
            if choice == "Accept" and nation.improvement_counts["Capital"] > 0:
                candidates_list.append(player_id)
            else:
                nation.update_stockpile("Political Power", 5)

        if len(candidates_list) == 0:
            Notifications.add("No nation took the Faustian Bargain. collaborate with the foreign nation.", 3)
            self.state = EventState.FINISHED
            return
        
        random.shuffle(candidates_list)
        nation_id = candidates_list.pop()
        nation = Nations.get(nation_id)

        new_tag = {
            "Expire Turn": 99999,
            "No Agenda Research": True
        }
        for resource_name in nation._resources:
            if resource_name not in ["Political Power", "Military Capacity"]:
                new_tag[f"{resource_name} Rate"] = 20
        nation.tags["Faustian Bargain"] = new_tag

        for alliance in Alliances:
            if nation.name in alliance.current_members:
                alliance.remove_member(nation.name)

        Notifications.add(f"{nation.name} took the Faustian Bargain and will collaborate with the foreign nation.", 3)

        self.state = EventState.ACTIVE
        self.duration = 99999

    def run_after(self) -> None:
        
        # identify collaborator
        for nation in Nations:
            if "Faustian Bargain" in nation.tags:
                break
        
        # check if collaborator has been defeated (no capital)
        if nation.improvement_counts["Capital"] == 0:
            del nation.tags["Faustian Bargain"]
            self.state = EventState.FINISHED
            Notifications.add(f"{self.name} event has ended.", 3)
            return

        self.state = EventState.ACTIVE

    def has_conditions_met(self) -> bool:

        if event_tools._is_first_event(self.game_id):
            return False
        
        if not event_tools._no_major_events(self.game_id):
            return False
        
        return True
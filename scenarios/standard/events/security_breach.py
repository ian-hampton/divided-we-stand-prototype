from scenarios.standard import event_tools
from app.event.event import Event, EventState
from app.nation.nations import Nations
from app.notifications import Notifications

EVENT_NAME = "Security Breach"

class SecurityBreach(Event):
    
    def __init__(self, game_id: str, event_name: str, event_data: dict):
        Event.__init__(self, game_id, event_name)
        self.type = "Standard Event"
        self.duration = 4
        self.targets: list = event_data.get("Targets", [])
        self.expire_turn: int = event_data.get("Expiration", -1)

    def activate(self):

        top_three = Nations.get_top_three("technology_count")
        victim_nation_name = top_three[0][0]
        self.targets.append(victim_nation_name)

        Notifications.add(f"{victim_nation_name} has suffered a {self.name}!", 3)

        self.state = EventState.PENDING

    def resolve(self):

        victim_name = self.targets[0]
        victim_nation = Nations.get(victim_name)

        for nation in Nations:
            
            if nation.name == victim_name:
                continue

            valid_research = False
            while not valid_research:
                research_name = input(f"Enter {nation.name} technology decision: ")
                if research_name not in victim_nation.completed_research:
                    continue
                valid_research = self._gain_free_research(research_name, nation)

        new_tag = {
            "Research Rate": -20,
            "Expire Turn": self.game.turn + self.duration + 1
        }
        victim_nation.tags["Security Breach"] = new_tag
        
        self.state = EventState.ACTIVE
        self.expire_turn = self.game.turn + self.duration + 1

    def has_conditions_met(self) -> bool:

        if not event_tools._no_ranking_tie(self.game_id, "technology_count"):
            return False
        
        return True
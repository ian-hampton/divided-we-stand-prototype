from scenarios.standard import event_tools
from app.event.event import Event, EventState
from app.nation.nations import Nations
from app.notifications import Notifications
from app.war.wars import Wars

EVENT_NAME = "Peacetime Rewards"

class PeacetimeRewards(Event):
    
    def __init__(self, game_id: str, event_name: str, event_data: dict):
        Event.__init__(self, game_id, event_name, event_data)

    def activate(self):
        
        names = []
        for nation in Nations:
            if Wars.at_peace_for_x(nation.id) >= 12:
                self.targets.append(nation.id)
                names.append(nation.name)
        nations_receiving_award_str = ", ".join(names)
        
        Notifications.add(f"New Event: {self.name}!", 3)
        Notifications.add(f"Receiving reward: {nations_receiving_award_str}.", 3)
        
        self.state = EventState.PENDING

    def resolve(self):
        
        for nation_id in self.targets:
            nation = Nations.get(nation_id)
            valid_research = False
            while not valid_research:
                research_name = input(f"Enter {nation.name} technology decision: ")
                valid_research = self._gain_free_research(research_name, nation)

        self.state = EventState.FINISHED

    def has_conditions_met(self) -> bool:

        if not event_tools._at_least_x_nations_at_peace_for_y_turns(self.game_id, 1, 12):
            return False
        
        return True
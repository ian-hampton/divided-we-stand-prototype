import random

from scenarios.standard import event_tools
from app.event.event import Event, EventState
from app.nation.nations import Nations
from app.notifications import Notifications
from app.region.regions import Regions

EVENT_NAME = "Decaying Infrastructure"

class DecayingInfrastructure(Event):
    
    def __init__(self, game_id: str, event_name: str, event_data: dict):
        Event.__init__(self, game_id, event_name)
        self.type = "Standard Event"
        self.duration = 0
        self.targets: list = event_data.get("Targets", [])
        self.expire_turn: int = event_data.get("Expiration", -1)

    def activate(self):

        top_three = Nations.get_top_three("nation_size")
        top_three_ids = set()
        for nation_name, nation_size in top_three:
            temp = Nations.get(nation_name)
            top_three_ids.add(temp.id)

        for region in Regions:
            if region.data.owner_id in top_three_ids and region.improvement.name is not None and region.improvement.name != "Capital":
                decay_roll = random.randint(1, 10)
                if decay_roll >= 9:
                    nation = Nations.get(region.data.owner_id)
                    nation.improvement_counts[region.improvement.name] -= 1
                    Notifications.add(f"{nation.name} {region.improvement.name} in {region.id} has decayed.", 3)
                    region.improvement.clear()

        self.state = EventState.FINISHED

    def has_conditions_met(self) -> bool:

        if event_tools._is_first_event(self.game_id):
            return False
        
        return True

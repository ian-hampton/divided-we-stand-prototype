import random

from scenarios.standard import event_tools
from app.event.event import Event, EventState
from app.region.regions import Regions
from app.nation.nations import Nations
from app.notifications import Notifications

EVENT_NAME = "Power Plant Meltdown"

class PowerPlantMeltdown(Event):
    
    def __init__(self, game_id: str, event_name: str, event_data: dict):
        Event.__init__(self, game_id, event_name, event_data)

    def activate(self):
        
        for region in Regions:
            if region.improvement.name == "Nuclear Power Plant":
                self.targets.append(region.id)
        random.shuffle(self.targets)
        meltdown_region_id = self.targets.pop()

        nation = Nations.get(str(meltdown_region_id))
        region = Regions.load(meltdown_region_id)

        nation.improvement_counts["Nuclear Power Plant"] -= 1
        region.improvement.clear()
        if region.unit.name is not None:
            nation.unit_counts[region.unit.name] -= 1
            region.unit.clear()
        region.data.fallout = 99999
        
        nation.update_stockpile("Political Power", 0, overwrite=True)
        Notifications.add(f"The {nation.name} Nuclear Power Plant in {meltdown_region_id} has melted down!", 3)
        
        self.state = EventState.FINISHED

    def has_conditions_met(self) -> bool:

        if not event_tools._global_count_of_x_improvement_at_least_y(self.game_id, "Nuclear Power Plant", 1):
            return False

        return True

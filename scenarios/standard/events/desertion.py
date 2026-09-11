import random

from scenarios.standard import event_tools
from app.event.event import Event, EventState
from app.region.regions import Regions
from app.nation.nations import Nations
from app.notifications import Notifications
from app.war.wars import Wars

EVENT_NAME = "Desertion"

class Desertion(Event):
    
    def __init__(self, game_id: str, event_name: str, event_data: dict):
        Event.__init__(self, game_id, event_name)
        self.type = "Standard Event"
        self.duration = 0
        self.targets: list = event_data.get("Targets", [])
        self.expire_turn: int = event_data.get("Expiration", -1)

    def activate(self):

        # retrieve lowest warscore for each nation
        lowest_warscore_dict = {}
        for nation in Nations:
            if Wars.is_at_peace(nation.id):
                continue
            lowest_warscore = 99999
            for war in Wars:
                if war.outcome != "TBD" or nation.id not in war.combatants:
                    continue
                nation_combatant_data = war.get_combatant(nation.id)
                score = war.attackers.total if "Attacker" in nation_combatant_data.role else war.defenders.total
                if score < lowest_warscore:
                    lowest_warscore = score
            lowest_warscore_dict[nation.id] = lowest_warscore
        
        # all nations with the lowest warscore are targets of this event
        min_value = min(lowest_warscore_dict.values())
        filtered_dict = {}
        for nation_id, defection_data in lowest_warscore_dict.items():
            if defection_data["lowestScore"] == min_value:
                filtered_dict[nation_id] = defection_data
        self.targets = list(filtered_dict.keys())
        
        # check all regions owned by targets
        for region_id in Regions:
            region = Regions.load(region_id)
            if region.unit.owner_id not in self.targets:
                continue
            defection_roll = random.randint(1, 10)
            if defection_roll >= 9:
                nation = Nations.get(region.unit.owner_id)
                nation.unit_counts[region.unit.name] -= 1
                Notifications.add(f"{nation.name} {region.unit.name} {region_id} has deserted.", 3)
                region.unit.clear()
        
        self.state = EventState.FINISHED

    def has_conditions_met(self) -> bool:

        if not event_tools._at_least_x_ongoing_wars(self.game_id, 1):
            return False

        return True

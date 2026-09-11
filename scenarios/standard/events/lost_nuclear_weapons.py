from app.event.event import Event, EventState
from app.region.regions import Regions
from app.nation.nations import Nations
from app.notifications import Notifications

EVENT_NAME = "Lost Nuclear Weapons"

class LostNuclearWeapons(Event):
    
    def __init__(self, game_id: str, event_name: str, event_data: dict):
        Event.__init__(self, game_id, event_name)
        self.type = "Standard Event"
        self.duration = 0
        self.targets: list = event_data.get("Targets", [])
        self.expire_turn: int = event_data.get("Expiration", -1)

    def activate(self):

        victim_player_id = Nations.get_random_id()
        victim_nation = Nations.get(victim_player_id)
        self.targets.append(victim_nation.id)

        Notifications.add(f"{victim_nation.name} has been randomly selected as the target for the {self.name} event!", 3)

        self.state = EventState.PENDING

    def resolve(self):
        
        self.choices = ["Claim", "Scuttle"]
        print(f"Available Options: {" or ".join(self.choices)}")
        decision_dict = self._collect_basic_decisions()

        for nation_id, decision in decision_dict.items():
            
            nation = Nations.get(nation_id)
            
            if decision == "Claim":
                valid_region_id = False
                while not valid_region_id:
                    silo_location_id = input("Enter region id for Missile Silo: ")
                    silo_location_id = silo_location_id.upper()
                    if silo_location_id in set(Regions.ids()):
                        valid_region_id = True
                nation.improvement_counts["Missile Silo"] += 1
                region = Regions.load(valid_region_id)
                region.improvement.set("Missile Silo")
                nation.nuke_count += 3
            
            elif decision == "Scuttle":
                nation.update_stockpile("Research", 15)
            
            Notifications.add(f"{nation.name} chose to {decision.lower()} the old military installation.", 3)
        
        self.state = EventState.FINISHED

    def has_conditions_met(self) -> bool:
        return True
import random

from scenarios.standard import event_tools
from app.event.event import Event, EventState
from app.region.regions import Regions
from app.nation.nations import Nations
from app.notifications import Notifications

EVENT_NAME = "Pandemic"

class Pandemic(Event):
    
    def __init__(self, game_id: str, event_name: str, event_data: dict):
        Event.__init__(self, game_id, event_name, event_data)
        self.intensify: int = event_data.get("Intensify Value", -1)
        self.spread: int = event_data.get("Spread Value", -1)
        self.cure_current: int = event_data.get("Completed Cure Research", -1)
        self.cure_threshold: int = event_data.get("Needed Cure Research", 99999)
        self.closed_borders: list = event_data.get("Closed Borders List", [])

    def activate(self):
        
        Notifications.add(f"New Event: {self.name}!", 3)
            
        self.intensify = random.randint(3, 9)
        self.spread = random.randint(3, 9)
        self.cure_current = 0
        self.cure_threshold = len(Nations) * 50
        self.closed_borders = []
        origin_region_id = random.choice(Regions.ids())
        
        region = Regions.load(origin_region_id)
        region.data.infection += 1
        
        self.state = EventState.ACTIVE
        self.expire_turn = 99999

    def run_after(self) -> None:
        
        if self.cure_current >= self.cure_threshold:
            
            # run pandemic decline procedure
            for region in Regions:
                region.data.infection -= 1

        else:

            # conduct intensify rolls
            for region in Regions:
                if region.data.infection > 0 and region.data.infection < 10:
                    # intensify check
                    intensify_roll = random.randint(1, 10)
                    if intensify_roll < self.intensify:
                        continue
                    # intensify more if near capital or city
                    if region.check_for_adjacent_improvement(improvement_names = {'Capital', 'City'}):
                        region.data.infection += 2
                    else:
                        region.data.infection += 1

            # get a list of regions infected before spreading starts
            infected_regions = []
            for region in Regions:
                if region.data.infection > 0:
                    infected_regions.append(region.id)

            # conduct spread roles
            for region_id in infected_regions:
                region = Regions.load(region_id)
                if region.data.infection == 0:
                    continue
                for adjacent_region in region.graph.iter_adjacent_regions():
                    adjacent_owner_id = adjacent_region.data.owner_id
                    # spread only to regions that are not yet infected
                    if adjacent_region.data.infection != 0:
                        continue
                    spread_roll = random.randint(1, 20)
                    # spread attempt
                    if not region.data.quarantine or (region.data.owner_id != adjacent_owner_id and adjacent_owner_id in self.closed_borders):
                        if spread_roll == 20:
                            adjacent_region.data.infection += 1
                    else:
                        if spread_roll >= self.spread:
                            adjacent_region.data.infection += 1

        # sum up total infection scores
        unowned_infection = 0
        infection_scores = [0] * len(Nations)
        for region in Regions:
            if region.data.owner_id != "0" and region.data.owner_id <= len(infection_scores):
                infection_scores[int(region.data.owner_id) - 1] += region.data.infection
            else:
                unowned_infection += region.data.infection
        # check if pandemic has been eradicated
        infection_total = sum(infection_scores) + unowned_infection
        if infection_total == 0:
            for region in Regions:
                region.data.quarantine = False
            Notifications.add("The pandemic has been eradicated!", 3)
            self.state = EventState.FINISHED
            return
        
        # print diplomacy log messages
        cure_percentage = float(self.cure_current / self.cure_threshold)
        cure_percentage = round(cure_percentage, 2)
        if infection_total != 0:
            if cure_percentage >= 0.5:
                Notifications.add(f"Pandemic intensify value: {self.intensify}", 3)
                Notifications.add(f"Pandemic spread value: {self.spread}", 3)
            if cure_percentage >= 0.75:
                for nation in Nations:
                    score = infection_scores[int(nation.id) - 1]
                    Notifications.add(f"{nation.name} pandemic infection score: {score}", 3)
            if cure_percentage < 1:
                Notifications.add(f"Pandemic cure research progress: {self.cure_current}/{self.cure_threshold}", 3)
            else:
                Notifications.add(f"Pandemic cure research has been completed! The pandemic is now in decline.", 3)

        self.state = EventState.ACTIVE

    def export(self) -> dict:
        
        return {
            "Name": self.name,
            "Type": self.type,
            "Duration": self.duration,
            "Targets": self.targets,
            "Expiration": self.expire_turn,
            "Intensify Value": self.intensify,
            "Spread Value": self.spread,
            "Completed Cure Research": self.cure_current,
            "Needed Cure Research": self.cure_threshold,
            "Closed Borders List": self.closed_borders
        }

    def has_conditions_met(self) -> bool:

        if event_tools._is_first_event(self.game_id):
            return False
        
        if not event_tools._no_major_events(self.game_id):
            return False
        
        return True
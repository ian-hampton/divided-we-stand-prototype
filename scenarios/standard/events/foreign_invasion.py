import random

from app.scenario.scenario import ScenarioInterface as SD
from app import actions
from app import palette
from scenarios.standard import event_tools
from app.event.event import Event, EventState
from app.region.regions import Regions
from app.nation.nations import Nations
from app.notifications import Notifications
from app.war.wars import Wars

EVENT_NAME = "Foreign Invasion"

class ForeignInvasion(Event):
    
    def __init__(self, game_id: str, event_name: str, event_data: dict):
        Event.__init__(self, game_id, event_name, event_data)

    def activate(self):
        
        Notifications.add(f"New Event: {self.name}!", 3)

        region_id_list = Regions.ids()
        invasion_point_id = None

        while True:
            
            invasion_point_id = random.choice(region_id_list)
            region = Regions.load(invasion_point_id)
            is_near_capital = any(adj_region.improvement.name == "Capital" for adj_region in region.graph.iter_adjacent_regions())
            if region.graph.is_edge and region.improvement.name != "Capital" and not is_near_capital:
                break
        
        color_candidates = list(palette.normal_to_occupied.keys())
        for nation in Nations:
            color_candidates.remove(nation.color)

        Nations.create("99", "NULL")
        foreign_invasion_nation = Nations.get("99")
        foreign_invasion_nation.color = random.choice(color_candidates)
        foreign_invasion_nation.name = "Foreign Adversary"
        foreign_invasion_nation.gov = "Foreign Nation"
        foreign_invasion_nation.fp = "Hostile"

        # note - all war justifications are set to null because this is not a conventional war
        Wars.create("99", "1", "NULL", [])
        war = Wars.get("Foreign Invasion")
        for nation in Nations:
            if nation.id == "1":
                combatant = war.get_combatant(nation.id)
                combatant.justification = "NULL"
            else:
                war.add_combatant(nation, "Secondary Defender", "N/A")
                combatant = war.get_combatant(nation.id)
                combatant.justification = "NULL"

        unit_name = self._foreign_invasion_determine_unit()
        invasion_point = Regions.load(invasion_point_id)
        self._foreign_invasion_initial_spawn(invasion_point_id, unit_name)
        for adj_id in invasion_point.graph.adjacent_regions:
            self._foreign_invasion_initial_spawn(adj_id, unit_name)
        
        self.state = EventState.ACTIVE
        self.expire_turn = self.game.turn + self.duration + 1

    def run_before(self, actions_dict: dict[str, list]) -> None:
        
        # generate movement actions
        destination_dict = {}
        for region in Regions:
            if region.unit.name is None or region.unit.owner_id != "99":
                continue
            ending_region_id, priority = self._foreign_invasion_calculate_target_region(list(region.graph.adjacent_regions.keys()), destination_dict)
            destination_dict[ending_region_id] = priority
            if ending_region_id is None:
                continue
            # foreign invasion always moves each unit one region at a time
            movement_action_str = f"Move {region.id}-{ending_region_id}"
            actions_dict["UnitMoveAction"].append(actions.UnitMoveAction(self.game_id, "99", movement_action_str))
        
        # generate deployment actions
        if self.game.turn % 4 == 0:
            Notifications.add("The Foreign Invasion has received reinforcements.", 3)
            for region in Regions:
                if region.data.owner_id == "99" and region.data.occupier_id == "0":
                    unit_name = self._foreign_invasion_determine_unit()
                    deploy_action_str = f"Deploy {unit_name} {region.id}"
                    actions_dict["UnitDeployAction"].append(actions.UnitDeployAction(self.game_id, "99", deploy_action_str))

        self.state = EventState.ACTIVE

    def run_after(self) -> None:
        
        foreign_invasion_nation = Nations.get("99")
                    
        # Foreign Invasion ends if no remaining units
        invasion_unit_count = 0
        for unit_name, count in foreign_invasion_nation.unit_counts.items():
            invasion_unit_count += count
        if invasion_unit_count == 0:
            self._foreign_invasion_end()
            self.state = EventState.FINISHED
            return
        
        # Foreign Invasion ends if no unoccupied reinforcement regions
        invasion_unoccupied_count = 0
        for region in Regions:
            if region.data.owner_id == "99" and region.data.occupier_id == "0":
                invasion_unoccupied_count += 1
        if invasion_unoccupied_count == 0:
            self._foreign_invasion_end()
            self.state = EventState.FINISHED
            return

        self.state = EventState.ACTIVE

    def has_conditions_met(self) -> bool:

        if event_tools._is_first_event(self.game_id):
            return False
        
        if not event_tools._no_major_events(self.game_id):
            return False
        
        return True
    
    def _foreign_invasion_determine_unit(self) -> str:

        if self.game.turn >= 40:
            return "Main Battle Tank"
        elif self.game.turn >= 32:
            return "Special Forces"
        elif self.game.turn >= 24:
            return "Mechanized Infantry"
        
        return "Infantry"
    
    def _foreign_invasion_initial_spawn(self, region_id: str, unit_name: str) -> None:

        region = Regions.load(region_id)
        unit_sd = SD.units[unit_name]

        if region.unit.name is not None:
            # remove old unit
            if region.unit.owner_id != "0":
                temp = Nations.get(region.unit.owner_id)
                temp.unit_counts[region.unit.name] -= 1
            region.unit.clear()

        if region.improvement.name is not None:
            # remove old improvement
            if region.data.owner_id != "0":
                temp = Nations.get(region.data.owner_id)
                temp.improvement_counts[region.improvement.name] -= 1
            region.improvement.clear()

        region.data.owner_id = "99"
        region.data.occupier_id = "0"
        region.unit.set(unit_name, unit_sd.abbreviation, 0, "99")

        foreign_nation = Nations.get("99")
        foreign_nation.unit_counts[unit_name] += 1

    def _foreign_invasion_calculate_target_region(self, adjacency_list: list, destination_dict: dict) -> tuple:
        """
        Function that contains Foreign Invasion attack logic.
        Designed to find path of least resistance but has no care for the health of its own units.
        """

        # TODO: make movement smarter as it currently can only "see" one region away so the invasion is stumbling around blind
        
        target_region_id = None
        target_region_health = 0
        target_region_priority = -1

        while adjacency_list != []:

            # get random adjacent region
            index = random.randrange(len(adjacency_list))
            adjacent_region_id = adjacency_list.pop(index)

            # get data from region
            region = Regions.load(adjacent_region_id)
            candidate_region_priority = 0
            candidate_region_health = 0
            
            # increase priority based on control data
            # occupied friendly is the highest priority
            if region.data.owner_id == "99" and region.data.occupier_id != "0":
                candidate_region_priority += 10
            # unoccupied unclaimed region
            elif region.data.owner_id == "0" and region.data.occupier_id != "99":
                candidate_region_priority += 4
            # occupied unclaimed region
            elif region.data.owner_id == "0":
                candidate_region_priority += 2
            # friendly unoccupied region
            elif region.data.owner_id == "99":
                candidate_region_priority += 0
            # unoccupied enemy region
            elif region.data.owner_id != "99" and region.data.occupier_id != "99":
                candidate_region_priority += 8
            # occupied enemy region
            elif region.data.owner_id != "99":
                candidate_region_priority += 6
            
            # increase priority by one if there is a hostile unit
            if region.unit.name != None and region.unit.owner_id != "0":
                candidate_region_priority += 1

            # try to prevent units from tripping over each other on unclaimed regions and friendly unoccupied regions
            if adjacent_region_id in destination_dict and (candidate_region_priority == 0 or candidate_region_priority == 2 or candidate_region_priority == 4):
                continue
            
            # calculate region health
            if region.improvement.name != None and region.improvement.health != "99" and region.data.owner_id != "99" and region.data.occupier_id != "99":
                candidate_region_health += region.improvement.health
            if region.unit.name != None and region.unit.owner_id != "0":
                candidate_region_health += region.unit.health
            
            #check if candidate region is an easier or higher priority target
            if candidate_region_priority > target_region_priority:
                target_region_id = adjacent_region_id
                target_region_health = candidate_region_health
                target_region_priority = candidate_region_priority
            elif candidate_region_priority == target_region_priority and candidate_region_health < target_region_health:
                target_region_id = adjacent_region_id
                target_region_health = candidate_region_health
                target_region_priority = candidate_region_priority
        
        return target_region_id, target_region_priority

    def _foreign_invasion_end(self):

        foreign_invasion_nation = Nations.get("99")
    
        for region in Regions:
            
            if region.data.owner_id == "99":
                region.data.owner_id = "0"
                region.data.occupier_id = "0"
            elif region.data.occupier_id == "99":
                region.data.occupier_id = "0"
            
            if region.unit.owner_id == "99":
                foreign_invasion_nation.unit_counts[region.unit.name] -= 1
                region.unit.clear()

            war = Wars.get("Foreign Invasion")
            war.end = self.game.turn
            war.outcome = "White Peace"
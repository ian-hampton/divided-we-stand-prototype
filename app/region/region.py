import copy
import json
from collections import deque

from app.game.games import Games
from app.nation.nation import Nation
from .improvement import ImprovementData
from .unit import UnitData

class Region:

    def __init__(self, region_id: str, data: dict, graph: dict, game_id: str):
        self.id = region_id
        self._data = data
        self.game_id = game_id
        
        self.data = RegionData(self._data["regionData"])
        self.graph = GraphData(graph)
        self.improvement = ImprovementData(self._data["improvementData"])
        self.unit = UnitData(self._data["unitData"])

        self.claim_list = []

    def __eq__(self, other):
        if isinstance(other, Region):
            return self.id == other.id
        return False
    
    def __lt__(self, other: 'Region'):
        return self.id < other.id
    
    def __hash__(self):
        return hash(self.id)

    def __str__(self):
        return f"R[{self.id}]"
    
    def __repr__(self):
        return self.__str__()

    def get_regions_in_radius(self, radius: int) -> set:
        
        queue = deque([(self, 0)])
        visited = set([self.id])
        
        while queue:
            
            region, depth = queue.popleft()
            
            if depth < radius:
                
                for adj_region in region.graph.iter_adjacent_regions():
                    if adj_region.id not in visited:
                        visited.add(adj_region.id)
                        queue.append((adj_region, depth + 1))
        
        return visited

    def check_for_adjacent_improvement(self, improvement_names: set) -> bool:
        for adj_region in self.graph.iter_adjacent_regions():
            if adj_region.data.owner_id != self.data.owner_id:
                continue
            if adj_region.improvement.name in improvement_names:
                return True
        return False
    
    def check_for_adjacent_unit(self, unit_names: set, desired_id: str) -> bool:
        for adj_region in self.graph.iter_adjacent_regions():
            if desired_id != adj_region.unit.owner_id:
                continue
            if adj_region.unit.name is None:
                continue
            if adj_region.unit.name in unit_names:
                return True
        return False

    def find_suitable_region(self) -> str | None:
        """
        Identifies a region for the unit in this region to withdraw to.

        Returns:
            str: Suitable region_id if found, otherwise None.
        """

        queue = deque([self])
        visited = set()

        while queue:
            
            region = queue.popleft()

            if region.id in visited:
                continue
            visited.add(region.id)

            if (
                region.data.owner_id == self.unit.owner_id    # region must be owned by the unit owner
                and region.unit.name is None                  # region must not have another unit in it
                and region.data.occupier_id == "0"            # region must not be occupied by another nation
            ):
                return region.id
            
            for adj_region in region.graph.iter_adjacent_regions():
                if adj_region.id not in visited:
                    queue.append(adj_region)

        return None

    def add_claim(self, player_id: str) -> None:
        """
        Adds player id to claim list. Used for region claim public action.
        """
        self.claim_list.append(player_id)

    def calculate_region_claim_cost(self, nation: 'Nation'):
        """
        Calculates cost of claiming a region for a specific nation.
        """
        
        cost_multiplier = 1.0
        for tag_data in nation.tags.values():
            cost_multiplier += float(tag_data.get("Region Claim Cost", 0))
    
        return int(self.data.purchase_cost * cost_multiplier)

    def set_fallout(self, starting_fallout=4) -> None:
        self.data.fallout = starting_fallout

    def is_valid_move(self, other_player_id: int) -> bool:
        """
        Determines if a unit owned by other_player_id can move into this region.
        Only takes into account ownership. Does not consider adjacency or other disqualifiers, that is the job of the move action function.

        Params:
            other_player_id (int): player_id to compare to
        
        Returns:
            bool: True if all checks pass. False otherwise.
        """
        from app.war.wars import Wars

        # you can always move into regions owned by you
        if self.data.owner_id == other_player_id:
            return True

        # you may move into unoccupied regions owned by an enemy
        if Wars.get_war_name(self.data.owner_id, other_player_id) is not None and self.data.occupier_id == "0":
            return True
        # or you may move into occupied regions owned by an enemy in two cases
        elif Wars.get_war_name(self.data.owner_id, other_player_id) is not None and self.data.occupier_id != "0":
            # you are the occupier
            if self.data.occupier_id == other_player_id:
                return True
            # you are also at war with the occupier
            if Wars.get_war_name(self.data.owner_id, other_player_id) is not None:
                return True
            
        # foreign invasion may move into unclaimed regions
        if self.data.owner_id == "0" and other_player_id == "99":
            return True
                
        return False

    def improvement_is_hostile(self, other_player_id: str) -> bool:

        # regions without an improvement cannot have a hostile improvement
        if self.improvement.name is None:
            return False

        # improvements with no health can never be hostile
        if not self.improvement.has_health:
            return False

        if self.data.owner_id == other_player_id and self.data.occupier_id == "0":
            # defensive improvements in a region that is owned by you and is unoccupied is never hostile
            return False
        elif self.data.owner_id != other_player_id:
            # defensive improvements in a region you don't own are not hostile if you already occupy the region
            if other_player_id != "0" and self.data.occupier_id == other_player_id:
                return False
        
        return True

    def move_unit(self, target_region: Region, *, withdraw=False) -> bool:
        """
        Attempts to move the unit in this region to the target region.

        Params:
            target_region (Region): Region object of target region (where this unit is moving to)
            withdraw: True if withdraw action. False otherwise.
        
        Returns:
            bool: True if action succeeded, False otherwise.
        """
        from app.combat.combat import CombatProcedure
        from app.combat.experience import ExperienceRewards

        def execute_move() -> None:
            # update region occupation
            if attacker_id != defender_id:
                self.unit.add_xp(ExperienceRewards.FROM_OCCUPATION)
                target_region.data.occupier_id = self.unit.owner_id
            elif target_region.data.occupier_id != "0":
                self.unit.add_xp(ExperienceRewards.FROM_OCCUPATION)
                target_region.data.occupier_id = "0"
            # move attacking unit
            target_region.unit.set(self.unit.name, self.unit.full_name, self.unit.xp, self.unit.owner_id, self.unit.health)
            target_region.unit.has_been_attacked = self.unit.has_been_attacked
            target_region.unit.has_movement_queued = self.unit.has_movement_queued
            self.unit.clear()

        # withdraw moves need not conduct combat
        if withdraw:
            execute_move()
            return True
        
        # conduct combat
        combat = CombatProcedure(self, target_region)
        combat.resolve()

        # check if unit can move
        if not combat.is_able_to_move():
            return False

        # execute move
        attacker_id = self.unit.owner_id
        defender_id = target_region.data.owner_id
        execute_move()
        combat.pillage()
        return True

    def calculate_yield(self, game_id: str, nation: Nation, improvement_income_dict: dict) -> dict:
        """
        Calculates the final yield of this improvement.

        Params:
            improvement_income_dict (dict): Contains the income and multiplier of this improvement type. From yield_dict.

        Returns:
            dict: Contains all yields from this improvement.
        """

        game = Games.load(game_id)

        improvement_income_dict = copy.deepcopy(improvement_income_dict)  # deepcopy required because of modifiers below

        # get modifer from central banks
        if self.improvement.name != "Capital" and self.check_for_adjacent_improvement(improvement_names={"Central Bank"}):
            for resource_name in improvement_income_dict:
                improvement_income_dict[resource_name]["Income Multiplier"] += 0.2

        # get modifer from remnant government
        capital_boost = any("Capital Boost" in tag_data for tag_data in nation.tags.values())
        if capital_boost and self.check_for_adjacent_improvement(improvement_names = {'Capital'}):
            for resource_name in improvement_income_dict:
                if resource_name in ["Political Power", "Military Capacity"]:
                    continue
                improvement_income_dict[resource_name]["Income Multiplier"] += 1.0
        
        # get pandemic multiplier
        if "Pandemic" in game.active_events:
            for resource_name in improvement_income_dict:
                multiplier = improvement_income_dict[resource_name]["Income Multiplier"]
                penalty = 0
                if self.data.infection > 0:
                    penalty += self.data.infection * 0.1
                if self.data.quarantine:
                    penalty += 0.5
                multiplier -= penalty
                if multiplier < 0:
                    multiplier = 0
                improvement_income_dict[resource_name]["Income Multiplier"] = multiplier

        # get income modifiers from tags
        for tag_name, tag_data in nation.tags.items():
            if "Improvement Income" not in tag_data:
                continue
            for improvement_name, resource_data in tag_data["Improvement Income"].items():
                if improvement_name != self.improvement.name:
                    continue
                for resource_name, income_modifier in resource_data.items():
                    improvement_income_dict[resource_name]["Income"] += income_modifier
        
        # get income multiplier modifiers from tags
        for tag_name, tag_data in nation.tags.items():
            if "Improvement Income Multiplier" not in tag_data:
                continue
            for improvement_name, resource_data in tag_data["Improvement Income Multiplier"].items():
                if improvement_name != self.improvement.name:
                    continue
                for resource_name, income_modifier in resource_data.items():
                    improvement_income_dict[resource_name]["Income Multiplier"] += income_modifier
        
        # get capital resource if able
        # TODO - find a way to not hard code this check
        if self.improvement.name == "Capital" and self.data.resource != "Empty":
            match self.data.resource:
                case "Coal":
                    if 'Coal Mining' in nation.completed_research:
                        improvement_income_dict[self.data.resource]["Income"] += 1
                case "Oil":
                    if 'Oil Drilling' in nation.completed_research:
                        improvement_income_dict[self.data.resource]["Income"] += 1
                case "Basic Materials":
                    improvement_income_dict[self.data.resource]["Income"] += 1
                case "Common Metals":
                    if 'Metal Extraction' in nation.completed_research:
                        improvement_income_dict[self.data.resource]["Income"] += 1
                case "Advanced Metals":
                    if 'Metallurgy' in nation.completed_research:
                        improvement_income_dict[self.data.resource]["Income"] += 1
                case "Uranium":
                    if 'Uranium Mining' in nation.completed_research:
                        improvement_income_dict[self.data.resource]["Income"] += 1
                case "Rare Earth Elements":
                    if 'Rare Earth Mining' in nation.completed_research:
                        improvement_income_dict[self.data.resource]["Income"] += 1
        
        # calculate final income
        final_yield_dict = {}
        for resource_name in improvement_income_dict:
            final_yield = improvement_income_dict[resource_name]["Income"] * improvement_income_dict[resource_name]["Income Multiplier"]
            final_yield_dict[resource_name] = final_yield

        return final_yield_dict

class RegionData:

    # TODO: move infection and quarantine code to scenario file somehow

    def __init__(self, d: dict):
        self._data = d

    @property
    def owner_id(self) -> str:
        return self._data["ownerID"]
    
    @owner_id.setter
    def owner_id(self, new_id: str) -> None:
        self._data["ownerID"] = new_id
    
    @property
    def occupier_id(self) -> str:
        return self._data["occupierID"]
    
    @occupier_id.setter
    def occupier_id(self, new_id: str) -> None:
        self._data["occupierID"] = new_id
    
    @property
    def purchase_cost(self) -> int:
        return self._data["purchaseCost"]
    
    @purchase_cost.setter
    def purchase_cost(self, value: int) -> None:
        self._data["purchaseCost"] = value
    
    @property
    def resource(self) -> str:
        return self._data["regionResource"]
    
    @resource.setter
    def resource(self, value: str) -> None:
        self._data["regionResource"] = value
    
    @property
    def fallout(self) -> int:
        return self._data["nukeTurns"]
    
    @fallout.setter
    def fallout(self, value: int) -> None:
        self._data["nukeTurns"] = value

    @property
    def infection(self) -> int:
        return self._data["infection"]
    
    @infection.setter
    def infection(self, value: int) -> None:
        self._data["infection"] = value

    @property
    def quarantine(self) -> bool:
        return self._data["quarantine"]
    
    @quarantine.setter
    def quarantine(self, value: bool) -> None:
        self._data["quarantine"] = value

class GraphData:
        
    def __init__(self, d: dict):
        self.full_name: str = d["fullName"]
        self.is_edge: bool = d["isEdgeOfMap"]
        self.is_significant: bool = d["hasRegionalCapital"]
        self.is_magnified: bool = d["isMagnified"]
        self.is_start: bool = d["randomStartAllowed"]
        self.map: dict[str] = d.get("adjacencyMap", {})
        self.sea_routes: dict[str] = d.get("seaRoutes", {})
        self.adjacent_regions: dict[str] = self.map | self.sea_routes
        self.additional_region_coordinates: list = d["additionalRegionCords"]
        self.improvement_coordinates: list = d["improvementCords"]
        self.unit_coordinates: list = d["unitCords"]

    def iter_adjacent_regions(self):
        from .regions import Regions
        for region_id in self.adjacent_regions:
            yield Regions.load(region_id)
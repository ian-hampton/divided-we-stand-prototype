import copy
import json
import os
from collections import deque
from dataclasses import dataclass
from typing import ClassVar

import core
from app.nationdata import Nation
from app.nationdata import NationTable

@dataclass
class Regions:

    game_id: ClassVar[str]
    _data: ClassVar[dict[str, dict]] = None
    _graph: ClassVar[dict[str, dict]] = None

    @classmethod
    def load(cls, game_id: str):
        cls.game_id = game_id
        regdata_filepath = f"gamedata/{Regions.game_id}/regdata.json"
        graph_filepath = f"maps/{core.get_map_str(Regions.game_id)}/graph.json"
        
        if not (os.path.exists(regdata_filepath) and os.path.exists(graph_filepath)):
            raise FileNotFoundError(f"Error: Unable to locate required game files for Regions class.")
        
        with open(regdata_filepath, 'r') as f:
            cls._data = json.load(f)
        with open(graph_filepath, 'r') as f:
            cls._graph = json.load(f)
    
    @classmethod
    def save(cls):
        if cls._data is None:
            raise RuntimeError("Error: Regions data not loaded.")
        
        regdata_filepath = f"gamedata/{cls.game_id}/regdata.json"
        
        with open(regdata_filepath, 'w') as json_file:
            json.dump(cls._data, json_file, indent=4)
    
    @classmethod
    def __iter__(cls):
        for region_id in cls._graph:
            yield Region(region_id)

class Region:

    def __init__(self, region_id: str):

        if Regions.game_id is None:
            raise RuntimeError("Error: Error: Regions data not loaded.")

        self.game_id = Regions.game_id

        self.region_id = region_id
        self.claim_list = []
        self.data = RegionData(Regions._data[self.region_id]["regionData"])
        self.graph = GraphData(Regions._graph[self.region_id])
        self.improvement = ImprovementData(
            Regions._data[self.region_id]["improvementData"],
            self.graph
        )
        self.unit = UnitData(
            Regions._data[self.region_id]["unitData"],
            self.graph
        )

    def __eq__(self, other):
        if isinstance(other, Region):
            return self.region_id == other.region_id
        return False
    
    def owned_adjacent_regions(self) -> list:
        owned_adjacent_list = []
        for region_id in self.graph.adjacent_regions:
            temp = Region(region_id)
            if temp.data.owner_id == self.data.owner_id:
                owned_adjacent_list.append(region_id)
        return owned_adjacent_list
    
    def get_regions_in_radius(self, radius: int) -> set:
        
        visited = set([self.region_id])
        queue = deque([(self.region_id, 0)])
        
        while queue:
            
            current_region_id, depth = queue.popleft()
            
            if depth < radius:
                
                current_region = Region(current_region_id)
                
                for adjacent_id in current_region.graph.adjacent_regions:
                    if adjacent_id not in visited:
                        visited.add(adjacent_id)
                        queue.append((adjacent_id, depth + 1))
        
        return visited

    def check_for_adjacent_improvement(self, improvement_names: set) -> bool:
        for region_id in self.owned_adjacent_regions():
            adjacent_region = Region(region_id)
            if adjacent_region.improvement.name in improvement_names:
                return True
        return False
    
    def check_for_adjacent_unit(self, unit_names: set, desired_id: str) -> bool:
        for region_id in self.graph.adjacent_regions:
            adjacent_region = Region(region_id)
            if adjacent_region.unit.name is None:
                continue
            if desired_id != adjacent_region.unit.owner_id:
                continue
            if adjacent_region.unit.name in unit_names:
                return True
        return False

    def find_suitable_region(self) -> str | None:
        """
        Identifies a region for the unit in this region to withdraw to.

        Returns:
            str: Suitable region_id if found, otherwise None.
        """

        queue = deque([self.region_id])
        visited = set()

        while queue:
            
            current_region_id = queue.popleft()

            if current_region_id in visited:
                continue
            visited.add(current_region_id)

            current_region = Region(current_region_id)

            if (
                current_region.data.owner_id == self.unit.owner_id    # region must be owned by the unit owner
                and current_region.unit.name is None                  # region must not have another unit in it
                and current_region.data.occupier_id == "0"            # region must not be occupied by another nation
            ):
                return current_region_id
            
            for adjacent_id in current_region.graph.adjacent_regions:
                if adjacent_id not in visited:
                    queue.append(adjacent_id)

        return None

    def add_claim(self, player_id: str) -> None:
        """
        Adds player id to claim list. Used for region claim public action.
        """
        self.claim_list.append(player_id)

    def set_fallout(self, starting_fallout=4) -> None:
        self.data.fallout = starting_fallout

    def is_valid_move(self, other_player_id: int) -> bool:
        """
        Determines if a unit owned by other_player_id can move into this region.
        Only takes into account ownership. Does not consider adjacency or other disqualifiers.

        Params:
            other_player_id (int): player_id to compare to
        
        Returns:
            bool: True if all checks pass. False otherwise.
        """
        
        from app.war import WarTable
        war_table = WarTable(self.game_id)

        # you can always move into regions owned by you
        if self.data.owner_id == other_player_id:
            return True

        # you may move into unoccupied regions owned by an enemy
        if war_table.get_war_name(self.data.owner_id, other_player_id) is not None and self.data.occupier_id == "0":
            return True
        
        # you may move into occupied regions owned by an enemy in two cases
        elif war_table.get_war_name(self.data.owner_id, other_player_id) is not None and self.data.occupier_id != "0":
            # you are the occupier
            if self.data.occupier_id == other_player_id:
                return True
            # you are also at war with the occupier
            if war_table.get_war_name(self.data.owner_id, other_player_id) is not None:
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
        if self.improvement.health in ["0", "99"]:
            return False

        if self.data.owner_id == other_player_id and self.data.occupier_id == "0":
            # defensive improvements in a region that is owned by you and is unoccupied is never hostile
            return False
        elif self.data.owner_id != other_player_id:
            # defensive improvements in a region you don't own are not hostile if you already occupy the region
            if other_player_id != "0" and self.data.occupier_id == other_player_id:
                return False
        
        return False

    def move_unit(self, target_region: "Region", *, withdraw=False) -> bool:
        """
        Attempts to move the unit in this region to the target region.

        Params:
            target_region (Region): Region object of target region (where this unit is moving to)
            withdraw: True if withdraw action. False otherwise.
        
        Returns:
            bool: True if action succeeded, False otherwise.
        """

        from app import combat
        from app.war import WarTable

        combat_occured = False

        if withdraw:
            self._execute_move(target_region)
            return True
        
        # conduct combat if needed
        if target_region.unit.is_hostile(self.unit.owner_id):
            combat.unit_vs_unit(self, target_region)
            combat_occured = True
        if self.unit.name is not None and target_region.improvement_is_hostile(self.unit.owner_id):
            combat.unit_vs_improvement(self, target_region)
            combat_occured = True

        # complete move if still alive and no resistance
        if (self.unit.name is not None
            and not target_region.unit.is_hostile(self.unit.owner_id)
            and not target_region.improvement_is_hostile(self.unit.owner_id)):
            
            unit_owner_id = copy.deepcopy(self.unit.owner_id)
            self._execute_move(target_region)

            if target_region.improvement_is_hostile(unit_owner_id) and target_region.improvement.name != "Capital":

                nation_table = NationTable(self.game_id)
                war_table = WarTable(self.game_id)

                # load war and combatant data
                attacking_nation = nation_table.get(str(unit_owner_id))
                defending_nation = nation_table.get(str(target_region.data.owner_id))
                war_name = war_table.get_war_name(attacking_nation.id, defending_nation.id)
                war = war_table.get(war_name)
                attacking_nation_combatant_data = war.get_combatant(attacking_nation.id)
                defending_nation_combatant_data = war.get_combatant(defending_nation.id)
                
                # award points and update stats
                war.attacker_destroyed_improvements += war.warscore_destroy_improvement
                attacking_nation_combatant_data.destroyed_improvements += 1
                defending_nation_combatant_data.lost_improvements += 1
                
                # save war data
                if combat_occured:
                    war.log.append(f"    {defending_nation.name} {target_region.improvement.name} has been destroyed!")
                else:
                    war.log.append(f"{attacking_nation.name} destroyed an undefended {defending_nation.name} {target_region.improvement.name}!")
                war.save_combatant(attacking_nation_combatant_data)
                war.save_combatant(defending_nation_combatant_data)
                war_table.save(war)

                # save nation data
                nation_table.save(attacking_nation)

                # remove improvement
                target_region.improvement.clear()
        
    def _execute_move(self, target_region: "Region") -> None:
        target_region.unit.transfer(self.unit)
        self.unit.clear()

    def calculate_yield(self, nation: Nation, improvement_income_dict: dict, active_games_dict: dict) -> dict:
        """
        Calculates the final yield of this improvement.

        Params:
            improvement_income_dict (dict): Contains the income and multiplier of this improvement type. From yield_dict.

        Returns:
            dict: Contains all yields from this improvement.
        """

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
                improvement_income_dict[resource_name]["Income Multiplier"] += 0.2
        
        # get pandemic multiplier
        if "Pandemic" in active_games_dict[self.game_id]["Active Events"]:
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

    def __init__(self, d: dict):

        # TODO: move infection and quarantine code to scenario file somehow

        self._regdata = d
    
        self._owner_id: str = d["ownerID"]
        self._occupier_id: str = d["occupierID"]
        self._purchase_cost: int = d["purchaseCost"]
        self._resource: str = d["regionResource"]
        self._fallout: int = d["nukeTurns"]
        self._infection: int = d["infection"]
        self._quarantine: bool = d["quarantine"]

    @property
    def owner_id(self):
        return self._owner_id
    
    @owner_id.setter
    def owner_id(self, new_id: str):
        self._owner_id = new_id
        self._regdata["ownerID"] = new_id
    
    @property
    def occupier_id(self):
        return self._occupier_id
    
    @occupier_id.setter
    def occupier_id(self, new_id: str):
        self._occupier_id = new_id
        self._regdata["occupierID"] = new_id
    
    @property
    def purchase_cost(self):
        return self._purchase_cost
    
    @purchase_cost.setter
    def purchase_cost(self, value: int):
        self._purchase_cost = value
        self._regdata["purchaseCost"] = value
    
    @property
    def resource(self):
        return self._resource
    
    @resource.setter
    def resource(self, value: str):
        self._resource = value
        self._regdata["regionResource"] = value
    
    @property
    def fallout(self):
        return self._fallout
    
    @fallout.setter
    def fallout(self, value: int):
        self._fallout = value
        self._regdata["nukeTurns"] = value

    @property
    def infection(self):
        return self._infection
    
    @infection.setter
    def infection(self, value: int):
        self._infection = value
        self._regdata["infection"] = value

    @property
    def quarantine(self):
        return self._quarantine
    
    @quarantine.setter
    def quarantine(self, value: bool):
        self._quarantine = value
        self._regdata["quarantine"] = value

class GraphData:
        
    def __init__(self, d: dict):

        self.is_edge: bool = d["isEdgeOfMap"]
        self.is_significant: bool = d["hasRegionalCapital"]
        self.is_magnified: bool = d["isMagnified"]
        self.is_start: bool = d["randomStartAllowed"]
        self.additional_region_coordinates: list = d["additionalRegionCords"]
        self.adjacent_regions: dict = d["adjacencyMap"]

class ImprovementData:
    
    def __init__(self, d: dict, graphdata: dict):

        self._impdata = d

        self._name: str = d["name"]
        self._health: int = d["health"]
        self._countdown: int = d["turnTimer"]
        self.coords: list = graphdata["improvementCords"]

        self._load_attributes_from_game_files()

    @property
    def name(self):
        return self._name
    
    @name.setter
    def name(self, value: str):
        self._name = value
        self._impdata["name"] = value

    @property
    def health(self):
        return self._health
    
    @health.setter
    def health(self, value: int):
        self._health = value
        self._impdata["health"] = value

    @property
    def countdown(self):
        return self._countdown
    
    @countdown.setter
    def countdown(self, value: int):
        self._countdown = value
        self._impdata["turnTimer"] = value

    def _load_attributes_from_game_files(self) -> None:
        
        data_dict = core.get_scenario_dict(Regions.game_id, "Improvements")
        if self.name is not None:
            self.max_health = data_dict[self.name]["Health"]
            self.hit_value = data_dict[self.name]["Combat Value"]
            self.missile_defense = data_dict[self.name]["Standard Missile Defense"]
            self.nuke_defense = data_dict[self.name]["Nuclear Missile Defense"]
        else:
            self.max_health = None
            self.hit_value = None
            self.missile_defense = None
            self.nuke_defense = None

    def set(self, improvement_name: str, starting_health=0) -> None:
        self.clear()
        self.name = improvement_name
        self._load_attributes_from_game_files()
        self.health = self.max_health if starting_health == 0 else starting_health

    def heal(self, amount: int) -> None:
        self.health += amount
        if self.health > self.max_health:
            self.health = self.max_health

    def decrease_countdown(self) -> None:
        if self.countdown != 99:
            self.countdown -= 1

    def clear(self) -> None:
        self.name = None
        self.health = 99
        self.countdown = 99
        self._load_attributes_from_game_files()

class UnitData:
    
    def __init__(self, d: dict, graphdata: dict):

        self._unitdata = d

        self._name: str = d["name"]
        self._health: int = d["health"]
        self._owner_id: str = d["ownerID"]
        self.coords: list = graphdata["unitCords"]

        self._load_attributes_from_game_files()

    @property
    def name(self):
        return self._name
    
    @name.setter
    def name(self, value: str):
        self._name = value
        self._unitdata["name"] = value

    @property
    def health(self):
        return self._health
    
    @health.setter
    def health(self, value: int):
        self._health = value
        self._unitdata["health"] = value

    @property
    def owner_id(self):
        return self._owner_id
    
    @owner_id.setter
    def owner_id(self, new_id: str):
        self._owner_id = new_id
        self._unitdata["ownerID"] = new_id

    def _load_attributes_from_game_files(self) -> None:
    
        data_dict = core.get_scenario_dict(Regions.game_id, "Units")
        if self.name is not None:
            self.type = data_dict[self.name]["Unit Type"]
            self.max_health = data_dict[self.name]["Health"]
            self.hit_value = data_dict[self.name]["Combat Value"]
            self.value = data_dict[self.name]["Point Value"]
        else:
            self.type = None
            self.max_health = None
            self.hit_value = None
            self.value = None

    def set(self, unit_name: str, starting_health=0) -> None:
        self.clear()
        self.name = unit_name
        self._load_attributes_from_game_files()
        self.health = self.max_health if starting_health == 0 else starting_health

    def heal(self, amount: int) -> None:
        self.health += amount
        if self.health > self.max_health:
            self.health = self.max_health

    def clear(self) -> None:
        self.name = None
        self.health = 99
        self.owner_id = "0"
        self._load_attributes_from_game_files()

    def is_hostile(self, other_player_id: str) -> bool:

        from app.war import WarTable
        war_table = WarTable(Regions.game_id)

        # if no unit return False
        if self.owner_id == "0" or other_player_id == "0":
            return False

        # if player_ids are the same than return False
        if self.owner_id == other_player_id:
            return False
        
        # if other_player_id = 99 return True (defending unit is controlled by event)
        if other_player_id == "99":
            return True
        
        # check if at war
        if war_table.get_war_name(self.owner_id, other_player_id) is not None:
            return True
        
        return False
    
    def transfer(self, other_unit_data: "UnitData") -> None:
        data = copy.deepcopy(other_unit_data)
        self.unitdata = data._unitdata
        self.name = data.name
        self.health = data.health
        self.owner_id = data.owner_id
        self._load_attributes_from_game_files()
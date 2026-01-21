import random

from app.scenario.scenario import ScenarioInterface as SD
from app.region.regions import Regions
from app.war.wars import Wars
from app.war.warscore import WarScore
from .strike import Strike

class StandardStrike(Strike):
    missile_str = "Standard Missile"

    def identify_best_missile_defense(self) -> tuple[str, float]:
        possible_defenders = {}
        defender_name = None
        defender_value = -1.0
        
        # check improvements
        for improvement_name, improvement_data in SD.improvements:
            if improvement_data.missile_defense != -1 and self.target_nation.improvement_counts[improvement_name] > 0:
                possible_defenders[improvement_name] = {"range": improvement_data.defense_range, "value": improvement_data.missile_defense}
            elif improvement_data.missile_defense == -1 and "Local Missile Defense" in self.target_nation.completed_research:
                possible_defenders[improvement_name] = {"range": 0, "value": 0.3}

        # check units
        for unit_name, unit_data in SD.units:
            if unit_data.missile_defense != -1 and self.target_nation.unit_counts[unit_name] > 0:
                possible_defenders[unit_name] = {"range": unit_data.defense_range, "value": unit_data.missile_defense}
        
        # determine best defense
        # this algorithm isn't very efficient - too bad!
        for name, data in possible_defenders.items():
            nearby_region_ids = self.target_region.get_regions_in_radius(data["range"])
            for temp_region_id in nearby_region_ids:
                temp_region = Regions.load(temp_region_id)
                if temp_region.improvement.name == name:
                    if data["value"] > defender_value and temp_region.data.owner_id == self.target_nation.id and temp_region.data.occupier_id == "0":
                        defender_name = name
                        defender_value = data["value"]
                elif temp_region.unit.name == name:
                    if data["value"] > defender_value and temp_region.unit.owner_id == self.target_nation.id:
                        defender_name = name
                        defender_value = data["value"]

        return defender_name, defender_value
    
    def fire_missile(self) -> None:
        self.nation.missile_count -= 1
        self.nation.action_log.append(f"Launched {self.missile.type} at {self.target_region.id}. See combat log for details.")
    
    def resolve_improvement_damage(self) -> bool:
        if self.target_region.improvement.name is None:
            return False
        
        # missile accuracy roll
        accuracy_roll = random.random()
        if accuracy_roll < self.missile.improvement_damage_chance:
            self.war.log.append(f"    Missile missed {self.target_region.improvement.name}. ({int(self.missile.improvement_damage_chance * 100)}% chance)")
            return False
        
        # improvement damage procedure - improvements with health bar
        if self.target_region.improvement.health != 99:
            
            # deal damage
            self.target_region.improvement.health -= self.missile.improvement_damage
            
            # improvement survived
            if self.target_region.improvement.health > 0:
                self.war.log.append(f"    Missile struck {self.target_region.improvement.name} in {self.target_region.id} and dealt {self.missile.improvement_damage} damage.")
                return True

            # OR improvement destroyed
            self._award_warscore("Attacker", "destroyed_improvements", WarScore.FROM_DESTROY_IMPROVEMENT)
            if self.target_region.improvement.name != 'Capital':
                self.attacking_combatant.destroyed_improvements += 1
                self.defending_combatant.lost_improvements += 1
                self.war.log.append(f"    Missile struck {self.target_region.improvement.name} in {self.target_region.id} and dealt {self.missile.improvement_damage} damage. Improvement destroyed!")
                self.target_nation.improvement_counts[self.target_region.improvement.name] -= 1
                self.target_region.improvement.clear()
            else:
                self.war.log.append(f"    Missile struck Capital in {self.target_region.id} and dealt {self.missile.improvement_damage} damage. Improvement rendered non-functional!")
            return True
        
        # improvement damage procedure - improvements without health bar
        elif self.target_region.improvement.health == 99:
            
            # improvement destroyed
            self._award_warscore("Attacker", "destroyed_improvements", WarScore.FROM_DESTROY_IMPROVEMENT)
            self.attacking_combatant.destroyed_improvements += 1
            self.defending_combatant.lost_improvements += 1
            self.war.log.append(f"    Missile struck {self.target_region.improvement.name} in {self.target_region.id}. Improvement destroyed!")
            self.target_nation.improvement_counts[self.target_region.improvement.name] -= 1
            self.target_region.improvement.clear()
            return True
    
    def resolve_unit_damage(self) -> bool:
        if self.target_region.unit.name is None:
            return False

        # missile accuracy roll
        accuracy_roll = random.random()
        if accuracy_roll < self.missile.unit_damage_chance:
            self.war.log.append(f"    Missile missed {self.target_region.unit.name}. ({int(self.missile.unit_damage_chance * 100)}% chance)")
            return False
        
        # deal damage
        self.target_region.unit.health -= 1
        
        # unit survived
        if self.target_region.unit.health > 0:
            self.war.log.append(f"    Missile struck {self.target_region.unit.name} in {self.target_region.id} and dealt {self.missile.unit_damage} damage.")
            return True
        
        # OR unit destroyed
        self._award_warscore("Attacker", "destroyed_units", self.target_region.unit.value)
        self.attacking_combatant.destroyed_units += 1
        self.defending_combatant.lost_units += 1
        self.war.log.append(f"    Missile struck {self.target_region.unit.name} in {self.target_region.id} and dealt {self.missile.unit_damage} damage. Unit destroyed!")
        self.target_nation.unit_counts[self.target_region.unit.name] -= 1
        self.target_region.unit.clear()
        return True
    
    def resolve_strike(self) -> bool:
        self.attacking_combatant.launched_missiles += 1
        improvement_damage_occurred = self.resolve_improvement_damage()
        unit_damage_occured = self.resolve_unit_damage()
        if improvement_damage_occurred or unit_damage_occured:
            return True
        return False
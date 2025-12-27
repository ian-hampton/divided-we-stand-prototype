import random
from enum import StrEnum

from app.nation.nations import Nations
from app.war.warscore import WarScore
from .combat import CombatProcedure

class UnitVsUnit:

    def __init__(self, combat: CombatProcedure):
        self.attacking_region = combat.attacking_region
        self.defending_region = combat.defending_region
        self.attacker_id = self.attacking_region.unit.owner_id
        self.defender_id = self.defending_region.unit.owner_id
        self.war = combat.war
        self.attacker = Nations.get(self.attacker_id)
        self.defender = Nations.get(self.defender_id)
        self.attacker_cd = self.war.get_combatant(self.attacker_id)
        self.defender_cd = self.war.get_combatant(self.defender_id)

        self.attacker_roll_modifier = 0
        self.defender_roll_modifier = 0
        self.attacker_damage_modifier = 0
        self.defender_damage_modifier = 0
        self.result: CombatOutcome = None

    def _award_warscore(self, side: str, category: str, amount: WarScore) -> None:
        """
        This function is silly but important.
        Since an "attacker" in this combat may not be the same as the "attacker" in the corresponding war, we need to identify what side should be rewarded.

        Args:
            side (str): _description_
            category (str): _description_
            amount (WarScore): _description_
        """
        if side == "Attacker":
            if "Attacker" in self.attacker_cd.role:
                self.war.update_warscore("Attacker", category, amount)
            else:
                self.war.update_warscore("Defender", category, amount)
        elif side == "Defender":
            if "Attacker" in self.defender_cd.role:
                self.war.update_warscore("Attacker", category, amount)
            else:
                self.war.update_warscore("Defender", category, amount)

    def _calculate_roll_modifiers(self) -> None:
        
        # calculate attacker roll modifier
        if "Attacker" in self.attacker_cd.role and "Superior Training" in self.attacker.completed_research:
            self.attacker_roll_modifier += 1
        elif "Defender" in self.attacker_cd.role and "Unyielding" in self.attacker.completed_research:
            self.attacker_roll_modifier += 1
        if self.attacking_region.unit.type == "Tank" and self.attacking_region.check_for_adjacent_unit({"Mechanized Infantry"}, self.attacking_region.unit.owner_id):
            self.attacker_roll_modifier += 1
        elif self.attacking_region.unit.type == "Infantry" and self.attacking_region.check_for_adjacent_unit({"Light Tank"}, self.attacking_region.unit.owner_id):
            self.attacker_roll_modifier += 1
        if self.attacking_region.unit.name == "Main Battle Tank" and self.defending_region.unit.type == "Infantry":
            self.attacker_roll_modifier += 1
        for tag_data in self.attacker.tags.values():
            if tag_data.get("Combat Roll Bonus") == self.defender.id:
                self.attacker_roll_modifier += 1

        # calculate defender roll modifier
        if "Attacker" in self.defender_cd.role and "Superior Training" in self.defender.completed_research:
            self.defender_roll_modifier += 1
        elif "Defender" in self.defender_cd.role and "Unyielding" in self.defender.completed_research:
            self.defender_roll_modifier += 1
        if self.defending_region.unit.type == "Tank" and self.defending_region.check_for_adjacent_unit({"Mechanized Infantry"}, self.defending_region.unit.owner_id):
            self.defender_roll_modifier += 1
        elif self.defending_region.unit.type == "Infantry" and self.defending_region.check_for_adjacent_unit({"Light Tank"}, self.defending_region.unit.owner_id):
            self.defender_roll_modifier += 1
        if self.defending_region.unit.name == "Main Battle Tank" and self.attacking_region.unit.type == "Infantry":
            self.defender_roll_modifier += 1
        for tag_data in self.defender.tags.values():
            if tag_data.get("Combat Roll Bonus") == self.attacker.id:
                self.defender_roll_modifier += 1

    def _calculate_damage_modifiers(self) -> None:
        
        # calculate attacker damage modifier
        if self.attacking_region.check_for_adjacent_unit({"Artillery"}, self.attacking_region.unit.owner_id):
            self.war.log.append(f"    Attacking unit has artillery support!")
            self.attacker_damage_modifier += 1
        if self.defending_region.improvement.name == "Trench":
            self.war.log.append(f"    Defending unit is entrenched!")
            self.attacker_damage_modifier -= 1

        # calculate defender damage modifier
        if self.defending_region.check_for_adjacent_unit({"Artillery"}, self.defending_region.unit.owner_id):
            self.war.log.append(f"    Defending unit has artillery support!")
            self.defender_damage_modifier += 1

    def _execute_combat(self) -> None:
        attacker_roll = random.randint(1, 10) + self.attacker_roll_modifier
        defender_roll = random.randint(1, 10) + self.defender_roll_modifier
        attacker_hit = False
        defender_hit = False
        if attacker_roll >= self.attacking_region.unit.hit_value:
            attacker_hit = True
        if defender_roll >= self.defending_region.unit.hit_value:
            defender_hit = True

        if attacker_hit and not defender_hit:
            # set result
            self.result = CombatOutcome.ATTACKER_VICTORY
            # update stats
            self._award_warscore("Attacker", "victories", WarScore.FROM_VICTORY)
            self.attacker_cd.battles_won += 1
            self.defender_cd.battles_lost += 1
            # take damage
            self.defending_region.unit.health -= self.attacking_region.unit.victory_damage + self.attacker_damage_modifier
        elif not attacker_hit and defender_hit:
            # set result
            self.result = CombatOutcome.DEFENDER_VICTORY
            # update stats
            self._award_warscore("Defender", "victories", WarScore.FROM_VICTORY)
            self.attacker_cd.battles_lost += 1
            self.defender_cd.battles_won += 1
            # take damage
            self.attacking_region.unit.health -= self.defending_region.unit.victory_damage + self.defender_damage_modifier
        else:
            # set result
            self.result = CombatOutcome.DRAW
            # take damage
            self.defending_region.unit.health -= self.attacking_region.unit.draw_damage + self.attacker_damage_modifier
            self.attacking_region.unit.health -= self.defending_region.unit.draw_damage + self.defender_damage_modifier
        
        if self.attacker_roll_modifier > 0 and self.defender_roll_modifier > 0:
            battle_str = f"    {self.attacker.name} rolled {attacker_roll} (+{self.attacker_roll_modifier}). {self.defender.name} rolled {defender_roll} (+{self.defender_roll_modifier})."
        elif self.attacker_roll_modifier > 0:
            battle_str = f"    {self.attacker.name} rolled {attacker_roll} (+{self.attacker_roll_modifier}). {self.defender.name} rolled {defender_roll}."
        elif self.defender_roll_modifier > 0:
            battle_str = f"    {self.attacker.name} rolled {attacker_roll}. {self.defender.name} rolled {defender_roll} (+{self.defender_roll_modifier})."
        else:
            battle_str = f"    {self.attacker.name} rolled {attacker_roll}. {self.defender.name} rolled {defender_roll}."
        battle_str += self.result.value
        self.war.log.append(battle_str)

    def _cleanup(self) -> None:
        
        # remove attacking unit if defeated
        if self.attacking_region.unit.health <= 0:
            self.war.log.append(f"    {self.attacker.name} {self.attacking_region.unit.name} has been lost!")
            # update stats
            self._award_warscore("Defender", "destroyed_units", self.attacking_region.unit.value)
            self.attacker_cd.lost_units += 1
            self.defender_cd.destroyed_units += 1
            # update player
            self.attacker.unit_counts[self.attacking_region.unit.name] -= 1
            self.attacking_region.unit.clear()
        
        # remove defending unit if defeated
        if self.defending_region.unit.health <= 0:
            self.war.log.append(f"    {self.defender.name} {self.defending_region.unit.name} has been lost!")
            # update stats
            self._award_warscore("Attacker", "destroyed_units", self.defending_region.unit.value)
            self.attacker_cd.destroyed_units += 1
            self.defender_cd.lost_units += 1
            # update player
            self.defender.unit_counts[self.defending_region.unit.name] -= 1
            self.defending_region.unit.clear()

    def resolve(self) -> None:
        """
        Resolve combat between the attacking and defending units.
        """
        self.war.log.append(f"{self.attacker.name} {self.attacking_region.unit.name} {self.attacking_region.id} vs {self.defender.name} {self.defending_region.unit.name} {self.defending_region.id}")
        self._calculate_roll_modifiers()
        self._calculate_damage_modifiers()
        self._execute_combat()
        self._cleanup()

class CombatOutcome(StrEnum):
    ATTACKER_VICTORY = " Attacker victory!"
    DEFENDER_VICTORY = " Defender victory!"
    DRAW = " Draw!"
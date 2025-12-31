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

        self.attacker_damage_modifier = 0
        self.defender_armor_modifier = 0

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

    def _calculate_damage_modifiers(self) -> None:

        # attacker damage from tags
        for tag_data in self.attacker.tags.values():
            if tag_data.get("Combat Roll Bonus") == self.defender.id:
                self.attacker_damage_modifier += 1
        
        # attacker damage from research
        if "Attacker" in self.attacker_cd.role and "Superior Training" in self.attacker.completed_research:
            self.war.log.append(f"    Attacking unit has Superior Training (+1).")
            self.attacker_damage_modifier += 1
        elif "Defender" in self.attacker_cd.role and "Unyielding" in self.attacker.completed_research:
            self.war.log.append(f"    Attacking unit has Unyielding (+1).")
            self.attacker_damage_modifier += 1
        
        # attacker damage from units
        if self.attacking_region.unit.name == "Main Battle Tank" and self.defending_region.unit.type == "Tank":
            self.war.log.append(f"    Attacking unit is effective against enemy tanks (+2).")
            self.attacker_damage_modifier += 2
        if self.attacking_region.check_for_adjacent_unit({"Artillery"}, self.attacking_region.unit.owner_id):
            self.war.log.append(f"    Attacking unit has Artillery support (+1).")
            self.attacker_damage_modifier += 1

        # attacker damage from improvements
        if self.attacking_region.improvement.name == "Military Base":
            self.war.log.append(f"    Attacking unit has Military Base support (+1).")
            self.attacker_damage_modifier += 1
        
    def _calculate_armor_modifiers(self) -> None:
        
        # defender entrenched
        if not self.defending_region.unit.has_movement_queued:
            self.war.log.append(f"    Defending unit is entrenched and gains +1 armor for this battle!")
            self.defender_armor_modifier += 1

        # defender armor from units
        if self.defending_region.unit.type == "Infantry" and self.defending_region.check_for_adjacent_unit({"Heavy Tank", "Main Battle Tank"}, self.defending_region.unit.owner_id):
            self.defender_armor_modifier += 1
        
        # defender armor from improvements
        if self.defending_region.unit.type == "Infantry" and self.defending_region.improvement.name in ["Trench", "Fort", "Military Base"]:
            self.defender_armor_modifier += 1

    def _execute_combat(self) -> None:
        
        # attacker deals damage to defender
        total_damage = self.attacking_region.unit.damage + self.attacker_damage_modifier
        total_armor = self.defending_region.unit.armor + self.defender_armor_modifier
        net_damage = total_damage - total_armor 
        self.defending_region.unit.health -= net_damage
        
        if net_damage > 3:
            # decisive victory
            self._award_warscore("Attacker", "victories", WarScore.FROM_VICTORY)
            self.attacker_cd.battles_won += 1
            battle_str = f"    {self.attacker.name} dealt {net_damage} to {self.defender.name} {self.defending_region.unit.name} ({total_damage} damage - {total_armor} armor). Decisive victory!"
            self.war.log.append(battle_str)
        else:
            # not a decisive victory
            self.attacking_region.unit.health -= 1
            self.attacker_cd.battles_won += 1
            battle_str = f"    {self.attacker.name} dealt {net_damage if net_damage > 0 else 0} to {self.defender.name} {self.defending_region.unit.name} ({total_damage} damage - {total_armor} armor)."
            self.war.log.append(battle_str)
            battle_str = f"    {self.attacker.name} {self.attacking_region.unit.name} suffers 1 damage."
            self.war.log.append(battle_str)

        # remove attacking unit if defeated
        if self.attacking_region.unit.health <= 0:
            self.war.log.append(f"    {self.attacker.name} {self.attacking_region.unit.name} has been defeated!")
            # update stats
            self._award_warscore("Defender", "destroyed_units", self.attacking_region.unit.value)
            self.attacker_cd.lost_units += 1
            self.defender_cd.destroyed_units += 1
            # update player
            self.attacker.unit_counts[self.attacking_region.unit.name] -= 1
            self.attacking_region.unit.clear()

        # cleanup - remove defending unit if defeated
        if self.defending_region.unit.health <= 0:
            self.war.log.append(f"    {self.defender.name} {self.defending_region.unit.name} has been defeated!")
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
        self.war.log.append(f"{self.attacker.name} {self.attacking_region.unit.name} {self.attacking_region.id} attacked {self.defender.name} {self.defending_region.unit.name} {self.defending_region.id}")
        self._calculate_damage_modifiers()
        self._calculate_armor_modifiers()
        self._execute_combat()
from app.nation.nations import Nations
from app.war.warscore import WarScore
from .battle import BattleTemplate
from .combat import CombatProcedure

class UnitVsImprovement(BattleTemplate):
    
    def __init__(self, combat: CombatProcedure):
        super().__init__(combat)
        self.attacker_id = self.attacking_region.unit.owner_id
        self.defender_id = self.defending_region.data.owner_id
        self.attacker = Nations.get(self.attacker_id)
        self.defender = Nations.get(self.defender_id)
        self.attacker_cd = self.war.get_combatant(self.attacker_id)
        self.defender_cd = self.war.get_combatant(self.defender_id)

        self.attacker_damage_modifier = 0
        self.defender_damage_modifier = 0

    def _calculate_damage_modifiers(self) -> None:
        """
        Calculates damage modifiers for attacker and defender.
        Partially implemented by parent class BattleTemplate.
        """
        super()._calculate_damage_modifiers()
        
        # attacker damage from units
        if self.attacking_region.unit.name == "Main Battle Tank":
            self.war.log.append(f"    Attacking unit is effective against improvements (+2).")
            self.attacker_damage_modifier += 2
        if self.attacking_region.check_for_adjacent_unit({"Artillery"}, self.attacking_region.unit.owner_id):
            self.war.log.append(f"    Attacking unit has Artillery support (+1).")
            self.attacker_damage_modifier += 1

        # defender damage from research
        if "Defender" in self.defender_cd.role and "Defensive Tactics" in self.defender.completed_research:
            self.war.log.append(f"    Defending improvement has Defensive Tactics (+1).")
            self.defender_damage_modifier += 1

    def _execute_combat(self) -> None:
        
        # attacker deals damage to defender
        total_damage = self.attacking_region.unit.damage + self.attacker_damage_modifier
        if self.attacking_region.unit.type == "Special Forces":
            total_armor = 0
            battle_str = f"    The attacking unit is a special forces. The defender's armor will be ignored!"
            self.war.log.append(battle_str)
        else:
            total_armor = self.defending_region.improvement.armor
        net_damage = total_damage - total_armor 
        self.defending_region.improvement.health -= net_damage

        self.attacker_cd.attacks += 1
        if net_damage >= 3:
            # decisive victory
            self._award_warscore("Attacker", "decisive_battles", WarScore.FROM_SUCCESSFUL_ATTACK)
            battle_str = f"    {self.attacker.name} dealt {net_damage} to {self.defender.name} {self.defending_region.improvement.name} ({total_damage} damage - {total_armor} armor). Decisive victory!"
            self.war.log.append(battle_str)
        else:
            # not a decisive victory
            self.attacking_region.unit.health -= 1
            battle_str = f"    {self.attacker.name} dealt {net_damage if net_damage > 0 else 0} to {self.defender.name} {self.defending_region.improvement.name} ({total_damage} damage - {total_armor} armor)."
            self.war.log.append(battle_str)
            battle_str = f"    {self.attacker.name} {self.attacking_region.unit.name} suffers 1 damage."
            self.war.log.append(battle_str)

        # defender damages the attacker
        defender_damage = self.defending_region.improvement.damage + self.defender_damage_modifier
        self.attacking_region.unit.health -= defender_damage
        battle_str = f"    {self.defender.name} {self.defending_region.improvement.name} dealt {defender_damage} damage."
        self.war.log.append(battle_str)

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

        # remove defending improvement if defeated
        if self.defending_region.improvement.health <= 0:
            self.attacker_cd.destroyed_improvements += 1
            self.defender_cd.lost_improvements += 1
            self.war.log.append(f"    {self.defender.name} {self.defending_region.improvement.name} has been captured!")
            self.defending_region.improvement.health = 0
            # special case - capital captured
            if self.defending_region.improvement.name == "Capital":
                self._award_warscore("Attacker", "captures", WarScore.FROM_CAPITAL_CAPTURE)
                return
            # improvement captured
            self._award_warscore("Attacker", "destroyed_improvements", WarScore.FROM_DESTROY_IMPROVEMENT)

    def resolve(self) -> None:
        """
        Resolve combat between the attacking and defending units.
        """
        battle_title = f"{self.attacker.name} {self.attacking_region.unit.name} {self.attacking_region.id} attacked {self.defender.name} {self.defending_region.improvement.name} {self.defending_region.id}"
        self.war.log.append(battle_title)
        self._calculate_damage_modifiers()
        self._execute_combat()
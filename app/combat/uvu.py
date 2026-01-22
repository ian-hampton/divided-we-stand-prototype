from app.nation.nations import Nations
from app.war.warscore import WarScore
from .battle import BattleTemplate
from .combat import CombatProcedure
from .experience import ExperienceRewards

class UnitVsUnit(BattleTemplate):

    def __init__(self, combat: CombatProcedure):
        super().__init__(combat)
        self.attacker_id = self.attacking_region.unit.owner_id
        self.defender_id = self.defending_region.unit.owner_id
        self.attacker = Nations.get(self.attacker_id)
        self.defender = Nations.get(self.defender_id)
        self.attacker_cd = self.war.get_combatant(self.attacker_id)
        self.defender_cd = self.war.get_combatant(self.defender_id)

        self.attacker_damage_modifier = 0
        self.defender_armor_modifier = 0

    def _calculate_damage_modifiers(self) -> None:
        """
        Calculates damage modifiers for attacker and defender.
        Partially implemented by parent class BattleTemplate.
        """
        super()._calculate_damage_modifiers()

        # attacker damage from units
        if self.attacking_region.unit.name == "Main Battle Tank" and self.defending_region.unit.type == "Tank":
            self.war.log.append(f"    Attacking unit is effective against enemy tanks (+2).")
            self.attacker_damage_modifier += 2
        if self.attacking_region.check_for_adjacent_unit({"Artillery"}, self.attacking_region.unit.owner_id):
            self.war.log.append(f"    Attacking unit has Artillery support (+1).")
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
        total_damage = self.attacking_region.unit.true_damage + self.attacker_damage_modifier
        if self.attacking_region.unit.type == "Special Forces":
            total_armor = 0
            battle_str = f"    The attacking unit is a special forces. The defender's armor will be ignored!"
            self.war.log.append(battle_str)
        else:
            total_armor = self.defending_region.unit.armor + self.defender_armor_modifier
        net_damage = total_damage - total_armor 
        self.defending_region.unit.health -= net_damage
        
        # update stats
        self.attacker_cd.attacks += 1
        self.attacking_region.unit.add_xp(ExperienceRewards.FROM_ATTACK_ENEMY)

        if net_damage >= 3:
            # decisive victory
            self._award_warscore("Attacker", "decisive_battles", WarScore.FROM_SUCCESSFUL_ATTACK)
            battle_str = f"    {self.attacker.name} dealt {net_damage} to {self.defender.name} {self.defending_region.unit.name} ({total_damage} damage - {total_armor} armor). Decisive victory!"
            self.war.log.append(battle_str)
        else:
            # not a decisive victory
            self.attacking_region.unit.health -= 1
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

        # remove defending unit if defeated
        if self.defending_region.unit.health <= 0:
            self.war.log.append(f"    {self.defender.name} {self.defending_region.unit.name} has been defeated!")
            # update stats
            self.attacking_region.unit.add_xp(ExperienceRewards.FROM_DEFEAT_ENEMY)
            self._award_warscore("Attacker", "destroyed_units", self.defending_region.unit.value)
            self.attacker_cd.destroyed_units += 1
            self.defender_cd.lost_units += 1
            # update player
            self.defender.unit_counts[self.defending_region.unit.name] -= 1
            self.defending_region.unit.clear()
        else:
            # award defending unit with xp if it survived this attack
            self.defending_region.unit.add_xp(ExperienceRewards.FROM_SURVIVE_ATTACK)

    def resolve(self) -> None:
        """
        Resolve combat between the attacking and defending units.
        """
        battle_title = f"{self.attacker.name} {self.attacking_region.unit.name} {self.attacking_region.id} attacked {self.defender.name} {self.defending_region.unit.name} {self.defending_region.id}"
        self.war.log.append(battle_title)
        self._calculate_damage_modifiers()
        self._calculate_armor_modifiers()
        self._execute_combat()
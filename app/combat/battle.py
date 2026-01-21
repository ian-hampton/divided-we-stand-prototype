from app.nation.nations import Nations
from app.war.warscore import WarScore
from .combat import CombatProcedure

class BattleTemplate:

    def __init__(self, combat: CombatProcedure):
        self.attacking_region = combat.attacking_region
        self.defending_region = combat.defending_region
        self.war = combat.war

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
                self.war.update_warscore("Attacker", category, amount.value)
            else:
                self.war.update_warscore("Defender", category, amount.value)
        elif side == "Defender":
            if "Attacker" in self.defender_cd.role:
                self.war.update_warscore("Attacker", category, amount.value)
            else:
                self.war.update_warscore("Defender", category, amount.value)
    
    def _calculate_damage_modifiers(self) -> None:
        """
        Shared initial implementation for calculate damage modifiers that are applicable to all battle types.
        """

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

        # attacker damage from improvements
        if self.attacking_region.improvement.name == "Military Base":
            self.war.log.append(f"    Attacking unit has Military Base support (+1).")
            self.attacker_damage_modifier += 1

    def _calculate_armor_modifiers(self) -> None:
        raise NotImplementedError
    
    def _execute_combat(self) -> None:
        raise NotImplementedError
    
    def resolve(self) -> None:
        raise NotImplementedError
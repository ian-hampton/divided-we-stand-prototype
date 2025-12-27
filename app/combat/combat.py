from app.region.region import Region
from app.war.wars import Wars

class CombatProcedure:

    def __init__(self, current_region: Region, target_region: Region):
        self.attacking_region = current_region
        self.defending_region = target_region
        self.attacker_id = self.attacking_region.unit.owner_id
        self.defender_id = self.defending_region.data.owner_id
        war_name = Wars.get_war_name(self.attacker_id, self.defender_id)
        self.war = Wars.get(war_name)
        self.has_conducted_combat = False

    def resolve(self) -> None:
        """
        Resolves combat in stages. Tracks if combat has actually occured.

        Returns:
            bool: True if combat occured, False otherwise.
        """
        
        # conduct unit vs unit combat if needed
        if self.defending_region.unit.is_hostile(self.attacking_region.unit.owner_id):
            combat_old.unit_vs_unit(self.attacking_region, self.defending_region)
            self.has_conducted_combat = True
        
        # conduct units vs improvement combat if needed
        if self.defending_region.improvement_is_hostile(self.attacking_region.unit.owner_id) and self.attacking_region.unit.name is not None:
            combat_old.unit_vs_improvement(self.attacking_region, self.defending_region)
            self.has_conducted_combat = True
        
        self.has_conducted_combat = False

    def is_able_to_move(self) -> bool:
        """
        Attacking unit can only move after combat if still alive and no remaining resistance in defending region.

        Returns:
            bool: _description_
        """
        if (self.attacking_region.unit.name is None
            or self.defending_region.unit.is_hostile(self.attacking_region.unit.owner_id)
            or self.defending_region.improvement_is_hostile(self.attacking_region.unit.owner_id)):
            return False
        return True
    
    def pillage(self) -> None:
        """
        If able, destroy an improvement in the defending region that is unable to defend itself.

        Why are only defenseless improvements checked here?
        If combat has made it this far, improvements that can defend themselves will have already been destroyed in the unit vs improvement combat step.
        """
        from war.warscore import WarScore

        # check if there is a defenseless improvement owned by an enemy that can be destroyed
        if (self.defending_region.improvement.name is None
            or self.defending_region.improvement.name == "Capital"
            or self.attacker_id == self.defender_id):
            return

        # load combatant data
        attacking_nation_combatant_data = self.war.get_combatant(self.attacker_id)
        defending_nation_combatant_data = self.war.get_combatant(self.defender_id)
        
        # award points and update stats
        self.war.attackers.destroyed_improvements += WarScore.FROM_DESTROY_IMPROVEMENT
        attacking_nation_combatant_data.destroyed_improvements += 1
        defending_nation_combatant_data.lost_improvements += 1
        
        # update combat log
        if self.has_conducted_combat:
            self.war.log.append(f"    {defending_nation_combatant_data.name} {self.defending_region.improvement.name} has been destroyed!")
        else:
            self.war.log.append(f"{attacking_nation_combatant_data.name} destroyed an undefended {defending_nation_combatant_data.name} {self.defending_region.improvement.name}!")

        # remove improvement
        self.defending_region.improvement.clear()
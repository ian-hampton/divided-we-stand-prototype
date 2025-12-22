import random

from app.scenario.scenario import ScenarioInterface as SD
from app.region import Region
from app.nation.nation import Nation
from app.war import War

class Strike:
    missile_str: str = None
    
    def __init__(self, nation: Nation, target_nation: Nation, target_region: Region, war: War):
        self.nation = nation
        self.target_nation = target_nation
        self.target_region = target_region
        self.war = war
        
        self.attacking_combatant = self.war.get_combatant(self.nation.id)
        self.defending_combatant = self.war.get_combatant(self.target_nation.id)

        try:
            self.missile = SD.missiles[self.missile_str]
        except:
            raise ValueError(f"Failed to init a Missile Strike. Invalid missile type.")

    def identify_best_missile_defense(self) -> tuple[str, int]:
        raise NotImplementedError

    def missile_defense(self) -> bool:
        defender_name, defender_value = self.identify_best_missile_defense()
        if defender_name is None:
            self.war.log.append(f"    {self.target_nation.name} has no missile defenses in the area.")
            return False
        
        self.war.log.append(f"    A nearby {defender_name} attempted to defend {self.target_region.id}.")
        missile_defense_roll = random.randint(1, 10)
        
        if missile_defense_roll >= defender_value:
            self.war.log.append(f"    {defender_name} missile defense rolled {missile_defense_roll} (needed {defender_value}+). Missile destroyed!")
            return True
        else:
            self.war.log.append(f"    {defender_name} missile defense rolled {missile_defense_roll} (needed {defender_value}+). Defenses missed!")
        
        return False

    def fire_missile(self) -> int:
        raise NotImplementedError
    
    def resolve(self):
        if self.missile_defense():
            return
        damage_delt = self.resolve_strike()
        if not damage_delt:
            self.war.log.append(f"    Missile reached its target failed to damage anything of strategic value.")

    def resolve_improvement_damage(self) -> bool:
        raise NotImplementedError
    
    def resolve_unit_damage(self) -> bool:
        raise NotImplementedError
    
    def resolve_strike(self) -> bool:
        raise NotImplementedError
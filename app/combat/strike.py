import random

from app.scenario.scenario import ScenarioInterface as SD
from app.region.region import Region
from app.nation.nation import Nation
from app.war.war import War

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

    def identify_best_missile_defense(self) -> tuple[str, float]:
        """
        Helper function for missile defense function.
        Retrieves the name and defense value of the best unit or improvement available to defend against the incoming missile.

        Raises:
            NotImplementedError: This function is not implemented by the Strike parent class.

        Returns:
            tuple: Best available defender as name-value pair.
        """
        raise NotImplementedError

    def missile_defense(self) -> bool:
        """
        Handles missile defense. Logs results to relevant war.

        Returns:
            bool: True if defense successful, False otherwise.
        """
        defender_name, defender_value = self.identify_best_missile_defense()
        if defender_name is None:
            self.war.log.append(f"    {self.target_nation.name} has no missile defenses in the area.")
            return False
        
        self.war.log.append(f"    A nearby {defender_name} attempted to defend {self.target_region.id}.")
        missile_defense_roll = random.random()
        
        if missile_defense_roll >= defender_value:
            self.war.log.append(f"    {defender_name} missile defense roll succeeded. Missile destroyed! ({int(defender_value * 100)}% chance)")
            return True
        else:
            self.war.log.append(f"    {defender_name} missile defense roll failed. Defenses missed! ({int(defender_value * 100)}% chance)")
        
        return False

    def fire_missile(self) -> None:
        """
        Handles missile launch. 
        This is a series of small tasks such as updating missile inventory, updating war log, etc.

        Raises:
            NotImplementedError: This function is not implemented by the Strike parent class.
       
        Returns:
            int: Launch cost.
        """
        raise NotImplementedError
    
    def resolve(self):
        """
        Resolves missile strike.
        """

        # missile interception oppertunity
        if self.missile_defense():
            return
        
        # resolve missile strike
        damage_delt = self.resolve_strike()
        
        # add failure message to war log if missile strike accomplished nothing
        if not damage_delt:
            self.war.log.append(f"    Missile reached its target but failed to damage anything of strategic value.")

    def resolve_improvement_damage(self) -> bool:
        """
        Resolves damage delt to improvement by missile.

        Raises:
            NotImplementedError: This function is not implemented by the Strike parent class.

        Returns:
            bool: True if damage was dealt by missile, False otherwise.
        """
        raise NotImplementedError
    
    def resolve_unit_damage(self) -> bool:
        """
        Resolves damage delt to unit by missile.

        Raises:
            NotImplementedError: This function is not implemented by the Strike parent class.

        Returns:
            bool: True if damage was dealt by missile, False otherwise.
        """
        raise NotImplementedError
    
    def resolve_strike(self) -> bool:
        """
        Implementation for missile-specific strike resolution.

        Raises:
            NotImplementedError: This function is not implemented by the Strike parent class.

        Returns:
            bool: True if damage was dealt by missile, False otherwise.
        """
        raise NotImplementedError
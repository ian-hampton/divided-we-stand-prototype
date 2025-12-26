import copy

class SD_Unit:

    
    def __init__(self, d: dict):
        
        self.d = d
        self.required_research: str = d["Required Research"]
        self.type: str = d["Unit Type"]
        self.abbreviation: str = d["Abbreviation"]
        self.value: int = d["Point Value"]
        self.color: str = d["Reference Color"]
        
        self.health: int = d.get("Health", 99)
        self.victory_damage: int = d.get("Victory Damage", 99)
        self.draw_damage: int = d.get("Draw Damage", 99)
        self.hit_value: int = d.get("Combat Value", 99)
        self.missile_defense: int = d.get("Standard Missile Defense", 99)
        self.nuclear_defense: int = d.get("Nuclear Missile Defense", 99)
        self.defense_range: int = d.get("Missile Defense Range", 99)
        
        self.movement: int = d.get("Movement", 0)
        self.abilities: list = d.get("Abilities", [])

    @property
    def upkeep(self) -> dict:
        return copy.deepcopy(self.d.get("Upkeep", {}))
    
    @property
    def cost(self) -> dict:
        return copy.deepcopy(self.d.get("Build Costs", {}))
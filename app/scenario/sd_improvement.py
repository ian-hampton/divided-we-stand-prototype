import copy

class SD_Improvement:
    
    def __init__(self, d: dict):
        
        self.d = d
        self.required_research: str = d["Required Research"]
        self.required_resource: str = d["Required Resource"]
        self.is_fog_of_war: bool = d.get("Fog of War") is not None
        self.color: str = d.get("Reference Color", "stat-grey")

        self.health: int = d.get("Health", 99)
        self.victory_damage: int = d.get("Victory Damage", 99)
        self.draw_damage: int = d.get("Draw Damage", 99)
        self.hit_value: int = d.get("Combat Value", 99)
        self.missile_defense: int = d.get("Standard Missile Defense", 99)
        self.nuclear_defense: int = d.get("Nuclear Missile Defense", 99)
        self.defense_range: int = d.get("Missile Defense Range", 99)

        self.income: dict = d.get("Income", {})
        self.abilities: list = d.get("Abilities", [])

    @property
    def upkeep(self) -> dict:
        return copy.deepcopy(self.d.get("Upkeep", {}))
    
    @property
    def cost(self) -> dict:
        return copy.deepcopy(self.d.get("Build Costs", {}))
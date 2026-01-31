import copy

class SD_Missile:
    
    def __init__(self, d: dict):
        
        self.d = d
        self.required_research: str = d["Required Research"]
        self.type: str = d["Type"]
        self.improvement_damage: int = d.get("Improvement Damage", -1)
        self.unit_damage: int = d.get("Unit Damage", -1)
        self.improvement_damage_chance: float = d.get("Improvement Damage Chance", -1.0)
        self.unit_damage_chance: float = d.get("Unit Damage Chance", -1.0)
        self.launch_cost: int = d["Launch Capacity"]

    @property
    def cost(self) -> dict:
        return copy.deepcopy(self.d.get("Build Costs", {}))
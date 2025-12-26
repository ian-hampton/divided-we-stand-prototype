import copy

class SD_Missile:
    
    def __init__(self, d: dict):
        
        self.d = d
        self.required_research: str = d["Required Research"]
        self.type: str = d["Type"]
        self.launch_cost: int = d["Launch Capacity"]

    @property
    def cost(self) -> dict:
        return copy.deepcopy(self.d.get("Build Costs", {}))
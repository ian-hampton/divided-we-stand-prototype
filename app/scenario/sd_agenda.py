class SD_Agenda:
    
    def __init__(self, d: dict):
        self.type: str = d["Agenda Type"]
        self.prerequisite: str | None = d["Prerequisite"]
        self.cost: int = d["Cost"]
        self.description: str = d["Description"]
        self.location: str = d["Location"]
        self.modifiers: dict = d["Modifiers"]
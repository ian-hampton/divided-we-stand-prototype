class SD_Event:
    
    def __init__(self, d: dict):
        self.type: str = d["Type"]
        self.duration: int = d["Duration"]
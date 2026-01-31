class SD_Alliance:
    
    def __init__(self, d: dict):
        self.required_agenda: str = d["Required Agenda"]
        self.capacity: bool = d.get("Capacity") is not None
        self.color_theme: str = d["Color Theme"]
        self.description: list = d["Description"]
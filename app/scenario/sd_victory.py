import copy
import json

class SD_VictoryCondition:
    
    def __init__(self):

        from .scenario import ScenarioInterface

        filename = "victory"
        filepath = f"scenarios/{ScenarioInterface.scenario}/{filename}.json"
        
        self.d = {}
        with open(filepath, 'r') as file:
            self.d = json.load(file)
        
    @property
    def easy(self):
        return copy.deepcopy(self.d["easy"])
    
    @property
    def medium(self):
        return copy.deepcopy(self.d["medium"])
    
    @property
    def hard(self):
        return copy.deepcopy(self.d["hard"])
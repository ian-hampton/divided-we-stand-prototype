from typing import Tuple

from app.game.games import Games
from app.scenario import ScenarioData as SD

class Alliance:
    
    def __init__(self, name: str, data: dict, game_id: str):
        self.name = name
        self._data = data
        self._game_id = game_id

    @property
    def type(self) -> str:
        return self._data["allianceType"]

    @type.setter
    def type(self, value: str) -> None:
        self._data["allianceType"] = value
    
    @property
    def turn_created(self) -> int:
        return self._data["turnCreated"]

    @turn_created.setter
    def turn_created(self, value: int) -> None:
        self._data["turnCreated"] = value

    @property
    def turn_ended(self) -> int:
        return self._data["turnEnded"]
    
    @turn_ended.setter
    def turn_ended(self, value: int) -> None:
        self._data["turnEnded"] = value
    
    @property
    def is_active(self) -> bool:
       return True if self.turn_ended == 0 else False

    @property
    def age(self) -> int:
        game = Games.load(self._game_id)
        if self.turn_ended == 0:
           return game.turn - self.turn_created
        else:
           return self.turn_ended - self.turn_created

    @property
    def current_members(self) -> dict[str, int]:
        return self._data["currentMembers"]

    @current_members.setter
    def current_members(self, value: dict) -> None:
        self._data["currentMembers"] = value

    @property
    def founding_members(self) -> dict[str, int]:
        return self._data["foundingMembers"]
    
    @founding_members.setter
    def founding_members(self, value: dict) -> None:
        self._data["foundingMembers"] = value

    @property
    def former_members(self) -> dict[str, int]:
        return self._data["formerMembers"]

    @former_members.setter
    def former_members(self, value: dict) -> None:
        self._data["formerMembers"] = value

    def add_member(self, nation_name: str) -> None:
        game = Games.load(self._game_id)
        if nation_name in self.former_members:
            del self.former_members[nation_name]
        self.current_members[nation_name] = game.turn

    def remove_member(self, nation_name: str) -> None:
        from app.nation.nations import Nations
        from app.truce import Truces
        
        game = Games.load(self._game_id)

        for allied_nation_name in self.current_members:
            
            if allied_nation_name == nation_name:
                continue

            nation = Nations.get(nation_name)
            allied_nation = Nations.get(allied_nation_name)
            Truces.create([nation.id, allied_nation.id], 2)
        
        del self.current_members[nation_name]
        self.former_members[nation_name] = game.turn

    def calculate_yield(self) -> Tuple[float, str | None]:
        
        from app.nation.nations import Nations

        if not self.is_active:
            return 0.0, None

        match self.type:
            
            case "Trade Agreement":
                
                total = 0.0
                for ally_name in self.current_members:
                    nation = Nations.get(ally_name)
                    total += nation.improvement_counts["Settlement"]
                    total += nation.improvement_counts["City"]
                    total += nation.improvement_counts["Central Bank"]
                    total += nation.improvement_counts["Capital"]
                
                return total * 0.5, "Dollars"

            case "Research Agreement":
                
                tech_set = set()
                for ally_name in self.current_members:
                    nation = Nations.get(ally_name)
                    ally_research_list = list(nation.completed_research.keys())
                    tech_set.update(ally_research_list)

                tech_set_filtered = set()
                for research_name in tech_set:
                    if research_name not in SD.agendas:
                        tech_set_filtered.add(research_name)

                return len(tech_set_filtered) * 0.2, "Research"

            case "Defense Pact":
                
                return len(self.current_members), "Military Capacity"

        return 0.0, None

    def end(self) -> None:

        game = Games.load(self._game_id)

        names = list(self.current_members.keys())
        for nation_name in names:
            self.remove_member(nation_name)
        
        self.current_members = {}
        self.turn_ended = game.turn
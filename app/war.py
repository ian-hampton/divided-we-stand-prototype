import json
import os
import random
from dataclasses import dataclass
from typing import ClassVar, Iterator, Tuple

from app import core
from app.nationdata import Nation, NationTable

class WarsMeta(type):
    
    def __iter__(cls) -> Iterator["War"]:
        for war_name in cls._data:
            yield War(war_name)

    def __len__(cls):
        return len(cls._data)

@dataclass
class Wars(metaclass=WarsMeta):
    
    game_id: ClassVar[str] = None
    _data: ClassVar[dict[str, dict]] = None

    @classmethod
    def load(cls, game_id: str) -> None:

        cls.game_id = game_id
        gamedata_filepath = f"gamedata/{cls.game_id}/gamedata.json"
        if not os.path.exists(gamedata_filepath):
            raise FileNotFoundError(f"Error: Unable to locate required game files for Alliances class.")
        
        with open(gamedata_filepath, 'r') as f:
            gamedata_dict = json.load(f)

        cls._data = gamedata_dict["wars"]

        cls.WARSCORE_FROM_VICTORY = 1
        cls.WARSCORE_FROM_OCCUPATION = 2
        cls.WARSCORE_FROM_DESTROY_IMPROVEMENT = 2
        cls.WARSCORE_FROM_CAPITAL_CAPTURE = 20
        cls.WARSCORE_FROM_NUCLEAR_STRIKE = 5

    @classmethod
    def save(cls) -> None:
        
        if cls._data is None:
            raise RuntimeError("Error: Wars has not been loaded.")
        
        gamedata_filepath = f"gamedata/{cls.game_id}/gamedata.json"
        with open(gamedata_filepath, 'r') as json_file:
            gamedata_dict = json.load(json_file)

        gamedata_dict["wars"] = cls._data
        with open(gamedata_filepath, 'w') as json_file:
            json.dump(gamedata_dict, json_file, indent=4)

    @classmethod
    def names(cls) -> list:
        return list(cls._data.keys())

    @classmethod
    def create(cls, main_attacker_id: str, main_defender_id: str, war_justification: str, war_claims = []) -> None:
        
        from app.alliance import Alliances
        nation_table = NationTable(cls.game_id)
        main_attacker = nation_table.get(main_attacker_id)
        main_defender = nation_table.get(main_defender_id)
        current_turn_num = core.get_current_turn_num(cls.game_id)

        # create new war
        war_name = cls._generate_war_name(main_attacker, main_defender, war_justification)
        new_war_data = {
            "start": current_turn_num,
            "end": 0,
            "outcome": "TBD",
            "combatants": {},
            "attackerWarScore": {
                "total": 0,
                "occupation": 0,
                "combatVictories": 0,
                "enemyUnitsDestroyed": 0,
                "enemyImprovementsDestroyed": 0,
                "capitalCaptures": 0,
                "nukedEnemyRegions": 0
            },
            "defenderWarScore": {
                "total": 0,
                "occupation": 0,
                "combatVictories": 0,
                "enemyUnitsDestroyed": 0,
                "enemyImprovementsDestroyed": 0,
                "capitalCaptures": 0,
                "nukedEnemyRegions": 0
            },
            "warLog": []
        }
        cls._data[war_name] = new_war_data
        new_war = cls.get(new_war)

        # add main attacker
        combatant = new_war.add_combatant(main_attacker, "Main Attacker", main_defender.id)
        combatant.justification = war_justification
        combatant.claims = cls._claim_pairs(war_claims)

        # add main defender
        combatant = new_war.add_combatant(main_defender, "Main Defender", "TBD")

        # call in main attacker allies
        # possible allies: puppet states
        puppet_states = core.get_subjects(cls.game_id, main_attacker.name, "Puppet State")
        possible_allies = set(puppet_states)
        for ally_id in possible_allies:
            ally = nation_table.get(ally_id)
            if (cls.get_war_name(main_defender.id, ally.id) is None                     # ally cannot already be at war with defender
                and not core.check_for_truce(cls.game_id, main_defender.id, ally.id)    # ally cannot have truce with defender
                and not Alliances.are_allied(main_defender.name, ally.name)             # ally cannot be allied with defender
                and not Alliances.former_ally_truce(main_defender.name, ally.name)):    # ally cannot be recently allied with defender
                combatant = new_war.add_combatant(ally, "Secondary Attacker", "TBD")

        # call in main defender allies
        # possible allies: puppet states, defensive pacts, overlord
        puppet_states = core.get_subjects(cls.game_id, main_defender.name, "Puppet State")
        defense_allies = Alliances.allies(main_defender.name, "Defense Pact")
        ally_player_ids = set(puppet_states) | set(defense_allies)
        if main_defender.status != "Independent Nation":
            for nation in nation_table:
                if nation.name in main_defender.status:
                    ally_player_ids.add(nation.id)
        for ally_id in possible_allies:
            ally = nation_table.get(ally_id)
            if (cls.get_war_name(main_attacker.id, ally.id) is None                     # ally cannot already be at war with attacker
                and not core.check_for_truce(cls.game_id, main_attacker.id, ally.id)    # ally cannot have truce with attacker
                and not Alliances.are_allied(main_attacker.name, ally.name)             # ally cannot be allied with attacker
                and not Alliances.former_ally_truce(main_attacker.name, ally.name)):    # ally cannot be recently allied with attacker
                combatant = new_war.add_combatant(ally, "Secondary Defender", "TBD")

    @classmethod
    def get(cls, war_name: str) -> "War":
        if war_name in cls._data:
            return War(war_name)
        return None

    @classmethod
    def get_war_name(cls, nation1_id: str, nation2_id: str) -> str | None:
        
        if nation1_id == nation2_id:
            return None

        for war in cls:
            if war.outcome == "TBD" and nation1_id in war.combatants and nation2_id in war.combatants:
                return war.name
            
        return None

    @classmethod
    def is_at_peace(cls, nation_id: str) -> bool:
        pass

    @classmethod
    def at_peace_for_x(cls, nation_id: str) -> int:
        pass

    @classmethod
    def total_units_lost(cls) -> int:
        pass

    @classmethod
    def total_improvements_lost(cls) -> int:
        pass

    @classmethod
    def total_missiles_launched(cls) -> int:
        pass

    @classmethod
    def find_longest_war(cls) -> tuple:
        pass

    @classmethod
    def add_warscore_from_occupations(cls) -> None:
        pass

    @classmethod
    def update_totals(cls) -> None:
        pass

    @classmethod
    def export_all_logs(cls) -> None:
        pass

    @classmethod
    def _generate_war_name(cls, main_attacker: Nation, main_defender: Nation, war_justification: str) -> str:
        
        match war_justification:
            
            case "Animosity":
                names = [
                    f"{main_attacker.name} - {main_defender.name} Conflict",
                    f"{main_attacker.name} - {main_defender.name} War",
                ]
           
            case "Border Skirmish":
                names = [
                    f"{main_attacker.name} - {main_defender.name} Conflict",
                    f"{main_attacker.name} - {main_defender.name} War",
                    f"{main_attacker.name} - {main_defender.name} War of Aggression",
                    f"{main_attacker.name} - {main_defender.name} Border Skirmish"
                ]
            
            case "Conquest":
                names = [
                    f"{main_attacker.name} - {main_defender.name} Conflict",
                    f"{main_attacker.name} - {main_defender.name} War",
                    f"{main_attacker.name} Invasion of {main_defender.name}",
                    f"{main_attacker.name} Conquest of {main_defender.name}",
                ]

            case "Containment":
                names = [
                    f"{main_attacker.name} - {main_defender.name} Conflict",
                    f"{main_attacker.name} - {main_defender.name} War",
                    f"{main_attacker.name} - {main_defender.name} Containment War",
                    f"{main_attacker.name} - {main_defender.name} Ideological War",
                    f"{main_attacker.name} - {main_defender.name} War of Ideology",
                ]
            
            case "Independence":
                names = [
                    f"{main_attacker.name} - {main_defender.name} Independence War",
                    f"{main_attacker.name} - {main_defender.name} Liberation War",
                    f"{main_attacker.name} War for Independence",
                    f"{main_attacker.name} Rebellion",
                ]
            
            case "Subjugation":
                names = [
                    f"{main_attacker.name} - {main_defender.name} Subjugation War"
                ]

            case "NULL":
                names = [
                    "Foreign Invasion"
                ]
        
        attempts = 0
        war_prefixes = ['2nd', '3rd', '4th', '5th', '6th', '7th', '8th', '9th', '10th']
        
        while True:
            
            war_name = random.sample(names, 1)[0]
            war_name_set = set(cls.names())
            
            while war_name in war_name_set:
                attempts += 1
                new_war_name = f'{war_prefixes[attempts]} {war_name}'
                if new_war_name not in war_name_set:
                    break
            
            return war_name

    @classmethod
    def _claim_pairs(cls, war_claims: list) -> dict:

        from app.region_new import Region

        pairs = {}
        
        for region_id in war_claims:
            region = Region(region_id)
            pairs[region_id] = region.data.owner_id

        return pairs

class War:

    def __init__(self, war_name: str):
    
        self._data = Wars._data[war_name]
        
        self.name = war_name
        self.combatants: dict = self._data["combatants"]
        self.attackers = WarScoreData(self._data["attackerWarScore"])
        self.defenders = WarScoreData(self._data["defenderWarScore"])
        self.log: list = self._data["warLog"]
        self._start: int = self._data["start"]
        self._end: int = self._data["end"]
        self._outcome: str = self._data["outcome"]

    @property
    def start(self):
        return self._start

    @property
    def end(self):
        return self._end
    
    @property
    def outcome(self):
        return self._outcome

    @end.setter
    def end(self, turn: int):
        self._end = turn
        self._data["end"] = turn

    @outcome.setter
    def outcome(self, outcome_str: str):
        self._outcome = outcome_str
        self._data["outcome"] = outcome_str

    def add_combatant(self, nation: Nation, role: str, target_id: str) -> None:
        
        combatant_data = {
            "id": nation.id,
            "role": role,
            "justification": "TBD",
            "targetID": target_id,
            "claims": {},
            "battlesWon": 0,
            "battlesLost": 0,
            "enemyUnitsDestroyed": 0,
            "enemyImprovementsDestroyed": 0,
            "friendlyUnitsDestroyed": 0,
            "friendlyImprovementsDestroyed": 0,
            "missilesLaunched": 0,
            "nukesLaunched": 0
        }

        self.combatants[nation.id] = combatant_data

    def get_combatant(self, nation_id: str) -> "Combatant":
        
        if nation_id in self.combatants:
            return Combatant(self.combatants[nation_id])
        
        raise Exception(f"Failed to retrieve nation #{nation_id} combatant data in war {self.name}.")

    def get_role(self, nation_id: str) -> str:
        pass

    def get_main_combatant_ids(self) -> tuple:
        pass

    def is_on_same_side(self, nation_id_1: str, nation_id_2: str) -> bool:
        pass

    def add_missing_justifications(self) -> None:
        pass

    def calculate_score_threshold(self) -> tuple:
        pass

    def _resolve_war_justification(nation_id: str):
        pass

class WarScoreData:
    
    def __init__(self, d: dict):

        self._data = d
        self._total: int = d["total"]
        self._occupation: int = d["occupation"]
        self._victories: int = d["combatVictories"]
        self._destroyed_units: int = d["enemyUnitsDestroyed"]
        self._destroyed_improvements: int = d["enemyImprovementsDestroyed"]
        self._captures: int = d["capitalCaptures"]
        self._nuclear_strikes: int = d["nukedEnemyRegions"]

    @property
    def total(self):
        return self._total

    @property
    def occupation(self):
        return self._occupation

    @property
    def victories(self):
        return self._victories
    
    @property
    def destroyed_units(self):
        return self._destroyed_units

    @property
    def destroyed_improvements(self):
        return self._destroyed_improvements
    
    @property
    def captures(self):
        return self._captures

    @property
    def nuclear_strikes(self):
        return self._nuclear_strikes
    
    @total.setter
    def total(self, value: int):
        self._total = value
        self._data["total"] = value

    @occupation.setter
    def occupation(self, value: int):
        self._occupation = value
        self._data["occupation"] = value

    @victories.setter
    def victories(self, value: int):
        self._victories = value
        self._data["combatVictories"] = value

    @destroyed_units.setter
    def destroyed_units(self, value: int):
        self._destroyed_units = value
        self._data["enemyUnitsDestroyed"] = value

    @destroyed_improvements.setter
    def destroyed_improvements(self, value: int):
        self._destroyed_improvements = value
        self._data["enemyImprovementsDestroyed"] = value

    @captures.setter
    def captures(self, value: int):
        self._captures = value
        self._data["capitalCaptures"] = value

    @nuclear_strikes.setter
    def nuclear_strikes(self, value: int):
        self._nuclear_strikes = value
        self._data["nukedEnemyRegions"] = value

class Combatant:
    
    def __init__(self, d: dict):

        self._data = d

        self.id: str = d["id"]
        self.role: str = d["role"]
        self.claims: dict = d["claims"]
        self.target_id: str = d["targetID"]
        self._justification: str = d["justification"]
        self._battles_won: int = d["battlesWon"]
        self._battles_lost: int = d["battlesLost"]
        self._destroyed_units: int = d["enemyUnitsDestroyed"]
        self._destroyed_improvements: int = d["enemyImprovementsDestroyed"]
        self._lost_units: int = d["friendlyUnitsDestroyed"]
        self._lost_improvements: int = d["friendlyImprovementsDestroyed"]
        self._launched_missiles: int = d["missilesLaunched"]
        self._launched_nukes: int = d["nukesLaunched"]

        # TODO: include attributes from Nation class (readonly)

    @property
    def justification(self):
        return self._justification
    
    @property
    def battles_won(self):
        return self._battles_won

    @property
    def battles_lost(self):
        return self._battles_lost
    
    @property
    def destroyed_units(self):
        return self._destroyed_units
    
    @property
    def destroyed_improvements(self):
        return self._destroyed_improvements

    @property
    def lost_units(self):
        return self._lost_units

    @property
    def lost_improvements(self):
        return self._lost_improvements

    @property
    def launched_missiles(self):
        return self._launched_missiles

    @property
    def launched_nukes(self):
        return self._launched_nukes

    @justification.setter
    def justification(self, value: str):
        self._justification = value
        self._data["justification"] = value

    @battles_won.setter
    def battles_won(self, value: int):
        self._battles_won = value
        self._data["battlesWon"] = value

    @battles_lost.setter
    def battles_lost(self, value: int):
        self._battles_lost = value
        self._data["battlesLost"] = value

    @destroyed_units.setter
    def destroyed_units(self, value: int):
        self._destroyed_units = value
        self._data["enemyUnitsDestroyed"] = value

    @destroyed_improvements.setter
    def destroyed_improvements(self, value: int):
        self._destroyed_improvements = value
        self._data["enemyImprovementsDestroyed"] = value

    @lost_units.setter
    def lost_units(self, value: int):
        self._lost_units = value
        self._data["friendlyUnitsDestroyed"] = value

    @lost_improvements.setter
    def lost_improvements(self, value: int):
        self._lost_improvements = value
        self._data["friendlyImprovementsDestroyed"] = value

    @launched_missiles.setter
    def launched_missiles(self, value: int):
        self._launched_missiles = value
        self._data["missilesLaunched"] = value

    @launched_nukes.setter
    def launched_nukes(self, value: int):
        self._launched_nukes = value
        self._data["nukesLaunched"] = value
import json
import os
import random
from dataclasses import dataclass
from typing import ClassVar, Iterator

from app.game.games import Games
from app.nation.nation import Nation
from .war import War
from .war_claims import ManageWarClaims
from .warscore import WarScore

class WarsMeta(type):
    
    def __iter__(cls) -> Iterator[War]:
        for war_name in cls._data:
            yield War(war_name, cls._data[war_name], cls.game_id)

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
        
        from app.alliance.alliances import Alliances
        from app.truce.truces import Truces
        from app.nation.nations import Nations

        game = Games.load(cls.game_id)
        main_attacker = Nations.get(main_attacker_id)
        main_defender = Nations.get(main_defender_id)

        # create new war
        war_name = cls._generate_war_name(main_attacker, main_defender, war_justification)
        new_war_data = {
            "start": game.turn,
            "end": 0,
            "outcome": "TBD",
            "combatants": {},
            "attackerWarScore": {
                "total": 0,
                "occupation": 0,
                "decisiveBattles": 0,
                "enemyUnitsDestroyed": 0,
                "enemyImprovementsDestroyed": 0,
                "capitalCaptures": 0,
                "nukedEnemyRegions": 0
            },
            "defenderWarScore": {
                "total": 0,
                "occupation": 0,
                "decisiveBattles": 0,
                "enemyUnitsDestroyed": 0,
                "enemyImprovementsDestroyed": 0,
                "capitalCaptures": 0,
                "nukedEnemyRegions": 0
            },
            "warLog": []
        }
        cls._data[war_name] = new_war_data
        new_war = cls.get(war_name)

        # add main attacker
        new_war.add_combatant(main_attacker, "Main Attacker", main_defender.id)
        combatant = new_war.get_combatant(main_attacker.id)
        combatant.justification = war_justification
        manage_claims = ManageWarClaims(combatant.name, combatant.justification)
        combatant.claims = manage_claims.claim_pairs(war_claims)

        # add main defender
        new_war.add_combatant(main_defender, "Main Defender", "TBD")

        # call in main attacker allies
        # possible allies: puppet states
        puppet_states = main_attacker.get_subjects("Puppet State", list(Nations))
        possible_allies = set(puppet_states)
        for ally_id in possible_allies:
            ally = Nations.get(ally_id)
            if (cls.get_war_name(main_defender.id, ally.id) is None              # ally cannot already be at war with defender
                and not Truces.are_truced(main_defender.id, ally.id)             # ally cannot have truce with defender
                and not Alliances.are_allied(main_defender.name, ally.name)):    # ally cannot be allied with defender
                new_war.add_combatant(ally, "Secondary Attacker", "TBD")

        # call in main defender allies
        # possible allies: puppet states, defensive pacts, overlord
        puppet_states = main_defender.get_subjects("Puppet State", list(Nations))
        defense_allies = Alliances.allies(main_defender.name, "Defense Pact")
        ally_player_ids = set(puppet_states) | set(defense_allies)
        if main_defender.status != "Independent Nation":
            for nation in Nations:
                if nation.name in main_defender.status:
                    ally_player_ids.add(nation.id)
        for ally_id in possible_allies:
            ally = Nations.get(ally_id)
            if (cls.get_war_name(main_attacker.id, ally.id) is None              # ally cannot already be at war with attacker
                and not Truces.are_truced(main_attacker.id, ally.id)             # ally cannot have truce with attacker
                and not Alliances.are_allied(main_attacker.name, ally.name)):    # ally cannot be allied with attacker
                new_war.add_combatant(ally, "Secondary Defender", "TBD")

    @classmethod
    def get(cls, war_name: str) -> War:
        if war_name in cls._data:
            return War(war_name, cls._data[war_name], cls.game_id)
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
        for war in cls:
            if war.outcome == "TBD" and nation_id in war.combatants:
                return False
        return True

    @classmethod
    def at_peace_for_x(cls, nation_id: str) -> int:
        
        game = Games.load(cls.game_id)

        last_at_war_turn = -1
        for war in cls:
            if nation_id not in war.combatants:
                continue
            if war.outcome == "TBD":
                return 0
            elif war.end > last_at_war_turn:
                last_at_war_turn = war.end
        
        return game.turn - last_at_war_turn

    @classmethod
    def total_units_lost(cls) -> int:
        
        total = 0
        for war in cls:
            for combatant_id in war.combatants:
                combatant = war.get_combatant(combatant_id)
                total += combatant.lost_units

        return total

    @classmethod
    def total_improvements_lost(cls) -> int:
        
        total = 0
        for war in cls:
            for combatant_id in war.combatants:
                combatant = war.get_combatant(combatant_id)
                total += combatant.lost_improvements

        return total

    @classmethod
    def total_missiles_launched(cls) -> int:
        
        total = 0
        for war in cls:
            for combatant_id in war.combatants:
                combatant = war.get_combatant(combatant_id)
                total += combatant.launched_nukes

        return total

    @classmethod
    def find_longest_war(cls) -> tuple:

        game = Games.load(cls.game_id)

        longest_name = None
        longest_time = 0

        for war in cls:
            
            if war.outcome == "TBD":
                war_duration = game.turn - war.start
            else:
                war_duration = war.end - war.start
            
            if war_duration > longest_time:
                longest_name = war.name
                longest_time = war_duration
        
        return longest_name, longest_time

    @classmethod
    def add_warscore_from_occupations(cls) -> None:
        
        from app.region.regions import Regions
        from app.nation.nations import Nations

        for region in Regions:
            
            if region.data.occupier_id in ["0", "99"]:
                continue

            war_name = cls.get_war_name(region.data.owner_id, region.data.occupier_id)
            war = cls.get(war_name)
            occupier_war_role = war.get_role(region.data.occupier_id)
            occupier_nation = Nations.get(region.data.occupier_id)

            if "Scorched Earth" in occupier_nation.completed_research:
                score += 1
            
            if "Attacker" in occupier_war_role:
                war.attackers.occupation += WarScore.FROM_OCCUPATION
            else:
                war.defenders.occupation += WarScore.FROM_OCCUPATION

    @classmethod
    def update_totals(cls) -> None:
        
        for war in cls:
            
            if war.outcome != "TBD":
                continue

            war.attackers.total = 0
            war.attackers.total += war.attackers.occupation
            war.attackers.total += war.attackers.victories
            war.attackers.total += war.attackers.destroyed_units
            war.attackers.total += war.attackers.destroyed_improvements
            war.attackers.total += war.attackers.captures
            war.attackers.total += war.attackers.nuclear_strikes

            war.defenders.total = 0
            war.defenders.total += war.defenders.occupation
            war.defenders.total += war.defenders.victories
            war.defenders.total += war.defenders.destroyed_units
            war.defenders.total += war.defenders.destroyed_improvements
            war.defenders.total += war.defenders.captures
            war.defenders.total += war.defenders.nuclear_strikes

    @classmethod
    def export_all_logs(cls) -> None:
        
        directory = f"gamedata/{cls.game_id}/logs"

        for war in cls:
            
            if war.outcome != "TBD":
                continue

            os.makedirs(directory, exist_ok=True)
            filename = os.path.join(directory, f"{war.name}.txt")
            
            with open(filename, 'w') as file:
                for entry in war.log:
                    file.write(entry + '\n')
            
            war.log = []

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
        
        # randomly select a war name based on the justification
        name = random.choice(names)
        if name not in cls._data:
            return name
        
        # add prefix to war name if war already occured
        war_prefixes = ['2nd', '3rd']
        for prefix in war_prefixes:
            new_name = f"{prefix} {name}"
            if new_name not in cls._data:
                return new_name
        
        # failsafe (highly unlikely this code will be used)
        prefix = 4
        while True:
            new_name = f"{prefix}th {name}"
            if new_name not in cls._data:
                return new_name
            prefix += 1
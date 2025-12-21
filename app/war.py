import json
import os
import random
from dataclasses import dataclass
from typing import ClassVar, Iterator, Tuple

from app import core
from app.scenario import ScenarioData as SD
from app.game.games import Games
from app.nation.nation import Nation


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

        # TODO - make these enums
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
        new_war = cls.get(war_name)

        # add main attacker
        new_war.add_combatant(main_attacker, "Main Attacker", main_defender.id)
        combatant = new_war.get_combatant(main_attacker.id)
        combatant.justification = war_justification
        combatant.claims = cls._claim_pairs(war_claims)

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
    def get_war_claims(cls, nation_name: str, war_justification: str) -> tuple[int, list]:
        
        claim_cost = -1
        
        while claim_cost == -1:
            region_claims_str = input(f"List the regions that {nation_name} is claiming using {war_justification}: ")
            region_claims_list = region_claims_str.split(',')
            claim_cost = cls._validate_war_claims(war_justification, region_claims_list)
        
        return claim_cost, region_claims_list

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
        
        from app.region import Regions
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
                war.attackers.occupation += cls.WARSCORE_FROM_OCCUPATION
            else:
                war.defenders.occupation += cls.WARSCORE_FROM_OCCUPATION

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

        from app.region import Regions

        pairs = {}
        
        for region_id in war_claims:
            region = Regions.load(region_id)
            pairs[region_id] = region.data.owner_id

        return pairs

    @classmethod
    def _validate_war_claims(cls, war_justification: str, region_claims_list: list[str]) -> int:

        from app.region import Regions

        region_id_set = set(Regions.ids())
        war_justification_data = SD.war_justificiations[war_justification]

        total = 0
        if not war_justification_data.has_war_claims:
            return 0

        for i, region_id in enumerate(region_claims_list):
            
            if region_id not in region_id_set:
                return -1
            
            if i + 1 > war_justification_data.max_claims:
                return -1
            
            if i + 1 > war_justification_data.free_claims:
                total += war_justification_data.claim_cost

        return total

class War:

    def __init__(self, war_name: str):
        self._data = Wars._data[war_name]
        self.name = war_name
        self.attackers = WarScoreData(self._data["attackerWarScore"])
        self.defenders = WarScoreData(self._data["defenderWarScore"])

    @property
    def start(self) -> int:
        return self._data["start"]

    @property
    def end(self) -> int:
        return self._data["end"]
    
    @end.setter
    def end(self, turn: int) -> None:
        self._data["end"] = turn

    @property
    def outcome(self) -> str:
        return self._data["outcome"]

    @outcome.setter
    def outcome(self, outcome_str: str) -> None:
        self._data["outcome"] = outcome_str

    @property
    def combatants(self) -> dict:
        return self._data["combatants"]

    @combatants.setter
    def combatants(self, value: dict) -> None:
        self._data["combatants"] = value

    @property
    def log(self) -> list:
        return self._data["warLog"]

    @log.setter
    def log(self, value: list) -> None:
        self._data["warLog"] = value

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
        if nation_id in self.combatants:
            combatant = self.get_combatant(nation_id)
            return combatant.role
        return None

    def get_main_combatant_ids(self) -> tuple[str, str]:
        
        main_attacker_id = ""
        main_defender_id = ""

        for nation_id in self.combatants:
            combatant = self.get_combatant(nation_id)
            if combatant.role == "Main Attacker":
                main_attacker_id = nation_id
            elif combatant.role == "Main Defender":
                main_defender_id = nation_id

        return main_attacker_id, main_defender_id
    
    def is_on_same_side(self, nation_id_1: str, nation_id_2: str) -> bool:
        
        combatant_1 = self.get_combatant(nation_id_1)
        combatant_2 = self.get_combatant(nation_id_2)

        if "Attacker" in combatant_1.role and "Attacker" in combatant_2.role:
            return True
        elif "Defender" in combatant_1.role and "Defender" in combatant_2.role:
            return True
        
        return False

    def add_missing_justifications(self) -> None:
        
        from app.nation.nations import Nations

        for combatant_id in self.combatants:
            
            combatant = self.get_combatant(combatant_id)
            combatant_nation = Nations.get(combatant_id)
            region_claims_list = []

            if combatant.justification != "TBD":
                continue
                
            war_justification = input(f"Please enter {combatant.name} war justification for {self.name} or enter SKIP to postpone: ")
            if war_justification == "SKIP":
                continue

            # process war claims
            if SD.war_justificiations[war_justification].has_war_claims:
                
                claim_cost, region_claims_list = Wars.get_war_claims(combatant.name, war_justification)
                if float(combatant_nation.get_stockpile("Political Power")) - claim_cost < 0:
                    combatant_nation.action_log.append(f"Error: Not enough political power for war claims.")
                    continue
                
                combatant.target_id = "N/A"
                combatant_nation.update_stockpile("Political Power", -1 * claim_cost)
                combatant.claims = Wars._claim_pairs(region_claims_list)
            
            # OR handle war justification that does not seize territory
            else:
                target_id = input(f"Enter nation_id of nation {combatant.name} is targeting with {war_justification}: ")
                combatant.target_id = str(target_id)
            
            combatant.justification = war_justification

    def calculate_score_threshold(self) -> tuple:
        
        from app.nation.nations import Nations

        # initial win threshold is a 100 point difference
        attacker_threshold = 100
        defender_threshold = 100

        # check for unyielding and crime syndicate
        for combatant_id in self.combatants:
            combatant = self.get_combatant(combatant_id)
            combatant_nation = Nations.get(combatant_id)
            
            # add modifiers to defender threshold
            if combatant.role == "Main Attacker" and defender_threshold == 100:
                if combatant_nation.gov == "Crime Syndicate":
                    defender_threshold = None
                elif "Unyielding" in combatant_nation.completed_research:
                    defender_threshold += 50
            
            # add modifiers to attacker threshold
            elif combatant.role == "Main Defender" and attacker_threshold == 100:
                if combatant_nation.gov == "Crime Syndicate":
                    attacker_threshold = None
                elif "Unyielding" in combatant_nation.completed_research:
                    attacker_threshold += 50

        # if not crime syndicate compute remaining threshold
        if attacker_threshold is not None:
            attacker_threshold += self.defenders.total
        if defender_threshold is not None:
            defender_threshold += self.attackers.total

        return attacker_threshold, defender_threshold

    def end_conflict(self, outcome: str) -> None:
        
        from app.nation.nations import Nations
        from app.region import Regions
        from app.truce.truces import Truces
        game = Games.load(Wars.game_id)
        
        # resolve war justifications
        truce_length = 4
        match outcome:
            
            case "Attacker Victory":
                for combatant_id in self.combatants:
                    combatant = self.get_combatant(combatant_id)
                    if combatant.justification in ["TBD", "N/A"]:
                        continue
                    if "Attacker" in combatant.role:
                        self._resolve_war_justification(combatant_id)
                    if "Main Attacker" == combatant.role:
                        truce_length = SD.war_justificiations[combatant.justification].truce_duration

            case "Defender Victory":
                for combatant_id in self.combatants:
                    combatant = self.get_combatant(combatant_id)
                    if "Defender" in combatant.role:
                        self._resolve_war_justification(combatant_id)
                    if "Main Defender" == combatant.role:
                        truce_length = SD.war_justificiations[combatant.justification].truce_duration
        
        # add truce periods
        for combatant_id in self.combatants:
            attacker = self.get_combatant(combatant_id)
            if 'Attacker' not in attacker.role:
                continue
            for temp_id in self.combatants:
                defender = self.get_combatant(temp_id)
                if temp_id == combatant_id or 'Defender' not in defender.role:
                    continue
                signatories = [attacker.id, defender.id]
                Truces.create(signatories, truce_length)

        # update war
        self.end = game.turn
        self.outcome = outcome

        # end occupations
        for region in Regions:
            if region.data.owner_id in self.combatants and region.data.occupier_id in self.combatants:
                region.data.occupier_id = "0"

        # withdraw units
        core.withdraw_units()

        # resolve foreign interference tag if applicable (event)
        attacker_id, defender_id = self.get_main_combatant_ids()
        attacker_nation = Nations.get(attacker_id)
        defender_nation = Nations.get(defender_id)
        if "Foreign Interference" in attacker_nation.tags and attacker_nation.tags["Foreign Interference"]["Foreign Interference Target"] == defender_nation.name:
            del attacker_nation.tags["Foreign Interference"]
            if outcome == "Attacker Victory":
                attacker_nation.update_stockpile("Dollars", 50)
                attacker_nation.update_stockpile("Research", 20)
                attacker_nation.update_stockpile("Advanced Metals", 10)

    def _resolve_war_justification(self, nation_id: str):
        
        from app.nation.nations import Nations
        from app.region import Regions
        game = Games.load(Wars.game_id)
        
        winner_nation = Nations.get(nation_id)
        winner_combatant_data = self.get_combatant(nation_id)
        war_justification_data = SD.war_justificiations[winner_combatant_data.justification]

        if war_justification_data.has_war_claims:
            for region_id, original_owner_id in winner_combatant_data.claims.items():
                region = Regions.load(region_id)
                
                # do not take over regions that have changed ownership since start of war
                if str(region.data.owner_id) != original_owner_id:
                    continue
                    
                if region.improvement.name is not None:
                    looser_nation = Nations.get(original_owner_id)
                    looser_nation.improvement_counts[region.improvement.name] -= 1
                    winner_nation.improvement_counts[region.improvement.name] += 1
                
                region.data.owner_id = winner_nation.id
                region.data.occupier_id = "0"

        for resource_name, amount in war_justification_data.winner_stockpile_gains:
            winner_nation.update_stockpile(resource_name, amount)

        for resource_name, amount in war_justification_data.looser_stockpile_gains:
            looser_nation = Nations.get(winner_combatant_data.target_id)
            looser_nation.update_stockpile(resource_name, amount)

        if war_justification_data.looser_penalties is not None:
            looser_nation = Nations.get(winner_combatant_data.target_id)
            war_justification_data.looser_penalties["Expire Turn"] = game.turn + war_justification_data.looser_penalty_duration + 1
            looser_nation.tags[f"Defeated by {winner_nation} in {self.name}"] = war_justification_data.looser_penalties

        if war_justification_data.winner_becomes_independent:
            winner_nation.status = "Independent Nation"

        if war_justification_data.looser_releases_all_puppet_states:
            looser_nation = Nations.get(winner_combatant_data.target_id)
            for nation in Nations:
                if looser_nation.name in nation.status:
                    winner_nation.status = "Independent Nation"

        if war_justification_data.looser_becomes_puppet_state:
            looser_nation = Nations.get(winner_combatant_data.target_id)
            looser_nation.status = f"Puppet State of {winner_nation.name}"

class WarScoreData:
    
    def __init__(self, d: dict):
        self._data = d

    @property
    def total(self) -> int:
        return self._data["total"]
    
    @total.setter
    def total(self, value: int) -> None:
        self._data["total"] = value

    @property
    def occupation(self) -> int:
        return self._data["occupation"]

    @occupation.setter
    def occupation(self, value: int) -> None:
        self._data["occupation"] = value

    @property
    def victories(self) -> int:
        return self._data["combatVictories"]
    
    @victories.setter
    def victories(self, value: int) -> None:
        self._data["combatVictories"] = value

    @property
    def destroyed_units(self) -> int:
        return self._data["enemyUnitsDestroyed"]

    @destroyed_units.setter
    def destroyed_units(self, value: int) -> None:
        self._data["enemyUnitsDestroyed"] = value

    @property
    def destroyed_improvements(self) -> int:
        return self._data["enemyImprovementsDestroyed"]
    
    @destroyed_improvements.setter
    def destroyed_improvements(self, value: int) -> None:
        self._data["enemyImprovementsDestroyed"] = value

    @property
    def captures(self) -> int:
        return self._data["capitalCaptures"]

    @captures.setter
    def captures(self, value: int) -> None:
        self._data["capitalCaptures"] = value

    @property
    def nuclear_strikes(self) -> int:
        return self._data["nukedEnemyRegions"]

    @nuclear_strikes.setter
    def nuclear_strikes(self, value: int) -> None:
        self._data["nukedEnemyRegions"] = value

class Combatant:
    
    def __init__(self, d: dict):
        self._data = d
        self.id: str = self._data["id"]
        self.role: str = self._data["role"]

        from app.nation.nations import Nations
        nation = Nations.get(self.id)
        self.name = nation.name
        # TODO - restructure Combatant and Nation to both pull nationattribute sfrom a parent class
    
    @property
    def target_id(self) -> str:
        return self._data["targetID"]
    
    @target_id.setter
    def target_id(self, value: str):
        self._data["targetID"] = value

    @property
    def justification(self) -> str:
        return self._data["justification"]

    @justification.setter
    def justification(self, value: str):
        self._data["justification"] = value

    @property
    def battles_won(self) -> int:
        return self._data["battlesWon"]

    @battles_won.setter
    def battles_won(self, value: int):
        self._data["battlesWon"] = value

    @property
    def battles_lost(self) -> int:
        return self._data["battlesLost"]
    
    @battles_lost.setter
    def battles_lost(self, value: int):
        self._data["battlesLost"] = value

    @property
    def destroyed_units(self) -> int:
        return self._data["enemyUnitsDestroyed"]
    
    @destroyed_units.setter
    def destroyed_units(self, value: int):
        self._data["enemyUnitsDestroyed"] = value

    @property
    def destroyed_improvements(self) -> int:
        return self._data["enemyImprovementsDestroyed"]

    @destroyed_improvements.setter
    def destroyed_improvements(self, value: int):
        self._data["enemyImprovementsDestroyed"] = value

    @property
    def lost_units(self) -> int:
        return self._data["friendlyUnitsDestroyed"]

    @lost_units.setter
    def lost_units(self, value: int):
        self._data["friendlyUnitsDestroyed"] = value

    @property
    def lost_improvements(self) -> int:
        return self._data["friendlyImprovementsDestroyed"]

    @lost_improvements.setter
    def lost_improvements(self, value: int):
        self._data["friendlyImprovementsDestroyed"] = value

    @property
    def launched_missiles(self) -> int:
        return self._data["missilesLaunched"]

    @launched_missiles.setter
    def launched_missiles(self, value: int):
        self._data["missilesLaunched"] = value

    @property
    def launched_nukes(self) -> int:
        return self._data["nukesLaunched"]

    @launched_nukes.setter
    def launched_nukes(self, value: int):
        self._data["nukesLaunched"] = value

    @property
    def claims(self) -> dict:
        return self._data["claims"]

    @claims.setter
    def claims(self, value: dict) -> None:
        self._data["claims"] = value
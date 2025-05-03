import json
import os
import random

from app import core
from app.region import Region
from app.nationdata import Nation
from app.nationdata import NationTable
from app.alliance import AllianceTable

class Combatant:
    
    def __init__(self, combatant_id: str, combatant_data: str, war_id: str):
        
        self.war_id = war_id

        self.id = combatant_id
        self.name: str = combatant_data["name"]
        self.role: str = combatant_data["role"]
        self.justification: str = combatant_data["justification"]
        self.claims: dict = combatant_data["claims"]

        self.battles_won : int = combatant_data["statistics"]["battlesWon"]
        self.battles_lost : int = combatant_data["statistics"]["battlesLost"]
        self.destroyed_units : int = combatant_data["statistics"]["enemyUnitsDestroyed"]
        self.destroyed_improvements : int = combatant_data["statistics"]["enemyImprovementsDestroyed"]
        self.lost_units : int = combatant_data["statistics"]["friendlyUnitsDestroyed"]
        self.lost_improvements : int = combatant_data["statistics"]["friendlyImprovementsDestroyed"]
        self.launched_missiles : int = combatant_data["statistics"]["missilesLaunched"]
        self.launched_nukes : int = combatant_data["statistics"]["nukesLaunched"]

    def _build(nation: Nation, role: str, war_id: str):

        combatant_data = {
            "name": nation.name,
            "role": role,
            "justification": "TBD",
            "claims": {},
            "statistics": {
                "battlesWon": 0,
                "battlesLost": 0,
                "enemyUnitsDestroyed": 0,
                "enemyImprovementsDestroyed": 0,
                "friendlyUnitsDestroyed": 0,
                "friendlyImprovementsDestroyed": 0,
                "missilesLaunched": 0,
                "nukesLaunched": 0
            }
        }

        return Combatant(nation.id, combatant_data, war_id)

class War:
    
    def __init__(self, war_id: str, war_data: dict, game_id: str):
        
        self.game_id = game_id

        self.id = war_id
        self.name: str = war_data["name"]
        self.start: int = war_data["start"]
        self.end: int = war_data["end"]
        self.outcome: str = war_data["outcome"]
        self.log: list = war_data["warLog"]
        self.combatants: dict = war_data["combatants"]

        self.attacker_total: int = war_data["attackerWarScore"]["total"]
        self.attacker_occupation: int = war_data["attackerWarScore"]["occupation"]
        self.attacker_victories: int = war_data["attackerWarScore"]["combatVictories"]
        self.attacker_destroyed_units: int = war_data["attackerWarScore"]["enemyUnitsDestroyed"]
        self.attacker_destroyed_improvements: int = war_data["attackerWarScore"]["enemyImprovementsDestroyed"]
        self.attacker_captures: int = war_data["attackerWarScore"]["capitalCaptures"]
        self.attacker_nuclear_strikes: int = war_data["attackerWarScore"]["nukedEnemyRegions"]

        self.defender_total: int = war_data["defenderWarScore"]["total"]
        self.defender_occupation: int = war_data["defenderWarScore"]["occupation"]
        self.defender_victories: int = war_data["defenderWarScore"]["combatVictories"]
        self.defender_destroyed_units: int = war_data["defenderWarScore"]["enemyUnitsDestroyed"]
        self.defender_destroyed_improvements: int = war_data["defenderWarScore"]["enemyImprovementsDestroyed"]
        self.defender_captures: int = war_data["defenderWarScore"]["capitalCaptures"]
        self.defender_nuclear_strikes: int = war_data["defenderWarScore"]["nukedEnemyRegions"]

    def build(game_id: str, war_id: str, main_attacker: Nation, main_defender: Nation, war_justification: str) -> "War":

        current_turn_num = core.get_current_turn_num(game_id)

        war_data = {
            "name": War._generate_war_name(game_id, main_attacker, main_defender, war_justification),
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

        return War(war_id, war_data, game_id)

    def _generate_war_name(game_id: str, main_attacker: Nation, main_defender: Nation, war_justification: str) -> str:
        """
        Generates a unique war name.

        Params:
            game_id (str): Game ID string.
            main_attacker_name (str): nation name of main attacker
            main_defender_name (str): nation name of main defender
            war_justification (str): war justification of main attacker

        Returns:
            war_name (str): generated war name
        """

        # get game data
        war_table = WarTable(game_id)

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
            
            case "Independence":
                names = [
                    f"{main_attacker.name} - {main_defender.name} Independence War",
                    f"{main_attacker.name} - {main_defender.name} Liberation War",
                    f"{main_attacker.name} War for Independence",
                    f"{main_attacker.name} Rebellion",
                ]
            
            case "Subjugation":
                names = [
                    f"{main_attacker.name} - {main_defender.name} Annexation Attempt",
                    f"{main_attacker.name} - {main_defender.name} Subjugation War",
                ]
        
        attempts = 0
        war_prefixes = ['2nd', '3rd', '4th', '5th', '6th', '7th', '8th', '9th', '10th']
        
        while True:
            
            war_name = random.sample(names, 1)[0]
            war_name_set = set(war_table._name_to_id.keys())
            
            while war_name in war_name_set:
                attempts += 1
                new_war_name = f'{war_prefixes[attempts]} {war_name}'
                if new_war_name not in war_name_set:
                    break
            
            return war_name
    
    def add_combatant(self, nation: Nation, role: str) -> Combatant:
        
        combatant = Combatant._build(nation, role, self.id)
        self.save_combatant(combatant)

        return combatant

    def save_combatant(self, combatant: Combatant) -> None:
        
        combatant_data = {
            "name": combatant.name,
            "role": combatant.role,
            "justification": combatant.justification,
            "claims": combatant.claims,
            "statistics": {
                "battlesWon": combatant.battles_won,
                "battlesLost": combatant.battles_lost,
                "enemyUnitsDestroyed": combatant.destroyed_units,
                "enemyImprovementsDestroyed": combatant.destroyed_improvements,
                "friendlyUnitsDestroyed": combatant.lost_units,
                "friendlyImprovementsDestroyed": combatant.lost_improvements,
                "missilesLaunched": combatant.launched_missiles,
                "nukesLaunched": combatant.launched_nukes
            }
        }

        self.combatants[combatant.id] = combatant_data

class WarTable:
    
    def __init__(self, game_id: str):

        gamedata_filepath = f'gamedata/{game_id}/gamedata.json'
        
        if os.path.exists(gamedata_filepath):
            self.game_id: str = game_id
            self.reload()
        else:
            raise FileNotFoundError(f"Error: Unable to locate {gamedata_filepath} during nation class initialization.")

    def __len__(self):
        return len(self.data)

    def __iter__(self):
        for war_id, war_data in self.data.items():
            yield War(war_id, war_data, self.game_id)

    def _get_id_from_name(self, war_name: str) -> str | None:
        
        for temp in self._name_to_id:
            if war_name.lower() == temp.lower():
                return self._name_to_id[temp]
        
        return None
    
    def _claim_pairs(self, war_claims: list) -> dict:

        from app.region import Region

        pairs = {}
        
        for region_id in war_claims:
            region = Region(region_id)
            pairs[region_id] = str(region.owner_id)

        return pairs

    def reload(self) -> None:
        
        gamedata_filepath = f'gamedata/{self.game_id}/gamedata.json'
        with open(gamedata_filepath, 'r') as json_file:
            gamedata_dict = json.load(json_file)
        
        self.data: dict = gamedata_dict["wars"]
        self._name_to_id = {}
        for war in self:
            self._name_to_id[war.name.lower()] = war.id

    def create(self, main_attacker_id: str, main_defender_id: str, war_justification: str, war_claims = []) -> War:

        # get game data
        nation_table = NationTable(self.game_id)
        alliance_table = AllianceTable(self.game_id)
        trucedata_filepath = f'gamedata/{self.game_id}/trucedata.csv'
        trucedata_list = core.read_file(trucedata_filepath, 1)
        current_turn_num = core.get_current_turn_num(self.game_id)

        # create war
        war_id = str(len(self) + 1)
        main_attacker = nation_table.get(main_attacker_id)
        main_defender = nation_table.get(main_defender_id)
        new_war: War = War.build(war_id, main_attacker, main_defender, war_justification)

        # add main attacker
        combatant = new_war.add_combatant(main_attacker, "Main Attacker")
        combatant.justification = war_justification
        combatant.claims = self._claim_pairs(war_claims)
        new_war.save_combatant(combatant)

        # add main defender
        combatant = War.add_combatant(main_defender, "Main Defender")

        # call in main attacker allies
        # possible allies: puppet states
        puppet_states = core.get_subjects(self.game_id, main_attacker.name, "Puppet State")
        possible_allies = set(puppet_states)
        for ally_id in possible_allies:
            ally = nation_table.get(ally_id)
            if (
                self.get_war(main_defender.id, ally.id) is None                                            # ally cannot already be at war with defender
                and not core.check_for_truce(trucedata_list, main_defender.id, ally.id, current_turn_num)  # ally cannot have truce with defender
                and not alliance_table.are_allied(main_defender.name, ally.name)                           # ally cannot be allied with defender
                and not alliance_table.former_ally_truce(main_defender.name, ally.name)                    # ally cannot be recently allied with defender
            ):
                combatant = new_war.add_combatant(ally, "Secondary Attacker")

        # call in main defender allies
        # possible allies: puppet states, defensive pacts, overlord
        puppet_states = core.get_subjects(self.game_id, main_defender.name, "Puppet State")
        defense_allies = alliance_table.get_allies(main_defender.name, "Defense Pact")
        ally_player_ids = set(puppet_states) | set(defense_allies)
        if main_defender.status != "Independent Nation":
            for nation in nation_table:
                if nation.name in main_defender.status:
                    ally_player_ids.add(nation.id)
        for ally_id in possible_allies:
            ally = nation_table.get(ally_id)
            if (
                self.get_war(main_attacker.id, ally.id) is None                                            # ally cannot already be at war with attacker
                and not core.check_for_truce(trucedata_list, main_attacker.id, ally.id, current_turn_num)  # ally cannot have truce with attacker
                and not alliance_table.are_allied(main_attacker.name, ally.name)                           # ally cannot be allied with attacker
                and not alliance_table.former_ally_truce(main_attacker.name, ally.name)                    # ally cannot be recently allied with attacker
            ):
                combatant = new_war.add_combatant(ally, "Secondary Defender")
        
        self.save(new_war)
        return new_war
    
    def save(self, war: War) -> None:
        
        war_data = {
            "warName": war.name,
            "start": war.start,
            "end": war.end,
            "outcome": war.outcome,
            "combatants": war.combatants,
            "attackerWarScore": {
                "total": war.attacker_total,
                "occupation": war.attacker_occupation,
                "combatVictories": war.attacker_victories,
                "enemyUnitsDestroyed": war.attacker_destroyed_units,
                "enemyImprovementsDestroyed": war.attacker_destroyed_improvements,
                "capitalCaptures": war.attacker_captures,
                "nukedEnemyRegions": war.attacker_nuclear_strikes
            },
            "defenderWarScore": {
                "total": war.defender_total,
                "occupation": war.defender_occupation,
                "combatVictories": war.defender_victories,
                "enemyUnitsDestroyed": war.defender_destroyed_units,
                "enemyImprovementsDestroyed": war.defender_destroyed_improvements,
                "capitalCaptures": war.defender_captures,
                "nukedEnemyRegions": war.defender_nuclear_strikes
            },
            "warLog": war.log
        }

        self.data[war.id] = war_data

        gamedata_filepath = f'gamedata/{self.game_id}/gamedata.json'
        with open(gamedata_filepath, 'r') as json_file:
            gamedata_dict = json.load(json_file)

        gamedata_dict["wars"] = self.data
        with open(gamedata_filepath, 'w') as json_file:
            json.dump(gamedata_dict, json_file, indent=4)

        self._name_to_id = {}
        for nation in self:
            self._name_to_id[nation.name.lower()] = nation.id

    def get_war(self, nation1_id: str, nation2_id: str) -> str | None:
        
        for war in self:
            if war.end == 0 and nation1_id in war.combatants and nation2_id in war.combatants:
                return war.name
            
        return None
                
import ast
import copy
import json
from json.decoder import JSONDecodeError
import random

from app import core

class WarData:

    def __init__(self, game_id: str):
        
        # check if game id is valid
        wardata_filepath = f'gamedata/{game_id}/wardata.json'
        wardata_dict = {}
        try:
            with open(wardata_filepath, 'r') as json_file:
                wardata_dict = json.load(json_file)
        except FileNotFoundError:
            print(f"Error: Unable to locate {wardata_filepath} during Wardata class initialization.")
        except JSONDecodeError:
            print(f"Error: {wardata_filepath} is not a valid JSON file. Initializing with empty data.")

        # set attributes now that all checks have passed
        self.game_id: str = game_id
        self.wardata_filepath: str = wardata_filepath
        self.wardata_dict = wardata_dict
        self.war_template = {
            "startTurn": 0,
            "endTurn": 0,
            "outcome": "TBD",
            "combatants": {},
            "attackerWarScore": {
                "total": 0,
                "occupation": 0,
                "combatVictories": 0,
                "enemyUnitsDestroyed": 0,
                "enemyImprovementsDestroyed": 0,
                "capitalCaptures": 0,
                "nukes": 0
            },
            "defenderWarScore": {
                "total": 0,
                "occupation": 0,
                "combatVictories": 0,
                "enemyUnitsDestroyed": 0,
                "enemyImprovementsDestroyed": 0,
                "capitalCaptures": 0,
                "nukes": 0
            },
            "warLog": []
        }
        self.combatant_template = {
            "role": "",
            "warJustification": "TBD",
            "warClaims": [],
            "statistics": {
                "battlesWon": 0,
                "battlesLost": 0,
                "enemyUnitsDestroyed": 0,
                "enemyImprovementsDestroyed": 0,
                "friendlyUnitsDestroyed": 0,
                "friendlyImprovementsDestroyed": 0,
                "missilesLaunched": 0,
                "nukesLaunched": 0,
            }
        }

    # private methods
    ################################################################################

    def _save_changes(self) -> None:
        with open(self.wardata_filepath, 'r') as json_file:
            wardata_dict = json.load(json_file)
        wardata_dict = self.wardata_dict
        with open(self.wardata_filepath, 'w') as json_file:
            json.dump(wardata_dict, json_file, indent=4)

    def _generate_war_name(self, main_attacker_name: str, main_defender_name: str, war_justification: str, current_turn_num: int) -> str:
        '''
        Generates a unique war name. Called only by create_war()

        :param main_attacker_name: Nation name of main attacker
        :param main_defender_name: Nation name of main defender
        :param war_justification: War justification of main attacker
        :param current_turn_num: Current turn number
        '''
        season, year = core.date_from_turn_num(current_turn_num)
        match war_justification:
            case 'Animosity':
                names = [
                    f'{main_attacker_name} - {main_defender_name} Conflict',
                    f'{main_attacker_name} - {main_defender_name} War of Aggression',
                    f'{main_attacker_name} - {main_defender_name} Confrontation',
                ]
            case 'Border Skirmish':
                names = [
                    f'{main_attacker_name} - {main_defender_name} Conflict',
                    f'{main_attacker_name} - {main_defender_name} War of Aggression',
                    f'{main_attacker_name} - {main_defender_name} War',
                    f'{main_attacker_name} -  {main_defender_name} Border Skirmish',
                    f'War of {year}'
                ]
            case 'Conquest':
                names = [
                    f'{main_attacker_name} - {main_defender_name} Conflict',
                    f'{main_attacker_name} - {main_defender_name} War',
                    f'{main_attacker_name} Invasion of {main_defender_name}',
                    f'{main_attacker_name} Conquest of {main_defender_name}',
                ]
            case 'Independence':
                names = [
                    f'{main_attacker_name} - {main_defender_name} Independence War',
                    f'{main_attacker_name} - {main_defender_name} Liberation War',
                    f'{main_attacker_name} Rebellion',
                ]
            case 'Subjugation':
                names = [
                    f'{main_attacker_name} - {main_defender_name} Annexation Attempt',
                    f'{main_attacker_name} - {main_defender_name} Subjugation War',
                ]
        
        attempts = 0
        war_prefixes = ['2nd', '3rd', '4th', '5th', '6th', '7th', '8th', '9th', '10th']
        while True:
            war_name = random.sample(names, 1)[0]
            war_name_set = set(self.wardata_dict.keys())
            if war_name in war_name_set and year in war_name:
                continue
            while war_name in war_name_set:
                attempts += 1
                new_war_name = f'{war_prefixes[attempts]} {war_name}'
                if new_war_name not in war_name_set:
                    break
            break

        return war_name

    # data methods
    ################################################################################
    
    def create_war(self, main_attacker_id: int, main_defender_id: int, main_attacker_war_justification: str, current_turn_num: int, region_claims_list: list) -> str:
        '''
        Fills out all the paperwork for a new war.

        :param main_attacker_id: Main attacker player_id
        :param main_defender_id: Main defender player_id
        :param main_attacker_war_justification: War justification provided by main attacker
        :param current_turn_num: Current turn number
        :param region_claims_list: List of regions provided by main attacker
        :returns: War name
        '''
        # import other game files
        playerdata_filepath = f'gamedata/{self.game_id}/playerdata.csv'
        playerdata_list = core.read_file(playerdata_filepath, 1)
        trucedata_filepath = f'gamedata/{self.game_id}/trucedata.csv'
        trucedata_list = core.read_file(trucedata_filepath, 1)

        # get information from playerdata
        main_attacker_name = playerdata_list[main_attacker_id - 1][1]
        main_defender_name = playerdata_list[main_defender_id - 1][1]
        nation_name_list = []
        for playerdata in playerdata_list:
            nation_name_list.append(playerdata[1])
        attacker_relations_data = ast.literal_eval(playerdata_list[main_attacker_id - 1][22])
        defender_relations_data = ast.literal_eval(playerdata_list[main_defender_id - 1][22])

        # add war entry
        war_name = self._generate_war_name(main_attacker_name, main_defender_name, main_attacker_war_justification, current_turn_num)
        self.wardata_dict[war_name] = copy.deepcopy(self.war_template)
        self.wardata_dict[war_name]["startTurn"] = current_turn_num

        # add main attacker
        combatant_dict = copy.deepcopy(self.combatant_template)
        combatant_dict["role"] = "Main Attacker"
        combatant_dict["warJustification"] = main_attacker_war_justification
        combatant_dict["warClaims"] = region_claims_list
        self.wardata_dict[war_name]["combatants"][main_attacker_name] = combatant_dict

        # add main defender
        combatant_dict = copy.deepcopy(self.combatant_template)
        combatant_dict["role"] = "Main Defender"
        self.wardata_dict[war_name]["combatants"][main_defender_name] = combatant_dict

        # call in main attacker allies
        # possible allies: defensive pacts, puppet states
        puppet_state_id_list = core.get_subjects(playerdata_list, main_attacker_name, "Puppet State")
        defense_pact_id_list = core.get_alliances(attacker_relations_data, "Defense Pact")
        ally_player_ids = set(puppet_state_id_list) | set(defense_pact_id_list)
        for player_id in ally_player_ids:
            nation_name = playerdata_list[player_id - 1][1]
            allied_with_md = False # to be added
            truce_with_md = core.check_for_truce(trucedata_list, player_id, main_defender_id, current_turn_num)
            already_at_war_with_md = self.are_at_war(player_id, main_defender_id)
            if not allied_with_md and not truce_with_md and not already_at_war_with_md:
                combatant_dict = self.combatant_template
                combatant_dict["role"] = "Secondary Attacker"
                self.wardata_dict[war_name]["combatants"][nation_name] = combatant_dict

        # call in main defender allies
        # possible allies: defensive pacts, puppet states, overlord
        puppet_state_id_list = core.get_subjects(playerdata_list, main_defender_name, "Puppet State")
        defense_pact_id_list = core.get_alliances(defender_relations_data, "Defense Pact")
        ally_player_ids = set(puppet_state_id_list) | set(defense_pact_id_list)
        for player_id in ally_player_ids:
            allied_with_ma = False # to be added
            truce_with_ma = core.check_for_truce(trucedata_list, player_id, main_attacker_id, current_turn_num)
            already_at_war_with_ma = self.are_at_war(player_id, main_attacker_id)
            if not allied_with_ma and not truce_with_ma and not already_at_war_with_ma:
                combatant_dict = self.combatant_template
                combatant_dict["role"] = "Secondary Defender"
                self.wardata_dict[war_name]["combatants"][nation_name] = combatant_dict
        defender_status = playerdata_list[main_defender_id - 1][28]
        if defender_status != "Independent Nation":
            overlord_nation_name = False
            for name in nation_name_list:
                if name.lower() in defender_status.lower():
                    overlord_nation_name = name
            if overlord_nation_name:
                overlord_player_id = nation_name_list.index(overlord_nation_name) + 1
                subject_truce_check = core.check_for_truce(trucedata_list, overlord_player_id, main_attacker_id, current_turn_num)
                if not subject_truce_check:
                    combatant_dict = self.combatant_template
                    combatant_dict["role"] = "Secondary Defender"
                    self.wardata_dict[war_name]["combatants"][overlord_nation_name] = combatant_dict
        
        self._save_changes()
        return war_name

    def get_combatant_names(self, war_name: str) -> list:
        '''
        Gets a list of all nations participating in a given war.
        '''
        result = []

        if war_name in self.wardata_dict:
            combatants_dict = self.wardata_dict[war_name]["combatants"]
            for nation_name in combatants_dict:
                result.append(nation_name)

        return result

    def are_at_war(self, player_id_1: int, player_id_2: int, return_war_name=False):
        '''
        Checks if two players are currently at war.

        :param return_war_name: Function will return war name as a string.
        :returns: True or False or war name string.
        '''
        playerdata_filepath = f'gamedata/{self.game_id}/playerdata.csv'
        playerdata_list = core.read_file(playerdata_filepath, 1)
        nation_name_1 = playerdata_list[player_id_1 - 1][1]
        nation_name_2 = playerdata_list[player_id_2 - 1][1]

        for war_name, war_data in self.wardata_dict.items():
            combatant_dict = war_data["combatants"]
            if war_data["outcome"] == "TBD" and nation_name_1 in combatant_dict and nation_name_2 in combatant_dict:
                if return_war_name:
                    return war_name
                else:
                    return True
        
        return False
    
    def get_war_role(self, nation_name: str, war_name: str) -> str:
        '''
        Returns the war role of a given nation in a given war.
        '''
        combatants_dict = self.wardata_dict[war_name]["combatants"]

        if nation_name in combatants_dict:
            return combatants_dict[nation_name]["role"]

        return None

    # log methods
    ################################################################################

import ast
import copy
import csv
import json
from json.decoder import JSONDecodeError
import os
import random

from typing import Union, Tuple, List

from app import core
from app.alliance import AllianceTable
from app.alliance import Alliance


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
        
        self.wardata_dict = wardata_dict
        self.wardata_filepath: str = wardata_filepath
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
        self.combatant_template = {
            "role": "",
            "warJustification": "TBD",
            "warClaims": [],
            "warClaimsOriginalOwners": [],
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
        """
        Generates a unique war name. Called only by create_war()

        Params:
            main_attacker_name (str): nation name of main attacker
            main_defender_name (str): nation name of main defender
            war_justification (str): war justification of main attacker
            current_turn_num (int): current turn number

        Returns:
            war_name (str): generated war name
        """
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

    def _resolve_war_justification(self, nation_name: str, war_dict: dict) -> None:
        """
        Resolves a player's war justification.

        Params:
            nation_name (str): Nation name of player to resolve.
            war_dict (dict): Nested dictionary representing a war. Taken from wardata.
        """
        from app.region import Region
        playerdata_filepath = f'gamedata/{self.game_id}/playerdata.csv'
        playerdata_list = core.read_file(playerdata_filepath, 1)
        nation_name_list = []
        for playerdata in playerdata_list:
            nation_name_list.append(playerdata[1])

        # get information for winner
        war_justification = war_dict["combatants"][nation_name]["warJustification"]
        war_claims = war_dict["combatants"][nation_name]["warClaims"]
        war_claims_original_ids = war_dict["combatants"][nation_name]["warClaimsOriginalOwners"]
        winner_role = war_dict["combatants"][nation_name]["role"]
        winner_player_id = nation_name_list.index(nation_name) + 1

        # get information for main looser if no war claims
        if war_claims == []:
            for temp_nation_name in war_dict["combatants"]:
                war_role = war_dict["combatants"][temp_nation_name]["role"]
                if 'Main' in war_role and winner_role != war_role:
                    looser_player_id = nation_name_list.index(temp_nation_name) + 1
                    break

        # resolve war justification
        match war_justification:
            
            case 'Border Skirmish' | 'Conquest':
                for index, region_id in enumerate(war_claims):
                    region = Region(region_id, self.game_id)
                    if region.owner_id == war_claims_original_ids[index]:
                        region.set_owner_id(winner_player_id)
                        region.set_occupier_id(0)
            
            case 'Animosity':
                # give winner 10 political power
                pp_economy_data = ast.literal_eval(playerdata_list[winner_player_id - 1][10])
                new_sum = float(pp_economy_data[0]) + 10
                pp_economy_data[0] = str(new_sum)
                playerdata_list[winner_player_id - 1][10] = str(pp_economy_data)
                # give winner 10 technology
                tech_economy_data = ast.literal_eval(playerdata_list[winner_player_id - 1][11])
                new_sum = float(tech_economy_data[0]) + 10
                tech_economy_data[0] = str(new_sum)
                playerdata_list[winner_player_id - 1][11] = str(tech_economy_data)
                # set looser to 0 political power
                pp_economy_data = ast.literal_eval(playerdata_list[looser_player_id - 1][10])
                pp_economy_data[0] = '0.00'
                playerdata_list[looser_player_id - 1][10] = str(pp_economy_data)
            
            case 'Subjugation':
                subject_type = 'Puppet State'
                looser_status = f'{subject_type} of {nation_name}'
                playerdata_list[looser_player_id - 1][28] = looser_status
            
            case 'Independence':
                playerdata_list[winner_player_id - 1][28] = 'Independent Nation'
        
        # save playerdata.csv
        with open(playerdata_filepath, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(core.player_data_header)
            writer.writerows(playerdata_list)

    def _withdraw_units(self) -> None:
        """
        Withdraws all units out of enemy territory upon the conclusion of a war.
        """

        from app import checks
        from app.region import Region
        from app.unit import Unit
        with open(f'gamedata/{self.game_id}/regdata.json', 'r') as json_file:
            regdata_dict = json.load(json_file)

        # look for units that need to withdraw
        for region_id in regdata_dict:
            region = Region(region_id, self.game_id)
            region_unit = Unit(region_id, self.game_id)
            # a unit can only be present in another nation without occupation if a war just ended 
            if (
                region_unit.name is not None
                and region_unit.owner_id != region.owner_id
                and region.occupier_id == 0 
            ):
                target_id = region.find_suitable_region()
                if target_id is not None:
                    region_unit.move(Region(target_id, self.game_id), withdraw=True)
                else:
                    region_unit.clear()
        
        # to be added - player log message
        # ( once i get around to creating the action logging classes )
        # player_action_log.append(f'Withdrew {current_region_unit.name} {current_region_id} - {target_region_id}.')

        checks.update_military_capacity(self.game_id)
                

    # data methods
    ################################################################################
    
    def create_war(self, main_attacker_id: int, main_defender_id: int, main_attacker_war_justification: str, current_turn_num: int, region_claims_list: list) -> str:
        """
        Fills out all the paperwork for a new war.

        Param:
            main_attacker_id (int): Main attacker player_id.
            main_defender_id (int): Main defender player_id.
            main_attacker_war_justification (str): War justification provided by main attacker.
            current_turn_num (int): Current turn number.
            region_claims_list (list): List of region_ids provided by main attacker.
        Returns:
            str: War name generated by this function.
        """
        # import other game files
        from app.region import Region
        playerdata_filepath = f'gamedata/{self.game_id}/playerdata.csv'
        playerdata_list = core.read_file(playerdata_filepath, 1)
        trucedata_filepath = f'gamedata/{self.game_id}/trucedata.csv'
        trucedata_list = core.read_file(trucedata_filepath, 1)
        alliance_table = AllianceTable(self.game_id)

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
        original_region_owners_list = []
        for region_id in region_claims_list:
            region = Region(region_id, self.game_id)
            original_region_owners_list.append(region.owner_id)
        combatant_dict["warClaimsOriginalOwners"] = original_region_owners_list
        self.wardata_dict[war_name]["combatants"][main_attacker_name] = combatant_dict
        
        # add main defender
        combatant_dict = copy.deepcopy(self.combatant_template)
        combatant_dict["role"] = "Main Defender"
        self.wardata_dict[war_name]["combatants"][main_defender_name] = combatant_dict

        # call in main attacker allies
        # possible allies: puppet states
        puppet_state_id_list = core.get_subjects(playerdata_list, main_attacker_name, "Puppet State")
        ally_player_ids = set(puppet_state_id_list)
        for player_id in ally_player_ids:
            nation_name = playerdata_list[player_id - 1][1]
            if (
                not self.are_at_war(player_id, main_defender_id)
                and not core.check_for_truce(trucedata_list, player_id, main_defender_id, current_turn_num)
                and not alliance_table.are_allied(nation_name, main_defender_name)
                and not alliance_table.former_ally_truce(nation_name, main_defender_name)
            ):
                combatant_dict = copy.deepcopy(self.combatant_template)
                combatant_dict["role"] = "Secondary Attacker"
                self.wardata_dict[war_name]["combatants"][nation_name] = combatant_dict

        # call in main defender allies
        # possible allies: defensive pacts, puppet states, overlord
        puppet_state_id_list = core.get_subjects(playerdata_list, main_defender_name, "Puppet State")
        defense_allies = alliance_table.get_allies(main_defender_name, "Defense Pact")
        defense_pact_id_list = []
        for ally_name in defense_allies:
            defense_pact_id_list.append(nation_name_list.index(ally_name) + 1)
        ally_player_ids = set(puppet_state_id_list) | set(defense_pact_id_list)
        for player_id in ally_player_ids:
            nation_name = playerdata_list[player_id - 1][1]
            if (
                not self.are_at_war(player_id, main_attacker_id)
                and not core.check_for_truce(trucedata_list, player_id, main_attacker_id, current_turn_num)
                and not alliance_table.are_allied(main_attacker_name, nation_name)
                and not alliance_table.former_ally_truce(main_attacker_name, nation_name)
            ):
                combatant_dict = copy.deepcopy(self.combatant_template)
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
                    combatant_dict = copy.deepcopy(self.combatant_template)
                    combatant_dict["role"] = "Secondary Defender"
                    self.wardata_dict[war_name]["combatants"][overlord_nation_name] = combatant_dict
        
        self._save_changes()
        return war_name

    def get_combatant_names(self, war_name: str) -> list:
        """
        Gets a list of all nations participating in a given war.

        Params:
            war_name (str): Name of war to check.
        """
        result = []

        if war_name in self.wardata_dict:
            combatants_dict = self.wardata_dict[war_name]["combatants"]
            for nation_name in combatants_dict:
                result.append(nation_name)

        return result

    def are_at_war(self, player_id_1: int, player_id_2: int, return_war_name=False) -> bool | str:
        """
        Checks if two players are currently at war.

        Params:
            player_id_1 (int):
            player_id_2 (int):
            return_war_name (bool): Function will return the war_name string if True.
        
        Returns:
            True or False or war name string.
        """
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

    def is_at_peace(self, player_id: int, value = False) -> bool | int:
        """
        Checks if a nation is at peace.

        Params:
            player_id (int): ID of nation we want to check.
            value (bool): Will turn number since last war. Used only for VC calculation.
        
        Returns:
            bool: True if at peace, False if involved in at least one war.
            int: Returns a turn number instead if value param is True.
        """
        playerdata_filepath = f'gamedata/{self.game_id}/playerdata.csv'
        playerdata_list = core.read_file(playerdata_filepath, 1)
        nation_name = playerdata_list[player_id - 1][1]

        for i in range(len(playerdata_list)):
            player_id_2 = i + 1
            if player_id == player_id_2:
                continue
            if self.are_at_war(player_id, player_id_2):
                return False
        
        if value:
            at_peace_since = 0
            for war, war_data in self.wardata_dict.items():
                if nation_name in war_data["combatants"] and war_data["outcome"] != "TBD":
                    if war_data["endTurn"] > at_peace_since:
                        at_peace_since = war_data["endTurn"]
            return at_peace_since
        else:
            return True

    def get_war_role(self, nation_name: str, war_name: str) -> str:
        """
        Returns the war role of a given nation in a given war.

        Params:
            nation_name (str): Name of nation to check.
            war_name (str): Name of war to check.

        Returns:
            str: Returns war role if found, otherwise returns None.
        """
        combatants_dict = self.wardata_dict[war_name]["combatants"]

        if nation_name in combatants_dict:
            return combatants_dict[nation_name]["role"]

        return None

    def query(self, nation_name: str, war_position: str, war_side: str, war_outcome: str) -> bool:
        """
        Checks if a war exists with the given parameters.
        Used for victory condition functions. Might replace this with something better later.

        Params:
            nation_name (str): Name of nation to check.
            war_position (str): Position rank of nation (main or secondary).
            war_side (str): Side nation is on (attacker or defender).
            war_outcome (str): War result.

        Returns:
            result (bool): True if war found with these conditions, False otherwise.
        """

        for war, war_data in self.wardata_dict.items():
            if nation_name in war_data["combatants"] and war_data["outcome"] == war_outcome:
                player_war_role = war_data["combatants"][nation_name]["role"]
                if war_side in player_war_role and war_position in player_war_role:
                    return True

        return False

    def add_missing_war_justifications(self, war_name: str) -> None:
        """
        Given a war name, prompts all nations that haven't submitted a war justification yet.

        Params:
            war_name (str): Name of war to check.
        """
        from app.region import Region
        playerdata_filepath = f'gamedata/{self.game_id}/playerdata.csv'
        playerdata_list = core.read_file(playerdata_filepath, 1)

        # check every nation involved in the war
        combatants_dict: dict = self.wardata_dict[war_name]["combatants"]
        for nation_name in combatants_dict:
            if combatants_dict[nation_name]["warJustification"] == "TBD":
                war_justification = input(f'Please enter {nation_name} war justification for the {war_name} or enter SKIP to postpone: ')
                if war_justification != 'SKIP':
                    
                    # validate war claims
                    region_claims_list = []
                    if war_justification == 'Border Skirmish' or war_justification == 'Conquest':
                        all_claims_valid = False
                        while not all_claims_valid:
                            # get region claims
                            region_claims_str = input(f'List the regions that {nation_name} is claiming using {war_justification}: ')
                            region_claims_list = region_claims_str.split(',')
                            all_claims_valid, playerdata_list = self.validate_war_claims(war_justification, region_claims_list, nation_name, playerdata_list)

                    # save information
                    combatants_dict[nation_name]["warJustification"] = war_justification
                    combatants_dict[nation_name]["warClaims"] = region_claims_list 
                    original_region_owners_list = []
                    for region_id in region_claims_list:
                        region = Region(region_id, self.game_id)
                        original_region_owners_list.append(region.owner_id)
                    combatants_dict[nation_name]["warClaimsOriginalOwners"] = original_region_owners_list

        self.wardata_dict[war_name]["combatants"] = combatants_dict
        self._save_changes()

        #Update playerdata.csv
        with open(playerdata_filepath, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(core.player_data_header)
            writer.writerows(playerdata_list)
    
    def validate_war_claims(self, war_justification: str, region_claims_list: list, nation_name: str, playerdata_list: List[List[any]]) -> Tuple[bool, List[List[any]]]:
        """
        Checks if all provided region_ids are valid. Kind of a patch job, might upgrade later.

        Params:
            war_justification (str): Name of war justification to check.
            region_claims_list (str): List of war claims to check.
            nation_name (str): Name of nation to check.
            playerdata_list (list of lists): Contains data for all players from playerdata.csv.
        """
        nation_name_list = []
        for playerdata in playerdata_list:
            nation_name_list.append(playerdata[1])
        with open(f'gamedata/{self.game_id}/regdata.json', 'r') as json_file:
            regdata_dict = json.load(json_file)

        # get war justification info
        if war_justification == 'Border Skirmish':
            free_claims = 3
            max_claims = 6
            claim_cost = 5
        elif war_justification == 'Conquest':
            free_claims = 5
            max_claims = 10
            claim_cost = 3
        
        # check that all claims are valid
        attacker_player_id = nation_name_list.index(nation_name) + 1
        for i, region_id in enumerate(region_claims_list):
            if region_id not in regdata_dict:
                return False, playerdata_list
            if i + 1 > free_claims:
                pp_economy_data = ast.literal_eval(playerdata_list[attacker_player_id - 1][10])
                new_sum = float(pp_economy_data[0]) - claim_cost
                if new_sum >= 0:
                    pp_economy_data[0] = str(new_sum)
                    playerdata_list[attacker_player_id - 1][10] = str(pp_economy_data)
                else:
                    return False, playerdata_list
            if i + 1 > max_claims:
                return False, playerdata_list

        return True, playerdata_list

    def statistic_add(self, war_name: str, nation_name: str, stat_name: str, count = 1) -> None:
        """
        Updates a given war statistic.

        Params:
            war_name (str): Name of war to check.
            nation_name (str): Name of nation to check.
            stat_name (str): Statistic name string, must match key exactly.
            count (int): How much to increment the score. Default is 1.
        """
        self.wardata_dict[war_name]["combatants"][nation_name]["statistics"][stat_name] += count
        self._save_changes()

    def end_war(self, war_name: str, outcome: str) -> None:
        """
        Calling this function does all the paperwork to end a war.
        
        Params:
            war_name (str): Name of war to end.
            outcome (str): Result of the war.
        """
        from app.region import Region
        war_dict: dict = self.wardata_dict[war_name]
        current_turn_num = core.get_current_turn_num(int(self.game_id[-1]))
        main_war_justification = None

        # resolve war justifications
        match outcome:
            
            case 'Attacker Victory':
                for nation_name, nation_war_data in war_dict["combatants"].items():
                    if 'Attacker' in nation_war_data["role"]:
                        self._resolve_war_justification(nation_name, war_dict)
                    if 'Main Attacker' == nation_war_data["role"]:
                        main_war_justification = nation_war_data["warJustification"]

            case 'Defender Victory':
                for nation_name, nation_war_data in war_dict["combatants"].items():
                    if 'Defender' in nation_war_data["role"]:
                        self._resolve_war_justification(nation_name, war_dict)
                    if 'Main Defender' == nation_war_data["role"]:
                        main_war_justification = nation_war_data["warJustification"]
            
            case 'White Peace':
                # stupid hack to make it so white peace always has a 8 turn truce period
                main_war_justification = 'Conquest'

        # add truce period
        # to do - come up with better solution for managing truce periods that doesn't involve a shitty csv file
        playerdata_filepath = f'gamedata/{self.game_id}/playerdata.csv'
        playerdata_list = core.read_file(playerdata_filepath, 1)
        nation_name_list = []
        for playerdata in playerdata_list:
            nation_name_list.append(playerdata[1])
        signatories_list = [False, False, False, False, False, False, False, False, False, False]
        for nation_name in war_dict["combatants"]:
            index = nation_name_list.index(nation_name)
            signatories_list[index] = True
        core.add_truce_period(self.game_id, signatories_list, main_war_justification, current_turn_num)

        # update wardata
        war_dict["endTurn"] = current_turn_num
        war_dict["outcome"] = outcome
        self.wardata_dict[war_name] = war_dict

        # end occupations
        with open(f'gamedata/{self.game_id}/regdata.json', 'r') as json_file:
            regdata_dict = json.load(json_file)
        for region_id in regdata_dict:
            region = Region(region_id, self.game_id)
            if not self.are_at_war(region.owner_id, region.occupier_id):
                region.set_occupier_id(0)

        # withdraw units
        self._withdraw_units()

        # save changes
        self._save_changes()

    def war_count(self) -> int:
        return len(self.wardata_dict)
    
    def unit_casualties(self) -> int:
        """
        Returns a combined total of all unit casualties across all wars.
        """

        casualties = 0
        for war_name, war_data in self.wardata_dict.items():
            for combatant_name, combatant_data in war_data["combatants"].items():
                casualties += combatant_data["statistics"]["friendlyUnitsDestroyed"]
        
        return casualties
    
    def improvement_casualties(self) -> int:
        """
        Returns a combined total of all improvement casualties across all wars.
        """

        casualties = 0
        for war_name, war_data in self.wardata_dict.items():
            for combatant_name, combatant_data in war_data["combatants"].items():
                casualties += combatant_data["statistics"]["friendlyImprovementsDestroyed"]
        
        return casualties
    
    def missiles_launched_count(self) -> int:
        """
        Returns a combined total of all missile launches across all wars.
        """

        count = 0
        for war_name, war_data in self.wardata_dict.items():
            for combatant_name, combatant_data in war_data["combatants"].items():
                count += combatant_data["statistics"]["missilesLaunched"]
                count += combatant_data["statistics"]["nukesLaunched"]
        
        return count
    
    def get_longest_war(self) -> Tuple[str, int]:
        """
        Identifies the longest war that has occured (finished or not).

        Returns:
            tuple: A tuple containing:
                - str: Name of the war or None if no war found.
                - int: Duration of war in turns.
        """

        longest_name = None
        longest_time = 0
        current_turn_num = core.get_current_turn_num(int(self.game_id[-1]))

        for war_name, war_data in self.wardata_dict.items():
            start_turn = war_data["startTurn"]
            end_turn = war_data["endTurn"]
            war_status = war_data["outcome"]
            if war_status == "TBD":
                war_duration = current_turn_num - start_turn
            else:
                war_duration = end_turn - start_turn
            if war_duration > longest_time:
                longest_name = war_name
                longest_time = war_duration
        
        return longest_name, longest_time


    # log methods
    ################################################################################

    def append_war_log(self, war_name: str, message: str) -> None:
        """
        Adds new entry to the war log of a given war.

        Params:
            war_name (str): Name of war to add war log to.
            message (str): The new entry.
        """
        self.wardata_dict[war_name]["warLog"].append(message)
        self._save_changes()

    def export_all_logs(self) -> None:
        """
        Saves all of the combat logs for ongoing wars as .txt files. Then wipes the logs.
        """
        directory = f'gamedata/{self.game_id}/logs'

        for war_name, war_data in self.wardata_dict.items():
            if war_data["outcome"] == "TBD":
                os.makedirs(directory, exist_ok=True)
                filename = os.path.join(directory, f'{war_name} Log.txt')
                with open(filename, 'w') as file:
                    for entry in self.wardata_dict[war_name]["warLog"]:
                        file.write(entry + '\n')
            self.wardata_dict[war_name]["warLog"] = []

        self._save_changes()


    # war score methods
    ################################################################################

    def warscore_add(self, war_name: str, war_role: str, stat_name: str, count = 1) -> None:
        """
        Increases the score of a warscore entry.

        Params:
            war_name (str): Name of war.
            war_role (str): Role of nation that triggered this function.
            stat_name (str): WarData key for a specific war score. Must match exactly.
            count (int): How much to increment the score. Default is 1.
        """
        if 'Attacker' in war_role:
            war_role_key = "attackerWarScore"
        elif 'Defender' in war_role:
            war_role_key = "defenderWarScore"
        self.wardata_dict[war_name][war_role_key][stat_name] += count
        self._save_changes()

    def calculate_score_threshold(self, war_name: str):
        """
        Calculates the war score threshold for victory for each side of a war.

        Params:
            war_name (str): Name of war.
        """
        playerdata_filepath = f'gamedata/{self.game_id}/playerdata.csv'
        playerdata_list = core.read_file(playerdata_filepath, 1)
        nation_name_list = []
        for nation_info in playerdata_list:
            nation_name_list.append(nation_info[1])
        war_dict = self.wardata_dict[war_name]

        # initial threshold is a 100 point difference
        attacker_threshold = 0
        defender_threshold = 0

        # check for unyielding and crime syndicate
        for combatant_name, combatant_data in war_dict["combatants"].items():
            combatant_id = nation_name_list.index(combatant_name) + 1
            combatant_research_list = ast.literal_eval(playerdata_list[combatant_id - 1][26])
            if combatant_data["role"] == "Main Attacker" and defender_threshold == 0:
                if playerdata_list[combatant_id - 1][3] == "Crime Syndicate":
                    defender_threshold = None
                elif "Unyielding" in combatant_research_list:
                    defender_threshold = 50
            elif combatant_data["role"] == "Main Defender" and attacker_threshold == 0:
                if playerdata_list[combatant_id - 1][3] == "Crime Syndicate":
                    attacker_threshold = None
                elif "Unyielding" in combatant_research_list:
                    attacker_threshold = 50

        # if not crime syndicate compute remaining threshold
        if attacker_threshold is not None:
            attacker_threshold += 100 + war_dict["defenderWarScore"]["total"]
        if defender_threshold is not None:
            defender_threshold += 100 + war_dict["attackerWarScore"]["total"]

        return attacker_threshold, defender_threshold
    
    def get_main_combatants(self, war_name: str):
        """
        Returns the nation names of the two main combatants.

        Params:
            war_name (str): Name of war.
        """
        playerdata_filepath = f'gamedata/{self.game_id}/playerdata.csv'
        playerdata_list = core.read_file(playerdata_filepath, 1)
        nation_name_list = []
        for nation_info in playerdata_list:
            nation_name_list.append(nation_info[1])
        war_dict = self.wardata_dict[war_name]

        for combatant_name, combatant_data in war_dict["combatants"].items():
            if combatant_data["role"] == "Main Attacker":
                main_attacker_name = combatant_name
            elif combatant_data["role"] == "Main Defender":
                main_defender_name = combatant_name
        
        return main_attacker_name, main_defender_name

    def add_warscore_from_occupations(self) -> None:
        """
        Adds warscore from occupied regions.
        """
        from app.region import Region
        playerdata_filepath = f'gamedata/{self.game_id}/playerdata.csv'
        playerdata_list = core.read_file(playerdata_filepath, 1)

        with open(f'gamedata/{self.game_id}/regdata.json', 'r') as json_file:
            regdata_dict = json.load(json_file)

        # for every region that is occupied
        for region_id in regdata_dict:
            region = Region(region_id, self.game_id)
            if region.occupier_id != 0 and region.occupier_id != 99:
                # get occupier information
                war_name = self.are_at_war(region.owner_id, region.occupier_id, True)
                occupier_nation_name = playerdata_list[region.occupier_id - 1][1]
                occupier_war_role = self.get_war_role(occupier_nation_name, war_name)
                occupier_research_list = ast.literal_eval(playerdata_list[region.occupier_id - 1][26])
                # add warscore
                if 'Scorched Earth' in occupier_research_list:
                    score = 3
                else:
                    score = 2
                self.warscore_add(war_name, occupier_war_role, "occupation", score)

    def update_totals(self) -> None:
        """
        Updates the total war scores of all ongoing wars.
        """
        for war_name, war_data in self.wardata_dict.items():
            if war_data["outcome"] == "TBD":
                
                new_total = 0
                for key, value in war_data["attackerWarScore"].items():
                    if key != 'total':
                        new_total += value
                self.wardata_dict[war_name]["attackerWarScore"]["total"] = new_total

                new_total = 0
                for key, value in war_data["defenderWarScore"].items():
                    if key != 'total':
                        new_total += value
                self.wardata_dict[war_name]["defenderWarScore"]["total"] = new_total

        self._save_changes()
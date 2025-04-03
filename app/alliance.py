import json
from typing import Union, Tuple, List

from app import core


class Alliance:
    
    def __init__(self, alliance_name: str, alliance_data: dict, game_id: str):
        
        self.name = alliance_name
        self.type: str = alliance_data["allianceType"]
        self.turn_created: int = alliance_data["turnCreated"]
        self.turn_ended: int = alliance_data["turnEnded"]
        self.current_members: dict = alliance_data["currentMembers"]
        self.founding_members: dict = alliance_data["foundingMembers"]
        self.former_members: dict = alliance_data["formerMembers"]

        if self.turn_ended == 0:
            self.is_active: bool = True
        else:
            self.is_active: bool = False

        if self.is_active:
            current_turn_num = core.get_current_turn_num(game_id)
            self.age: int = current_turn_num - self.turn_created
        else:
            self.age: int = self.turn_ended - self.turn_created

        self.game_id = game_id
    
    def build(alliance_name: str, alliance_type: str, founding_members: list[str], game_id: str) -> "Alliance":
        """
        Creates a new Alliance instance from scratch when called by AllianceTable factory method.

        Params:
            alliance_name (str): Name of alliance to create.
            alliance_type (str): Type of alliance.
            founding_members (list): List of nations who are founding the alliance.
            game_id (str): Game ID string.

        Returns:
            Alliance: A created alliance.
        """

        current_turn_num = core.get_current_turn_num(game_id)

        new_alliance_data = {
            "allianceType": alliance_type,
            "turnCreated": current_turn_num,
            "turnEnded": 0,
            "currentMembers": {},
            "foundingMembers": {},
            "formerMembers": {}
        }

        for nation_name in founding_members:
            new_alliance_data["currentMembers"][nation_name] = current_turn_num
            new_alliance_data["foundingMembers"][nation_name] = current_turn_num

        return Alliance(alliance_name, new_alliance_data, game_id)

    def add_member(self, nation_name: str) -> None:
        """
        Adds a nation to the alliance.
        Input validation is done by the public action function that calls this method.

        Params:
            nation_name (str): Nation to add to the alliance.
        """

        current_turn_num = core.get_current_turn_num(self.game_id)

        if nation_name in self.former_members:
            del self.former_members[nation_name]

        self.current_members[nation_name] = current_turn_num
        
    def remove_member(self, nation_name: str) -> None:
        """
        Removes a nation from the alliance.
        Input validation is done by the public action function that calls this method.

        Params:
            nation_name (str): Nation to remove from the alliance.
        """

        current_turn_num = core.get_current_turn_num(self.game_id)

        del self.current_members[nation_name]

        self.former_members[nation_name] = current_turn_num

    def end(self) -> None:
        """
        Retires an alliance.
        """
        
        current_turn_num = core.get_current_turn_num(self.game_id)

        for nation_name in self.current_members:
            self.former_members[nation_name] = current_turn_num
        
        self.current_members = {}
        self.turn_ended = current_turn_num



class AllianceTable:    
    
    def __init__(self, game_id):

        # check if game id is valid
        gamedata_filepath = f'gamedata/{game_id}/gamedata.json'
        gamedata_dict = {}
        try:
            with open(gamedata_filepath, 'r') as json_file:
                gamedata_dict = json.load(json_file)
        except FileNotFoundError:
            print(f"Error: Unable to locate {gamedata_filepath} during Wardata class initialization.")

        # set attributes
        self.game_id: str = game_id
        self.data: dict = gamedata_dict["alliances"]

    def __iter__(self):
        for alliance_name, alliance_data in self.data.items():
            yield Alliance(alliance_name, alliance_data, self.game_id)

    def __len__(self):
        return len(self.data)

    def save(self, alliance: Alliance) -> None:
        """
        Saves an alliance to the AllianceTable and gamedata.json.

        Params:
            alliance (Alliance): Alliance to save/update.
        """

        alliance_data = {
            "allianceType": alliance.type,
            "turnCreated": alliance.turn_created,
            "turnEnded": alliance.turn_ended,
            "currentMembers": alliance.current_members,
            "foundingMembers": alliance.founding_members,
            "formerMembers": alliance.former_members
        }

        self.data[alliance.name] = alliance_data

        gamedata_filepath = f'gamedata/{self.game_id}/gamedata.json'
        with open(gamedata_filepath, 'r') as json_file:
            gamedata_dict = json.load(json_file)
        
        gamedata_dict["alliances"] = self.data
        with open(gamedata_filepath, 'w') as json_file:
            json.dump(gamedata_dict, json_file, indent=4)
    
    def create(self, alliance_name: str, alliance_type: str, founding_members: list[str]) -> Alliance:
        """
        Factory method to create new Alliance instance.
        Input validation is done by the public action function that calls this method.

        Params:
            alliance_name (str): Name of alliance to create.
            alliance_type (str): Type of alliance to create.
            founding_members (list): List of nation names that are founders 

        Returns:
            Alliance: Newly created alliance.
        """

        new_alliance = Alliance.build(alliance_name, alliance_type, founding_members, self.game_id)
        self.save(new_alliance)

        return new_alliance
    
    def get(self, alliance_name: str) -> Alliance:
        """
        Retrieves an Alliance from the AllianceTable.

        Params:
            alliance_name (str): Name of alliance to get.
        
        Returns:
            Alliance: Alliance corresponding to alliance_name or None if match not found.
        """
        
        if alliance_name in self.data:
            return Alliance(alliance_name, self.data[alliance_name], self.game_id)

        return None
    
    def are_allied(self, nation_name_1: str, nation_name_2: str) -> bool:
        """
        Checks if two players are a part of at least one active alliance together.

        Params:
            nation_name_1 (str): First nation name string.
            nation_name_2 (str): Second nation name string.

        Returns:
            bool: True if an alliance found, False otherwise.
        """

        for alliance in self:
            if (
                alliance.is_active
                and nation_name_1 in alliance.current_members
                and nation_name_2 in alliance.current_members
            ):
                return True

        return False
    
    def former_ally_truce(self, nation_name_1: str, nation_name_2: str) -> bool:
        """
        Nations are not allowed to declare war on their former allies until 2 turns have passed.

        Params:
            nation_name_1 (str): First nation name string.
            nation_name_2 (str): Second nation name string.

        Returns:
            bool: True if an grace period is still in effect, False otherwise.
        """

        current_turn_num = core.get_current_turn_num(self.game_id)

        for alliance in self:
            if nation_name_1 in alliance.former_members and nation_name_2 in alliance.former_members:
                if (
                    current_turn_num - alliance.former_members[nation_name_1] < 2
                    or current_turn_num - alliance.former_members[nation_name_2] < 2
                ):
                    return True
            elif nation_name_1 in alliance.former_members and nation_name_2 in alliance.current_members:
                if current_turn_num - alliance.former_members[nation_name_1] < 2:
                    return True
            elif nation_name_2 in alliance.former_members and nation_name_1 in alliance.current_members:
                if current_turn_num - alliance.former_members[nation_name_2] < 2:
                    return True

        return False
    
    def report(self, nation_name: str) -> dict:
        """
        Creates a dictionary containting counts of a specific player's alliances.

        Params:
            nation_name (str): Nation name string.
        
        Returns:
            dict: Dictionary of alliance counts.
        """

        alliance_type_dict = {}
        alliance_type_dict["Total"] = 0
        alliance_type_dict["Non-Aggression Pact"] = 0
        alliance_type_dict["Defense Pact"] = 0
        alliance_type_dict["Trade Agreement"] = 0
        alliance_type_dict["Research Agreement"] = 0

        for alliance in self:
            if alliance.is_active and nation_name in alliance.current_members:
                alliance_type_dict["Total"] += 1
                alliance_type_dict[alliance.type] += 1
        
        return alliance_type_dict
    
    def get_allies(self, nation_name: str, type_to_search = 'ALL') -> list:
        """
        Creates a list of all nations a player is allied with, no duplicates.

        Params:
            nation_name (str): Nation name string.
            type_to_search (str): Type of alliance to check or 'ALL' to check all aliances.
        
        Returns:
            list: List of allies found.
        """

        allies_set = set()

        for alliance in self:
            if alliance.is_active and nation_name in alliance.current_members:
                if type_to_search != 'ALL' and type_to_search != alliance.type:
                    continue
                for alliance_member_name in alliance.current_members:
                    if alliance_member_name != nation_name:
                        allies_set.add(alliance_member_name)

        allies_list = list(allies_set)
        return allies_list
    
    def get_longest_alliance(self) -> Tuple[str, int]:
        """
        Identifies the longest alliance of the game.

        Returns:
            Tuple:
                str: Name of longest alliance or None if no alliances found.
                int: Length of the longest alliance.

        """

        longest_alliance_name = None
        longest_alliance_duration = -1

        for alliance in self:
            if alliance.age > longest_alliance_duration:
                longest_alliance_name = alliance.name
                longest_alliance_duration = alliance.age

        return longest_alliance_name, longest_alliance_duration
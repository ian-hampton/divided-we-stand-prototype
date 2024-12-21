import json

from app import core

class Alliance:
    
    def __init__(self, alliance_name: str, alliance_data: dict, game_id: str):
        
        self.name = alliance_name
        self.type: str = alliance_data["allianceType"]
        self.turn_created: int = alliance_data["turnCreated"]
        self.turn_ended: int = alliance_data["turnEnded"]
        self.current_members: dict = alliance_data["currentMembers"]
        self.founding_members: dict = alliance_data["foundingMembers"]
        self.truces: dict = alliance_data["allianceTruces"]

        if self.turn_ended == 0:
            self.is_active: bool = True
        else:
            self.is_active: bool = False

        if self.is_active:
            current_turn_num = core.get_current_turn_num(int(game_id[-1]))
            self.age: int = current_turn_num - self.turn_created
        else:
            self.age: int = self.turn_ended - self.turn_created
    
    def build(alliance_name: str, alliance_type: str, founding_members: list, game_id: str):
        """
        """

        current_turn_num = core.get_current_turn_num(int(game_id[-1]))

        new_alliance_data = {
            "allianceType": alliance_type,
            "turnCreated": current_turn_num,
            "turnEnded": 0,
            "currentMembers": {},
            "foundingMembers": {},
            "allianceTruces": {}
        }

        for nation_name in founding_members:
            new_alliance_data["currentMembers"][nation_name] = current_turn_num
            new_alliance_data["foundingMembers"][nation_name] = current_turn_num

        return Alliance(alliance_name, new_alliance_data, game_id)

    def add_member(self, nation_name: str) -> None:
        """
        """
        pass

    def remove_member(self, nation_name: str) -> None:
        """
        """
        pass

    def end(self) -> None:
        """
        """
        pass

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
    
    def create(self, alliance_name: str, alliance_type: str, founding_members: list) -> Alliance:
        """
        """

        new_alliance = Alliance.build(alliance_name, alliance_type, founding_members, self.game_id)
        self.save(new_alliance)

        return new_alliance

    def save(self, alliance: Alliance) -> None:
        """
        """

        alliance_data = {
            "allianceType": alliance.type,
            "turnCreated": alliance.turn_created,
            "turnEnded": alliance.turn_ended,
            "currentMembers": alliance.current_members,
            "foundingMembers": alliance.founding_members,
            "allianceTruces": alliance.truces
        }

        self.data[alliance.name] = alliance_data

        gamedata_filepath = f'gamedata/{self.game_id}/gamedata.json'
        with open(gamedata_filepath, 'r') as json_file:
            gamedata_dict = json.load(json_file)
        
        gamedata_dict["alliances"] = self.data
        with open(gamedata_filepath, 'w') as json_file:
            json.dump(gamedata_dict, json_file, indent=4)
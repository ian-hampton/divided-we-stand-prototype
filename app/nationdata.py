import json
import random

class Nation:
    
    def __init__(self, nation_id: str | int, nation_data: dict, game_id: str):\

        self.game_id = game_id

        self.id = nation_id
        self.name: str = nation_data["nationName"]
        self.player_id = nation_data["playerID"]
        self.color = nation_data["color"]
        self.gov: str = nation_data["government"]
        self.fp: str = nation_data["foreignPolicy"]
        self.status: str = nation_data["status"]
        self.trade_fee: str = nation_data["tradeFee"]
        self.completed_research: dict = nation_data["completedResearch"]
        self.income_details: list = nation_data["incomeDetails"]

        self.used_mc: int = nation_data["militaryCapacity"]["used"]
        self.total_mc: int = nation_data["militaryCapacity"]["max"]

        self.missile_count: int = nation_data["missileStockpile"]["standardMissile"]
        self.nuke_count: int = nation_data["missileStockpile"]["nuclearMissile"]

        self.score: int = nation_data["score"]
        self.chosen_vc_set: str = nation_data["chosenVictorySet"]

        self._upkeep_manager: dict = nation_data["upkeepManager"]
        self._sets: dict = nation_data["victorySets"]
        self._resources: dict = nation_data["resources"]
        self._records: dict = nation_data["records"]
        self._improvement_count: list = nation_data["improvementCount"]

    def _generate_vc_sets(count: int) -> dict:
        """
        Generates victory condition sets for a player.

        Params:
            count (int): Number of sets to generate.

        Returns:
            dict: Nested dictionary of victory coonditions.
        """

        vc_sets = {}
        random_easys = random.sample(EASY_LIST, len(EASY_LIST))
        random_normals = random.sample(NORMAL_LIST, len(NORMAL_LIST))
        random_hards = random.sample(HARD_LIST, len(HARD_LIST))

        for i in range(count):
            name = f"set{i+1}"
            vc_sets[name] = {}
            vc_sets[name][random_easys.pop()] = False
            vc_sets[name][random_normals.pop()] = False
            vc_sets[name][random_hards.pop()] = False

        return vc_sets

    def build(nation_id: int, player_id: int, game_id: str) -> "Nation":
        """
        Creates a new Nation instance from scratch when called by NationTable factory method.

        Params:
            nation_id (int): ID of nation.
            player_id (int): ID of player controlling this nation.
            game_id (str): Game ID string.

        Returns:
            Nation: A new nation.
        """

        vc_sets = Nation._generate_vc_sets(2)
        nation_data = {
            "nationName": "N/A",
            "playerID": player_id,
            "color": "#ffffff",
            "government": "N/A",
            "foreignPolicy": "N/A",
            "status": "Independent Nation",
            "militaryCapacity": {
                "used": 0,
                "max": 0
            },
            "tradeFee": "1:2",
            "missileStockpile": {
                "standardMissile": 0,
                "nuclearMissile": 0
            },
            "upkeepManager": {
                "totalUpkeepCosts": "0.00",
                "coalUpkeep": "0.00",
                "oilUpkeep": "0.00",
                "greenUpkeep": "0.00",
            },
            "score": 0,
            "chosenVictorySet": "N/A",
            "victorySets": vc_sets,
            "resources": {
                "dollars": {
                    "stored": "0.00",
                    "income": "0.00",
                    "max": 100,
                    "rate": 100
                },
                "politicalPower": {
                    "stored": "0.00",
                    "income": "0.00",
                    "max": 50,
                    "rate": 100
                },
                "technology": {
                    "stored": "0.00",
                    "income": "0.00",
                    "max": 50,
                    "rate": 100
                },
                "coal": {
                    "stored": "0.00",
                    "income": "0.00",
                    "max": 50,
                    "rate": 100
                },
                "oil": {
                    "stored": "0.00",
                    "income": "0.00",
                    "max": 50,
                    "rate": 100
                },
                "greenEnergy": {
                    "stored": "0.00",
                    "income": "0.00",
                    "max": 50,
                    "rate": 100
                },
                "basicMaterials": {
                    "stored": "0.00",
                    "income": "0.00",
                    "max": 50,
                    "rate": 100
                },
                "commonMetals": {
                    "stored": "0.00",
                    "income": "0.00",
                    "max": 50,
                    "rate": 100
                },
                "advancedMetals": {
                    "stored": "0.00",
                    "income": "0.00",
                    "max": 50,
                    "rate": 100
                },
                "uranium": {
                    "stored": "0.00",
                    "income": "0.00",
                    "max": 50,
                    "rate": 100
                },
                "rareEarthElements": {
                    "stored": "0.00",
                    "income": "0.00",
                    "max": 50,
                    "rate": 100
                }
            },
            "records": {
                "militaryStrength": [],
                "nationSize": [],
                "netIncome": [],
                "researchCount": [],
                "transactionCount": []
            },
            "improvementCount": [],
            "completedResearch": {},
            "incomeDetails": []
            
        }

        return Nation(nation_id, nation_data, game_id)

    def get_vc_list(self) -> list:
        """
        This function is a piece of garbage that exists only because I do not want to refactor the frontend right now.

        Returns:
            list: List of all victory conditions across all sets.
        """
        results = []
        for key in self._sets["set1"]:
            results.append(key)
        for key in self._sets["set2"]:
            results.append(key)
        return results

class NationTable:
    
    def __init__(self, game_id):

        # check if game id is valid
        gamedata_filepath = f'gamedata/{game_id}/gamedata.json'
        gamedata_dict = {}
        try:
            with open(gamedata_filepath, 'r') as json_file:
                gamedata_dict = json.load(json_file)
        except FileNotFoundError:
            print(f"Error: Unable to locate {gamedata_filepath} during nation class initialization.")

        # set attributes
        self.game_id: str = game_id
        self.data: dict = gamedata_dict["nations"]
        self._name_to_id = {}
        for nation in self:
            self._name_to_id[nation.name] = nation.id

    def __iter__(self):
        for nation_id, nation_data in self.data.items():
            yield Nation(nation_id, nation_data, self.game_id)

    def __len__(self):
        return len(self.data)
    
    def _get_name_from_id(self, nation_name: str) -> str | None:
        """
        Params:
            nation_name (str): A nation name.
        
        Returns:
            str: Corresponding nation id or None if no match found.
        """
        
        # tba - make this function smarter and able to handle non-exact matches
        if nation_name in self._name_to_id:
            return self._name_to_id[nation_name]
        
        return None

    def create(self, nation_id: int, player_id: int) -> Nation:
        """
        Factory method to create new Nation instance.

        Params:
            nation_id (int): ID of nation.
            player_id (int): ID of player controlling this nation.

        Returns:
            Nation: A new nation.
        """

        new_nation = Nation.build(nation_id, player_id, self.game_id)
        self.save(new_nation)

        return new_nation

    def get(self, nation_identifier: str) -> Nation:
        """
        Retrieves a Nation from the NationTable.

        Params:
            nation_identifier (str): Either the nation name or the nation id.
        
        Returns:
            Nation: Nation corresponding to nation_identifier or None if match not found.
        """

        nation_id = str(nation_identifier)

        # check if nation id was provided
        if nation_id in self.data:
            return Nation(nation_id, self.data[nation_id], self.game_id)
        
        # check if nation name was provided
        nation_id = self._get_name_from_id(nation_identifier)
        if nation_id is not None:
            return Nation(nation_id, self.data[nation_id], self.game_id)

        return None

    def save(self, nation: Nation) -> None:
        """
        Saves a Nation to the NationTable and updates gamedata.json.

        Params:
            nation (Nation): Nation to save/update.
        """

        nation_data = {
            "nationName": nation.name,
            "playerID": nation.player_id,
            "color": nation.color,
            "government": nation.gov,
            "foreignPolicy": nation.fp,
            "status": nation.status,
            "militaryCapacity": {
                "used": nation.used_mc,
                "max": nation.total_mc
            },
            "tradeFee": nation.trade_fee,
            "missileStockpile": {
                "standardMissile": nation.missile_count,
                "nuclearMissile": nation.nuke_count
            },
            "score": nation.score,
            "upkeepManager": nation._upkeep_manager,
            "chosenVictorySet": nation.chosen_vc_set,
            "victorySets": nation._sets,
            "resources": nation._resources,
            "records": nation._records,
            "improvementCount": nation._improvement_count,
            "completedResearch": nation.completed_research,
            "incomeDetails": nation.income_details
            
        }

        self.data[nation.id] = nation_data

        gamedata_filepath = f'gamedata/{self.game_id}/gamedata.json'
        with open(gamedata_filepath, 'r') as json_file:
            gamedata_dict = json.load(json_file)
        
        gamedata_dict["nations"] = self.data
        with open(gamedata_filepath, 'w') as json_file:
            json.dump(gamedata_dict, json_file, indent=4)

        self._name_to_id = {}
        for nation in self:
            self._name_to_id[nation.name] = nation.id

# to do - move these to a scenario file
EASY_LIST = [
    "Breakthrough",
    "Diversified Economy",
    "Energy Economy",
    "Industrial Focus",
    "Leading Defense",
    "Major Exporter",
    "Reconstruction Effort",
    "Secure Strategic Resources"
]
NORMAL_LIST = [
    "Backstab",
    "Diversified Army",
    "Hegemony",
    "New Empire",
    "Nuclear Deterrent",
    "Reliable Ally",
    "Sphere of Influence",
    "Warmonger"
]
HARD_LIST = [
    "Economic Domination",
    "Influence Through Trade",
    "Military Superpower",
    "Scientific Leader",
    "Territorial Control"
]
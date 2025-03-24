import json
import random

from app import core

class Nation:
    
    def __init__(self, nation_id: str | int, nation_data: dict, game_id: str):

        self.game_id = game_id

        self.id = nation_id
        self.name: str = nation_data["nationName"]
        self.player_id = nation_data["playerID"]
        self.color = nation_data["color"]
        self.gov: str = nation_data["government"]
        self.fp: str = nation_data["foreignPolicy"]
        self.status: str = nation_data["status"]
        self.trade_fee: str = nation_data["tradeFee"]
        self.completed_research: dict = nation_data["unlockedTechs"]
        self.income_details: list = nation_data["incomeDetails"]

        self.used_mc: int = nation_data["militaryCapacity"]["used"]
        self.total_mc: int = nation_data["militaryCapacity"]["max"]

        self.missile_count: int = nation_data["missileStockpile"]["standardMissile"]
        self.nuke_count: int = nation_data["missileStockpile"]["nuclearMissile"]

        self.score: int = nation_data["score"]
        self.chosen_vc_set: str = nation_data["chosenVictorySet"]

        self.improvement_counts: dict = nation_data["improvementCounts"]
        self.unit_counts: dict = nation_data["unitCounts"]

        self._upkeep_manager: dict = nation_data["upkeepManager"]
        self._sets: dict = nation_data["victorySets"]
        self._resources: dict = nation_data["resources"]
        self._records: dict = nation_data["records"]

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
        improvement_dict = core.get_scenario_dict(game_id, "Improvements")
        unit_dict = core.get_scenario_dict(game_id, "Units")
        improvement_cache = {}
        for key in improvement_dict:
            improvement_cache[key] = 0
        unit_cache = {}
        for key in unit_dict:
            unit_cache[key] = 0

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
                "Dollars": {
                    "stored": "10.00",
                    "income": "0.00",
                    "max": 100,
                    "rate": 100
                },
                "Political Power": {
                    "stored": "0.00",
                    "income": "0.00",
                    "max": 50,
                    "rate": 100
                },
                "Technology": {
                    "stored": "0.00",
                    "income": "0.00",
                    "max": 50,
                    "rate": 100
                },
                "Coal": {
                    "stored": "0.00",
                    "income": "0.00",
                    "max": 50,
                    "rate": 100
                },
                "Oil": {
                    "stored": "0.00",
                    "income": "0.00",
                    "max": 50,
                    "rate": 100
                },
                "Green Energy": {
                    "stored": "0.00",
                    "income": "0.00",
                    "max": 50,
                    "rate": 100
                },
                "Basic Materials": {
                    "stored": "0.00",
                    "income": "0.00",
                    "max": 50,
                    "rate": 100
                },
                "Common Metals": {
                    "stored": "0.00",
                    "income": "0.00",
                    "max": 50,
                    "rate": 100
                },
                "Advanced Metals": {
                    "stored": "0.00",
                    "income": "0.00",
                    "max": 50,
                    "rate": 100
                },
                "Uranium": {
                    "stored": "0.00",
                    "income": "0.00",
                    "max": 50,
                    "rate": 100
                },
                "Rare Earth Elements": {
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
            "improvementCounts": improvement_cache,
            "unitCounts": unit_cache,
            "unlockedTechs": {},
            "incomeDetails": []
        }

        return Nation(nation_id, nation_data, game_id)

    def add_tech(self, technology_name: str) -> None:
        """
        Marks an agenda or technology as unlocked.

        Params:
            technology_name: Name of agenda or technology to add.

        Returns:
            None
        """

        if technology_name in self.completed_research:
            return None

        tech_dict = core.get_scenario_dict(self.game_id, "Technologies")
        agenda_dict = core.get_scenario_dict(self.game_id, "Agendas")
        if technology_name not in tech_dict and technology_name not in agenda_dict:
            return None

        self.completed_research[technology_name] = True

    def reset_income_rates(self) -> None:
        """
        Sets income rates based on government choice. Called at the start of the game.

        Returns:
            None
        """

        for resource_name in self._resources:
            amount = INCOME_RATES[self.gov][resource_name]
            self.update_rate(resource_name, amount, overwrite = True)

    def update_rate(self, resource_name: str, amount: int, *, overwrite = False) -> None:
        """
        Updates the income rate of a resource.

        Params:
            resource_name (str): Exact name of resource.
            amount (int): Percentage you wish to add or set, where the integer 100 is 100%.
            overwrite (bool): Adds amount to current income rate if False, will overwrite instead if True.

        Returns:
            None
        """

        if resource_name not in self._resources:
            return None
        
        if not isinstance(amount, int):
            return None
        
        if overwrite:
            self._resources[resource_name]["rate"] = amount
        else:
            self._resources[resource_name]["rate"] += amount

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
            "improvementCounts": nation.improvement_counts,
            "unitCounts": nation.unit_counts,
            "unlockedTechs": nation.completed_research,
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

# tba - move everything below to a scenario file
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
INCOME_RATES = {
    "Republic": {
        "Dollars": 100,
        "Political Power": 100,
        "Technology": 100,
        "Coal": 100,
        "Oil": 100,
        "Green Energy": 100,
        "Basic Materials": 100,
        "Common Metals": 100,
        "Advanced Metals": 100,
        "Uranium": 100,
        "Rare Earth Elements": 100
    },
    "Technocracy": {
        "Dollars": 100,
        "Political Power": 100,
        "Technology": 100,
        "Coal": 100,
        "Oil": 100,
        "Green Energy": 100,
        "Basic Materials": 100,
        "Common Metals": 100,
        "Advanced Metals": 100,
        "Uranium": 100,
        "Rare Earth Elements": 100
    },
    "Olgarchy": {
        "Dollars": 120,
        "Political Power": 100,
        "Technology": 100,
        "Coal": 120,
        "Oil": 120,
        "Green Energy": 120,
        "Basic Materials": 100,
        "Common Metals": 100,
        "Advanced Metals": 100,
        "Uranium": 100,
        "Rare Earth Elements": 100
    },
    "Totalitarian": {
        "Dollars": 100,
        "Political Power": 100,
        "Technology": 100,
        "Coal": 100,
        "Oil": 100,
        "Green Energy": 100,
        "Basic Materials": 100,
        "Common Metals": 100,
        "Advanced Metals": 100,
        "Uranium": 100,
        "Rare Earth Elements": 100
    },
    "Remnant": {
        "Dollars": 100,
        "Political Power": 100,
        "Technology": 100,
        "Coal": 100,
        "Oil": 100,
        "Green Energy": 100,
        "Basic Materials": 100,
        "Common Metals": 100,
        "Advanced Metals": 100,
        "Uranium": 100,
        "Rare Earth Elements": 100
    },
    "Protectorate": {
        "Dollars": 100,
        "Political Power": 80,
        "Technology": 100,
        "Coal": 100,
        "Oil": 100,
        "Green Energy": 100,
        "Basic Materials": 100,
        "Common Metals": 100,
        "Advanced Metals": 100,
        "Uranium": 100,
        "Rare Earth Elements": 100
    },
    "Military Junta": {
        "Dollars": 100,
        "Political Power": 100,
        "Technology": 80,
        "Coal": 100,
        "Oil": 100,
        "Green Energy": 100,
        "Basic Materials": 100,
        "Common Metals": 100,
        "Advanced Metals": 100,
        "Uranium": 100,
        "Rare Earth Elements": 100
    },
    "Crime Syndicate": {
        "Dollars": 80,
        "Political Power": 100,
        "Technology": 100,
        "Coal": 100,
        "Oil": 100,
        "Green Energy": 100,
        "Basic Materials": 100,
        "Common Metals": 100,
        "Advanced Metals": 100,
        "Uranium": 100,
        "Rare Earth Elements": 100
    }
}
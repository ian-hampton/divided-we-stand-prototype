import json
import random
import os

from app import core
from app.region import Region

class Nation:
    
    def __init__(self, nation_id: str, nation_data: dict, game_id: str):

        self.game_id = game_id

        self.id: str = nation_id
        self.name: str = nation_data["nationName"]
        self.player_id = nation_data["playerID"]
        self.color = nation_data["color"]
        self.gov: str = nation_data["government"]
        self.fp: str = nation_data["foreignPolicy"]
        self.status: str = nation_data["status"]
        self.trade_fee: str = nation_data["tradeFee"]
        self.completed_research: dict = nation_data["unlockedTechs"]
        self.income_details: list = nation_data["incomeDetails"]
        self.action_log: list = nation_data["actionLog"]

        self.missile_count: int = nation_data["missileStockpile"]["standardMissile"]
        self.nuke_count: int = nation_data["missileStockpile"]["nuclearMissile"]

        self.score: int = nation_data["score"]
        self.chosen_vc_set: str = nation_data["chosenVictorySet"]
        self._sets: dict = nation_data["victorySets"]
        self.victory_conditions: dict = self._sets.get(self.chosen_vc_set)

        self.improvement_counts: dict = nation_data["improvementCounts"]
        self.unit_counts: dict = nation_data["unitCounts"]
        self.regions_owned: int = nation_data["statistics"]["regionsOwned"]
        self.regions_occupied: int = nation_data["statistics"]["regionsOccupied"]
        self.resources_given: int = nation_data["statistics"]["resourcesGiven"]
        self.resources_received: int = nation_data["statistics"]["resourcesReceived"]

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
            "tradeFee": "1:2",
            "missileStockpile": {
                "standardMissile": 0,
                "nuclearMissile": 0
            },
            "score": 0,
            "chosenVictorySet": "N/A",
            "victorySets": vc_sets,
            "resources": {
                "Dollars": {
                    "stored": "10.00",
                    "income": "0.00",
                    "grossIncome": "0.00",
                    "max": 100,
                    "rate": 100
                },
                "Political Power": {
                    "stored": "0.00",
                    "income": "0.00",
                    "grossIncome": "0.00",
                    "max": 50,
                    "rate": 100
                },
                "Technology": {
                    "stored": "0.00",
                    "income": "0.00",
                    "grossIncome": "0.00",
                    "max": 50,
                    "rate": 100
                },
                "Coal": {
                    "stored": "0.00",
                    "income": "0.00",
                    "grossIncome": "0.00",
                    "max": 50,
                    "rate": 100
                },
                "Oil": {
                    "stored": "0.00",
                    "income": "0.00",
                    "grossIncome": "0.00",
                    "max": 50,
                    "rate": 100
                },
                "Basic Materials": {
                    "stored": "0.00",
                    "income": "0.00",
                    "grossIncome": "0.00",
                    "max": 50,
                    "rate": 100
                },
                "Common Metals": {
                    "stored": "0.00",
                    "income": "0.00",
                    "grossIncome": "0.00",
                    "max": 50,
                    "rate": 100
                },
                "Advanced Metals": {
                    "stored": "0.00",
                    "income": "0.00",
                    "grossIncome": "0.00",
                    "max": 50,
                    "rate": 100
                },
                "Uranium": {
                    "stored": "0.00",
                    "income": "0.00",
                    "grossIncome": "0.00",
                    "max": 50,
                    "rate": 100
                },
                "Rare Earth Elements": {
                    "stored": "0.00",
                    "income": "0.00",
                    "grossIncome": "0.00",
                    "max": 50,
                    "rate": 100
                },
                "Energy": {
                    "income": "0.00",
                    "grossIncome": "0.00",
                    "rate": 100
                },
                "Military Capacity": {
                    "used": "0.00",
                    "max": "0.00",
                    "rate": 100
                },
            },
            "statistics": {
                "regionsOwned": 0,
                "regionsOccupied": 0,
                "resourcesGiven": 0,
                "resourcesReceived": 0
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
            "incomeDetails": [],
            "actionLog": []
        }

        return Nation(nation_id, nation_data, game_id)

    def update_victory_progress(self) -> None:
        """
        Updates victory condition progress. Be sure to save the nation object in order to commit the update!
        """
        
        from app import checks
        current_turn_num = core.get_current_turn_num(self.game_id)
        vc_results, score = checks.check_victory_conditions(self.game_id, int(self.id), current_turn_num)

        self.victory_conditions = vc_results
        self.score = score

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
            raise Exception(f"{technology_name} not recognized as an agenda/technology.")

        self.completed_research[technology_name] = True

    def export_action_log(self) -> None:
        """
        Exports player actions as a text file.
        """

        log_dir = f"gamedata/{self.game_id}/logs/nation{self.id}.txt"
        if os.path.exists(log_dir):
            os.remove(log_dir)
        
        os.makedirs(log_dir)
        with open(log_dir, 'w') as file:
            for string in self.action_log:
                file.write(string + '\n')

    def get_stockpile(self, resource_name: str) -> str:
        """
        Retrieves stockpile of a given resource.
        """
        if resource_name not in self._resources:
            raise Exception(f"Resource {resource_name} not recognized.")

        return self._resources[resource_name]["stored"]

    def update_stockpile(self, resource_name: str, amount: int | float) -> None:
        """
        Updates the stockpile of a given resource.
        """
        if resource_name not in self._resources:
            raise Exception(f"Resource {resource_name} not recognized.")
        
        if not isinstance(amount, float) and not isinstance(amount, int):
            raise TypeError(f"Invalid amount provided. Expected a float or integer.")
        
        stored = float(self._resources[resource_name]["stored"])
        stored += amount
        stored_max = int(self.get_max(resource_name))
        if stored > stored_max:
            stored = stored_max
        self._resources[resource_name]["stored"] = f"{stored:.2f}"

    def get_income(self, resource_name: str) -> str:
        """
        Retrives income of a given resource.
        """
        if resource_name not in self._resources:
            raise Exception(f"Resource {resource_name} not recognized.")
        
        if resource_name == "Military Capacity":
            return self.get_max_mc()

        return self._resources[resource_name]["income"]

    def update_income(self, resource_name: str, amount: int | float, *, overwrite = False) -> None:
        """
        Updates the income of a specific resource by a specific amount.

        Params:
            resource_name (str): Exact name of resource to update.
            amount (int | float): Amount you wish to add.
            overwrite (bool): Adds amount to current income if False, will overwrite instead if True.

        Returns:
            None
        """
        
        if resource_name not in self._resources:
            raise Exception(f"Resource {resource_name} not recognized.")
        
        if not isinstance(amount, float) and not isinstance(amount, int):
            raise TypeError(f"Invalid amount provided. Expected a float or integer.")
        
        if resource_name == "Military Capacity":
            return
        
        if overwrite:
            self._resources[resource_name]["income"] = f"{amount:.2f}"
            return

        income = float(self._resources[resource_name]["income"])
        income += amount
        self._resources[resource_name]["income"] = f"{income:.2f}"

    def get_gross_income(self, resource_name: str) -> str:
        """
        Retrieves gross income of a given resource.
        """
        if resource_name not in self._resources:
            raise Exception(f"Resource {resource_name} not recognized.")
        
        if resource_name == "Military Capacity":
            return self.get_max_mc()

        return self._resources[resource_name]["grossIncome"]

    def update_gross_income(self, resource_name: str, amount: int | float, *, overwrite = False) -> None:
        """
        Updates the gross income of a specific resource by a specific amount.

        Params:
            resource_name (str): Exact name of resource to update.
            amount (float): Amount you wish to add.
            overwrite (bool): Adds amount to current income if False, will overwrite instead if True.

        Returns:
            None
        """
        
        if resource_name not in self._resources:
            raise Exception(f"Resource {resource_name} not recognized.")
        
        if not isinstance(amount, float) and not isinstance(amount, int):
            raise TypeError(f"Invalid amount provided. Expected a float or integer.")
        
        if resource_name == "Military Capacity":
            self.update_max_mc(amount, overwrite=overwrite)
            return

        if overwrite:
            self._resources[resource_name]["grossIncome"] = f"{amount:.2f}"
            return
        
        income = float(self._resources[resource_name]["grossIncome"])
        income += amount
        self._resources[resource_name]["grossIncome"] = f"{income:.2f}"

    def get_max(self, resource_name: str) -> None:
        """
        Retrives max storage amount of a given resource.
        """
        if resource_name not in self._resources:
            raise Exception(f"Resource {resource_name} not recognized.")

        return self._resources[resource_name]["max"]

    def update_max(self, resource_name: str, amount: int, *, overwrite = False) -> None:
        """
        Updates max storage amount of a given resource.
        """

        if resource_name not in self._resources:
            raise Exception(f"Resource {resource_name} not recognized.")
        
        if not isinstance(amount, int):
            raise TypeError(f"Invalid amount provided. Expected an integer.")
        
        if overwrite:
            self._resources[resource_name]["max"] = f"{amount:.2f}"
            return
        
        income = float(self._resources[resource_name]["max"])
        income += amount
        self._resources[resource_name]["max"] = f"{income:.2f}"

    def get_rate(self, resource_name: str) -> str:
        """
        Retrieves income rate of a given resource.
        """
        if resource_name not in self._resources:
            raise Exception(f"Resource {resource_name} not recognized.")

        return self._resources[resource_name]["rate"]

    def update_rate(self, resource_name: str, amount: int, *, overwrite = False) -> None:
        """
        Updates the income rate of a resource.

        Params:
            resource_name (str): Exact name of resource to update.
            amount (int): Percentage you wish to add or set, where the integer 100 is 100%.
            overwrite (bool): Adds amount to current rate if False, will overwrite instead if True.

        Returns:
            None
        """

        if resource_name not in self._resources:
            raise Exception(f"Resource {resource_name} not recognized.")
        
        if not isinstance(amount, int):
            raise TypeError(f"Invalid amount provided. Expected an integer.")
        
        if overwrite:
            self._resources[resource_name]["rate"] = amount
        else:
            self._resources[resource_name]["rate"] += amount

    def reset_income_rates(self) -> None:
        """
        Sets income rates based on government choice. Called at the start of the game.

        Returns:
            None
        """

        for resource_name in self._resources:
            amount = INCOME_RATES[self.gov][resource_name]
            self.update_rate(resource_name, amount, overwrite = True)

    def get_used_mc(self) -> float:
        """
        Returns used military capacity of this nation.
        """
        return float(self._resources["Military Capacity"]["used"])

    def update_used_mc(self, amount: int | float, *, overwrite = False) -> None:
        """
        Updates used military capacity of this nation.
        """
        
        if not isinstance(amount, float) and not isinstance(amount, int):
            raise TypeError(f"Invalid amount provided. Expected a float or integer.")
        
        if overwrite:
            self._resources["Military Capacity"]["used"] = f"{amount:.2f}"
            return
        
        income = float(self._resources["Military Capacity"]["used"])
        income += amount
        self._resources["Military Capacity"]["used"] = f"{income:.2f}"

    def get_max_mc(self) -> float:
        """
        Returns military capacity limit of this nation.
        """
        return float(self._resources["Military Capacity"]["max"])

    def update_max_mc(self, amount: int | float, *, overwrite = False) -> None:
        """
        Updates max military capacity of this nation.
        """
        
        if not isinstance(amount, float) and not isinstance(amount, int):
            raise TypeError(f"Invalid amount provided. Expected a float or integer.")
        
        if overwrite:
            self._resources["Military Capacity"]["max"] = f"{amount:.2f}"
            return
        
        income = float(self._resources["Military Capacity"]["max"])
        income += amount
        self._resources["Military Capacity"]["max"] = f"{income:.2f}"

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

        if nation_name in self._name_to_id:
            return self._name_to_id[nation_name]
        
        for temp in self._name_to_id:
            if nation_name.lower() == temp.lower():
                return self._name_to_id[temp]
        
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

        raise Exception(f"Failed to retrieve nation with identifier {nation_identifier}.")

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
            "tradeFee": nation.trade_fee,
            "missileStockpile": {
                "standardMissile": nation.missile_count,
                "nuclearMissile": nation.nuke_count
            },
            "score": nation.score,
            "chosenVictorySet": nation.chosen_vc_set,
            "victorySets": nation._sets,
            "resources": nation._resources,
            "statistics": {
                "regionsOwned": nation.regions_owned,
                "regionsOccupied": nation.regions_occupied,
                "resourcesGiven": nation.resources_given,
                "resourcesReceived": nation.resources_received
            },
            "records": nation._records,
            "improvementCounts": nation.improvement_counts,
            "unitCounts": nation.unit_counts,
            "unlockedTechs": nation.completed_research,
            "incomeDetails": nation.income_details,
            "actionLog": nation.action_log
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

    def update_records(self) -> None:
        """
        Updates leaderboard records in each nation.
        """

        current_turn_num = core.get_current_turn_num(self.game_id)
        tech_data_dict = core.get_scenario_dict(self.game_id, "Technologies")
        rmdata_filepath = f'gamedata/{self.game_id}/rmdata.csv'
        rmdata_all_transaction_list = core.read_rmdata(rmdata_filepath, current_turn_num, False, False)

        for nation in self:

            # update military strength
            military_strength = 0
            for unit_name, unit_count in nation.unit_counts.items():
                military_strength += unit_count
            nation._records["militaryStrength"].append(military_strength)

            # update nation size
            nation._records["nationSize"].append(nation.regions_owned)

            # update net income total
            net_income_total = 0
            for resource_name in nation._resources:
                if resource_name == "Military Capacity":
                    continue
                income = float(nation.get_income(resource_name))
                net_income_total += income
            nation._records["netIncome"].append(f"{net_income_total:.2f}")

            # update tech count
            technology_count = 0
            for technology_name in nation.completed_research:
                if technology_name in tech_data_dict:
                    technology_count += 1
            nation._records["researchCount"].append(technology_count)

            # update transaction count
            transaction_count = 0
            for transaction in rmdata_all_transaction_list:
                if transaction[1] == nation.name:
                    transaction_count += int(transaction[3])
            transaction_count += nation.resources_given
            transaction_count += nation.resources_received
            nation._records["transactionCount"].append(transaction_count)

            self.save(nation)

    def get_top_three(self, record_name: str) -> list:
        """
        Retrieves the top three of a given record.
        """

        data = {}
        for nation in self:
            if record_name == "netIncome":
                data[nation.name] = float(nation._records[record_name][-1])
            else:
                data[nation.name] = nation._records[record_name][-1]

        sorted_data = dict(sorted(data.items(), key=lambda item: item[1], reverse=True))
        top_three = list(sorted_data.items())[:3]
        
        return top_three

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
        "Energy": 100,
        "Basic Materials": 100,
        "Common Metals": 100,
        "Advanced Metals": 100,
        "Uranium": 100,
        "Rare Earth Elements": 100,
        "Military Capacity": 100
    },
    "Technocracy": {
        "Dollars": 100,
        "Political Power": 100,
        "Technology": 100,
        "Coal": 100,
        "Oil": 100,
        "Energy": 100,
        "Basic Materials": 100,
        "Common Metals": 100,
        "Advanced Metals": 100,
        "Uranium": 100,
        "Rare Earth Elements": 100,
        "Military Capacity": 100
    },
    "Oligarchy": {
        "Dollars": 120,
        "Political Power": 100,
        "Technology": 100,
        "Coal": 120,
        "Oil": 120,
        "Energy": 120,
        "Basic Materials": 100,
        "Common Metals": 100,
        "Advanced Metals": 100,
        "Uranium": 100,
        "Rare Earth Elements": 100,
        "Military Capacity": 100
    },
    "Totalitarian": {
        "Dollars": 100,
        "Political Power": 100,
        "Technology": 100,
        "Coal": 100,
        "Oil": 100,
        "Energy": 100,
        "Basic Materials": 100,
        "Common Metals": 100,
        "Advanced Metals": 100,
        "Uranium": 100,
        "Rare Earth Elements": 100,
        "Military Capacity": 120
    },
    "Remnant": {
        "Dollars": 100,
        "Political Power": 100,
        "Technology": 100,
        "Coal": 100,
        "Oil": 100,
        "Energy": 100,
        "Basic Materials": 100,
        "Common Metals": 100,
        "Advanced Metals": 100,
        "Uranium": 100,
        "Rare Earth Elements": 100,
        "Military Capacity": 100
    },
    "Protectorate": {
        "Dollars": 100,
        "Political Power": 80,
        "Technology": 100,
        "Coal": 100,
        "Oil": 100,
        "Energy": 100,
        "Basic Materials": 100,
        "Common Metals": 100,
        "Advanced Metals": 100,
        "Uranium": 100,
        "Rare Earth Elements": 100,
        "Military Capacity": 100
    },
    "Military Junta": {
        "Dollars": 100,
        "Political Power": 100,
        "Technology": 80,
        "Coal": 100,
        "Oil": 100,
        "Energy": 100,
        "Basic Materials": 100,
        "Common Metals": 100,
        "Advanced Metals": 100,
        "Uranium": 100,
        "Rare Earth Elements": 100,
        "Military Capacity": 100
    },
    "Crime Syndicate": {
        "Dollars": 80,
        "Political Power": 100,
        "Technology": 100,
        "Coal": 100,
        "Oil": 100,
        "Energy": 100,
        "Basic Materials": 100,
        "Common Metals": 100,
        "Advanced Metals": 100,
        "Uranium": 100,
        "Rare Earth Elements": 100,
        "Military Capacity": 100
    }
}
import json
import os
import random
from dataclasses import dataclass
from typing import ClassVar, Iterator, Tuple
from enum import StrEnum

from app.game.games import Games
from app.scenario import ScenarioData as SD
from .nation import Nation

class NationsMeta(type):

    def __iter__(cls) -> Iterator["Nation"]:
        for nation_id in cls._data:
            nation = Nation(nation_id, cls._data[nation_id], cls.game_id)
            if nation.is_active:
                yield nation

    def __len__(cls):
        length = 0
        for nation_id in cls._data:
            nation = Nation(nation_id, cls._data[nation_id], cls.game_id)
            if nation.is_active:
                length += 1
        return length

@dataclass
class Nations(metaclass=NationsMeta):

    game_id: ClassVar[str] = None
    _data: ClassVar[dict[str, dict]] = None

    @classmethod
    def load(cls, game_id: str) -> None:

        cls.game_id = game_id
        gamedata_filepath = f"gamedata/{cls.game_id}/gamedata.json"
        if not os.path.exists(gamedata_filepath):
            raise FileNotFoundError(f"Error: Unable to locate required game files for Nations class.")

        with open(gamedata_filepath, 'r') as f:
            gamedata_dict = json.load(f)

        cls._data = gamedata_dict["nations"]

    @classmethod
    def save(cls) -> None:

        if cls._data is None:
            raise RuntimeError("Error: Nations has not been loaded.")

        gamedata_filepath = f"gamedata/{cls.game_id}/gamedata.json"
        with open(gamedata_filepath, 'r') as json_file:
            gamedata_dict = json.load(json_file)

        gamedata_dict["nations"] = cls._data
        with open(gamedata_filepath, 'w') as json_file:
            json.dump(gamedata_dict, json_file, indent=4)

    @classmethod
    def create(cls, nation_id: str, player_id: int) -> None:

        nation_data = {
            "nationName": "N/A",
            "playerID": player_id,
            "color": "#ffffff",
            "government": "N/A",
            "foreignPolicy": "N/A",
            "status": "Independent Nation",
            "tradeFee": "1:2",
            "standardMissileStockpile": 0,
            "nuclearMissileStockpile": 0,
            "stealActionRecord": [0, ""],
            "score": 0,
            "chosenVictorySet": {},
            "victorySets": cls._generate_vc_sets(2),
            "satisfiedVictorySet": {},
            "resources": {
                "Dollars": {
                    "stored": "5.00",
                    "income": "0.00",
                    "grossIncome": "0.00",
                    "max": 100,
                    "rate": 100
                },
                "Political Power": {
                    "stored": "1.00",
                    "income": "0.00",
                    "grossIncome": "0.00",
                    "max": 50,
                    "rate": 100
                },
                "Research": {
                    "stored": "0.00",
                    "income": "0.00",
                    "grossIncome": "0.00",
                    "max": 50,
                    "rate": 100
                },
                "Food": {
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
                "regionsOnEdge": 0,
                "resourcesGiven": 0,
                "resourcesReceived": 0
            },
            "records": {
                "agendaCount": [],
                "developmentScore": [],
                "energyIncome": [],
                "industrialIncome": [],
                "militarySize": [],
                "militaryStrength": [],
                "nationSize": [],
                "netIncome": [],
                "researchCount": [],
                "transactionCount": [],
                "netExports": []
            },
            "improvementCounts": {improvement_name: 0 for improvement_name, improvement_data in SD.improvements},
            "unitCounts": {unit_name: 0 for unit_name, unit_data in SD.units},
            "unlockedResearch": {},
            "incomeDetails": [],
            "tags": {},
            "actionLog": []
        }
        
        cls._data[nation_id] = nation_data

    @classmethod
    def get(cls, string: str) -> "Nation":
        
        # check if nation id was provided
        if string in cls._data:
            return Nation(string, cls._data[string], cls.game_id)
        
        # check if nation name was provided
        for nation in cls:
            if nation.name.lower() == string.lower():
                return Nation(nation.id, cls._data[nation.id], cls.game_id)

        raise Exception(f"Failed to retrieve nation with identifier {string}.")
    
    @classmethod
    def get_random_id(cls) -> str:
        
        nation_ids = []

        for nation in cls:
            if nation.is_active:
                nation_ids.append(nation.id)

        return random.choice(nation_ids)

    @classmethod
    def update_records(cls) -> None:

        game = Games.load(cls.game_id)
        
        rmdata_all_transaction_list = game.get_market_data(refine=0)

        for nation in cls:

            nation.records.nation_size.append(nation.stats.regions_owned)

            net_income_total = 0
            for resource_name in nation._resources:
                if resource_name == "Military Capacity":
                    continue
                income = float(nation.get_income(resource_name))
                net_income_total += income
            nation.records.net_income.append(f"{net_income_total:.2f}")

            industrial_income_total = 0
            energy_income_total = 0
            for resource_name in nation._resources:
                if resource_name == "Military Capacity":
                    continue
                income = float(nation.get_gross_income(resource_name))
                if resource_name in ["Basic Materials", "Common Metals", "Advanced Metals"]:
                    industrial_income_total += income
                if resource_name in ["Energy", "Coal", "Oil"]:
                    energy_income_total += income
            nation.records.industrial_income.append(f"{industrial_income_total:.2f}")
            nation.records.energy_income.append(f"{energy_income_total:.2f}")

            development_score = 0
            development_score += nation.improvement_counts.get("Central Bank", 0) * 1
            development_score += nation.improvement_counts.get("Research Institute", 0) * 1
            development_score += nation.improvement_counts.get("Settlement", 0) * 1
            development_score += nation.improvement_counts.get("City", 0) * 3
            development_score += nation.improvement_counts.get("Capital", 0) * 10
            nation.records.development.append(development_score)

            military_size = 0
            for unit_name, unit_count in nation.unit_counts.items():
                military_size += unit_count
            nation.records.military_size.append(military_size)

            military_strength = 0
            for unit_name, unit_data in SD.units:
                military_strength += nation.unit_counts.get(unit_name, 0) * unit_data.value
            nation.records.military_strength.append(military_strength)

            agenda_count = 0
            technology_count = 0
            for name in nation.completed_research:
                if name in SD.agendas:
                    agenda_count += 1
                elif name in SD.technologies:
                    technology_count += 1
            nation.records.agenda_count.append(agenda_count)
            nation.records.technology_count.append(technology_count)

            transaction_count = 0
            for transaction in rmdata_all_transaction_list:
                if transaction[1] == nation.name:
                    transaction_count += int(transaction[3])
            transaction_count += nation.stats.resources_given
            transaction_count += nation.stats.resources_received
            nation.records.transaction_count.append(int(transaction_count))

            net_exports = 0
            for transaction in rmdata_all_transaction_list:
                if transaction[1] == nation.name and transaction[2] == "Bought":
                    net_exports -= int(transaction[3])
                elif transaction[1] == nation.name and transaction[2] == "Sold":
                    net_exports += int(transaction[3])
            net_exports += nation.stats.resources_given
            net_exports -= nation.stats.resources_received
            nation.records.net_exports.append(int(net_exports))

    @classmethod
    def get_top_three(cls, record: LeaderboardRecordNames) -> list[Tuple[str, float|int]]:

        data = {}
        
        for nation in cls:
            record_data: list = getattr(nation.records, record.value)
            if record is LeaderboardRecordNames.NET_INCOME:
                data[nation.name] = float(record_data[-1])
            else:
                data[nation.name] = record_data[-1]

        sorted_data = dict(sorted(data.items(), key=lambda item: item[1], reverse=True))
        top_three = list(sorted_data.items())[:3]
        
        return top_three

    @classmethod
    def get_lowest_in_record(cls, record_name: str) -> Tuple[str, float|int]:
        
        data = {}
        
        for nation in cls:
            record_data: list = getattr(nation.records, record_name)
            if record_name == "net_income":
                data[nation.name] = float(record_data[-1])
            else:
                data[nation.name] = record_data[-1]

        return min(data.items(), key=lambda item: item[1])

    @classmethod
    def add_leaderboard_bonuses(cls) -> None:
        
        # leaderboard bonuses only begin starting on turn 5
        game = Games.load(cls.game_id)
        if game.turn < 5:
            return

        bonus = [1, 0.5, 0.25]
        record_name_to_string = {
            "nation_size": "from nation size",
            "net_income": "from economic power",
            "net_exports": "from trade power",
            "military_strength": "from military strength",
            "technology_count": "from technology progress"
        }

        for record_name, string in record_name_to_string.items():

            top_three = cls.get_top_three(record_name)

            valid = 2
            if top_three[0][1] == top_three[1][1]:
                valid = -1
            elif top_three[1][1] == top_three[2][1]:
                valid = 0

            for i, entry in enumerate(top_three):

                nation_name = entry[0]
                score = entry[1]

                if i <= valid and score != 0:

                    # add political power bonus to stockpile and income
                    nation = cls.get(nation_name)
                    nation.update_stockpile("Political Power", bonus[i])
                    nation.update_income("Political Power", bonus[i])

                    # add income string to income details
                    pp_index = nation._find_pp_index()
                    p1 = nation.income_details[:pp_index + 1]
                    p2 = nation.income_details[pp_index + 1:]
                    p1.append(f"&Tab;+{bonus[i]:.2f} {string}")
                    nation.income_details = p1 + p2

    @classmethod
    def attribute_to_title(cls, attribute_name: str) -> str:

        attribute_str_to_name_str = {
            "military_strength": "Strongest Militaries",
            "nation_size": "Largest Nations",
            "net_income": "Highest Net Incomes",
            "technology_count": "Most Technologies",
            "net_exports": "Highest Net Exports"
        }

        return attribute_str_to_name_str.get(attribute_name, "NULL")

    @classmethod
    def check_tags(cls) -> None:
        
        game = Games.load(cls.game_id)
        
        for nation in cls:
            
            tags_filtered = {}
            for tag_name, tag_data in nation.tags.items():
                if tag_data["Expire Turn"] > game.turn:
                    tags_filtered[tag_name] = tag_data
            
            nation.tags = tags_filtered

    @classmethod
    def prune_eliminated_nations(cls) -> None:

        from app.notifications import Notifications
        
        for nation in cls:
            if nation.status != "Eliminated" and nation.stats.regions_owned == 0:
                nation.status = "Eliminated"
                Notifications.add(f"{nation.name} has been eliminated!", 1)

    @classmethod
    def _generate_vc_sets(cls, count: int) -> dict:

        easy_list = SD.victory_conditions.easy
        medium_list = SD.victory_conditions.medium
        hard_List = SD.victory_conditions.hard

        vc_sets = {}
        random_easys = random.sample(easy_list, len(easy_list))
        random_mediums = random.sample(medium_list, len(medium_list))
        random_hards = random.sample(hard_List, len(hard_List))

        for i in range(count):
            name = f"set{i+1}"
            vc_sets[name] = {}
            vc_sets[name][random_easys.pop()] = False
            vc_sets[name][random_mediums.pop()] = False
            vc_sets[name][random_hards.pop()] = False

        return vc_sets
    
class LeaderboardRecordNames(StrEnum):
    NATION_SIZE = "nation_size"
    NET_INCOME = "net_income"
    MILITARY_STRENGTH = "military_strength"
    TECHNOLOGY_COUNT = "technology_count"
    NET_EXPORTS = "net_exports"
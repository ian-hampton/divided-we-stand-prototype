import json
import os
import random
from dataclasses import dataclass
from typing import ClassVar, Iterator, Tuple

from app import core

class NationsMeta(type):

    def __iter__(cls) -> Iterator["Nation"]:
        for nation in cls:
            if nation.is_active:
                yield Nation(nation.id)

    def __len__(cls):
        length = 0
        for nation in cls:
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

        from app.scenario import ScenarioData as SD

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
            return Nation(string)
        
        # check if nation name was provided
        for nation in cls:
            if nation.name.lower() == string.lower():
                return Nation(nation.id)

        raise Exception(f"Failed to retrieve nation with identifier {string}.")
    
    @classmethod
    def get_random_name(cls) -> str:
        pass

    @classmethod
    def update_records(cls) -> None:

        from app.scenario import ScenarioData as SD
        
        current_turn_num = core.get_current_turn_num(cls.game_id)
        rmdata_filepath = f"gamedata/{cls.game_id}/rmdata.csv"
        rmdata_all_transaction_list = core.read_rmdata(rmdata_filepath, current_turn_num, False, False)

        for nation in cls:

            # update military strength
            military_strength = 0
            for unit_name, unit_count in nation.unit_counts.items():
                military_strength += unit_count
            nation._records["militaryStrength"].append(military_strength)

            # update nation size
            nation._records["nationSize"].append(nation.stats.regions_owned)

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
                if technology_name in SD.technologies:
                    technology_count += 1
            nation._records["researchCount"].append(technology_count)

            # update transaction count
            transaction_count = 0
            for transaction in rmdata_all_transaction_list:
                if transaction[1] == nation.name:
                    transaction_count += int(transaction[3])
            transaction_count += nation.stats.resources_given
            transaction_count += nation.stats.resources_received
            nation._records["transactionCount"].append(transaction_count)

    @classmethod
    def get_top_three(cls, record_name: str) -> list[Tuple[str, float|int]]:
        
        data = {}
        for nation in cls:
            if record_name == "netIncome":
                data[nation.name] = float(nation._records[record_name][-1])
            else:
                data[nation.name] = nation._records[record_name][-1]

        sorted_data = dict(sorted(data.items(), key=lambda item: item[1], reverse=True))
        top_three = list(sorted_data.items())[:3]
        
        return top_three

    @classmethod
    def get_lowest_in_record(cls, record_name: str) -> Tuple[str, float|int]:
        
        data = {}
        for nation in cls:
            if record_name == "netIncome":
                data[nation.name] = float(nation._records[record_name][-1])
            else:
                data[nation.name] = nation._records[record_name][-1]

        return min(data.items(), key=lambda item: item[1])

    @classmethod
    def add_leaderboard_bonuses(cls) -> None:
        
        # leaderboard bonuses only begin starting on turn 5
        current_turn_num = core.get_current_turn_num(cls.game_id)
        if current_turn_num < 5:
            return

        bonus = [1, 0.5, 0.25]
        records = ["nationSize", "netIncome", "transactionCount", "militaryStrength", "researchCount"]
        record_string = ["from nation size",
                         "from economic strength",
                         "from trade power",
                         "from military strength",
                         "from research progress"]
        
        for i, record_name in enumerate(records):
            
            top_three = cls.get_top_three(record_name)

            valid = 2
            if top_three[0][1] == top_three[1][1]:
                valid = -1
            elif top_three[1][1] == top_three[2][1]:
                valid = 0

            for j, entry in enumerate(top_three):
                nation_name = entry[0]
                score = entry[1]
                
                if j <= valid and score != 0:
                    
                    # add political power bonus to stockpile and income
                    nation = cls.get(nation_name)
                    nation.update_stockpile("Political Power", bonus[j])
                    nation.update_income("Political Power", bonus[j])

                    # add income string to income details
                    pp_index = nation._find_pp_index()
                    p1 = nation.income_details[:pp_index + 1]
                    p2 = nation.income_details[pp_index + 1:]
                    p1.append(f"&Tab;+{bonus[j]:.2f} {record_string[i]}")
                    nation.income_details = p1 + p2

    @classmethod
    def check_tags(cls) -> None:
        
        current_turn_num = core.get_current_turn_num(cls.game_id)
        
        for nation in cls:
            
            tags_filtered = {}
            for tag_name, tag_data in nation.tags.items():
                if tag_data["Expire Turn"] > current_turn_num:
                    tags_filtered[tag_name] = tag_data
            
            nation.tags = tags_filtered

    @classmethod
    def prune_eliminated_nations(cls) -> None:

        from app.notifications import Notifications
        
        for nation in cls:
            if nation.stats.regions_owned == 0:
                nation.status = "Eliminated"
                Notifications.add(f"{nation.name} has been eliminated!", 1)

    @classmethod
    def _generate_vc_sets(cls, count: int) -> dict:

        from app.scenario import ScenarioData as SD
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

class Nation:
    
    def __init__(self, nation_id: str):

        self._data = Nations._data[nation_id]

        self.id: str = nation_id
        self._name: str = self._data["nationName"]
        self._player_id: str = self._data["playerID"]
        self._color: str = self._data["color"]
        self._gov: str = self._data["government"]
        self._fp: str = self._data["foreignPolicy"]
        self._status: str = self._data["status"]
        self._trade_fee: str = self._data["tradeFee"]
        self._missile_count: int = self._data["standardMissileStockpile"]
        self._nuke_count: int = self._data["nuclearMissileStockpile"]
        self._score: int = self._data["score"]

        self.stats = NationStatistics(self._data["statistics"])

    @property
    def name(self):
        return self._name
    
    @property
    def player_id(self):
        return self._player_id
    
    @property
    def is_active(self) -> bool:
        """
        Returns True if Nation is not eliminated or controlled by an event.
        """

        if self.status != "Eliminated" and self.id != 99:
            return True
        
        return False

    @property
    def color(self):
        return self._color
    
    @property
    def gov(self):
        return self._gov
    
    @property
    def fp(self):
        return self._fp
    
    @property
    def status(self):
        return self._status
    
    @property
    def trade_fee(self):
        return self._trade_fee
    
    @property
    def missile_count(self):
        return self._missile_count
    
    @property
    def nuke_count(self):
        return self._nuke_count
    
    @property
    def score(self):
        return self._score
    
    @property
    def victory_conditions(self) -> dict:
        return self._data["chosenVictorySet"]

    @property
    def completed_research(self) -> dict:
        return self._data["unlockedResearch"]

    @property
    def improvement_counts(self) -> dict:
        return self._data["improvementCounts"]

    @property
    def unit_counts(self) -> dict:
        return self._data["unitCounts"]

    @property
    def tags(self) -> dict:
        return self._data["tags"]

    @property
    def action_log(self) -> list:
        return self._data["actionLog"]

    @property
    def income_details(self) -> list:
        return self._data["incomeDetails"]
    
    @property
    def _sets(self) -> dict:
        return self._data["victorySets"]

    @property
    def _satisfied(self) -> dict:
        return self._data["satisfiedVictorySet"]

    @property
    def _records(self) -> dict:
        return self._data["records"]

    @property
    def _resources(self) -> dict:
        return self._data["resources"]

    @name.setter
    def name(self, value: str):
        self._name = value
        self._data["nationName"] = value

    @player_id.setter
    def player_id(self, value: str):
        self._player_id = value
        self._data["playerID"] = value

    @color.setter
    def color(self, value: str):
        self._color = value
        self._data["color"] = value

    @gov.setter
    def gov(self, value: str):
        self._gov = value
        self._data["government"] = value

    @fp.setter
    def fp(self, value: str):
        self._fp = value
        self._data["foreignPolicy"] = value

    @status.setter
    def status(self, value: str):
        self._status = value
        self._data["status"] = value

    @trade_fee.setter
    def trade_fee(self, value: str):
        self._trade_fee = value
        self._data["tradeFee"] = value

    @missile_count.setter
    def missile_count(self, value: int):
        self._missile_count = value
        self._data["standardMissileStockpile"] = value

    @nuke_count.setter
    def nuke_count(self, value: int):
        self._nuke_count = value
        self._data["nuclearMissileStockpile"] = value

    @score.setter
    def score(self, value: int):
        self._score = value
        self._data["score"] = value

    @victory_conditions.setter
    def victory_conditions(self, value: dict) -> None:
        self._data["chosenVictorySet"] = value

    @completed_research.setter
    def completed_research(self, value: dict) -> None:
        self._data["unlockedResearch"] = value

    @improvement_counts.setter
    def improvement_counts(self, value: dict) -> None:
        self._data["improvementCounts"] = value

    @unit_counts.setter
    def unit_counts(self, value: dict) -> None:
        self._data["unitCounts"] = value

    @tags.setter
    def tags(self, value: dict) -> None:
        self._data["tags"] = value

    @action_log.setter
    def action_log(self, value: list) -> None:
        self._data["actionLog"] = value

    @income_details.setter
    def income_details(self, value: list) -> None:
        self._data["incomeDetails"] = value

    @_sets.setter
    def _sets(self, value: dict) -> None:
        self._data["victorySets"] = value

    @_satisfied.setter
    def _satisfied(self, value: dict) -> None:
        self._data["satisfiedVictorySet"] = value

    @_records.setter
    def _records(self, value: dict) -> None:
        self._data["records"] = value

    @_resources.setter
    def _resources(self, value: dict) -> None:
        self._data["resources"] = value

    def add_gov_tags(self) -> None:
        
        match self.gov:

            case "Republic":
                new_tag = {
                    "Alliance Limit Modifier": 1,
                    "Expire Turn": 99999
                }
                self.tags["Republic"] = new_tag

            case "Technocracy":
                new_tag = {
                    "Research Rate": 20,
                    "Expire Turn": 99999
                }
                self.tags["Technocracy"] = new_tag

            case "Oligarchy":
                new_tag = {
                    "Dollars Rate": 20,
                    "Coal Rate": 20,
                    "Oil Rate": 20,
                    "Energy Rate": 20,
                    "Expire Turn": 99999
                }
                self.tags["Oligarchy"] = new_tag

            case "Totalitarian":
                new_tag = {
                    "Military Capacity Rate": 20,
                    "Research Bonus": {
                        "Amount": 2,
                        "Resource": "Political Power",
                        "Categories": ["Energy", "Infrastructure"]
                    },
                    "Expire Turn": 99999
                }
                self.tags["Totalitarian"] = new_tag

            case "Remnant":
                new_tag = {
                    "Build Discount": 0.2,
                    "Capital Boost": True,
                    "Agenda Cost": 5,
                    "Expire Turn": 99999
                }
                self.tags["Remnant"] = new_tag

            case "Protectorate":
                new_tag = {
                    "Basic Materials Rate": 20,
                    "Market Buy Modifier": 0.2,
                    "Market Sell Modifier": 0.2,
                    "Improvement Income Multiplier": {
                        "Settlement": {
                            "Dollars": -0.2
                        },
                        "City": {
                            "Dollars": -0.2
                        }
                    },
                    "Expire Turn": 99999
                }
                self.tags["Protectorate"] = new_tag

            case "Military Junta":
                new_tag = {
                    "Improvement Income Multiplier": {
                        "Research Laboratory": {
                            "Research": -0.2
                        },
                        "Research Institute": {
                            "Research": -0.2
                        }
                    },
                    "Expire Turn": 99999
                }
                self.tags["Military Junta"] = new_tag

            case "Crime Syndicate":
                new_tag = {
                    "Region Claim Cost": 0.2,
                    "Expire Turn": 99999
                }
                self.tags["Crime Syndicate"] = new_tag

    def update_victory_progress(self) -> None:
        
        import app.victory_conditions as vc
        
        self.score = 0
        for name in self.victory_conditions.keys():
            self.victory_conditions[name] = False

        for name in self.victory_conditions.keys():
            
            # do not check vcs that have already been permanently satisfied
            if self._satisfied[name]:
                self.score += 1
                continue

            name_to_func = {
                "Ambassador": vc.ambassador,
                "Backstab": vc.backstab,
                "Breakthrough": vc.breakthrough,
                "Diversified Economy": vc.breakthrough,
                "Double Down": vc.double_down,
                "New Empire": vc.new_empire,
                "Reconstruction Effort": vc.reconstruction_effort,
                "Reliable Ally": vc.reliable_ally,
                "Secure Strategic Resources": vc.secure_strategic_resources,
                "Threat Containment": vc.threat_containment,
                "Energy Focus": vc.energy_focus,
                "Industrial Focus": vc.industrial_focus,
                "Hegemony": vc.hegemony,
                "Monopoly": vc.monopoly,
                "Nuclear Deterrent": vc.nuclear_deterrent,
                "Strong Research Agreement": vc.strong_research_agreement,
                "Strong Trade Agreement": vc.strong_trade_agreement,
                "Sphere of Influence": vc.sphere_of_influence,
                "Underdog": vc.underdog,
                "Warmonger": vc.warmonger,
                "Economic Domination": vc.economic_domination,
                "Influence Through Trade": vc.influence_through_trade,
                "Military Superpower": vc.military_superpower,
                "Scientific Leader": vc.scientific_leader,
                "Territorial Control": vc.territorial_control
            }
            
            if name in name_to_func:

                if name_to_func[name](self):
                    
                    # mark victory condition as completed
                    self.score += 1
                    self.victory_conditions[name] = True

                    # mark victory condition as permanently satisfied if needed
                    one_and_done = {"Ambassador", "Backstab", "Breakthrough", "Double Down", "Reliable Ally", "Threat Containment",
                                    "Monopoly", "Strong Research Agreement", "Strong Trade Agreement", "Sphere of Influence", "Underdog", "Warmonger"}
                    if name in one_and_done:
                        self._satisfied[name] = True

    def add_tech(self, technology_name: str) -> None:
        
        from app.scenario import ScenarioData as SD

        if technology_name not in SD.agendas and technology_name not in SD.technologies:
            raise Exception(f"{technology_name} not recognized as an agenda/technology.")

        self.completed_research[technology_name] = True

    def update_trade_fee(self) -> None:
        
        trade_fee_list = ["3:1", "2:1", "1:1", "1:2", "1:3", "1:4", "1:5"]
        trade_index = 3

        if "Improved Logistics" in self.completed_research:
            trade_index += 1

        for tag_data in self.tags.values():
            trade_index += tag_data.get("Trade Fee Modifier", 0)

        self.trade_fee = trade_fee_list[trade_index]

    def award_research_bonus(self, research_name: str) -> None:
        
        from app.scenario import ScenarioData as SD

        for tag_data in self.tags.values():
            
            if "Research Bonus" not in tag_data:
                continue
            
            bonus_dict = tag_data["Research Bonus"]
            sd_technology = SD.technologies[research_name]

            if sd_technology.type in bonus_dict["Categories"]:
                resource_name: str = bonus_dict["Resource"]
                resource_amount: int = bonus_dict["Amount"]
                self.update_stockpile(resource_name, resource_amount)
                self.action_log.append(f"Gained {resource_amount} {resource_name} for researching {research_name}.")

    def apply_build_discount(self, build_cost_dict: dict) -> None:
        
        build_cost_rate = 1.0
        for tag_data in self.tags.values():
            build_cost_rate -= float(tag_data.get("Build Discount", 0))

        for key in build_cost_dict:
            build_cost_dict[key] *= build_cost_rate

    def calculate_agenda_cost_adjustment(self, agenda_name: str) -> int:
        
        from app.scenario import ScenarioData as SD

        adjustment = 0

        agenda_cost_adjustment = {
            "Cooperative": {
                "Diplomatic": -5,
                "Commercial": 0,
                "Isolationist": 5,
                "Imperialist": 0
            },
            "Economic": {
                "Diplomatic": 0,
                "Commercial": -5,
                "Isolationist": 0,
                "Imperialist": 5
            },
            "Security": {
                "Diplomatic": 0,
                "Commercial": 5,
                "Isolationist": -5,
                "Imperialist": 0,
            },
            "Warfare": {
                "Diplomatic": 5,
                "Commercial": 0,
                "Isolationist": 0,
                "Imperialist": -5,
            }
        }

        sd_agenda = SD.agendas[agenda_name]
        adjustment += agenda_cost_adjustment[sd_agenda.type][self.fp]

        # cost adjustment from tags
        for tag_data in self.tags.values():
            adjustment += int(tag_data.get("Agenda Cost", 0))
        
        return adjustment

    def region_claim_political_power_cost(self) -> float:
        pp_cost = 0.0
        for tag_data in self.tags.values():
            pp_cost += float(tag_data.get("Region Claim Cost", 0))
        return pp_cost

    def calculate_alliance_capacity(self) -> tuple[int, int]:
        
        from app.scenario import ScenarioData as SD
        from app.alliance import Alliances

        capacity_used = 0
        for alliance in Alliances:
            if (alliance.is_active
                and self.name in alliance
                and SD.alliances[alliance.type].capacity
                ):
                capacity_used += 1
        
        capacity_limit = 2
        for agenda_name, agenda_data in SD.agendas:
            capacity_limit += agenda_data.modifiers.get("Alliance Limit Modifier", 0)
        for tag_data in self.tags.values():
            capacity_limit += tag_data.get("Alliance Limit Modifier", 0)

        return capacity_used, capacity_limit

    def fetch_alliance_data(self) -> dict:

        from app.scenario import ScenarioData as SD

        alliance_count, alliance_capacity = self.calculate_alliance_capacity()

        data = {
            "Header": f"Alliances ({alliance_count}/{alliance_capacity})",
            "Names": list(SD.alliances.names()),
            "Colors": []
        }

        types_sorted = sorted(SD.alliances.names())
        for alliance_type_name in types_sorted:
            required_agenda = SD.alliances[alliance_type_name].required_agenda
            if required_agenda in self.completed_research:
                data["Colors"].append("#00ff00")
            else:
                data["Colors"].append("#ff0000")

        return data

    def get_subjects(self, subject_type: str) -> list:
        
        subjects = []

        for nation in Nations:
            if self.name in nation.status and subject_type in nation.status:
                subjects.append(nation.id)
        
        return subjects

    def export_action_log(self) -> None:
        
        log_file = f"gamedata/{Nations.game_id}/logs/nation{self.id}.txt"
        log_dir = os.path.dirname(log_file)

        os.makedirs(log_dir, exist_ok=True)
        with open(log_file, 'w') as file:
            for string in self.action_log:
                file.write(string + '\n')

    def get_stockpile(self, resource_name: str) -> str:
        if resource_name not in self._resources:
            raise Exception(f"Resource {resource_name} not recognized.")
        return self._resources[resource_name]["stored"]

    def update_stockpile(self, resource_name: str, amount: int | float, *, overwrite = False) -> None:
        
        if resource_name not in self._resources:
            raise Exception(f"Resource {resource_name} not recognized.")
        
        if not isinstance(amount, float) and not isinstance(amount, int):
            raise TypeError(f"Invalid amount provided. Expected a float or integer.")
        
        if overwrite:
            self._resources[resource_name]["stored"] = f"{amount:.2f}"
            return
        
        stored = float(self._resources[resource_name]["stored"])
        stored += amount
        
        stored_max = int(self.get_max(resource_name))
        if stored > stored_max:
            stored = stored_max
        if stored < 0:
            stored = 0

        self._resources[resource_name]["stored"] = f"{stored:.2f}"

    def get_income(self, resource_name: str) -> str:
        
        if resource_name not in self._resources:
            raise Exception(f"Resource {resource_name} not recognized.")
        
        if resource_name == "Military Capacity":
            return self.get_max_mc()

        return self._resources[resource_name]["income"]

    def update_income(self, resource_name: str, amount: int | float, *, overwrite = False) -> None:
        
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
        
        if resource_name not in self._resources:
            raise Exception(f"Resource {resource_name} not recognized.")
        
        if resource_name == "Military Capacity":
            return self.get_max_mc()

        return self._resources[resource_name]["grossIncome"]

    def update_gross_income(self, resource_name: str, amount: int | float, *, overwrite = False) -> None:
        
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

    def get_max(self, resource_name: str) -> int:
        if resource_name not in self._resources:
            raise Exception(f"Resource {resource_name} not recognized.")
        return self._resources[resource_name]["max"]

    def update_max(self, resource_name: str, amount: int, *, overwrite = False) -> None:
        
        if resource_name not in self._resources:
            raise Exception(f"Resource {resource_name} not recognized.")
        
        if not isinstance(amount, int):
            raise TypeError(f"Invalid amount provided. Expected an integer.")
        
        if overwrite:
            self._resources[resource_name]["max"] = f"{amount}"
            return
        
        max = int(self._resources[resource_name]["max"])
        max += amount
        self._resources[resource_name]["max"] = f"{max}"

    def update_stockpile_limits(self) -> None:
        
        for resource_name in self._resources:

            if resource_name in ["Energy", "Military Capacity"]:
                continue
            
            new_max = 50
            cb_count = self.improvement_counts.get("Central Bank", 0)
            new_max += cb_count * 20
            
            # dollars stockpile is always 50 more than other resources
            if resource_name == "Dollars":
                new_max += 50
            
            self.update_max(resource_name, int(new_max), overwrite=True)

    def get_rate(self, resource_name: str) -> int:
        
        if resource_name not in self._resources:
            raise Exception(f"Resource {resource_name} not recognized.")
        
        rate = self._resources[resource_name]["rate"]
        for tag_data in self.tags.values():
            rate += tag_data.get(f"{resource_name} Rate", 0)

        return rate

    def update_rate(self, resource_name: str, amount: int, *, overwrite = False) -> None:
        
        if resource_name not in self._resources:
            raise Exception(f"Resource {resource_name} not recognized.")
        
        if not isinstance(amount, int):
            raise TypeError(f"Invalid amount provided. Expected an integer.")
        
        if overwrite:
            self._resources[resource_name]["rate"] = amount
        else:
            self._resources[resource_name]["rate"] += amount

    def get_used_mc(self) -> float:
        return float(self._resources["Military Capacity"]["used"])

    def update_used_mc(self, amount: int | float, *, overwrite = False) -> None:
        
        if not isinstance(amount, float) and not isinstance(amount, int):
            raise TypeError(f"Invalid amount provided. Expected a float or integer.")
        
        if overwrite:
            self._resources["Military Capacity"]["used"] = f"{amount:.2f}"
            return
        
        income = float(self._resources["Military Capacity"]["used"])
        income += amount
        self._resources["Military Capacity"]["used"] = f"{income:.2f}"

    def get_max_mc(self) -> float:
        
        # do not enforce military capacity restrictions on foreign adversary
        if self.name == "Foreign Adversary":
            return 99999

        return float(self._resources["Military Capacity"]["max"])

    def update_max_mc(self, amount: int | float, *, overwrite = False) -> None:
        
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

    def _find_pp_index(self) -> int:
        """
        Returns in index of where the political power log starts.
        """
        for i, str in enumerate(self.income_details):
            if "Political Power" in str:
                return i

class NationStatistics:

    def __init__(self, d: dict):

        self._data = d
        self._regions_owned: int = d["regionsOwned"]
        self._regions_occupied: int = d["regionsOccupied"]
        self._resources_given: float = d["resourcesGiven"]
        self._resources_received: float = d["resourcesReceived"]

    @property
    def regions_owned(self):
        return self._regions_owned
    
    @property
    def regions_occupied(self):
        return self._regions_occupied
    
    @property
    def resources_given(self):
        return self._resources_given
    
    @property
    def resources_received(self):
        return self._resources_received
    
    @regions_owned.setter
    def regions_owned(self, value: int):
        self._regions_owned = value
        self._data["regionsOwned"] = value

    @regions_occupied.setter
    def regions_occupied(self, value: int):
        self._regions_occupied = value
        self._data["regionsOccupied"] = value

    @resources_given.setter
    def resources_given(self, value: float):
        self._resources_given = value
        self._data["resourcesGiven"] = value

    @resources_received.setter
    def resources_received(self, value: float):
        self._resources_received = value
        self._data["resourcesReceived"] = value
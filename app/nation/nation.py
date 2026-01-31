import os
from collections.abc import Generator

from app.scenario.scenario import ScenarioInterface as SD

class Nation:
    
    def __init__(self, nation_id: str, data: dict, game_id: str):
        self.id: str = nation_id
        self._data = data
        self._game_id = game_id
        self.stats = NationStatistics(self._data["statistics"])
        self.records = NationRecords(self._data["records"])

    @property
    def name(self) -> str:
        return self._data["nationName"]

    @name.setter
    def name(self, value: str):
        self._data["nationName"] = value

    @property
    def player_id(self) -> str:
        return self._data["playerID"]

    @player_id.setter
    def player_id(self, value: str):
        self._data["playerID"] = value

    @property
    def is_active(self) -> bool:
        """
        Returns True if Nation is not eliminated or controlled by an event.
        """

        if self.status != "Eliminated" and self.id != 99:
            return True
        
        return False

    @property
    def color(self) -> str:
        return self._data["color"]

    @color.setter
    def color(self, value: str) -> None:
        self._data["color"] = value

    @property
    def gov(self) -> str:
        return self._data["government"]

    @gov.setter
    def gov(self, value: str) -> None:
        self._data["government"] = value

    @property
    def fp(self) -> str:
        return self._data["foreignPolicy"]

    @fp.setter
    def fp(self, value: str) -> None:
        self._data["foreignPolicy"] = value

    @property
    def status(self) -> str:
        return self._data["status"]

    @status.setter
    def status(self, value: str) -> None:
        self._data["status"] = value

    @property
    def trade_fee(self) -> str:
        return self._data["tradeFee"]

    @trade_fee.setter
    def trade_fee(self, value: str) -> None:
        self._data["tradeFee"] = value

    @property
    def missile_count(self) -> int:
        return self._data["standardMissileStockpile"]

    @missile_count.setter
    def missile_count(self, value: int) -> None:
        self._data["standardMissileStockpile"] = value

    @property
    def nuke_count(self) -> int:
        return self._data["nuclearMissileStockpile"]

    @nuke_count.setter
    def nuke_count(self, value: int) -> None:
        self._data["nuclearMissileStockpile"] = value

    @property
    def score(self) -> int:
        return self._data["score"]

    @score.setter
    def score(self, value: int) -> None:
        self._data["score"] = value

    @property
    def victory_conditions(self) -> dict:
        return self._data["chosenVictorySet"]

    @victory_conditions.setter
    def victory_conditions(self, value: dict) -> None:
        self._data["chosenVictorySet"] = value

    @property
    def completed_research(self) -> dict:
        return self._data["unlockedResearch"]

    @completed_research.setter
    def completed_research(self, value: dict) -> None:
        self._data["unlockedResearch"] = value

    @property
    def improvement_counts(self) -> dict:
        return self._data["improvementCounts"]

    @improvement_counts.setter
    def improvement_counts(self, value: dict) -> None:
        self._data["improvementCounts"] = value

    @property
    def unit_counts(self) -> dict:
        return self._data["unitCounts"]

    @unit_counts.setter
    def unit_counts(self, value: dict) -> None:
        self._data["unitCounts"] = value

    @property
    def unit_counts_lifetime(self) -> dict:
        return self._data["unitCountsLifetime"]

    @unit_counts_lifetime.setter
    def unit_counts_lifetime(self, value: dict) -> None:
        self._data["unitCountsLifetime"] = value

    @property
    def steal_action_record(self) -> list:
        return self._data["stealActionRecord"]

    @steal_action_record.setter
    def stealActionRecord(self, value: list) -> None:
        self._data["stealActionRecord"] = value

    @property
    def tags(self) -> dict:
        return self._data["tags"]

    @tags.setter
    def tags(self, value: dict) -> None:
        self._data["tags"] = value

    @property
    def action_log(self) -> list:
        return self._data["actionLog"]

    @action_log.setter
    def action_log(self, value: list) -> None:
        self._data["actionLog"] = value

    @property
    def income_details(self) -> list:
        return self._data["incomeDetails"]

    @income_details.setter
    def income_details(self, value: list) -> None:
        self._data["incomeDetails"] = value

    @property
    def _sets(self) -> dict:
        return self._data["victorySets"]

    @_sets.setter
    def _sets(self, value: dict) -> None:
        self._data["victorySets"] = value

    @property
    def _satisfied(self) -> dict:
        return self._data["satisfiedVictorySet"]

    @_satisfied.setter
    def _satisfied(self, value: dict) -> None:
        self._data["satisfiedVictorySet"] = value

    @property
    def _resources(self) -> dict:
        return self._data["resources"]

    @_resources.setter
    def _resources(self, value: dict) -> None:
        self._data["resources"] = value

    def __lt__(self, other: 'Nation'):
        return self.name < other.name

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
                    "Starting XP Bonus": 10,
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
                "Energy Focus": vc.energy_focus,
                "Industrial Focus": vc.industrial_focus,
                "Hegemony": vc.hegemony,
                "Monopoly": vc.monopoly,
                "Nuclear Deterrent": vc.nuclear_deterrent,
                "Strong Research Agreement": vc.strong_research_agreement,
                "Strong Trade Agreement": vc.strong_trade_agreement,
                "Sphere of Influence": vc.sphere_of_influence,
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
                    one_and_done = {"Ambassador", "Backstab", "Breakthrough", "Double Down", "Energy Focus", "Industrial Focus", "Monopoly", "Strong Research Agreement", "Strong Trade Agreement", "Sphere of Influence", "Warmonger"}
                    if name in one_and_done:
                        self._satisfied[name] = True

    def add_tech(self, technology_name: str) -> None:

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

    def calculate_alliance_capacity(self) -> tuple[int, int]:

        from app.alliance.alliances import Alliances

        capacity_used = 0
        for alliance in Alliances:
            if (alliance.is_active
                and self.name in alliance.current_members
                and SD.alliances[alliance.type].capacity
                ):
                capacity_used += 1
        
        capacity_limit = 2
        for name in self.completed_research:
            if name in SD.agendas:
                agenda_data = SD.agendas[name]
                capacity_limit += agenda_data.modifiers.get("Alliance Limit Modifier", 0)
            elif name in SD.technologies:
                technology_data = SD.technologies[name]
                capacity_limit += technology_data.modifiers.get("Alliance Limit Modifier", 0)
        for tag_data in self.tags.values():
            capacity_limit += tag_data.get("Alliance Limit Modifier", 0)

        return capacity_used, capacity_limit

    def fetch_alliance_data(self) -> dict:

        alliance_count, alliance_capacity = self.calculate_alliance_capacity()

        data = {
            "Header": f"Alliances ({alliance_count}/{alliance_capacity})"
        }

        types_sorted = sorted(SD.alliances.names())
        for alliance_type_name in types_sorted:
            required_agenda = SD.alliances[alliance_type_name].required_agenda
            if required_agenda in self.completed_research:
                data[alliance_type_name] = "#00ff00"
            else:
                data[alliance_type_name] = "#ff0000"

        return data

    def get_subjects(self, subject_type: str, nation_list: list[Nation]) -> list:
        
        subjects = []

        for nation in nation_list:
            if self.name in nation.status and subject_type in nation.status:
                subjects.append(nation.id)
        
        return subjects

    def export_action_log(self) -> None:
        
        log_file = f"gamedata/{self._game_id}/logs/nation{self.id}.txt"
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

    def update_military_capacity(self) -> None:
        used_military_capacity = 0
        for count in self.unit_counts.values():
            used_military_capacity += count
        self._resources["Military Capacity"]["used"] = f"{used_military_capacity:.2f}"

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
            
    def generate_full_unit_name(self, unit_name: str) -> str:
        """
        Creates the full name for a unit using its name and number.

        Args:
            unit_name (str): A string name representing what unit it is.

        Returns:
            str: Full unit name.
        """
        self.unit_counts_lifetime[unit_name] += 1
        count = self.unit_counts_lifetime[unit_name]
        if 10 <= count % 100 <= 13:
            suffix = "th"
        else:
            match count % 10:
                case 1:
                    suffix = "st"
                case 2:
                    suffix = "nd"
                case 3:
                    suffix = "rd"
                case _:
                    suffix = "th"
        return f"{count}{suffix} {unit_name}"

    def calculate_starting_xp(self) -> int:
        """
        Calculates the amount of XP each unit deployed by this nation starts with.

        Returns:
            int: Starting XP value.
        """
        amount = 0
        for tag_data in self.tags.values():
            amount += int(tag_data.get("Starting XP Bonus", 0))
        return amount

class NationStatistics:

    def __init__(self, d: dict):
        self._data = d

    @property
    def regions_owned(self) -> int:
        return self._data["regionsOwned"]
        
    @regions_owned.setter
    def regions_owned(self, value: int) -> None:
        self._data["regionsOwned"] = value

    @property
    def regions_on_map_edge(self) -> int:
        return self._data["regionsOnEdge"]
    
    @regions_on_map_edge.setter
    def regions_on_map_edge(self, value: int) -> None:
        self._data["regionsOnEdge"] = value

    @property
    def regions_occupied(self) -> int:
        return self._data["regionsOccupied"]
    
    @regions_occupied.setter
    def regions_occupied(self, value: int) -> None:
        self._data["regionsOccupied"] = value

    @property
    def resources_given(self) -> float:
        return self._data["resourcesGiven"]

    @resources_given.setter
    def resources_given(self, value: float) -> None:
        self._data["resourcesGiven"] = value

    @property
    def resources_received(self) -> float:
        return self._data["resourcesReceived"]

    @resources_received.setter
    def resources_received(self, value: float) -> None:
        self._data["resourcesReceived"] = value

class NationRecords:

    def __init__(self, d: dict):
        self._data = d

    @property
    def agenda_count(self) -> list:
        return self._data["agendaCount"]
        
    @agenda_count.setter
    def agenda_count(self, value: list) -> None:
        self._data["agendaCount"] = value

    @property
    def development(self) -> list:
        return self._data["developmentScore"]
    
    @development.setter
    def development(self, value: list) -> None:
        self._data["developmentScore"] = value

    @property
    def energy_income(self) -> list:
        return self._data["energyIncome"]

    @energy_income.setter
    def energy_income(self, value: list) -> None:
        self._data["energyIncome"] = value
    
    @property
    def industrial_income(self) -> list:
        return self._data["industrialIncome"]
    
    @industrial_income.setter
    def industrial_income(self, value: list) -> None:
        self._data["industrialIncome"] = value

    @property
    def military_size(self) -> list:
        return self._data["militarySize"]

    @military_size.setter
    def military_size(self, value: list) -> None:
        self._data["militarySize"] = value

    @property
    def military_strength(self) -> list:
        return self._data["militaryStrength"]

    @military_strength.setter
    def military_strength(self, value: list) -> None:
        self._data["militaryStrength"] = value

    @property
    def nation_size(self) -> list:
        return self._data["nationSize"]

    @nation_size.setter
    def nation_size(self, value: list) -> None:
        self._data["nationSize"] = value

    @property
    def net_income(self) -> list:
        return self._data["netIncome"]

    @net_income.setter
    def net_income(self, value: list) -> None:
        self._data["netIncome"] = value

    @property
    def technology_count(self) -> list:
        return self._data["researchCount"]

    @technology_count.setter
    def technology_count(self, value: list) -> None:
        self._data["researchCount"] = value

    @property
    def transaction_count(self) -> list:
        return self._data["transactionCount"]

    @transaction_count.setter
    def transaction_count(self, value: list) -> None:
        self._data["transactionCount"] = value

    @property
    def net_exports(self) -> list:
        return self._data["netExports"]

    @net_exports.setter
    def net_exports(self, value: list) -> None:
        self._data["netExports"] = value

    def iter_leaderboard_records(self) -> Generator[tuple[str, list], None, None]:
        from .nations import LeaderboardRecordNames
        for record in LeaderboardRecordNames:
            value = getattr(self, record.value)
            yield record.value, value

    def iter_all_records(self) -> Generator[tuple[str, list], None, None]:

        for attribute_name in dir(self):
            
            if attribute_name[0] == "_":
                continue

            value = getattr(self, attribute_name)
            if callable(value):
                continue

            yield attribute_name, value
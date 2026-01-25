import copy
from collections import defaultdict

from app.scenario.scenario import ScenarioInterface as SD
from app.alliance.alliances import Alliances
from app.nation.nation import Nation
from app.nation.nations import Nations
from app.region.regions import Regions
from app.war.wars import Wars
from . import economic_helpers

class UpdateIncomeProcess:

    def __init__(self, game_id: str):
        self.game_id = game_id
        self.yield_dict: dict[str, dict] = {}
        self.upkeep_dict: dict[str, dict] = {}
        self.text_dict: dict[str, dict] = {}

    def _prepare_nations(self) -> None:
        """
        Prepare for income calculation by executing initial work and calculations on nations.
        """
        
        for nation in Nations:

            self.yield_dict[nation.name] = economic_helpers.create_player_yield_dict(nation)
            self.upkeep_dict[nation.name] = economic_helpers.create_player_upkeep_dict(nation)
            self.text_dict[nation.name] = {}
            
            for resource_name in nation._resources:
                self.text_dict[nation.name][resource_name] = defaultdict(int)
                if resource_name == "Military Capacity":
                    nation.update_max_mc(0.00, overwrite=True)
                else:
                    nation.update_gross_income(resource_name, 0.00, overwrite=True)

            # reset the statistics that are calculated by this function
            nation.stats.regions_owned = 0
            nation.stats.regions_occupied = 0
            nation.stats.regions_on_map_edge = 0

    def _calculate_gross_income(self) -> None:
    
        for region in Regions:
            
            # skip if region is unowned or controlled by an event
            if region.data.owner_id in ["0", "99"]:
                continue
            
            # update stats based on region
            nation = Nations.get(region.data.owner_id)
            nation.stats.regions_owned += 1
            if region.data.occupier_id != "0":
                nation.stats.regions_occupied += 1
            if region.graph.is_edge:
                nation.stats.regions_on_map_edge += 1
            
            # skip if region is empty
            if region.improvement.name is None and region.unit.name is None:
                continue
            
            # collect improvement income
            if region.improvement.name is not None and region.improvement.health != 0 and region.data.occupier_id == "0":
                
                if region.improvement.name[-1] != 'y':
                    plural_improvement_name = f"{region.improvement.name}s"
                else:
                    plural_improvement_name = f"{region.improvement.name[:-1]}ies"
                
                nation = Nations.get(region.data.owner_id)
                improvement_income_dict = self.yield_dict[nation.name][region.improvement.name]
                improvement_yield_dict = region.calculate_yield(self.game_id, nation, improvement_income_dict)
                
                for resource_name, amount_gained in improvement_yield_dict.items():
                    if amount_gained == 0:
                        continue
                    nation.update_gross_income(resource_name, amount_gained)
                    income_str = f"+{amount_gained:.2f} from {plural_improvement_name}"
                    self.text_dict[nation.name][resource_name][income_str] += 1

            if region.unit.name is not None:

                # trigger boot camp ability
                if region.improvement.name == "Boot Camp" and region.unit.xp < 10:
                    region.unit.xp = 10
                    region.unit.calculate_level()
        
        for nation in Nations:

            # add political power income from alliances
            alliance_income = 0
            alliance_count, alliance_capacity = nation.calculate_alliance_capacity()
            for name in nation.completed_research:
                if name in SD.agendas:
                    agenda_data = SD.agendas[name]
                    alliance_income += agenda_data.modifiers.get("Alliance Political Power Bonus", 0)
                elif name in SD.technologies:
                    technology_data = SD.technologies[name]
                    alliance_income += technology_data.modifiers.get("Alliance Political Power Bonus", 0)
            for tag_data in nation.tags.values():
                alliance_income += tag_data.get("Alliance Political Power Bonus", 0)
            if alliance_income * alliance_count != 0:
                nation.update_gross_income("Political Power", alliance_income * alliance_count)
                for i in range(alliance_count):
                    income_str = f"+{alliance_income:.2f} from alliances"
                    self.text_dict[nation.name]["Political Power"][income_str] += 1

            # add political power income from wars
            war_win_count = 0
            for war in Wars:
                if war.outcome == "Attacker Victory" and war.get_role(nation.id) == "Main Attacker":
                    war_win_count += 1
            if war_win_count != 0 and "Early Expansion" in nation.completed_research:
                nation.update_gross_income("Political Power", 0.5 * war_win_count)
                for i in range(war_win_count):
                    income_str = f"+0.5 from winning a war"
                    self.text_dict[nation.name]["Political Power"][income_str] += 1

            # add income from tags
            for resource_name in nation._resources:
                for tag_name, tag_data in nation.tags.items():
                    amount = float(tag_data.get(f"{resource_name} Income", 0))
                    if amount == 0:
                        continue
                    nation.update_gross_income(resource_name, amount)
                    income_str = f"{amount:+.2f} from {tag_name}."
                    self.text_dict[nation.name][resource_name][income_str] += 1

        # alliance yields
        for alliance in Alliances:
            amount, resource_name = alliance.calculate_yield()
            if amount == 0 or resource_name is None:
                continue
            for ally_name in alliance.current_members:
                nation = Nations.get(ally_name)
                if "Alliance Centralization" in nation.completed_research:
                    amount = round(amount * 1.5, 2)
                if resource_name == "Military Capacity":
                    nation.update_max_mc(amount)
                else:
                    nation.update_gross_income(resource_name, amount)
                income_str = f"+{amount:.2f} from {alliance.name}."
                self.text_dict[nation.name][resource_name][income_str] += 1

        # apply income rate to gross income
        for nation in Nations:
            for resource_name in nation._resources:
                
                total = float(nation.get_gross_income(resource_name))
                rate = float(nation.get_rate(resource_name)) / 100
                final_gross_income = round(total * rate, 2)
                rate_diff = round(final_gross_income - total, 2)
                
                if rate_diff != 0:
                    income_str = f"{rate_diff:+.2f} from income rate."
                    self.text_dict[nation.name][resource_name][income_str] += 1
                
                nation.update_gross_income(resource_name, final_gross_income, overwrite=True)

    def _pay_energy(self, nation: Nation, resouce_name: str, income=True) -> None:
        
        energy_income = float(nation.get_income("Energy"))
        
        if income:
            source = "income"
            resource_amount = float(nation.get_income(resouce_name))
        else:
            source = "reserves"
            resource_amount = float(nation.get_stockpile(resouce_name))

        sum = float(energy_income) + float(resource_amount)

        if sum > 0:
            upkeep_payment = resource_amount - sum
            nation.update_income("Energy", upkeep_payment)
            nation.update_income(resouce_name, -1 * upkeep_payment)
        else:
            upkeep_payment = resource_amount
            nation.update_income("Energy", upkeep_payment)
            nation.update_income(resouce_name, 0.00, overwrite=True)
            
        income_str = f"+{upkeep_payment:.2f} from {resouce_name.lower()} {source}."
        self.text_dict[nation.name]["Energy"][income_str] += 1
        
        income_str = f"-{upkeep_payment:.2f} from energy upkeep costs."
        self.text_dict[nation.name][resouce_name][income_str] += 1

    def _calculate_net_income(self) -> None:
    
        for nation in Nations:

            # reset net income
            for resource_name in nation._resources:
                gross_income = float(nation.get_gross_income(resource_name))
                nation.update_income(resource_name, gross_income, overwrite=True)
            
            # account for puppet state dues
            if "Puppet State" in nation.status:
                
                for temp in Nations:
                    if temp in nation.status:
                        overlord = temp
                        break
                
                for resource_name in nation._resources:
                    
                    if resource_name == "Military Capacity":
                        continue
                    
                    tax_amount = nation.get_gross_income(resource_name) * 0.2
                    tax_amount = round(tax_amount, 2)
                    
                    nation.update_income(resource_name, -1 * tax_amount)
                    income_str = f"-{tax_amount:.2f} from tribute to {overlord.name}."
                    self.text_dict[nation.name][resource_name][income_str] += 1
                    
                    overlord.update_income(resource_name, tax_amount)
                    income_str = f"{tax_amount:.2f} from puppet state tribute."
                    self.text_dict[nation.name][resource_name][income_str] += 1

            # calculate player upkeep costs
            player_upkeep_costs_dict = {}
            upkeep_resources = ["Dollars", "Food", "Oil", "Uranium", "Energy"]
            for resource_name in upkeep_resources:
                inner_dict = {
                    "From Units": economic_helpers.calculate_upkeep(resource_name, self.upkeep_dict[nation.name], nation.unit_counts),
                    "From Improvements": economic_helpers.calculate_upkeep(resource_name, self.upkeep_dict[nation.name], nation.improvement_counts)
                }
                player_upkeep_costs_dict[resource_name] = copy.deepcopy(inner_dict)
            
            # pay non-energy upkeep
            for resource_name in upkeep_resources:
                if resource_name == "Energy":
                    continue
                upkeep = player_upkeep_costs_dict[resource_name]["From Units"] + player_upkeep_costs_dict[resource_name]["From Improvements"]
                if upkeep > 0:
                    nation.update_income(resource_name, -1 * upkeep)
                    income_str = f'-{upkeep:.2f} from upkeep costs.'
                    self.text_dict[nation.name][resource_name][income_str] += 1

            # add energy upkeep to net income
            energy_upkeep = player_upkeep_costs_dict["Energy"]["From Units"] + player_upkeep_costs_dict["Energy"]["From Improvements"]
            nation.update_income("Energy", -1 * energy_upkeep)
            if energy_upkeep > 0:
                income_str = f"-{energy_upkeep:.2f} from energy upkeep costs."
                self.text_dict[nation.name][resource_name][income_str] += 1
            
            # attempt to spend coal income to pay remaining energy upkeep
            energy_income = float(nation.get_income("Energy"))
            coal_income = float(nation.get_income("Coal"))
            if energy_income < 0 and coal_income > 0:
                self._pay_energy(nation, "Coal")
            
            # attempt to spend oil income to pay remaining energy upkeep
            energy_income = float(nation.get_income("Energy"))
            oil_income = float(nation.get_income("Oil"))
            if energy_income < 0 and oil_income > 0:
                self._pay_energy(nation, "Oil")
            
            # attempt to spend coal reserves to pay remaining energy upkeep
            energy_income = float(nation.get_income("Energy"))
            coal_reserves = float(nation.get_stockpile("Coal"))
            if energy_income < 0 and coal_reserves > 0:
                self._pay_energy(nation, "Coal", income=False)
            
            # attempt to spend oil reserves to pay remaining energy upkeep
            energy_income = float(nation.get_income("Energy"))
            oil_reserves = float(nation.get_stockpile("Oil"))
            if energy_income < 0 and oil_reserves > 0:
                self._pay_energy(nation, "Oil", income=False)

    def _refine_income_strings(self) -> None:
    
        # create strings for net incomes
        final_income_strings = {}
        for nation in Nations:
            final_income_strings[nation.name] = {}
            for resource_name in nation._resources:
                str_list = []
                resource_total = float(nation.get_income(resource_name))
                str_list.append(f"<section> {resource_total:+.2f} {resource_name}")
                final_income_strings[nation.name][resource_name] = str_list

        # add counts
        for nation in Nations:
            for resource_name in nation._resources:
                for income_string, count in self.text_dict[nation.name][resource_name].items():
                    if count > 1:
                        income_string = f"{income_string} [{count}x]"
                    final_income_strings[nation.name][resource_name].append(income_string)

        # save income strings
        for nation in Nations:
            resource_string_lists = final_income_strings[nation.name]
            temp = []
            for resource_name, string_list in resource_string_lists.items():
                if len(string_list) > 1 or resource_name in ["Dollars", "Political Power", "Research", "Military Capacity", "Energy"]:
                    temp += string_list
            nation.income_details = temp

    def run(self) -> None:
        self._prepare_nations()
        self._calculate_gross_income()
        self._calculate_net_income()
        self._refine_income_strings()
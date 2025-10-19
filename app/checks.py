import copy
import random
from collections import defaultdict

from app import core
from app.nation import Nation, Nations
from app.notifications import Notifications

def update_income(game_id: str) -> None:

    from app.scenario import ScenarioData as SD

    from app.alliance import Alliances
    from app.region import Regions

    def calculate_gross_income() -> None:
    
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
                improvement_income_dict = yield_dict[nation.name][region.improvement.name]
                improvement_yield_dict = region.calculate_yield(game_id, nation, improvement_income_dict)
                
                for resource_name, amount_gained in improvement_yield_dict.items():
                    if amount_gained == 0:
                        continue
                    nation.update_gross_income(resource_name, amount_gained)
                    income_str = f"&Tab;+{amount_gained:.2f} from {plural_improvement_name}"
                    text_dict[nation.name][resource_name][income_str] += 1

            # collect unit income
            if region.unit.name is not None:
                nation = Nations.get(region.unit.owner_id)
                if nation.gov == "Military Junta":
                    nation.update_gross_income("Political Power", 0.1)
                    income_str = "&Tab;+0.10 from Military Junta bonus."
                    text_dict[nation.name]["Political Power"][income_str] += 1
        
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
            if alliance_income * alliance_count == 0:
                continue
            nation.update_gross_income("Political Power", alliance_income * alliance_count)
            for i in range(alliance_count):
                income_str = f"&Tab;+{alliance_income:.2f} from alliances"
                text_dict[nation.name]["Political Power"][income_str] += 1

            for resource_name in nation._resources:
                
                # add income from tags
                for tag_name, tag_data in nation.tags.items():
                    
                    amount = float(tag_data.get(f"{resource_name} Income", 0))
                    if amount == 0:
                        continue

                    nation.update_gross_income(resource_name, amount)
                    income_str = f"&Tab;{amount:+.2f} from {tag_name}."
                    text_dict[nation.name][resource_name][income_str] += 1

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
                income_str = f"&Tab;+{amount:.2f} from {alliance.name}."
                text_dict[nation.name][resource_name][income_str] += 1

        # apply income rate to gross income
        for nation in Nations:
            for resource_name in nation._resources:
                
                total = float(nation.get_gross_income(resource_name))
                rate = float(nation.get_rate(resource_name)) / 100
                final_gross_income = round(total * rate, 2)
                rate_diff = round(final_gross_income - total, 2)
                
                if rate_diff != 0:
                    income_str = f"&Tab;+{rate_diff:+.2f} from income rate."
                    text_dict[nation.name][resource_name][income_str] += 1
                
                nation.update_gross_income(resource_name, final_gross_income, overwrite=True)

    def calculate_net_income() -> None:
    
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
                    income_str = f"&Tab;-{tax_amount:.2f} from tribute to {overlord.name}."
                    text_dict[nation.name][resource_name][income_str] += 1
                    
                    overlord.update_income(resource_name, tax_amount)
                    income_str = f"&Tab;{tax_amount:.2f} from puppet state tribute."
                    text_dict[nation.name][resource_name][income_str] += 1

            # calculate player upkeep costs
            player_upkeep_costs_dict = {}
            upkeep_resources = ["Dollars", "Food", "Oil", "Uranium", "Energy"]
            for resource_name in upkeep_resources:
                inner_dict = {
                    "From Units": core.calculate_upkeep(resource_name, upkeep_dict[nation.name], nation.unit_counts),
                    "From Improvements": core.calculate_upkeep(resource_name, upkeep_dict[nation.name], nation.improvement_counts)
                }
                player_upkeep_costs_dict[resource_name] = copy.deepcopy(inner_dict)
            
            # pay non-energy upkeep
            for resource_name in upkeep_resources:
                if resource_name == "Energy":
                    continue
                upkeep = player_upkeep_costs_dict[resource_name]["From Units"] + player_upkeep_costs_dict[resource_name]["From Improvements"]
                if upkeep > 0:
                    nation.update_income(resource_name, -1 * upkeep)
                    income_str = f'&Tab;-{upkeep:.2f} from upkeep costs.'
                    text_dict[nation.name][resource_name][income_str] += 1

            # add energy upkeep to net income
            energy_upkeep = player_upkeep_costs_dict["Energy"]["From Units"] + player_upkeep_costs_dict["Energy"]["From Improvements"]
            nation.update_income("Energy", -1 * energy_upkeep)
            if energy_upkeep > 0:
                income_str = f"&Tab;-{energy_upkeep:.2f} from energy upkeep costs."
                text_dict[nation.name][resource_name][income_str] += 1
            
            # attempt to spend coal income to pay remaining energy upkeep
            energy_income = float(nation.get_income("Energy"))
            coal_income = float(nation.get_income("Coal"))
            if energy_income < 0 and coal_income > 0:
                nation = pay_energy(nation, "Coal")
            
            # attempt to spend oil income to pay remaining energy upkeep
            energy_income = float(nation.get_income("Energy"))
            oil_income = float(nation.get_income("Oil"))
            if energy_income < 0 and oil_income > 0:
                nation = pay_energy(nation, "Oil")
            
            # attempt to spend coal reserves to pay remaining energy upkeep
            energy_income = float(nation.get_income("Energy"))
            coal_reserves = float(nation.get_stockpile("Coal"))
            if energy_income < 0 and coal_reserves > 0:
                nation = pay_energy(nation, "Coal", income=False)
            
            # attempt to spend oil reserves to pay remaining energy upkeep
            energy_income = float(nation.get_income("Energy"))
            oil_reserves = float(nation.get_stockpile("Oil"))
            if energy_income < 0 and oil_reserves > 0:
                nation = pay_energy(nation, "Oil", income=False)

    def refine_income_strings() -> None:
    
        # create strings for net incomes
        final_income_strings = {}
        for nation in Nations:
            final_income_strings[nation.name] = {}
            for resource_name in nation._resources:
                str_list = []
                resource_total = float(nation.get_income(resource_name))
                str_list.append(f"{resource_total:+.2f} {resource_name}")
                final_income_strings[nation.name][resource_name] = str_list

        # add counts
        for nation in Nations:
            for resource_name in nation._resources:
                for income_string, count in text_dict[nation.name][resource_name].items():
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

    def pay_energy(nation: Nation, resouce_name: str, income=True):
        
        energy_income = float(nation.get_income("Energy"))
        
        if income:
            source = "income"
            resource_amount = float(nation.get_income("Oil"))
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
            
        income_str = f"&Tab;+{upkeep_payment:.2f} from {resouce_name.lower()} {source}."
        text_dict[nation.name]["Energy"][income_str] += 1
        
        income_str = f"&Tab;-{upkeep_payment:.2f} from energy upkeep costs."
        text_dict[nation.name][resouce_name][income_str] += 1

        return nation

    yield_dict = {}
    upkeep_dict = {}
    text_dict = {}

    for nation in Nations:

        yield_dict[nation.name] = core.create_player_yield_dict(nation)
        upkeep_dict[nation.name] = core.create_player_upkeep_dict(nation)
        text_dict[nation.name] = {}
        
        for resource_name in nation._resources:
            text_dict[nation.name][resource_name] = defaultdict(int)
            if resource_name == "Military Capacity":
                nation.update_used_mc(0.00, overwrite=True)
                nation.update_max_mc(0.00, overwrite=True)
            else:
                nation.update_gross_income(resource_name, 0.00, overwrite=True)

        # reset the statistics that are calculated by this function
        nation.stats.regions_owned = 0
        nation.stats.regions_occupied = 0
        nation.stats.regions_on_map_edge = 0
    
    calculate_gross_income()
    calculate_net_income()
    refine_income_strings()

def gain_income() -> None:

    for nation in Nations:

        for resource_name in nation._resources:
            if resource_name in ["Energy", "Military Capacity"]:
                continue
            amount = float(nation.get_income(resource_name))
            nation.update_stockpile(resource_name, amount)

def gain_market_income(market_results: dict) -> None:
    for nation_name, market_info in market_results.items():
        nation = Nations.get(nation_name)
        for resource_name, amount in market_info.items():
            if resource_name == "Thieves":
                continue
            nation.update_stockpile(resource_name, amount)

def countdown() -> None:
    """
    Resolves improvements/units that have countdowns associated with them.
    """

    from app.region import Region, Regions
    
    # resolve nuked regions
    for region in Regions:
        if region.data.fallout != 0:
            region.data.fallout -= 1

def resolve_resource_shortages() -> None:
    """
    Resolves resource shortages by pruning units and improvements that cost upkeep.
    """

    for nation in Nations:

        if nation.name == "Foreign Invasion":
            continue

        upkeep_dict = core.create_player_upkeep_dict(nation)

        _resolve_shortage("Oil", upkeep_dict, nation)
        _resolve_shortage("Coal", upkeep_dict, nation)
        _resolve_shortage("Energy", upkeep_dict, nation)
        _resolve_shortage("Uranium", upkeep_dict, nation)
        _resolve_shortage("Food", upkeep_dict, nation)
        _resolve_shortage("Dollars", upkeep_dict, nation)

def _resolve_shortage(resource_name: str, upkeep_dict: dict, nation: Nation) -> None:
    """
    Helper function for resolve_resource_shortages().
    """

    # get pool of resource consumers
    consumers_list = []
    for target_name, resource_upkeep_dict in upkeep_dict.items():
        if resource_name in resource_upkeep_dict and resource_upkeep_dict[resource_name]["Upkeep"] > 0 and resource_upkeep_dict[resource_name]["Upkeep Multiplier"] > 0:
            consumers_list.append(target_name)
    
    # update stockpile variable
    if resource_name == "Energy":
        resource_stockpile = float(nation.get_income(resource_name))
    else:
        resource_stockpile = float(nation.get_stockpile(resource_name))

    # prune until resource shortage eliminated or no consumers left
    while resource_stockpile < 0 and consumers_list != []:
        
        # select random consumer and identify if it is an improvement or unit
        consumer_name = random.choice(consumers_list)
        if consumer_name in nation.unit_counts:
            consumer_type = "unit"
        else:
            consumer_type = "improvement"
        
        # remove consumer
        if consumer_type == "improvement":
            region_id = core.search_and_destroy(nation.id, consumer_name)
            nation.improvement_counts[consumer_name] -= 1
        else:
            region_id, victim = core.search_and_destroy_unit(nation.id, consumer_name)
            nation.unit_counts[consumer_name] -= 1
        Notifications.add(f'{nation.name} lost a {consumer_name} in {region_id} due to {resource_name.lower()} shortages.', 7)
        
        # update stockpile
        consumer_upkeep = upkeep_dict[consumer_name][resource_name]["Upkeep"] * upkeep_dict[consumer_name][resource_name]["Upkeep Multiplier"]
        resource_stockpile += consumer_upkeep
        if resource_name == "Energy":
            nation.update_income(resource_name, consumer_upkeep)
        else:
            nation.update_stockpile(resource_name, consumer_upkeep)

        # update stockpile variable
        if resource_name == "Energy":
            resource_stockpile = float(nation.get_income(resource_name))
        else:
            resource_stockpile = float(nation.get_stockpile(resource_name))
        
        # remove consumer from selection pool if no more of it remains
        if consumer_type == "improvement":
            count_dict = nation.improvement_counts
        else:
            count_dict = nation.unit_counts
        if count_dict[consumer_name] == 0:
            consumers_list.remove(consumer_name)
            del upkeep_dict[consumer_name]

def resolve_military_capacity_shortages(game_id: str) -> None:
    """
    Resolves military capacity shortages for each player by removing units randomly.
    """

    for nation in Nations:
        
        while float(nation.get_used_mc()) > float(nation.get_max_mc()):
            
            region_id, victim = core.search_and_destroy_unit(nation.id, 'ANY')
            nation.update_used_mc(-1)
            nation.unit_counts[victim] -= 1

            Notifications.add(f"{nation.name} lost {victim} {region_id} due to insufficient military capacity.", 6)

def bonus_phase_heals() -> None:
    """
    Heals all units and defensive improvements by 2 health.
    """
    
    from app.region import Region, Regions
    from app.war import Wars
    
    for region in Regions:
        
        if region.data.owner_id not in ["0", "99"]:

            nation_improvement = Nations.get(region.data.owner_id)

            # heal improvement
            if region.data.owner_id != "0" and region.improvement.name != None and region.improvement.health != 99:
                region.improvement.heal(2)
                if nation_improvement.id != "0" and "Peacetime Recovery" in nation_improvement.completed_research and Wars.is_at_peace(nation_improvement.id):
                    region.improvement.heal(100)
        
        if region.unit.name is not None and region.unit.owner_id not in ["0", "99"]:
            
            nation_unit = Nations.get(region.unit.owner_id)
            heal_allowed = False

            # check if unit is allowed to heal
            if region.unit.name == "Special Forces":
                heal_allowed = True
            elif "Scorched Earth" in nation_unit.completed_research:
                heal_allowed = True
            elif region.data.owner_id == region.unit.owner_id:
                heal_allowed = True
            else:
                for adjacent_region_id in region.graph.adjacent_regions:
                    adjacent_region = Region(adjacent_region_id)
                    if adjacent_region.unit.owner_id == region.unit.owner_id:
                        heal_allowed = True

            # heal unit
            if heal_allowed:
                region.unit.heal(2)
                if nation_unit.id != "0" and "Peacetime Recovery" in nation_unit.completed_research and Wars.is_at_peace(nation_unit.id):
                    region.unit.heal(100)

def prompt_for_missing_war_justifications() -> None:
    """
    Prompts in terminal when a war justification has not been entered for an ongoing war.
    """
    from app.war import Wars
    for war in Wars:
        if war.outcome == "TBD":
            war.add_missing_justifications()

def total_occupation_forced_surrender() -> None:
    """
    Forces a player to surrender if they are totally occupied.

    Params:
        game_id (str): Game ID string.
    """
    
    # get game data
    from app.region import Regions
    from app.war import Wars

    # check all regions for occupation
    non_occupied_found_list = [False] * len(Nations)
    for region in Regions:
        if region.data.owner_id != "0" and region.data.owner_id != "99" and region.data.occupier_id == "0":
            non_occupied_found_list[int(region.data.owner_id) - 1] = True
    
    # if no unoccupied region found for a player force surrender if main combatant
    for index, region_found in enumerate(non_occupied_found_list):
        looser_id = str(index + 1)
        looser_name = Nations.get(looser_id).name
        
        if not region_found:
            
            # look for wars to surrender to
            for war in Wars:

                if war.outcome == "TBD" and looser_name in war.combatants and "Main" in war.get_role(str(looser_id)):

                    # never force end the war caused by foreign invasion
                    if war.name == "Foreign Invasion":
                        continue
                    
                    main_attacker_id, main_defender_id = war.get_main_combatant_ids()
                    
                    if looser_id == main_attacker_id:
                        outcome = "Defender Victory"
                    elif looser_id == main_defender_id:
                        outcome = "Attacker Victory"
                    war.end_conflict(outcome)

                    Notifications.add(f"{war.name} has ended due to {looser_name} total occupation.", 5)

def war_score_forced_surrender() -> None:
    """
    Forces a side to surrender if critical war score difference reached.

    Params:
        game_id (str): Game ID string.
    """

    from app.war import Wars

    for war in Wars:
        if war.outcome == "TBD":

            if war.name == "Foreign Invasion":
                continue
        
            attacker_threshold, defender_threshold = war.calculate_score_threshold()
            attacker_id, defender_id = war.get_main_combatant_ids()
            attacker_nation = Nations.get(attacker_id)
            defender_nation = Nations.get(defender_id)
            
            if attacker_threshold is not None and war.attackers.total >= attacker_threshold:
                war.end_conflict("Attacker Victory")
                Notifications.add(f"{defender_nation.name} surrendered to {attacker_nation.name}.", 5)
                Notifications.add(f"{war.name} has ended due to war score.", 5)

            elif defender_threshold is not None and war.defenders.total >= defender_threshold:
                war.end_conflict("Defender Victory")
                Notifications.add(f"{attacker_nation.name} surrendered to {defender_nation.name}.", 5)
                Notifications.add(f"{war.name} has ended due to war score.", 5)

def prune_alliances() -> None:
    """
    Ends all alliances that have less than 2 members.

    Params:
        game_id (str): Game ID string.
    """

    from app.alliance import Alliances

    for alliance in Alliances:
        if alliance.is_active and len(alliance.current_members) < 2:
            alliance.end()
            Notifications.add(f"{alliance.name} has dissolved.", 8)
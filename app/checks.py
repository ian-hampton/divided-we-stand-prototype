import copy
import csv
import json
import random
import datetime

from app import core
from app.notifications import Notifications
from app.nationdata import NationTable
from app.nationdata import Nation
from app.alliance import AllianceTable
from app.war import WarTable

def update_income(game_id: str) -> None:
    """
    Updates the incomes of all players and saves results to playerdata.

    Params:
        game_id (str): Game ID string.

    Returns:
        None
    """
    
    # get game data
    from app.region_new import Region, Regions
    nation_table = NationTable(game_id)
    alliance_table = AllianceTable(game_id)
    with open("active_games.json", 'r') as json_file:
        active_games_dict = json.load(json_file)

    # reset gross income and create dict for tracking income strings
    text_dict = {}
    for nation in nation_table:
        nation.regions_owned = 0
        nation.regions_occupied = 0
        text_dict[nation.name] = {}
        for resource_name in nation._resources:
            text_dict[nation.name][resource_name] = {}
            if resource_name == "Military Capacity":
                nation.update_used_mc(0.00, overwrite=True)
                nation.update_max_mc(0.00, overwrite=True)
            else:
                nation.update_gross_income(resource_name, 0.00, overwrite=True)
        nation_table.save(nation)

    # create dicts for tracking improvement yields and upkeep costs
    yield_dict = {}
    upkeep_dict = {}
    for nation in nation_table:
        yield_dict[nation.name] = core.create_player_yield_dict(game_id, nation)
        upkeep_dict[nation.name] = core.create_player_upkeep_dict(game_id, nation)


    ### calculate gross income ###

    # add income from regions
    for region in Regions:
        # skip if region is unowned
        if region.data.owner_id in ["0", "99"]:
            continue
        # update statistics
        nation = nation_table.get(region.data.owner_id)
        nation.regions_owned += 1
        if region.data.occupier_id != "0":
            nation.regions_occupied += 1
        nation_table.save(nation)
        # skip if region is empty
        if region.improvement.name is None and region.unit.name is None:
            continue
        # add improvement yields
        if region.improvement.name is not None and region.improvement.health != 0 and region.data.occupier_id == "0":
            if region.improvement.name[-1] != 'y':
                plural_improvement_name = f"{region.improvement.name}s"
            else:
                plural_improvement_name = f"{region.improvement.name[:-1]}ies"
            nation = nation_table.get(region.data.owner_id)
            improvement_income_dict = yield_dict[nation.name][region.improvement.name]
            improvement_yield_dict = region.calculate_yield(nation, improvement_income_dict, active_games_dict)
            for resource_name, amount_gained in improvement_yield_dict.items():
                if amount_gained != 0:
                    nation.update_gross_income(resource_name, amount_gained)
                    income_str = f'&Tab;+{amount_gained:.2f} from {plural_improvement_name}'
                    _update_text_dict(text_dict, nation.name, resource_name, income_str)
                    nation_table.save(nation)
        # add unit military capacity cost
        if region.unit.name is not None:
            nation = nation_table.get(region.unit.owner_id)
            nation.update_used_mc(1.00)
            if nation.gov == "Military Junta":
                nation.update_gross_income("Political Power", 0.1)
                income_str = "&Tab;+0.10 from Military Junta bonus."
                _update_text_dict(text_dict, nation.name, "Political Power", income_str)
                nation_table.save(nation)

    # political power income from alliances
    for nation in nation_table:
        alliance_income = 0
        alliance_count, alliance_capacity = core.get_alliance_count(game_id, nation)
        if "Power Broker" in nation.completed_research:
            alliance_income += 0.25
        for tag_data in nation.tags.values():
            alliance_income += tag_data.get("Alliance Political Power Bonus", 0)
        if alliance_income * alliance_count == 0:
            continue
        nation.update_gross_income("Political Power", alliance_income * alliance_count)
        for i in range(alliance_count):
            income_str = f'&Tab;+{alliance_income:.2f} from alliances'
            _update_text_dict(text_dict, nation.name, "Political Power", income_str)
        nation_table.save(nation)

    # political power from events
    for nation in nation_table:
        if "Observer Status" in nation.tags:
            nation.update_gross_income("Political Power", 0.5)
            income_str = f"&Tab;+{0.5:.2f} from Observer Status"
            _update_text_dict(text_dict, nation.name, "Political Power", income_str)
        nation_table.save(nation)

    # alliance yields
    for alliance in alliance_table:
        amount, resource_name = alliance.get_yield()
        if amount == 0 or resource_name is None:
            continue
        for ally_name in alliance.current_members:
            nation = nation_table.get(ally_name)
            if "Alliance Centralization" in nation.completed_research:
                amount = round(amount * 1.5, 2)
            if resource_name == "Military Capacity":
                nation.update_max_mc(amount)
            else:
                nation.update_gross_income(resource_name, amount)
            income_str = f'&Tab;+{amount:.2f} from {alliance.name}.'
            _update_text_dict(text_dict, nation.name, resource_name, income_str)
            nation_table.save(nation)
        
    # apply income rate to gross income
    for nation in nation_table:
        for resource_name in nation._resources:
            total = float(nation.get_gross_income(resource_name))
            rate = float(nation.get_rate(resource_name)) / 100
            final_total = total * rate
            final_total = round(final_total, 2)
            rate_diff = round(final_total - total, 2)
            if rate_diff > 0:
                income_str = f'&Tab;+{rate_diff:.2f} from income rate.'
                _update_text_dict(text_dict, nation.name, resource_name, income_str)
            elif rate_diff < 0:
                income_str = f'&Tab;{rate_diff:.2f} from income rate.'
                _update_text_dict(text_dict, nation.name, resource_name, income_str)
            nation.update_gross_income(resource_name, final_total, overwrite=True)
        nation_table.save(nation)
    

    ### calculate net income ###

    # reset income
    for nation in nation_table:
        for resource_name in nation._resources:
            gross_income = float(nation.get_gross_income(resource_name))
            nation.update_income(resource_name, gross_income, overwrite=True)
        nation_table.save(nation)

    for nation in nation_table:
        
        # account for puppet state dues
        if 'Puppet State' in nation.status:
            for temp in nation_table:
                if temp in nation.status:
                    overlord = temp
                    break
            for resource_name in nation._resources:
                if resource_name == "Military Capacity":
                    continue
                tax_amount = nation.get_gross_income(resource_name) * 0.2
                tax_amount = round(tax_amount, 2)
                # take tax from puppet state
                nation.update_income(resource_name, -1 * tax_amount)
                income_str = f"&Tab;-{tax_amount:.2f} from puppet state tribute."
                _update_text_dict(text_dict, nation.name, resource_name, income_str)
                # give tax to overlord
                overlord.update_income(resource_name, tax_amount)
                income_str = f"&Tab;{tax_amount:.2f} from puppet state tribute."
                _update_text_dict(text_dict, overlord.name, resource_name, income_str)
                nation_table.save(overlord)

        # calculate player upkeep costs
        # tba - check if there is even a need to calculate unit and improvement upkeep seperately anymore
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
                _update_text_dict(text_dict, nation.name, resource_name, income_str)

        # pay energy upkeep
        energy_upkeep = player_upkeep_costs_dict["Energy"]["From Units"] + player_upkeep_costs_dict["Energy"]["From Improvements"]
        nation.update_income("Energy", -1 * energy_upkeep)
        if energy_upkeep > 0:
            income_str = f'&Tab;-{energy_upkeep:.2f} from energy upkeep costs.'
            _update_text_dict(text_dict, nation.name, resource_name, income_str)
        
        # pay energy upkeep - spend coal income if needed
        energy_income = float(nation.get_income("Energy"))
        coal_income = float(nation.get_income("Coal"))
        if energy_income < 0 and coal_income > 0:
            nation = _pay_energy(text_dict, nation, energy_income, "Coal", coal_income)
        
        # pay energy upkeep - spend oil income if needed
        energy_income = float(nation.get_income("Energy"))
        oil_income = float(nation.get_income("Oil"))
        if energy_income < 0 and oil_income > 0:
            nation = _pay_energy(text_dict, nation, energy_income, "Oil", oil_income)
        
        # pay energy upkeep - spend coal reserves if needed
        energy_income = float(nation.get_income("Energy"))
        coal_reserves = float(nation.get_stockpile("Coal"))
        if energy_income < 0 and coal_reserves > 0:
            nation = _pay_energy(text_dict, nation, energy_income, "Coal", coal_reserves, income=False)
        
        # pay energy upkeep - spend oil reserves if needed
        energy_income = float(nation.get_income("Energy"))
        oil_reserves = float(nation.get_stockpile("Oil"))
        if energy_income < 0 and coal_reserves > 0:
            nation = _pay_energy(text_dict, nation, energy_income, "Oil", oil_reserves, income=False)

        nation_table.save(nation)


    ### refine income strings ###

    # create strings for net incomes
    final_income_strings = {}
    for nation in nation_table:
        final_income_strings[nation.name] = {}
        for resource_name in nation._resources:
            str_list = []
            resource_total = float(nation.get_income(resource_name))
            if resource_total >= 0:
                str_list.append(f'+{resource_total:.2f} {resource_name}')
            elif resource_total < 0:
                str_list.append(f'{resource_total:.2f} {resource_name}')
            final_income_strings[nation.name][resource_name] = str_list

    # add counts
    for nation in nation_table:
        for resource_name in nation._resources:
            for income_string, count in text_dict[nation.name][resource_name].items():
                if count > 1:
                    income_string = f'{income_string} [{count}x]'
                final_income_strings[nation.name][resource_name].append(income_string)

    # save income strings
    for nation in nation_table:
        resource_string_lists = final_income_strings[nation.name]
        temp = []
        for resource_name, string_list in resource_string_lists.items():
            if len(string_list) > 1 or resource_name in ["Dollars", "Political Power", "Research", "Military Capacity", "Energy"]:
                temp += string_list
        nation.income_details = temp
        nation_table.save(nation)

def _update_text_dict(text_dict: dict, nation_name: str, resource_name: str, income_str: str) -> None:
    """
    Adds income string to text dictionary. Helper function for update_income().
    """
    if income_str not in text_dict[nation_name][resource_name]:
        text_dict[nation_name][resource_name][income_str] = 1
    else:
        text_dict[nation_name][resource_name][income_str] += 1

def _pay_energy(text_dict: dict, nation: Nation, energy_income: float, resouce_name: str, resource_amount: float, income=True):
    """
    Handles paying off energy upkeep. Helper function for update_income().
    """

    sum = float(energy_income) + float(resource_amount)
    if income:
        source = "income"
    else:
        source = "reserves"

    if sum > 0:
        upkeep_payment = resource_amount - sum
        nation.update_income("Energy", upkeep_payment)
        nation.update_income(resouce_name, -1 * upkeep_payment)
        income_str = f'&Tab;+{upkeep_payment:.2f} from {resouce_name.lower()} {source}.'
        _update_text_dict(text_dict, nation.name, "Energy", income_str)
        income_str = f'&Tab;-{upkeep_payment:.2f} from energy upkeep costs.'
        _update_text_dict(text_dict, nation.name, resouce_name, income_str)
    else:
        nation.update_income("Energy", resource_amount)
        nation.update_income(resouce_name, 0.00, overwrite=True)
        income_str = f'&Tab;+{resource_amount:.2f} from {resouce_name.lower()} {source}.'
        _update_text_dict(text_dict, nation.name, "Energy", income_str)
        income_str = f'&Tab;-{resource_amount:.2f} from energy upkeep costs.'
        _update_text_dict(text_dict, nation.name, resouce_name, income_str)

    return nation

def gain_income(game_id: str) -> None:

    nation_table = NationTable(game_id)

    for nation in nation_table:

        for resource_name in nation._resources:
            if resource_name in ["Energy", "Military Capacity"]:
                continue
            amount = float(nation.get_income(resource_name))
            nation.update_stockpile(resource_name, amount)

        nation_table.save(nation)

def countdown(game_id: str) -> None:
    """
    Resolves improvements/units that have countdowns associated with them.
    """

    from app.region_new import Region, Regions
    
    # resolve nuked regions
    for region in Regions:
        if region.data.fallout != 0:
            region.data.fallout -= 1

def resolve_resource_shortages(game_id: str) -> None:
    """
    Resolves resource shortages by pruning units and improvements that cost upkeep.
    """

    # get game info
    nation_table = NationTable(game_id)

    for nation in nation_table:

        if nation.name == "Foreign Invasion":
            continue

        upkeep_dict = core.create_player_upkeep_dict(game_id, nation)

        # handle shortages
        _resolve_shortage("Oil", upkeep_dict, nation, game_id)
        _resolve_shortage("Coal", upkeep_dict, nation, game_id)
        _resolve_shortage("Energy", upkeep_dict, nation, game_id)
        _resolve_shortage("Uranium", upkeep_dict, nation, game_id)
        _resolve_shortage("Food", upkeep_dict, nation, game_id)
        _resolve_shortage("Dollars", upkeep_dict, nation, game_id)
    
        # update nation data
        nation_table.save(nation)

def _resolve_shortage(resource_name: str, upkeep_dict: dict, nation: Nation, game_id: str) -> None:
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
            region_id = core.search_and_destroy(game_id, nation.id, consumer_name)
            nation.improvement_counts[consumer_name] -= 1
        else:
            region_id, victim = core.search_and_destroy_unit(game_id, nation.id, consumer_name)
            nation.unit_counts[consumer_name] -= 1
        Notifications.add(f'{nation.name} lost a {consumer_name} in {region_id} due to {resource_name.lower()} shortages.', 6)
        
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

    nation_table = NationTable(game_id)

    for nation in nation_table:
        
        while float(nation.get_used_mc()) > float(nation.get_max_mc()):
            
            # disband a random unit
            region_id, victim = core.search_and_destroy_unit(game_id, nation.id, 'ANY')
            nation.update_used_mc(-1)
            nation.unit_counts[victim] -= 1
            Notifications.add(f'{nation.name} lost {victim} {region_id} due to insufficient military capacity.', 5)

        # update nation data
        nation_table.save(nation)

def bonus_phase_heals(game_id: str) -> None:
    """
    Heals all units and defensive improvements by 2 health.
    """
    
    from app.region_new import Region, Regions
    nation_table = NationTable(game_id)
    war_table = WarTable(game_id)
    
    for region in Regions:
        
        if region.data.owner_id not in ["0", "99"]:

            nation_improvement = nation_table.get(region.data.owner_id)

            # heal improvement
            if region.data.owner_id != "0" and region.improvement.name != None and region.improvement.health != 99:
                region.improvement.heal(2)
                if nation_improvement.id != "0" and "Peacetime Recovery" in nation_improvement.completed_research and war_table.is_at_peace(nation_improvement.id):
                    region.improvement.heal(100)
        
        if region.unit.name is not None and region.unit.owner_id not in ["0", "99"]:
            
            nation_unit = nation_table.get(region.unit.owner_id)
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
                if nation_unit.id != "0" and "Peacetime Recovery" in nation_unit.completed_research and war_table.is_at_peace(nation_unit.id):
                    region.unit.heal(100)

def prompt_for_missing_war_justifications(game_id: str) -> None:
    """
    Prompts in terminal when a war justification has not been entered for an ongoing war.

    :param game_id: The full game_id of the active game.
    """

    war_table = WarTable(game_id)

    for war in war_table:
        if war.outcome == "TBD":
            war.add_missing_justifications()
            war_table.save(war)

def total_occupation_forced_surrender(game_id: str) -> None:
    """
    Forces a player to surrender if they are totally occupied.

    Params:
        game_id (str): Game ID string.
    """
    
    # get game data
    from app.region_new import Region, Regions
    nation_table = NationTable(game_id)
    war_table = WarTable(game_id)

    # check all regions for occupation
    non_occupied_found_list = [False] * len(nation_table)
    for region in Regions:
        if region.data.owner_id != "0" and region.data.owner_id != "99" and region.data.occupier_id == "0":
            non_occupied_found_list[int(region.data.owner_id) - 1] = True
    
    # if no unoccupied region found for a player force surrender if main combatant
    for index, region_found in enumerate(non_occupied_found_list):
        looser_id = index + 1
        looser_name = nation_table.get(looser_id).name
        
        if not region_found:
            
            # look for wars to surrender to
            for war in war_table:

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

                    Notifications.add(f"{war.name} has ended due to {looser_name} total occupation.", 4)
                    war_table.save(war)

def war_score_forced_surrender(game_id: str) -> None:
    """
    Forces a side to surrender if critical war score difference reached.

    Params:
        game_id (str): Game ID string.
    """

    # get game data
    nation_table = NationTable(game_id)
    war_table = WarTable(game_id)

    for war in war_table:
        if war.outcome == "TBD":

            # never force end the war caused by foreign invasion
            if war.name == "Foreign Invasion":
                continue
        
            attacker_threshold, defender_threshold = war.calculate_score_threshold()
            attacker_id, defender_id = war.get_main_combatant_ids()
            attacker_nation = nation_table.get(attacker_id)
            defender_nation = nation_table.get(defender_id)
            
            if attacker_threshold is not None and war.attacker_total >= attacker_threshold:
                war.end_conflict("Attacker Victory")
                Notifications.add(f"{defender_nation.name} surrendered to {attacker_nation.name}.", 4)
                Notifications.add(f"{war.name} has ended due to war score.", 4)
                war_table.save(war)

            elif defender_threshold is not None and war.defender_total >= defender_threshold:
                war.end_conflict("Defender Victory")
                Notifications.add(f"{attacker_nation.name} surrendered to {defender_nation.name}.", 4)
                Notifications.add(f"{war.name} has ended due to war score.", 4)
                war_table.save(war)

def prune_alliances(game_id: str) -> None:
    """
    Ends all alliances that have less than 2 members.

    Params:
        game_id (str): Game ID string.
    """

    alliance_table = AllianceTable(game_id)

    for alliance in alliance_table:
        if alliance.is_active and len(alliance.current_members) < 2:
            alliance.end()
            alliance_table.save(alliance)
            Notifications.add(f"{alliance.name} has dissolved.", 7)

def gain_market_income(game_id: str, market_results: str) -> None:
    """
    Adds resources gained from market actions to a player's stockpile.
    """
    
    # get game data
    nation_table = NationTable(game_id)

    # award income
    for nation_name, market_info in market_results.items():
        nation = nation_table.get(nation_name)
        for resource_name, amount in market_info.items():
            if resource_name == "Thieves":
                continue
            nation.update_stockpile(resource_name, amount)
        nation_table.save(nation)
import copy
import random
from collections import defaultdict

from app import core
from app.scenario.scenario import ScenarioInterface as SD
from app.alliance.alliances import Alliances
from app.nation.nation import Nation
from app.nation.nations import Nations
from app.notifications import Notifications
from app.region.regions import Regions
from app.war.wars import Wars

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
            nation.unit_counts[victim] -= 1
            nation.update_military_capacity()

            Notifications.add(f"{nation.name} lost {victim} {region_id} due to insufficient military capacity.", 6)

def bonus_phase_heals() -> None:
    """
    Heals all units and defensive improvements by 2 health.
    """
    
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
                for adjacent_region in region.graph.iter_adjacent_regions():
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
    
    for war in Wars:
        if war.outcome == "TBD":
            war.add_missing_justifications()

def total_occupation_forced_surrender() -> None:
    """
    Forces a player to surrender if they are totally occupied.

    Params:
        game_id (str): Game ID string.
    """

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

    for alliance in Alliances:
        if alliance.is_active and len(alliance.current_members) < 2:
            alliance.end()
            Notifications.add(f"{alliance.name} has dissolved.", 8)
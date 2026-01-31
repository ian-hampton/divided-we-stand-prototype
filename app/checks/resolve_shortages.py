import random

from app.nation.nation import Nation
from app.nation.nations import Nations
from app.notifications import Notifications
from . import economic_helpers
from . import destroy

RESOURCES = {"Oil", "Coal", "Energy", "Uranium", "Food", "Dollars"}

def _resolve_shortage(resource_name: str, upkeep_dict: dict, nation: Nation) -> None:
    """
    Helper function for resolving a resource shortage.
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
            region_id = destroy.search_and_destroy_improvement(nation.id, consumer_name)
            nation.improvement_counts[consumer_name] -= 1
        else:
            region_id, victim = destroy.search_and_destroy_unit(nation.id, consumer_name)
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

def resolve_resource_shortages() -> None:
    """
    Resolves resource shortages by pruning units and improvements that cost upkeep.
    """

    for nation in Nations:

        if nation.name == "Foreign Invasion":
            continue

        upkeep_dict = economic_helpers.create_player_upkeep_dict(nation)

        for resource in RESOURCES:
            _resolve_shortage(resource, upkeep_dict, nation)
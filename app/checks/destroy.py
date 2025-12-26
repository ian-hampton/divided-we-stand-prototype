import random
import copy

def search_and_destroy_improvement(player_id: str, target_improvement: str) -> str:
    """
    Searches for a specific improvement and removes it.
    """
    from app.region.regions import Regions
    
    # find all regions belonging to a player with target improvement
    candidate_region_ids = []
    for region in Regions:
        if region.improvement.name == target_improvement and region.data.owner_id == int(player_id):
            candidate_region_ids.append(region.id)

    # randomly select one of the candidate regions
    random.shuffle(candidate_region_ids)
    chosen_region_id = candidate_region_ids.pop()
    target_region = Regions.load(chosen_region_id)
    target_region.improvement.clear()
    
    return chosen_region_id

def search_and_destroy_unit(player_id: str, desired_unit_name: str) -> tuple[str, str]:
    """
    Randomly destroys one unit of a given type belonging to a specific player.
    """
    from app.region.regions import Regions

    # get list of regions with desired_unit_name owned by player_id
    candidate_region_ids = []
    for region in Regions:
        if (desired_unit_name == 'ANY' or region.unit.name == desired_unit_name) and region.unit.owner_id == player_id:
            candidate_region_ids.append(region.id)

    # randomly select one of the candidate regions
    # there should always be at least one candidate region because we have already checked that the target unit exists
    random.shuffle(candidate_region_ids)
    chosen_region_id = candidate_region_ids.pop()
    target_region = Regions.load(chosen_region_id)
    victim = copy.deepcopy(target_region.unit.name)
    target_region.unit.clear()

    return chosen_region_id, victim
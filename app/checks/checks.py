from app.alliance.alliances import Alliances
from app.nation.nations import Nations
from app.notifications import Notifications
from app.region.regions import Regions
from app.war.wars import Wars
from . import destroy

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

def resolve_military_capacity_shortages(game_id: str) -> None:
    """
    Resolves military capacity shortages for each player by removing units randomly.
    """

    for nation in Nations:
        
        while float(nation.get_used_mc()) > float(nation.get_max_mc()):
            
            region_id, victim = destroy.search_and_destroy_unit(nation.id, 'ANY')
            nation.unit_counts[victim] -= 1
            nation.update_military_capacity()

            Notifications.add(f"{nation.name} lost {victim} {region_id} due to insufficient military capacity.", 6)

def prompt_for_missing_war_justifications() -> None:
    """
    Prompts in terminal when a war justification has not been entered for an ongoing war.
    """
    
    for war in Wars:
        if war.outcome == "TBD":
            war.add_missing_justifications()

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
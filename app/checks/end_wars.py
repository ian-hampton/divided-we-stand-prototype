from app.nation.nations import Nations
from app.notifications import Notifications
from app.region.regions import Regions
from app.war.wars import Wars

def total_occupation_forced_surrender() -> None:
    """
    Forces a player to surrender if they are totally occupied.

    Params:
        game_id (str): Game ID string.
    """

    # check all regions for occupation
    non_occupied_found = {}
    for nation in Nations:
        non_occupied_found[nation.id] = False
    for region in Regions:
        if region.data.occupier_id == "0" and region.data.owner_id not in ["0", "99"]:
            non_occupied_found[nation.id] = True
    
    # if no unoccupied region found for a player force surrender if main combatant
    for nation_id, region_found in non_occupied_found.items():

        if region_found:
            continue
            
        # look for active wars to surrender to
        for war in Wars:

            if war.outcome != "TBD":
                continue

            if nation_id not in war.combatants or "Main" not in war.get_role(str(nation_id)):
                continue

            # never force end the war caused by foreign invasion
            if war.name == "Foreign Invasion":
                continue

            main_attacker_id, main_defender_id = war.get_main_combatant_ids()
            outcome = "Attacker Victory"
            if nation_id == main_attacker_id:
                outcome = "Defender Victory"

            war.end_conflict(outcome)

            looser_name = Nations.get(nation_id).name
            Notifications.add(f"{war.name} has ended due to {looser_name} total occupation.", 5)

def war_score_forced_surrender() -> None:
    """
    Forces a side to surrender if critical war score difference reached.

    Params:
        game_id (str): Game ID string.
    """

    for war in Wars:

        if war.outcome != "TBD":
            continue

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
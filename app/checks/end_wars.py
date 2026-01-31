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
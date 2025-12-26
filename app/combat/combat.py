import random
from typing import Union, Tuple

from app.region.region import Region
from app.nation.nations import Nations
from app.war.wars import Wars

def unit_vs_unit(attacker_region: Region, defender_region: Region) -> None:

    unit_vs_unit_standard(attacker_region, defender_region)

def unit_vs_unit_standard(attacker_region: Region, defender_region: Region) -> None:

    # get nation data
    attacker = Nations.get(attacker_region.unit.owner_id)
    defender = Nations.get(defender_region.unit.owner_id)

    # get war data
    war_name = Wars.get_war_name(attacker.id, defender.id)
    war = Wars.get(war_name)
    attacker_cd = war.get_combatant(attacker.id)
    defender_cd = war.get_combatant(defender.id)
    war.log.append(f"{attacker.name} {attacker_region.unit.name} {attacker_region.id} vs {defender.name} {defender_region.unit.name} {defender_region.id}")

    # calculate attacker roll modifier
    attacker_roll_modifier = 0
    if "Attacker" in attacker_cd.role and "Superior Training" in attacker.completed_research:
        attacker_roll_modifier += 1
    elif "Defender" in attacker_cd.role and "Unyielding" in attacker.completed_research:
        attacker_roll_modifier += 1
    if attacker_region.unit.type == "Tank" and attacker_region.check_for_adjacent_unit({"Mechanized Infantry"}, attacker_region.unit.owner_id):
        attacker_roll_modifier += 1
    elif attacker_region.unit.type == "Infantry" and attacker_region.check_for_adjacent_unit({"Light Tank"}, attacker_region.unit.owner_id):
        attacker_roll_modifier += 1
    if attacker_region.unit.name == "Main Battle Tank" and defender_region.unit.type == "Infantry":
        attacker_roll_modifier += 1
    for tag_data in attacker.tags.values():
        if tag_data.get("Combat Roll Bonus") == defender.id:
            attacker_roll_modifier += 1

    # calculate defender roll modifier
    defender_roll_modifier = 0
    if "Attacker" in defender_cd.role and "Superior Training" in defender.completed_research:
        defender_roll_modifier += 1
    elif "Defender" in defender_cd.role and "Unyielding" in defender.completed_research:
        defender_roll_modifier += 1
    if defender_region.unit.type == "Tank" and defender_region.check_for_adjacent_unit({"Mechanized Infantry"}, defender_region.unit.owner_id):
        defender_roll_modifier += 1
    elif defender_region.unit.type == "Infantry" and defender_region.check_for_adjacent_unit({"Light Tank"}, defender_region.unit.owner_id):
        defender_roll_modifier += 1
    if defender_region.unit.name == "Main Battle Tank" and attacker_region.unit.type == "Infantry":
        defender_roll_modifier += 1
    for tag_data in defender.tags.values():
        if tag_data.get("Combat Roll Bonus") == attacker.id:
            defender_roll_modifier += 1

    # calculate attacker damage modifier
    attacker_damage_modifier = 0
    if attacker_region.check_for_adjacent_unit({"Artillery"}, attacker_region.unit.owner_id):
        war.log.append(f"    Attacking unit has artillery support!")
        attacker_damage_modifier += 1
    if defender_region.improvement.name == "Trench":
        war.log.append(f"    Defending unit is entrenched!")
        attacker_damage_modifier -= 1

    # calculate defender damage modifier
    defender_damage_modifier = 0
    if defender_region.check_for_adjacent_unit({"Artillery"}, defender_region.unit.owner_id):
        war.log.append(f"    Defending unit has artillery support!")
        defender_damage_modifier += 1

    # execute combat
    outcome, battle_str = _conduct_combat(attacker_region, defender_region, attacker.name, attacker_roll_modifier, defender.name, defender_roll_modifier)
    if outcome == 1:
        battle_str += " Attacker victory!"
        if "Attacker" in attacker_cd.role:
            war.attackers.victories += Wars.WARSCORE_FROM_VICTORY
        else:
            war.defenders.victories += Wars.WARSCORE_FROM_VICTORY
        attacker_cd.battles_won += 1
        defender_cd.battles_lost += 1
    elif outcome == 2:
        battle_str += " Defender victory!"
        if "Attacker" in defender_cd.role:
            war.attackers.victories += Wars.WARSCORE_FROM_VICTORY
        else:
            war.defenders.victories += Wars.WARSCORE_FROM_VICTORY
        attacker_cd.battles_lost += 1
        defender_cd.battles_won += 1
    else:
        battle_str += " Draw!"
    war.log.append(battle_str)

    # apply damage
    if outcome == 1:
        defender_region.unit.health -= attacker_region.unit.victory_damage + attacker_damage_modifier
    elif outcome == 2:
        attacker_region.unit.health -= defender_region.unit.victory_damage + defender_damage_modifier
    else:
        defender_region.unit.health -= attacker_region.unit.draw_damage + attacker_damage_modifier
        attacker_region.unit.health -= defender_region.unit.draw_damage + defender_damage_modifier
    
    # remove attacking unit if defeated
    if attacker_region.unit.health <= 0:
        if "Attacker" in defender_cd.role:
            war.attackers.destroyed_units += attacker_region.unit.value
        else:
            war.defenders.destroyed_units += attacker_region.unit.value
        attacker_cd.lost_units += 1
        defender_cd.destroyed_units += 1
        war.log.append(f"    {attacker.name} {attacker_region.unit.name} has been lost!")
        attacker.unit_counts[attacker_region.unit.name] -= 1
        attacker_region.unit.clear()
    
    # remove defending unit if defeated
    if defender_region.unit.health <= 0:
        if "Attacker" in attacker_cd.role:
            war.attackers.destroyed_units += defender_region.unit.value
        else:
            war.defenders.destroyed_units += defender_region.unit.value
        attacker_cd.destroyed_units += 1
        defender_cd.lost_units += 1
        war.log.append(f"    {defender.name} {defender_region.unit.name} has been lost!")
        defender.unit_counts[defender_region.unit.name] -= 1
        defender_region.unit.clear()

def unit_vs_improvement(attacker_region: Region, defender_region: Region) -> None:

    if attacker_region.unit.name == "Special Forces" and not defender_region.unit.is_hostile(attacker_region.unit.owner_id):
        unit_vs_improvement_sf(attacker_region, defender_region)
    else:
        unit_vs_improvement_standard(attacker_region, defender_region)

def unit_vs_improvement_standard(attacker_region: Region, defender_region: Region) -> None:

    # get nation data
    attacker = Nations.get(attacker_region.unit.owner_id)
    defender = Nations.get(defender_region.data.owner_id)

    # get information from wardata
    war_name = Wars.get_war_name(attacker.id, defender.id)
    war = Wars.get(war_name)
    attacker_cd = war.get_combatant(attacker.id)
    defender_cd = war.get_combatant(defender.id)
    war.log.append(f"{attacker.name} {attacker_region.unit.name} {attacker_region.id} vs {defender.name} {defender_region.improvement.name} {defender_region.id}")

    # calculate attacker roll modifier
    attacker_roll_modifier = 0
    if 'Attacker' in attacker_cd.role and 'Superior Training' in attacker.completed_research:
        attacker_roll_modifier += 1
    elif 'Defender' in attacker_cd.role and 'Unyielding' in attacker.completed_research:
        attacker_roll_modifier += 1
    if attacker_region.unit.type == 'Tank' and attacker_region.check_for_adjacent_unit({"Mechanized Infantry"}, attacker_region.unit.owner_id):
        attacker_roll_modifier += 1
    elif attacker_region.unit.type == 'Infantry' and attacker_region.check_for_adjacent_unit({"Light Tank"}, attacker_region.unit.owner_id):
        attacker_roll_modifier += 1
    if attacker_region.unit.name == 'Main Battle Tank':
        attacker_roll_modifier += 1
    for tag_data in attacker.tags.values():
        if tag_data.get("Combat Roll Bonus") == defender.id:
            attacker_roll_modifier += 1

    # calculate defender roll modifier
    defender_roll_modifier = 0
    if 'Defensive Tactics' in defender.completed_research:
        defender_roll_modifier += 1

    # calculate attacker damage modifier
    attacker_damage_modifier = 0
    if attacker_region.check_for_adjacent_unit({"Artillery"}, attacker_region.unit.owner_id):
        war.log.append(f"    Attacking unit has artillery support!")
        attacker_damage_modifier += 1
    
    # calculate defender damage modifier
    defender_damage_modifier = 0

    # execute combat
    outcome, battle_str = _conduct_combat(attacker_region, defender_region, attacker.name, attacker_roll_modifier, defender.name, defender_roll_modifier)
    if outcome == 1:
        battle_str += " Attacker victory!"
        if "Attacker" in attacker_cd.role:
            war.attackers.victories += Wars.WARSCORE_FROM_VICTORY
        else:
            war.defenders.victories += Wars.WARSCORE_FROM_VICTORY
        attacker_cd.battles_won += 1
        defender_cd.battles_lost += 1
    elif outcome == 2:
        battle_str += " Defender victory!"
        if "Attacker" in defender_cd.role:
            war.attackers.victories += Wars.WARSCORE_FROM_VICTORY
        else:
            war.defenders.victories += Wars.WARSCORE_FROM_VICTORY
        attacker_cd.battles_lost += 1
        defender_cd.battles_won += 1
    else:
        battle_str += " Draw!"
    war.log.append(battle_str)

    # apply damage
    if outcome == 1:
        defender_region.improvement.health -= attacker_region.unit.victory_damage + attacker_damage_modifier
    elif outcome == 2:
        attacker_region.unit.health -= defender_region.improvement.victory_damage + defender_damage_modifier
    else:
        defender_region.improvement.health -= attacker_region.unit.draw_damage + attacker_damage_modifier
        attacker_region.unit.health -= defender_region.improvement.draw_damage + defender_damage_modifier
    
    # remove attacking unit if defeated
    if attacker_region.unit.health <= 0:
        if "Attacker" in defender_cd.role:
            war.attackers.destroyed_units += attacker_region.unit.value
        else:
            war.defenders.destroyed_units += attacker_region.unit.value
        attacker_cd.lost_units += 1
        defender_cd.destroyed_units += 1
        war.log.append(f"    {attacker.name} {attacker_region.unit.name} has been lost!")
        attacker.unit_counts[attacker_region.unit.name] -= 1
        attacker_region.unit.clear()
    
    # remove defending improvement if defeated
    if defender_region.improvement.health <= 0:
        attacker_cd.destroyed_improvements += 1
        defender_cd.lost_improvements += 1
        if defender_region.improvement.name != 'Capital':
            if "Attacker" in attacker_cd.role:
                war.attackers.destroyed_improvements += Wars.WARSCORE_FROM_DESTROY_IMPROVEMENT
            else:
                war.defenders.destroyed_improvements += Wars.WARSCORE_FROM_DESTROY_IMPROVEMENT
            war.log.append(f"    {defender.name} {defender_region.improvement.name} has been destroyed!")
            defender.improvement_counts[defender_region.improvement.name] -= 1
            defender_region.improvement.clear()
        else:
            if "Attacker" in attacker_cd.role:
                war.attackers.captures += Wars.WARSCORE_FROM_CAPITAL_CAPTURE
            else:
                war.defenders.captures += Wars.WARSCORE_FROM_CAPITAL_CAPTURE
            war.log.append(f"    {defender.name} {defender_region.improvement.name} has been captured!")
            defender_region.improvement.health = 0

def unit_vs_improvement_sf(attacker_region: Region, defender_region: Region) -> None:
    """
    Resolves special case of special forces vs a lone defensive improvement.

    Params:
        attacking_unit (Unit): object representing attacking unit
        defending_unit (Improvement): object representing defending improvement

    Returns:
        None
    """

    # get nation data
    attacker = Nations.get(attacker_region.unit.owner_id)
    defender = Nations.get(defender_region.data.owner_id)

    # get war data
    war_name = Wars.get_war_name(attacker.id, defender.id)
    war = Wars.get(war_name)
    attacker_cd = war.get_combatant(attacker.id)
    defender_cd = war.get_combatant(defender.id)
    war.log.append(f"{attacker.name} {attacker_region.unit.name} {attacker_region.id} vs {defender.name} {defender_region.improvement.name} {defender_region.id}")

    # determine outcome - special forces always wins
    if "Attacker" in attacker_cd.role:
        war.attackers.victories += Wars.WARSCORE_FROM_VICTORY
    else:
        war.defenders.victories += Wars.WARSCORE_FROM_VICTORY
    attacker_cd.battles_won += 1
    defender_cd.battles_lost += 1
    battle_str = f"    {attacker.name} {attacker_region.unit.name} has defeated {defender.name} {defender_region.improvement.name}."
    war.log.append(battle_str)

    # save defending improvement
    attacker_cd.destroyed_improvements += 1
    defender_cd.lost_improvements += 1
    if defender_region.improvement.name != 'Capital':
        if "Attacker" in attacker_cd.role:
            war.attackers.destroyed_improvements += Wars.WARSCORE_FROM_DESTROY_IMPROVEMENT
        else:
            war.defenders.destroyed_improvements += Wars.WARSCORE_FROM_DESTROY_IMPROVEMENT
        war.log.append(f"    {defender.name} {defender_region.improvement.name} has been destroyed!")
        defender.improvement_counts[defender_region.improvement.name] -= 1
        defender_region.improvement.clear()
    else:
        war.attackers.captures += Wars.WARSCORE_FROM_CAPITAL_CAPTURE
        war.log.append(f"    {defender.name} {defender_region.improvement.name} has been captured!")
        defender_region.improvement.health = 0

def _conduct_combat(attacker_region: Region, defender_region: Region, attacker_nation_name: str, attacker_roll_modifier: int, defender_nation_name: str, defender_roll_modifier: int) -> Tuple[int, str]:

    attacker_roll = random.randint(1, 10) + attacker_roll_modifier
    defender_roll = random.randint(1, 10) + defender_roll_modifier
    attacker_hit = False
    defender_hit = False

    if attacker_roll >= attacker_region.unit.hit_value:
        attacker_hit = True
    if defender_roll >= defender_region.unit.hit_value:
        defender_hit = True

    if attacker_hit and not defender_hit:
        outcome = 1
    elif not attacker_hit and defender_hit:
        outcome = 2
    else:
        outcome = 3
    
    if attacker_roll_modifier > 0 and defender_roll_modifier > 0:
        battle_str = f"    {attacker_nation_name} rolled {attacker_roll} (+{attacker_roll_modifier}). {defender_nation_name} rolled {defender_roll} (+{defender_roll_modifier})."
    elif attacker_roll_modifier > 0:
        battle_str = f"    {attacker_nation_name} rolled {attacker_roll} (+{attacker_roll_modifier}). {defender_nation_name} rolled {defender_roll}."
    elif defender_roll_modifier > 0:
        battle_str = f"    {attacker_nation_name} rolled {attacker_roll}. {defender_nation_name} rolled {defender_roll} (+{defender_roll_modifier})."
    else:
        battle_str = f"    {attacker_nation_name} rolled {attacker_roll}. {defender_nation_name} rolled {defender_roll}."

    return outcome, battle_str
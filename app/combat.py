import ast
import random
from typing import Union, Tuple

from app import core
from app.region import Region
from app.improvement import Improvement
from app.unit import Unit
from app.nationdata import NationTable
from app.war import WarTable

def unit_vs_unit(attacking_unit: Unit, defending_unit: Unit) -> None:
    """
    Resolves unit vs unit combat.

    Params:
        attacking_unit (Unit): object representing attacking unit
        defending_unit (Unit): object representing defending unit
    """

    unit_vs_unit_standard(attacking_unit, defending_unit)

def unit_vs_unit_standard(attacking_unit: Unit, defending_unit: Unit) -> None:
    """
    Resolves standard unit vs unit combat.

    Params:
        attacking_unit (Unit): object representing attacking unit
        defending_unit (Unit): object representing defending unit

    Returns:
        None
    """

    # get region data
    GAME_ID = attacking_unit.game_id
    attacker_region = Region(attacking_unit.region_id, GAME_ID)
    defender_region = Region(defending_unit.region_id, GAME_ID)

    # get nation data
    nation_table = NationTable(GAME_ID)
    attacker = nation_table.get(str(attacking_unit.owner_id))
    defender = nation_table.get(str(defending_unit.owner_id))

    # get war data
    war_table = WarTable(GAME_ID)
    war_name = war_table.get_war_name(attacker.id, defender.id)
    war = war_table.get(war_name)
    attacker_cd = war.get_combatant(attacker.id)
    defender_cd = war.get_combatant(defender.id)
    war.log.append(f"{attacker.name} {attacking_unit.name} {attacking_unit.region_id} vs {defender.name} {defending_unit.name} {defending_unit.region_id}")

    # calculate attacker roll modifier
    attacker_roll_modifier = 0
    if "Attacker" in attacker_cd.role and "Superior Training" in attacker.completed_research:
        attacker_roll_modifier += 1
    elif "Defender" in attacker_cd.role and "Unyielding" in attacker.completed_research:
        attacker_roll_modifier += 1
    if attacking_unit.type == "Tank" and attacker_region.check_for_adjacent_unit({"Mechanized Infantry"}, attacking_unit.owner_id):
        attacker_roll_modifier += 1
    elif attacking_unit.type == "Infantry" and attacker_region.check_for_adjacent_unit({"Light Tank"}, attacking_unit.owner_id):
        attacker_roll_modifier += 1
    if attacking_unit.name == "Main Battle Tank" and defending_unit.type == "Infantry":
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
    if defending_unit.type == "Tank" and defender_region.check_for_adjacent_unit({"Mechanized Infantry"}, defending_unit.owner_id):
        defender_roll_modifier += 1
    elif defending_unit.type == "Infantry" and defender_region.check_for_adjacent_unit({"Light Tank"}, defending_unit.owner_id):
        defender_roll_modifier += 1
    if defending_unit.name == "Main Battle Tank" and attacking_unit.type == "Infantry":
        defender_roll_modifier += 1
    for tag_data in defender.tags.values():
        if tag_data.get("Combat Roll Bonus") == attacker.id:
            defender_roll_modifier += 1

    # calculate attacker damage modifier
    attacker_damage_modifier = 0
    if attacker_region.check_for_adjacent_unit({"Artillery"}, attacking_unit.owner_id):
        war.log.append(f"    {attacker.name} {attacking_unit.name} has artillery support!")
        attacker_damage_modifier += 1

    # calculate defender damage modifier
    defender_damage_modifier = 0
    if defender_region.check_for_adjacent_unit({"Artillery"}, defending_unit.owner_id):
        war.log.append(f"    {defender.name} {defending_unit.name} has artillery support!")
        defender_damage_modifier += 1

    # execute combat
    outcome, battle_str = _conduct_combat(attacking_unit, defending_unit, attacker.name, attacker_roll_modifier, defender.name, defender_roll_modifier)
    if outcome == 1:
        battle_str += " Attacker victory!"
        war.attacker_victories += war.warscore_victory
        attacker_cd.battles_won += 1
        defender_cd.battles_lost += 1
    elif outcome == 2:
        battle_str += " Defender victory!"
        war.defender_victories += war.warscore_victory
        attacker_cd.battles_lost += 1
        defender_cd.battles_won += 1
    else:
        battle_str += " Draw!"
    war.log.append(battle_str)

    # resolve outcome
    unit_data_dict = core.get_scenario_dict(attacking_unit.game_id, "Units")
    if outcome == 1:
        attacker_damage = unit_data_dict[attacking_unit.name]["Victory Damage"]
        defending_unit.health -= attacker_damage + attacker_damage_modifier
    elif outcome == 2:
        defender_damage = unit_data_dict[defending_unit.name]["Victory Damage"]
        attacking_unit.health -= defender_damage + defender_damage_modifier
    else:
        attacker_damage = unit_data_dict[attacking_unit.name]["Draw Damage"]
        defender_damage = unit_data_dict[defending_unit.name]["Draw Damage"]
        defending_unit.health -= attacker_damage + attacker_damage_modifier
        attacking_unit.health -= defender_damage + defender_damage_modifier
    
    # save attacking unit
    if attacking_unit.health > 0:
        attacking_unit._save_changes()
    else:
        war.defender_destroyed_units += attacking_unit.value
        attacker_cd.lost_units += 1
        defender_cd.destroyed_units += 1
        war.log.append(f"    {attacker.name} {attacking_unit.name} has been lost!")
        attacker.unit_counts[attacking_unit.name] -= 1
        nation_table.save(attacker)
        attacking_unit.clear()
    
    # save defending unit
    if defending_unit.health > 0:
        defending_unit._save_changes()
    else:
        war.attacker_destroyed_units += defending_unit.value
        attacker_cd.destroyed_units += 1
        defender_cd.lost_units += 1
        war.log.append(f"    {defender.name} {defending_unit.name} has been lost!")
        defender.unit_counts[defending_unit.name] -= 1
        nation_table.save(defender)
        defending_unit.clear()

    # save war data
    war.save_combatant(attacker_cd)
    war.save_combatant(defender_cd)
    war_table.save(war)

def unit_vs_improvement(attacking_unit: Unit, defending_improvement: Improvement) -> None:
    """
    Resolves unit vs improvement combat.

    Params:
        attacking_unit (Unit): object representing attacking unit
        defending_unit (Improvement): object representing defending improvement
    """

    target_region_unit = Unit(defending_improvement.region_id, defending_improvement.game_id)

    if attacking_unit.name == "Special Forces" and not target_region_unit.is_hostile(attacking_unit.owner_id):
        unit_vs_improvement_sf(attacking_unit, defending_improvement)
    else:
        unit_vs_improvement_standard(attacking_unit, defending_improvement)

def unit_vs_improvement_standard(attacking_unit: Unit, defending_improvement: Improvement) -> None:
    """
    Resolves standard unit vs improvement combat.

    Params:
        attacking_unit (Unit): object representing attacking unit
        defending_unit (Improvement): object representing defending improvement

    Returns:
        None
    """

    # get region data
    GAME_ID = attacking_unit.game_id
    attacker_region = Region(attacking_unit.region_id, GAME_ID)

    # get nation data
    nation_table = NationTable(GAME_ID)
    attacker = nation_table.get(str(attacking_unit.owner_id))
    defender = nation_table.get(str(defending_improvement.owner_id))

    # get information from wardata
    war_table = WarTable(GAME_ID)
    war_name = war_table.get_war_name(attacker.id, defender.id)
    war = war_table.get(war_name)
    attacker_cd = war.get_combatant(attacker.id)
    defender_cd = war.get_combatant(defender.id)
    war.log.append(f"{attacker.name} {attacking_unit.name} {attacking_unit.region_id} vs {defender.name} {defending_improvement.name} {defending_improvement.region_id}")

    # calculate attacker roll modifier
    attacker_roll_modifier = 0
    if 'Attacker' in attacker_cd.role and 'Superior Training' in attacker.completed_research:
        attacker_roll_modifier += 1
    elif 'Defender' in attacker_cd.role and 'Unyielding' in attacker.completed_research:
        attacker_roll_modifier += 1
    if attacking_unit.type == 'Tank' and attacker_region.check_for_adjacent_unit({"Mechanized Infantry"}, attacking_unit.owner_id):
        attacker_roll_modifier += 1
    elif attacking_unit.type == 'Infantry' and attacker_region.check_for_adjacent_unit({"Light Tank"}, attacking_unit.owner_id):
        attacker_roll_modifier += 1
    if attacking_unit.name == 'Main Battle Tank':
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
    if attacker_region.check_for_adjacent_unit({"Artillery"}, attacking_unit.owner_id):
        war.log.append(f"    {attacker.name} {attacking_unit.name} has artillery support!")
        attacker_damage_modifier += 1
    
    # calculate defender damage modifier
    defender_damage_modifier = 0

    # execute combat
    outcome, battle_str = _conduct_combat(attacking_unit, defending_improvement, attacker.name, attacker_roll_modifier, defender.name, defender_roll_modifier)
    if outcome == 1:
        battle_str += " Attacker victory!"
        war.attacker_victories += war.warscore_victory
        attacker_cd.battles_won += 1
        defender_cd.battles_lost += 1
    elif outcome == 2:
        battle_str += " Defender victory!"
        war.defender_victories += war.warscore_victory
        attacker_cd.battles_lost += 1
        defender_cd.battles_won += 1
    else:
        battle_str += " Draw!"
    war.log.append(battle_str)

    # resolve outcome
    unit_data_dict = core.get_scenario_dict(attacking_unit.game_id, "Units")
    improvement_data_dict = core.get_scenario_dict(attacking_unit.game_id, "Improvements")
    if outcome == 1:
        attacker_damage = unit_data_dict[attacking_unit.name]["Victory Damage"]
        defending_improvement.health -= attacker_damage + attacker_damage_modifier
    elif outcome == 2:
        defender_damage = improvement_data_dict[defending_improvement.name]["Victory Damage"]
        attacking_unit.health -= defender_damage + defender_damage_modifier
    else:
        attacker_damage = unit_data_dict[attacking_unit.name]["Draw Damage"]
        defender_damage = improvement_data_dict[defending_improvement.name]["Draw Damage"]
        defending_improvement.health -= attacker_damage + attacker_damage_modifier
        attacking_unit.health -= defender_damage + defender_damage_modifier
    
    # save attacking unit
    if attacking_unit.health > 0:
        attacking_unit._save_changes()
    else:
        war.defender_destroyed_units += attacking_unit.value
        attacker_cd.lost_units += 1
        defender_cd.destroyed_units += 1
        war.log.append(f"    {attacker.name} {attacking_unit.name} has been lost!")
        attacker.unit_counts[attacking_unit.name] -= 1
        nation_table.save(attacker)
        attacking_unit.clear()
    
    # save defending improvement
    if defending_improvement.health > 0:
        defending_improvement._save_changes()
    else:
        attacker_cd.destroyed_improvements += 1
        defender_cd.lost_improvements += 1
        if defending_improvement.name != 'Capital':
            war.attacker_destroyed_improvements += war.warscore_destroy_improvement
            war.log.append(f"    {defender.name} {defending_improvement.name} has been destroyed!")
            defender.improvement_counts[defending_improvement.name] -= 1
            nation_table.save(defender)
            defending_improvement.clear()
        else:
            war.attacker_captures += war.warscore_capital_capture
            war.log.append(f"    {defender.name} {defending_improvement.name} has been captured!")
            defending_improvement.health = 0
            defending_improvement._save_changes()

    # save war data
    war.save_combatant(attacker_cd)
    war.save_combatant(defender_cd)
    war_table.save(war)

def unit_vs_improvement_sf(attacking_unit: Unit, defending_improvement: Improvement) -> None:
    """
    Resolves special case of special forces vs a lone defensive improvement.

    Params:
        attacking_unit (Unit): object representing attacking unit
        defending_unit (Improvement): object representing defending improvement

    Returns:
        None
    """

    # get nation data
    GAME_ID = attacking_unit.game_id
    nation_table = NationTable(GAME_ID)
    attacker = nation_table.get(str(attacking_unit.owner_id))
    defender = nation_table.get(str(defending_improvement.owner_id))

    # get war data
    war_table = WarTable(GAME_ID)
    war_name = war_table.get_war_name(attacker.id, defender.id)
    war = war_table.get(war_name)
    attacker_cd = war.get_combatant(attacker.id)
    defender_cd = war.get_combatant(defender.id)
    war.log.append(f"{attacker.name} {attacking_unit.name} {attacking_unit.region_id} vs {defender.name} {defending_improvement.name} {defending_improvement.region_id}")

    # determine outcome - special forces always wins
    war.attacker_victories += war.warscore_victory
    attacker_cd.battles_won += 1
    defender_cd.battles_lost += 1
    battle_str = f"    {attacker.name} {attacking_unit.name} has defeated {defender.name} {defending_improvement.name}."
    war.log.append(battle_str)

    # save defending improvement
    attacker_cd.destroyed_improvements += 1
    defender_cd.lost_improvements += 1
    if defending_improvement.name != 'Capital':
        war.attacker_destroyed_improvements += war.warscore_destroy_improvement
        war.log.append(f"    {defender.name} {defending_improvement.name} has been destroyed!")
        defender.improvement_counts[defending_improvement.name] -= 1
        nation_table.save(defender)
        defending_improvement.clear()
    else:
        war.attacker_captures += war.warscore_capital_capture
        war.log.append(f"    {defender.name} {defending_improvement.name} has been captured!")
        defending_improvement.health = 0
        defending_improvement._save_changes()

    # save war data
    war.save_combatant(attacker_cd)
    war.save_combatant(defender_cd)
    war_table.save(war)

def _conduct_combat(attacking_unit: Unit, other: Union[Unit, Improvement], attacker_nation_name: str, attacker_roll_modifier: int, defender_nation_name: str, defender_roll_modifier: int) -> Tuple[int, str]:
    """
    Calculates result of combat between an attacking unit and some defender.

    Params:
        attacking_unit (Unit): Object representing attacking unit
        other (Unit or Improvement): Object representing defending force
        attacker_nation_name (str):
        attacker_roll_modifier (int):
        defender_nation_name (str):
        defender_roll_modifier (int):

    Returns:
        tuple: A tuple containing:
            - attacker_hit (bool)
            - defender_hit (bool)
            - battle_str (str)
    """

    attacker_roll = random.randint(1, 10) + attacker_roll_modifier
    defender_roll = random.randint(1, 10) + defender_roll_modifier
    attacker_hit = False
    defender_hit = False

    if attacker_roll >= attacking_unit.hit_value:
        attacker_hit = True
    if defender_roll >= other.hit_value:
        defender_hit = True

    if attacker_hit and not defender_hit:
        outcome = 1
    elif not attacker_hit and defender_hit:
        outcome = 2
    else:
        outcome = 3
    
    if attacker_roll_modifier > 0 and defender_roll_modifier > 0:
        battle_str = f'    {attacker_nation_name} rolled {attacker_roll} (+{attacker_roll_modifier}). {defender_nation_name} rolled {defender_roll} (+{defender_roll_modifier}).'
    elif attacker_roll_modifier > 0:
        battle_str = f'    {attacker_nation_name} rolled {attacker_roll} (+{attacker_roll_modifier}). {defender_nation_name} rolled {defender_roll}.'
    elif defender_roll_modifier > 0:
        battle_str = f'    {attacker_nation_name} rolled {attacker_roll}. {defender_nation_name} rolled {defender_roll} (+{defender_roll_modifier}).'
    else:
        battle_str = f'    {attacker_nation_name} rolled {attacker_roll}. {defender_nation_name} rolled {defender_roll}.'

    return outcome, battle_str
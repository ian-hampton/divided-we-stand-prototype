import ast
import random
from typing import Union, Tuple

from app import core
from app.region import Region
from app.improvement import Improvement
from app.unit import Unit
from app.wardata import WarData
from app.notifications import Notifications

def unit_vs_unit(attacking_unit: Unit, defending_unit: Unit) -> None:
    """
    Resolves unit vs unit combat.

    Params:
        attacking_unit (Unit): object representing attacking unit
        defending_unit (Unit): object representing defending unit
    """

    if attacking_unit.owner_id == 99:
        unit_vs_unit_fi(attacking_unit, defending_unit)
        return

    unit_vs_unit_standard(attacking_unit, defending_unit)

def unit_vs_unit_standard(attacking_unit: Unit, defending_unit: Unit) -> None:
    """
    Resolves standard unit vs unit combat.

    Params:
        attacking_unit (Unit): object representing attacking unit
        defending_unit (Unit): object representing defending unit
    """

    # get classes
    attacker_region = Region(attacking_unit.region_id, attacking_unit.game_id)
    defender_region = Region(defending_unit.region_id, defending_unit.game_id)
    wardata = WarData(attacking_unit.game_id)

    # get information from playerdata
    playerdata_filepath = f'gamedata/{attacking_unit.game_id}/playerdata.csv'
    playerdata_list = core.read_file(playerdata_filepath, 1)
    attacker_nation_name = playerdata_list[attacking_unit.owner_id - 1][1]
    defender_nation_name = playerdata_list[defending_unit.owner_id - 1][1]
    attacker_research_list = ast.literal_eval(playerdata_list[attacking_unit.owner_id - 1][26])
    defender_research_list = ast.literal_eval(playerdata_list[defending_unit.owner_id - 1][26])

    # get information from wartdata
    war_name = wardata.are_at_war(attacking_unit.owner_id, defending_unit.owner_id, True)
    attacker_war_role = wardata.get_war_role(attacker_nation_name, war_name)
    defender_war_role = wardata.get_war_role(defender_nation_name, war_name)
    wardata.append_war_log(war_name, f"{attacker_nation_name} {attacking_unit.name} {attacking_unit.region_id} vs {defender_nation_name} {defending_unit.name} {defending_unit.region_id}")

    # calculate attacker roll modifier
    attacker_roll_modifier = 0
    if 'Attacker' in attacker_war_role and 'Superior Training' in attacker_research_list:
        attacker_roll_modifier += 1
    elif 'Defender' in attacker_war_role and 'Unyielding' in attacker_research_list:
        attacker_roll_modifier += 1
    if attacking_unit.type == 'Tank' and attacker_region.check_for_adjacent_unit({"Mechanized Infantry"}, attacking_unit.owner_id):
        attacker_roll_modifier += 1
    elif attacking_unit.type == 'Infantry' and attacker_region.check_for_adjacent_unit({"Light Tank"}, attacking_unit.owner_id):
        attacker_roll_modifier += 1
    if attacking_unit.name == 'Main Battle Tank' and defending_unit.type == 'Infantry':
        attacker_roll_modifier += 1

    # calculate defender roll modifier
    defender_roll_modifier = 0
    if 'Attacker' in defender_war_role and 'Superior Training' in defender_research_list:
        defender_roll_modifier += 1
    elif 'Defender' in defender_war_role and 'Unyielding' in defender_research_list:
        defender_roll_modifier += 1
    if defending_unit.type == 'Tank' and defender_region.check_for_adjacent_unit({"Mechanized Infantry"}, defending_unit.owner_id):
        defender_roll_modifier += 1
    elif defending_unit.type == 'Infantry' and defender_region.check_for_adjacent_unit({"Light Tank"}, defending_unit.owner_id):
        defender_roll_modifier += 1
    if defending_unit.name == 'Main Battle Tank' and attacking_unit.type == 'Infantry':
        defender_roll_modifier += 1

    # calculate attacker damage modifier
    attacker_damage_modifier = 0
    if attacker_region.check_for_adjacent_unit({"Artillery"}, attacking_unit.owner_id):
        wardata.append_war_log(war_name, f"    {attacker_nation_name} {attacking_unit.name} has artillery support!")
        attacker_damage_modifier += 1

    # calculate defender damage modifier
    defender_damage_modifier = 0
    if defender_region.check_for_adjacent_unit({"Artillery"}, defending_unit.owner_id):
        wardata.append_war_log(war_name, f"    {defender_nation_name} {defending_unit.name} has artillery support!")
        defender_damage_modifier += 1

    # execute combat
    combat_results = _conduct_combat(attacking_unit, defending_unit, attacker_nation_name, attacker_roll_modifier, defender_nation_name, defender_roll_modifier)
    attacker_hit = combat_results[0]
    defender_hit = combat_results[1]
    battle_str = combat_results[2]

    # determine outcome
    if attacker_hit and not defender_hit:
        battle_str += ' Attacker victory!'
        wardata.statistic_add(war_name, attacker_nation_name, "battlesWon")
        wardata.statistic_add(war_name, defender_nation_name, "battlesLost")
        wardata.warscore_add(war_name, attacker_war_role, "combatVictories")
    elif not attacker_hit and defender_hit:
        battle_str += ' Defender victory!'
        wardata.statistic_add(war_name, defender_nation_name, "battlesWon")
        wardata.statistic_add(war_name, attacker_nation_name, "battlesLost")
        wardata.warscore_add(war_name, defender_war_role, "combatVictories")
    else:
        battle_str += ' Draw!'
    wardata.append_war_log(war_name, battle_str)

    # resolve outcome
    unit_data_dict = core.get_scenario_dict(attacking_unit.game_id, "Units")
    if attacker_hit and not defender_hit:
        attacker_damage = unit_data_dict[attacking_unit.name]["Victory Damage"]
        defending_unit.health -= attacker_damage + attacker_damage_modifier
    elif not attacker_hit and defender_hit:
        defender_damage = unit_data_dict[defending_unit.name]["Victory Damage"]
        attacking_unit.health -= defender_damage + defender_damage_modifier
    else:
        attacker_damage = unit_data_dict[attacking_unit.name]["Draw Damage"]
        defender_damage = unit_data_dict[defending_unit.name]["Draw Damage"]
        defending_unit.health -= attacker_damage + attacker_damage_modifier
        attacking_unit.health -= defender_damage + defender_damage_modifier
    
    if attacking_unit.health > 0:
        attacking_unit._save_changes()
    else:
        wardata.statistic_add(war_name, defender_nation_name, "enemyUnitsDestroyed")
        wardata.statistic_add(war_name, attacker_nation_name, "friendlyUnitsDestroyed")
        unit_bounty = _get_warscore_from_unit(attacking_unit.name)
        wardata.warscore_add(war_name, defender_war_role, "enemyUnitsDestroyed", unit_bounty)
        wardata.append_war_log(war_name, f"    {attacker_nation_name} {attacking_unit.name} has been lost!")
        attacking_unit.clear()
    
    if defending_unit.health > 0:
        defending_unit._save_changes()
    else:
        wardata.statistic_add(war_name, attacker_nation_name, "enemyUnitsDestroyed")
        wardata.statistic_add(war_name, defender_nation_name, "friendlyUnitsDestroyed")
        unit_bounty = _get_warscore_from_unit(defending_unit.name)
        wardata.warscore_add(war_name, attacker_war_role, "enemyUnitsDestroyed", unit_bounty)
        wardata.append_war_log(war_name, f"    {defender_nation_name} {defending_unit.name} has been lost!")
        defending_unit.clear()

def unit_vs_unit_fi(attacking_unit: Unit, defending_unit: Unit) -> None:
    """
    Resolves foreign invasion unit vs unit combat.

    Params:
        attacking_unit (Unit): object representing attacking unit
        defending_unit (Unit): object representing defending unit
    """

    # get classes
    attacker_region = Region(attacking_unit.region_id, attacking_unit.game_id)
    defender_region = Region(defending_unit.region_id, defending_unit.game_id)
    notifications = Notifications(attacking_unit.game_id)

    # get information from playerdata
    playerdata_filepath = f'gamedata/{attacking_unit.game_id}/playerdata.csv'
    playerdata_list = core.read_file(playerdata_filepath, 1)
    defender_nation_name = playerdata_list[defending_unit.owner_id - 1][1]

    # calculate attacker roll modifier
    attacker_roll_modifier = 0
    if attacking_unit.type == 'Tank' and attacker_region.check_for_adjacent_unit({"Mechanized Infantry"}, attacking_unit.owner_id):
        attacker_roll_modifier += 1
    elif attacking_unit.type == 'Infantry' and attacker_region.check_for_adjacent_unit({"Light Tank"}, attacking_unit.owner_id):
        attacker_roll_modifier += 1
    if attacking_unit.name == 'Main Battle Tank' and defending_unit.type == 'Infantry':
        attacker_roll_modifier += 1

    # calculate defender roll modifier
    defender_roll_modifier = 0
    if defending_unit.type == 'Tank' and defender_region.check_for_adjacent_unit({"Mechanized Infantry"}, defending_unit.owner_id):
        defender_roll_modifier += 1
    elif defending_unit.type == 'Infantry' and defender_region.check_for_adjacent_unit({"Light Tank"}, defending_unit.owner_id):
        defender_roll_modifier += 1
    if defending_unit.name == 'Main Battle Tank' and attacking_unit.type == 'Infantry':
        defender_roll_modifier += 1

    # calculate attacker damage modifier
    attacker_damage_modifier = 0
    if attacker_region.check_for_adjacent_unit({"Artillery"}, attacking_unit.owner_id):
        attacker_damage_modifier += 1

    # calculate defender damage modifier
    defender_damage_modifier = 0
    if defender_region.check_for_adjacent_unit({"Artillery"}, defending_unit.owner_id):
        defender_damage_modifier += 1

    # execute combat
    attacker_roll = random.randint(1, 10) + attacker_roll_modifier
    defender_roll = random.randint(1, 10)
    attacker_hit = False
    defender_hit = False
    if attacker_roll >= attacking_unit.hit_value:
        attacker_hit = True
    if defender_roll >= defending_unit.hit_value:
        defender_hit = True

    # resolve outcome
    unit_data_dict = core.get_scenario_dict(attacking_unit.game_id, "Units")
    if attacker_hit and not defender_hit:
        attacker_damage = unit_data_dict[attacking_unit.name]["Victory Damage"]
        defending_unit.health -= attacker_damage + attacker_damage_modifier
        notifications.append(f"Foreign Invasion attacked {defender_nation_name} {defending_unit.name} {defending_unit.region_id}. Attacker victory!", 2)
    elif not attacker_hit and defender_hit:
        defender_damage = unit_data_dict[defending_unit.name]["Victory Damage"]
        attacking_unit.health -= defender_damage + defender_damage_modifier
        notifications.append(f"Foreign Invasion attacked {defender_nation_name} {defending_unit.name} {defending_unit.region_id}. Defender victory!", 2)
    else:
        attacker_damage = unit_data_dict[attacking_unit.name]["Draw Damage"]
        defender_damage = unit_data_dict[defending_unit.name]["Draw Damage"]
        defending_unit.health -= attacker_damage + attacker_damage_modifier
        attacking_unit.health -= defender_damage + defender_damage_modifier
        notifications.append(f"Foreign Invasion attacked {defender_nation_name} {defending_unit.name} {defending_unit.region_id}. Draw!", 2)
    
    if attacking_unit.health > 0:
        attacking_unit._save_changes()
    else:
        notifications.append(f"Foreign Invasion unit defeated!", 2)
        attacking_unit.clear()
    
    if defending_unit.health > 0:
        defending_unit._save_changes()
    else:
        notifications.append(f"{defender_nation_name} {defending_unit.name} unit defeated!", 2)
        defending_unit.clear()

def unit_vs_improvement(attacking_unit: Unit, defending_improvement: Improvement) -> None:
    """
    Resolves unit vs improvement combat.

    Params:
        attacking_unit (Unit): object representing attacking unit
        defending_unit (Improvement): object representing defending improvement
    """

    target_region_unit = Unit(defending_improvement.region_id, defending_improvement.game_id)

    if attacking_unit.owner_id == 99:
        unit_vs_improvement_fi(attacking_unit, defending_improvement)
        return
    elif attacking_unit.name == 'Special Forces' and not target_region_unit.is_hostile(attacking_unit.owner_id):
        unit_vs_improvement_sf(attacking_unit, defending_improvement)
        return

    unit_vs_improvement_standard(attacking_unit, defending_improvement)

def unit_vs_improvement_standard(attacking_unit: Unit, defending_improvement: Improvement) -> None:
    """
    Resolves standard unit vs improvement combat.

    Params:
        attacking_unit (Unit): object representing attacking unit
        defending_unit (Improvement): object representing defending improvement
    """

    # get classes
    attacker_region = Region(attacking_unit.region_id, attacking_unit.game_id)
    wardata = WarData(attacking_unit.game_id)

    # get information from playerdata
    playerdata_filepath = f'gamedata/{attacking_unit.game_id}/playerdata.csv'
    playerdata_list = core.read_file(playerdata_filepath, 1)
    attacker_nation_name = playerdata_list[attacking_unit.owner_id - 1][1]
    defender_nation_name = playerdata_list[defending_improvement.owner_id - 1][1]
    attacker_research_list = ast.literal_eval(playerdata_list[attacking_unit.owner_id - 1][26])
    defender_research_list = ast.literal_eval(playerdata_list[defending_improvement.owner_id - 1][26])

    # get information from wardata
    war_name = wardata.are_at_war(attacking_unit.owner_id, defending_improvement.owner_id, True)
    attacker_war_role = wardata.get_war_role(attacker_nation_name, war_name)
    defender_war_role = wardata.get_war_role(defender_nation_name, war_name)
    wardata.append_war_log(war_name, f"{attacker_nation_name} {attacking_unit.name} {attacking_unit.region_id} vs {defender_nation_name} {defending_improvement.name} {defending_improvement.region_id}")

    # calculate attacker roll modifier
    attacker_roll_modifier = 0
    if 'Attacker' in attacker_war_role and 'Superior Training' in attacker_research_list:
        attacker_roll_modifier += 1
    elif 'Defender' in attacker_war_role and 'Unyielding' in attacker_research_list:
        attacker_roll_modifier += 1
    if attacking_unit.type == 'Tank' and attacker_region.check_for_adjacent_unit({"Mechanized Infantry"}, attacking_unit.owner_id):
        attacker_roll_modifier += 1
    elif attacking_unit.type == 'Infantry' and attacker_region.check_for_adjacent_unit({"Light Tank"}, attacking_unit.owner_id):
        attacker_roll_modifier += 1
    if attacking_unit.name == 'Main Battle Tank':
        attacker_roll_modifier += 1

    # calculate defender roll modifier
    defender_roll_modifier = 0
    if 'Defensive Tactics' in defender_research_list:
        defender_roll_modifier += 1

    # calculate attacker damage modifier
    attacker_damage_modifier = 0
    if attacker_region.check_for_adjacent_unit({"Artillery"}, attacking_unit.owner_id):
        wardata.append_war_log(war_name, f"    {attacker_nation_name} {attacking_unit.name} has artillery support!")
        attacker_damage_modifier += 1
    
    # calculate defender damage modifier
    defender_damage_modifier = 0

    # execute combat
    combat_results = _conduct_combat(attacking_unit, defending_improvement, attacker_nation_name, attacker_roll_modifier, defender_nation_name, defender_roll_modifier)
    attacker_hit = combat_results[0]
    defender_hit = combat_results[1]
    battle_str = combat_results[2]

    # determine outcome
    if attacker_hit and not defender_hit:
        battle_str += ' Attacker victory!'
        wardata.statistic_add(war_name, attacker_nation_name, "battlesWon")
        wardata.statistic_add(war_name, defender_nation_name, "battlesLost")
        wardata.warscore_add(war_name, attacker_war_role, "combatVictories")
    elif not attacker_hit and defender_hit:
        battle_str += ' Defender victory!'
        wardata.statistic_add(war_name, defender_nation_name, "battlesWon")
        wardata.statistic_add(war_name, attacker_nation_name, "battlesLost")
        wardata.warscore_add(war_name, defender_war_role, "combatVictories")
    else:
        battle_str += ' Draw!'
    wardata.append_war_log(war_name, battle_str)

    # resolve outcome
    unit_data_dict = core.get_scenario_dict(attacking_unit.game_id, "Units")
    improvement_data_dict = core.get_scenario_dict(attacking_unit.game_id, "Improvements")
    if attacker_hit and not defender_hit:
        attacker_damage = unit_data_dict[attacking_unit.name]["Victory Damage"]
        defending_improvement.health -= attacker_damage + attacker_damage_modifier
    elif not attacker_hit and defender_hit:
        defender_damage = improvement_data_dict[defending_improvement.name]["Victory Damage"]
        attacking_unit.health -= defender_damage + defender_damage_modifier
    else:
        attacker_damage = unit_data_dict[attacking_unit.name]["Draw Damage"]
        defender_damage = improvement_data_dict[defending_improvement.name]["Draw Damage"]
        defending_improvement.health -= attacker_damage + attacker_damage_modifier
        attacking_unit.health -= defender_damage + defender_damage_modifier
    
    if attacking_unit.health > 0:
        attacking_unit._save_changes()
    else:
        wardata.statistic_add(war_name, defender_nation_name, "enemyUnitsDestroyed")
        wardata.statistic_add(war_name, attacker_nation_name, "friendlyUnitsDestroyed")
        unit_bounty = _get_warscore_from_unit(attacking_unit.name)
        wardata.warscore_add(war_name, defender_war_role, "enemyUnitsDestroyed", unit_bounty)
        wardata.append_war_log(war_name, f"    {attacker_nation_name} {attacking_unit.name} has been lost!")
        attacking_unit.clear()
    
    if defending_improvement.health > 0:
        defending_improvement._save_changes()
    else:
        wardata.statistic_add(war_name, attacker_nation_name, "enemyImprovementsDestroyed")
        wardata.statistic_add(war_name, defender_nation_name, "friendlyImprovementsDestroyed")
        if defending_improvement.name != 'Capital':
            wardata.warscore_add(war_name, attacker_war_role, "enemyImprovementsDestroyed", 2)
            wardata.append_war_log(war_name, f"    {defender_nation_name} {defending_improvement.name} has been destroyed!")
            defending_improvement.clear()
        else:
            wardata.warscore_add(war_name, attacker_war_role, "capitalCaptures", 20)
            wardata.append_war_log(war_name, f"    {defender_nation_name} {defending_improvement.name} has been captured!")
            defending_improvement.health = 0
            defending_improvement._save_changes()

def unit_vs_improvement_sf(attacking_unit: Unit, defending_improvement: Improvement) -> None:
    """
    Resolves special case of special forces vs a lone defensive improvement.

    Params:
        attacking_unit (Unit): object representing attacking unit
        defending_unit (Improvement): object representing defending improvement
    """
    # get classes
    wardata = WarData(attacking_unit.game_id)

    # get information from playerdata
    playerdata_filepath = f'gamedata/{attacking_unit.game_id}/playerdata.csv'
    playerdata_list = core.read_file(playerdata_filepath, 1)
    attacker_nation_name = playerdata_list[attacking_unit.owner_id - 1][1]
    defender_nation_name = playerdata_list[defending_improvement.owner_id - 1][1]

    # get information from wardata
    war_name = wardata.are_at_war(attacking_unit.owner_id, defending_improvement.owner_id, True)
    attacker_war_role = wardata.get_war_role(attacker_nation_name, war_name)
    wardata.append_war_log(war_name, f"{attacker_nation_name} {attacking_unit.name} {attacking_unit.region_id} vs {defender_nation_name} {defending_improvement.name} {defending_improvement.region_id}")

    # determine outcome - special forces always wins
    wardata.statistic_add(war_name, attacker_nation_name, "battlesWon")
    wardata.statistic_add(war_name, defender_nation_name, "battlesLost")
    wardata.warscore_add(war_name, attacker_war_role, "combatVictories")
    battle_str = f"    {attacker_nation_name} {attacking_unit.name} has defeated {defender_nation_name} {defending_improvement.name}."
    wardata.append_war_log(war_name, battle_str)
    
    # resolve outcome
    wardata.statistic_add(war_name, attacker_nation_name, "enemyImprovementsDestroyed")
    wardata.statistic_add(war_name, defender_nation_name, "friendlyImprovementsDestroyed")
    if defending_improvement.name != 'Capital':
        wardata.warscore_add(war_name, attacker_war_role, "enemyImprovementsDestroyed", 2)
        wardata.append_war_log(war_name, f"    {defender_nation_name} {defending_improvement.name} has been destroyed!")
        defending_improvement.clear()
    else:
        wardata.warscore_add(war_name, attacker_war_role, "capitalCaptures", 20)
        wardata.append_war_log(war_name, f"    {defender_nation_name} {defending_improvement.name} has been captured!")
        defending_improvement.health = 0
        defending_improvement._save_changes()

def unit_vs_improvement_fi(attacking_unit: Unit, defending_improvement: Improvement) -> None:
    """
    Resolves foreign invasion unit vs improvement combat.

    Params:
        attacking_unit (Unit): object representing attacking unit
        defending_unit (Improvement): object representing defending improvement
    """

    # get classes
    attacker_region = Region(attacking_unit.region_id, attacking_unit.game_id)
    notifications = Notifications(attacking_unit.game_id)

    # get information from playerdata
    playerdata_filepath = f'gamedata/{attacking_unit.game_id}/playerdata.csv'
    playerdata_list = core.read_file(playerdata_filepath, 1)
    defender_nation_name = playerdata_list[defending_improvement.owner_id - 1][1]

    # calculate attacker roll modifier
    attacker_roll_modifier = 0
    if attacking_unit.type == 'Tank' and attacker_region.check_for_adjacent_unit({"Mechanized Infantry"}, attacking_unit.owner_id):
        attacker_roll_modifier += 1
    elif attacking_unit.type == 'Infantry' and attacker_region.check_for_adjacent_unit({"Light Tank"}, attacking_unit.owner_id):
        attacker_roll_modifier += 1
    if attacking_unit.name == 'Main Battle Tank':
        attacker_roll_modifier += 1

    # execute combat
    attacker_roll = random.randint(1, 10) + attacker_roll_modifier
    defender_roll = random.randint(1, 10)
    attacker_hit = False
    defender_hit = False
    if attacker_roll >= attacking_unit.hit_value:
        attacker_hit = True
    if defender_roll >= defending_improvement.hit_value:
        defender_hit = True

    # resolve outcome
    unit_data_dict = core.get_scenario_dict(attacking_unit.game_id, "Units")
    improvement_data_dict = core.get_scenario_dict(attacking_unit.game_id, "Improvements")
    if attacker_hit and not defender_hit:
        attacker_damage = unit_data_dict[attacking_unit.name]["Victory Damage"]
        defending_improvement.health -= attacker_damage
        notifications.append(f"Foreign Invasion attacked {defender_nation_name} {defending_improvement.name} {defending_improvement.region_id}. Attacker victory!", 2)
    elif not attacker_hit and defender_hit:
        defender_damage = improvement_data_dict[defending_improvement.name]["Victory Damage"]
        attacking_unit.health -= defender_damage
        notifications.append(f"Foreign Invasion attacked {defender_nation_name} {defending_improvement.name} {defending_improvement.region_id}. Defender victory!", 2)
    else:
        attacker_damage = unit_data_dict[attacking_unit.name]["Draw Damage"]
        defender_damage = improvement_data_dict[defending_improvement.name]["Draw Damage"]
        defending_improvement.health -= attacker_damage
        attacking_unit.health -= defender_damage
        notifications.append(f"Foreign Invasion attacked {defender_nation_name} {defending_improvement.name} {defending_improvement.region_id}. Draw!", 2)
    
    if attacking_unit.health > 0:
        attacking_unit._save_changes()
    else:
        notifications.append(f"Foreign Invasion unit defeated!", 2)
        attacking_unit.clear()
    
    if defending_improvement.health > 0:
        defending_improvement._save_changes()
    else:
        notifications.append(f"{defender_nation_name} {defending_improvement.name} improvement defeated!", 2)
        if defending_improvement.name != 'Capital':
            defending_improvement.clear()
        else:
            defending_improvement._save_changes()        

def _conduct_combat(attacking_unit: Unit, other: Union[Unit, Improvement], attacker_nation_name: str, attacker_roll_modifier: int, defender_nation_name: str, defender_roll_modifier: int) -> Tuple[bool, bool, str]:
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
    if attacker_roll_modifier > 0 and defender_roll_modifier > 0:
        battle_str = f'    {attacker_nation_name} rolled {attacker_roll} (+{attacker_roll_modifier}). {defender_nation_name} rolled {defender_roll} (+{defender_roll_modifier}).'
    elif attacker_roll_modifier > 0:
        battle_str = f'    {attacker_nation_name} rolled {attacker_roll} (+{attacker_roll_modifier}). {defender_nation_name} rolled {defender_roll}.'
    elif defender_roll_modifier > 0:
        battle_str = f'    {attacker_nation_name} rolled {attacker_roll}. {defender_nation_name} rolled {defender_roll} (+{defender_roll_modifier}).'
    else:
        battle_str = f'    {attacker_nation_name} rolled {attacker_roll}. {defender_nation_name} rolled {defender_roll}.'

    return attacker_hit, defender_hit, battle_str

def _get_warscore_from_unit(unit_name: str) -> int:
    """
    Fetches the war score rewarded from defeating a unit.

    Params:
        unit_name (str):

    Returns:
        int: calculated war score
    """
    match unit_name:
        case 'Infantry' | 'Artillery' | 'Motorized Infantry':
            return 3
        case 'Mechanized Infantry' | 'Light Tank ':
            return 5
        case 'Special Forces' | 'Heavy Tank' | 'Main Battle Tank':
            return 7
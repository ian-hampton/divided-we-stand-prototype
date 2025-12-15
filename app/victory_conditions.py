from collections import defaultdict

from app.nation import Nation, Nations

# easy

def ambassador(nation: Nation) -> bool:

    from app.alliance import Alliances
    
    # count alliances
    alliances_found = defaultdict(int)
    for alliance in Alliances:
        if nation.name in alliance.founding_members and alliance.type != "Non-Aggression Pact":
            alliances_found[alliance.type] += 1
    
    # if at least 3 of same type vc fullfilled
    for count in alliances_found.values():
        if count >= 3:
            return True
        
    return False

def backstab(nation: Nation) -> bool:

    from app.alliance import Alliances
    from app.war import Wars

    # get set of all nations defeated in war
    nations_defeated = set()
    for war in Wars:
        if war.outcome == "TBD" or nation.name not in war.combatants:
            # we do not care about wars player was not involved in
            continue
        if "Attacker" in war.get_role(nation.id):
            nation_side = "Attacker"
        else:
            nation_side = "Defender"
        if nation_side not in war.outcome:
            # we do not care about wars the player lost or white peaced
            continue
        for combatant_id in war.combatants:
            if nation_side not in war.get_role(combatant_id):
                nations_defeated.add(combatant_id)
    
    # get set of all nations you lost a war to
    nations_lost_to = set()
    for war in Wars:
        if war.outcome == "TBD" or nation.name not in war.combatants:
            # we do not care about wars player was not involved in
            continue
        if "Attacker" in war.get_role(nation.id):
            nation_side = "Attacker"
        else:
            nation_side = "Defender"
        if nation_side in war.outcome or "White Peace" == war.outcome:
            # we do not care about wars the player won or white peaced
            continue
        for combatant_id in war.combatants:
            if nation_side not in war.get_role(combatant_id):
                nations_lost_to.add(combatant_id)
    
    # get set of all former allies
    current_allies = set()
    former_allies = set()
    for alliance in Alliances:
        if alliance.is_active and nation.name in alliance.current_members:
            for ally_name in alliance.current_members:
                current_allies.add(ally_name)
            for ally_name in alliance.former_members:
                former_allies.add(ally_name)
        elif not alliance.is_active and nation.name in alliance.former_members:
            for ally_name in alliance.former_members:
                former_allies.add(ally_name)
    if nation.name in current_allies:
        current_allies.remove(nation.name)
    if nation.name in former_allies:
        former_allies.remove(nation.name)
    former_allies_filtered = set()
    for ally_name in former_allies:
        if ally_name not in current_allies:
            former_allies_filtered.add(ally_name)
    former_allies = former_allies_filtered
    
    # win a war against a former ally
    for former_ally in former_allies:
        temp = Nations.get(former_ally)
        if temp.id in nations_defeated:
            return True
    
    # win a war against someone you lost to
    for enemy_id in nations_lost_to:
        if enemy_id in nations_defeated:
            return True
    
    return False

def breakthrough(nation: Nation) -> bool:

    from app.scenario import ScenarioData as SD

    # build set of all techs other players have researched so we can compare
    completed_research_all = set()
    for temp in Nations:
        if temp.name != nation.name:
            temp_research_list = list(temp.completed_research.keys())
            completed_research_all.update(temp_research_list)
    
    # find 20 point or greater tech that is not in completed_research_all
    for tech_name in nation.completed_research:
        if (tech_name in SD.technologies
            and tech_name not in completed_research_all
            and SD.technologies.get(tech_name).cost >= 20):
            return True

    return False

def diverse_economy(nation: Nation) -> bool:

    non_zero_count = sum(1 for count in nation.improvement_counts.values() if count != 0)
    
    if non_zero_count >= 16:
        return True

    return False

def double_down(nation: Nation) -> bool:

    # load game data
    from app.war import Wars

    # count wars
    wars_found = defaultdict(int)
    for war in Wars:
        
        if nation.id not in war.combatants:
            continue
        
        if war.outcome == "Attacker Victory" and "Attacker" in war.get_combatant(nation.id).role:
            for temp_id in war.combatants:
                if temp_id != nation.id and not war.is_on_same_side(nation.id, temp_id):
                    wars_found[temp_id] += 1
                    
        elif war.outcome == "Defender Victory" and "Defender" in war.get_combatant(nation.id).role:
            for temp_id in war.combatants:
                if temp_id != nation.id and not war.is_on_same_side(nation.id, temp_id):
                    wars_found[temp_id] += 1

    # check
    for count in wars_found.values():
        if count >= 2:
            return True

    return False

def new_empire(nation: Nation) -> bool:

    if nation.improvement_counts["Capital"] >= 2:
        return True

    return False

def reconstruction_effort(nation: Nation) -> bool:

    for other_nation in Nations:
        if other_nation.name != nation.name and other_nation.records.development >= nation.records.development:
            return False

    return True

def reliable_ally(nation: Nation) -> bool:

    from app.alliance import Alliances

    longest_alliance_name, duration = Alliances.longest_alliance()
    if longest_alliance_name is not None:
        longest_alliance = Alliances.get(longest_alliance_name)
        if nation.name in longest_alliance.founding_members and longest_alliance.age >= 12:
            return True
        
    return False

def secure_strategic_resources(nation: Nation) -> bool:

    if (nation.improvement_counts["Advanced Metals Mine"] > 0
        and nation.improvement_counts["Uranium Mine"] > 0
        and nation.improvement_counts["Rare Earth Elements Mine"] > 0):
        return True

    return False

# medium

def energy_focus(nation: Nation) -> bool:

    if nation.records.energy_income < 24:
        return False
    
    for other_nation in Nations:
        if other_nation.name != nation.name and other_nation.records.energy_income >= nation.records.energy_income:
            return False

    return True

def industrial_focus(nation: Nation) -> bool:

    if nation.records.industrial_income < 50:
        return False
    
    for other_nation in Nations:
        if other_nation.name != nation.name and other_nation.records.industrial_income >= nation.records.industrial_income:
            return False

    return True

def hegemony(nation: Nation) -> bool:
    
    puppet_str = f"{nation.name} Puppet State"
    for temp in Nations:
        if puppet_str == temp.status:
            return True

    return False

def monopoly(nation: Nation) -> bool:

    # create tag for tracking this if it doesn't already exist
    if "Monopoly" not in nation.tags:
        new_tag = {
            "Expire Turn": 99999
        }
        nation.tags["Monopoly"] = new_tag

    # check resources
    for resource_name in nation._resources:
        
        if resource_name == "Military Capacity":
            continue
        
        # check nation gross income of resource vs all other players
        if any(float(nation.get_gross_income(resource_name)) <= float(temp.get_gross_income(resource_name)) for temp in Nations):
            if resource_name in nation.tags["Monopoly"]:
                # reset streak if broken by deleting record
                del nation.tags["Monopoly"][resource_name]
            continue
        
        # update monopoly streak
        if resource_name in nation.tags["Monopoly"]:
            nation.tags["Monopoly"][resource_name] += 1
        else:
            nation.tags["Monopoly"][resource_name] = 1

        # return true if streak has reached thresh
        if nation.tags["Monopoly"][resource_name] >= 16:
            return True

    return False

def nuclear_deterrent(nation: Nation) -> bool:

    # get nuke counts
    sum_dict = {}
    for temp in Nations:
        sum_dict[temp.name] = temp.nuke_count
    
    # check if nation has the greatest sum
    nation_name_sum = sum_dict[nation.name]
    for temp_nation_name, sum in sum_dict.items():
        if temp_nation_name != nation.name and sum >= nation_name_sum:
            return False
        
    # check if nation has at least 6 nukes
    if nation.nuke_count < 6:
        return False

    return True

def strong_research_agreement(nation: Nation) -> bool:

    from app.alliance import Alliances

    for alliance in Alliances:
        if nation.name in alliance.current_members and alliance.type == "Research Agreement":
            amount, resource_name = alliance.calculate_yield()
            if amount >= 8:
                return True

    return False

def strong_trade_agreement(nation: Nation) -> bool:

    from app.alliance import Alliances

    for alliance in Alliances:
        if nation.name in alliance.current_members and alliance.type == "Trade Agreement":
            amount, resource_name = alliance.calculate_yield()
            if amount >= 24:
                return True

    return False

def sphere_of_influence(nation: Nation) -> bool:

    if nation.records.agenda_count >= 8:
        return True

    return False

def warmonger(nation: Nation) -> bool:

    from app.war import Wars

    count = 0
    for war in Wars:
        if war.outcome == "Attacker Victory" and war.get_role(nation.id) == "Main Attacker":
            count += 1
    
    if count >= 3:
        return True

    return False

# hard

def economic_domination(nation: Nation) -> bool:

    # check if first and not tied
    first, second, third = Nations.get_top_three("net_income")
    if nation.name in first[0] and (first[1] > second[1]):
        return True

    return False

def influence_through_trade(nation: Nation) -> bool:

    # check if first and not tied
    first, second, third = Nations.get_top_three("transaction_count")
    if nation.name in first[0] and (first[1] > second[1]):
        return True

    return False

def military_superpower(nation: Nation) -> bool:

    for other_nation in Nations:
        if other_nation.name != nation.name and other_nation.records.military_strength >= nation.records.military_strength:
            return False

    return True

def scientific_leader(nation: Nation) -> bool:

    # check if first and not tied
    first, second, third = Nations.get_top_three("technology_count")
    if nation.name in first[0] and (first[1] > second[1]):
        return True

    return False

def territorial_control(nation: Nation) -> bool:

    # check if first and not tied
    first, second, third = Nations.get_top_three("nation_size")
    if nation.name in first[0] and (first[1] > second[1]):
        return True

    return False
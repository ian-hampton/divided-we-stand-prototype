from app.nation.nations import Nations
from app.region.regions import Regions
from app.war.wars import Wars

def heal_units():
    """
    Heals every unit that is eligible to be healed.
    """

    for region in Regions:

        # check that unit exists
        if region.unit.name is None:
            continue

        # do not heal units owned by an event player (99)
        if region.data.owner_id == "99":
            continue

        # do not heal units that have been attacked this turn
        if region.unit.has_been_attacked:
            continue

        unit_owner = Nations.get(region.unit.owner_id)
        heal_allowed = False

        # check if unit is allowed to heal based on its positioning
        if region.unit.type == "Special Forces":
            heal_allowed = True    # special forces can always heal
        elif "Scorched Earth" in unit_owner.completed_research:
            heal_allowed = True    # unit can always heal if Scorched Earth researched
        elif region.data.owner_id == region.unit.owner_id:
            heal_allowed = True    # unit can always heal within its own territory
        else:
            for adjacent_region in region.graph.iter_adjacent_regions():
                if adjacent_region.unit.owner_id == region.unit.owner_id:
                    heal_allowed = True    # unit can heal if located next to a friendly unit
        
        if not heal_allowed:
            continue

        region.unit.heal(1)
        if "Peacetime Recovery" in unit_owner.completed_research and Wars.is_at_peace(unit_owner.id):
            region.unit.heal(1)

def heal_improvements():
    """
    Heals every improvement that is eligible to be healed.
    """
    
    for region in Regions:

        # check that improvement exists and has health
        if region.improvement.name is None or region.improvement.health == 99:
            continue

        # do not heal unowned improvements (0) or improvements owned by an event player (99)
        if region.data.owner_id in ["0", "99"]:
            continue

        # do not heal improvements that have been attacked this turn
        if region.improvement.has_been_attacked:
            continue

        region.improvement.heal(1)

        improvement_owner = Nations.get(region.data.owner_id)
        if "Peacetime Recovery" in improvement_owner.completed_research and Wars.is_at_peace(improvement_owner.id):
            region.improvement.heal(1)

def heal_all():
    """
    Perform end of turn healing for eligible units and improvements.
    """
    heal_improvements()
    heal_units()
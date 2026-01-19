from app.nation.nations import Nations
from app.region.regions import Regions
from app.war.wars import Wars

def heal_units():
    pass

def heal_improvements():
    """
    Heals every improvement that is eligible to be healed.
    """
    
    for region in Regions:

        # do not heal unowned improvements (0) or improvements owned by an event player (99)
        if region.data.owner_id in ["0", "99"]:
            continue
        
        if region.improvement.name is None or region.improvement.health == 99:
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
from app.nation.nations import Nations
from app.region.regions import Regions
from app.war.wars import Wars

def heals() -> None:
    """
    Heals all units and defensive improvements by 2 health.
    """
    
    for region in Regions:
        
        if region.data.owner_id not in ["0", "99"]:

            nation_improvement = Nations.get(region.data.owner_id)

            # heal improvement
            if region.data.owner_id != "0" and region.improvement.name != None and region.improvement.health != 99:
                region.improvement.heal(2)
                if nation_improvement.id != "0" and "Peacetime Recovery" in nation_improvement.completed_research and Wars.is_at_peace(nation_improvement.id):
                    region.improvement.heal(100)
        
        if region.unit.name is not None and region.unit.owner_id not in ["0", "99"]:
            
            nation_unit = Nations.get(region.unit.owner_id)
            heal_allowed = False

            # check if unit is allowed to heal
            if region.unit.name == "Special Forces":
                heal_allowed = True
            elif "Scorched Earth" in nation_unit.completed_research:
                heal_allowed = True
            elif region.data.owner_id == region.unit.owner_id:
                heal_allowed = True
            else:
                for adjacent_region in region.graph.iter_adjacent_regions():
                    if adjacent_region.unit.owner_id == region.unit.owner_id:
                        heal_allowed = True

            # heal unit
            if heal_allowed:
                region.unit.heal(2)
                if nation_unit.id != "0" and "Peacetime Recovery" in nation_unit.completed_research and Wars.is_at_peace(nation_unit.id):
                    region.unit.heal(100)
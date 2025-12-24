from app.nation.nation import Nation
from app.region import Region
from app.war.war import War

from .strike import Strike
from .strike_standard import StandardStrike
from .strike_nuclear import NuclearStrike

def strike_factory(missile_type_str: str, nation: Nation, target_nation: Nation, target_region: Region, war: War) -> Strike:
    if missile_type_str == "Nuclear Missile":
        return NuclearStrike(nation, target_nation, target_region, war)
    return StandardStrike(nation, target_nation, target_region, war)

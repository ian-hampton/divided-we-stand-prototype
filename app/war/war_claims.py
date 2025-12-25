from app.scenario.scenario import ScenarioInterface as SD
from app.region.regions import Regions

class ManageWarClaims:

    def __init__(self, nation_name: str, war_justification: str):
        self.nation_name = nation_name
        self.justification = war_justification

    def validate_war_claims(self, region_claims_list: list[str]) -> int:
        """
        Helper function for get_war_claims().
        Calculates total cost of region claims and makes sure they are valid.

        Args:
            region_claims_list (list[str]): List of claimed region ids.

        Returns:
            int: Total cost of region claims.
        """

        region_id_set = set(Regions.ids())
        war_justification_data = SD.war_justificiations[self.justification]

        total = 0
        if not war_justification_data.has_war_claims:
            return 0

        for i, region_id in enumerate(region_claims_list):
            
            if region_id not in region_id_set:
                return -1
            
            if i + 1 > war_justification_data.max_claims:
                return -1
            
            if i + 1 > war_justification_data.free_claims:
                total += war_justification_data.claim_cost

        return total

    def get_war_claims(self) -> tuple[int, list]:
        """
        Fetch and validate war claims using the terminal.

        Returns:
            tuple: Total cost of war claims and list of those war claims.
        """
        
        claim_cost = -1
        
        while claim_cost == -1:
            region_claims_str = input(f"List the regions that {self.nation_name} is claiming using {self.justification}: ")
            region_claims_list = region_claims_str.split(',')
            claim_cost = self.validate_war_claims(self.justification, region_claims_list)
        
        return claim_cost, region_claims_list
    
    def claim_pairs(self, war_claims: list) -> dict:
        """
        Creates dict of region id - original owner id pairs.

        Args:
            war_claims (list): List of claimed region ids.

        Returns:
            dict: A dictionary of region id - original owner id pairs.
        """

        pairs = {}
        
        for region_id in war_claims:
            region = Regions.load(region_id)
            pairs[region_id] = region.data.owner_id

        return pairs
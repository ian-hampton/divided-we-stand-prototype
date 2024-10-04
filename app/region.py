import json

from app.improvement import Improvement

class Region:

    def __init__(self, region_id: str, game_id: str):
        
        # check if game id is valid
        regdata_filepath = f'gamedata/{game_id}/regdata.json'
        try:
            with open(regdata_filepath, 'r') as json_file:
                regdata_dict = json.load(json_file)
        except FileNotFoundError:
            print(f"Error: Unable to locate {regdata_filepath} during Region class initialization.")

        # check if region id is valid
        try:
            region_data = regdata_dict[region_id]["regionData"]
        except KeyError:
            print(f"Error: {region_id} not recognized during Region class initialization.")

        # set attributes now that all checks have passed
        self.region_id = region_id
        self.data = region_data
        self.game_id = game_id
        self.regdata_filepath = regdata_filepath
        self.claim_list = []
    
    def __eq__(self, other):
        '''
        Equality comparison.
        '''
        if isinstance(other, Region):
            return self.region_id == other.region_id
        return False

    def _save_changes(self) -> None:
        '''
        Saves changes made to Region object to game files.
        '''
        with open(self.regdata_filepath, 'r') as json_file:
            regdata_dict = json.load(json_file)
        regdata_dict[self.region_id]["regionData"] = self.data
        with open(self.regdata_filepath, 'w') as json_file:
            json.dump(regdata_dict, json_file, indent=4)

    def owner_id(self) -> int:
        '''
        Returns the player_id of the region owner.
        '''
        return self.data["ownerID"]
    
    def set_owner_id(self, new_owner_id: int) -> None:
        '''
        Changes the owner of a region.
        '''
        self.data["ownerID"] = new_owner_id
        self._save_changes()
    
    def occupier_id(self) -> int:
        '''
        Returns the player_id of the region occupier.
        '''
        return self.data["occupierID"]
    
    def set_occupier_id(self, new_owner_id: int) -> None:
        '''
        Changes the occupier of a region.
        '''
        self.data["occupierID"] = new_owner_id
        self._save_changes()

    def purchase_cost(self) -> int:
        '''
        Returns purchase cost of region.
        '''
        return self.data["purchaseCost"]
    
    def increase_purchase_cost(self, amount=5) -> None:
        '''
        Increases purchase cost of the region.
        Default value is 5 dollars.
        '''
        self.data["purchaseCost"] += amount
        self._save_changes()
    
    def resource(self) -> str:
        '''
        Returns resource present in region.
        '''
        return self.data["regionResource"]
    
    def set_resource(self, new_resource: str) -> None:
        '''
        Changes the resource in a region.
        '''
        self.data["regionResource"] = new_resource
        self._save_changes()

    def fallout(self) -> int:
        '''
        Returns the amount of remaining turns that a region is under the effects of a nuke.
        '''
        return self.data["nukeTurns"]
    
    def set_fallout(self, amount=4) -> None:
        '''
        Sets fallout amount. Default is 4 turns.
        '''
        self.data["nukeTurns"] = amount
        self._save_changes()
    
    def decrease_fallout(self) -> None:
        '''
        Decreases fallout by one turn.
        '''
        self.data["nukeTurns"] -= 1
        self._save_changes()
    
    def is_edge(self) -> bool:
        '''
        Returns True if region is on the edge of the map.
        '''
        return self.data["edgeOfMap"]
    
    def is_significant(self) -> bool:
        '''
        Returns True if region contains a regional capital city.
        '''
        return self.data["containsRegionalCapital"]

    def adjacent_regions(self) -> list:
        '''
        Returns the region_ids of adjacent regions.
        '''
        return self.data["adjacencyList"]
    
    def add_claim(self, player_id: int) -> None:
        '''
        Adds player id to claim list.
        Used for region purchase action.
        '''
        self.claim_list.append(player_id)

    def get_claim_list(self) -> list:
        '''
        Returns list of player_ids claiming this region.
        Used for region purchase action.
        '''
        return self.claim_list

    # basic methods
    ################################################################################

    def owned_adjacent_regions(self) -> list:
        '''
        Returns the region_ids of adjacent regions owned by the player.
        '''
        adjacent_list = self.adjacent_regions()
        owned_adjacent_list = []
        for region_id in adjacent_list:
            temp = Region(region_id, self.game_id)
            if temp.owner_id() == self.owner_id():
                owned_adjacent_list.append(region_id)
        return owned_adjacent_list

    def get_regions_in_radius(self, radius: int) -> set:
        '''
        Returns a set of region_ids for all regions within a given radius of this region.
        The set includes the original region.
        '''
        regions_in_radius = set([self.region_id])
        for i in range(0, radius):
            new_regions_in_radius = set()
            for region_id in regions_in_radius:
                region = Region(region_id, self.game_id)
                new_regions_in_radius.update(region.adjacent_regions())
            regions_in_radius.update(new_regions_in_radius)
        return regions_in_radius
    
    def check_for_adjacent_improvement(self, improvement_names: set) -> bool:
        '''
        Checks if there is an improvement in improvement_names in an owned adjacent region.
        
        :param improvement_names: A set of improvement names.
        :return: True if improvement found. False otherwise.
        '''
        owned_adjacent_list = self.owned_adjacent_regions()
        for region_id in owned_adjacent_list:
            region_improvement = Improvement(region_id, self.game_id)
            if region_improvement.name() in improvement_names:
                return True

        return False
    
    # event specific methods
    ################################################################################

    def infection(self) -> int:
        '''
        Returns infection score of region.
        Used for Pandemic event.
        '''
        return self.data["infection"]
    
    def add_infection(self, amount=1) -> int:
        '''
        Increases infection score of region.
        Used for Pandemic event.
        '''
        self.data["infection"] += amount
        if self.data["infection"] > 10:
            self.data["infection"] = 10
        elif self.data["infection"] < 0:
            self.data["infection"] = 0
        self._save_changes()
    
    def is_quarantined(self) -> bool:
        '''
        Returns True if region is quarantined.
        Used for Pandemic event.
        '''
        return self.data["quarantine"]
    
    def set_quarantine(self, enable=True) -> None:
        '''
        Toggles region. quarantine
        Used for Pandemic event.
        '''
        self.data["quarantine"] = enable
        self._save_changes()

    
        
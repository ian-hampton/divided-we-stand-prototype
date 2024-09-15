import json

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
    
    def occupier_id(self) -> int:
        '''
        Returns the player_id of the region occupier.
        '''
        return self.data["occupierID"]
    
    def fallout(self) -> int:
        '''
        Returns the amount of remaining turns that a region is under the effects of a nuke.
        '''
        return self.data["nukeTurns"]
    
    def resource(self) -> str:
        '''
        Returns resource present in region.
        '''
        return self.data["regionResource"]
    
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
    
    def infection(self) -> int:
        '''
        Returns infection score of region.
        Used for Pandemic event.
        '''
        return self.data["infection"]
    
    def is_quarantined(self) -> bool:
        '''
        Returns True if region is quarantined.
        Used for Pandemic event.
        '''
        return self.data["quarantine"]

    def set_owner_id(self, new_owner_id: int) -> None:
        '''
        Changes the owner of a region.
        '''
        self.data["ownerID"] = new_owner_id
        self._save_changes()

    def set_resource(self, new_resource: str) -> None:
        '''
        Changes the resource in a region.
        '''
        self.data["regionResource"] = new_resource
        self._save_changes()

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
        
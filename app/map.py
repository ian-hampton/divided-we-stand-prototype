import json
import random

from PIL import Image, ImageDraw

from app import core
from app import palette
from app.region import Region
from app.improvement import Improvement
from app.unit import Unit
from app.nationdata import NationTable

class GameMaps:
    
    """Class used for generating and updating map images."""

    def __init__(self, game_id: str):

        self.game_id = game_id
        self.map_str = core.get_map_str(self.game_id)
        self.turn_num: any = core.get_current_turn_num(self.game_id)    # TODO: game state needs to be tracked independently instead of relying on current turn #
        with open(f"maps/{self.map_str}/config.json", 'r') as json_file:
            self.map_config_dict = json.load(json_file)

    def update_all(self) -> None:
        """
        """
        pass

    def populate_main_map(self) -> None:
        """
        Spawns random improvements on random regions. Should only be called at the start of the game.
        """
        
        # get game data
        nation_table = NationTable(self.game_id)
        improvement_data_dict = core.get_scenario_dict(self.game_id, "Improvements")
        with open(f'gamedata/{self.game_id}/regdata.json', 'r') as json_file:
            regdata_dict = json.load(json_file)
        region_id_list = list(regdata_dict.keys())
        
        # get list of improvements that can spawn
        improvement_candidates_list = []
        DO_NOT_SPAWN = {'Capital', 'Military Base', 'Missile Defense Network', 'Missile Silo', 'Oil Refinery', 'Research Institute', 'Surveillance Center', 'Nuclear Power Plant'}
        for improvement_name in improvement_data_dict:
            if improvement_data_dict[improvement_name]['Required Resource'] == None and improvement_name not in DO_NOT_SPAWN:
                improvement_candidates_list.append(improvement_name)
        
        # place improvements randomly
        count = 0
        placement_quota = 2 * len(nation_table)
        while count < placement_quota and len(region_id_list) != 0:
            random_region_id = random.choice(region_id_list)
            region_id_list.remove(random_region_id)
            random_region = Region(random_region_id, self.game_id)
            random_region_improvement = Improvement(random_region_id, self.game_id)
            
            # improvement cannot be spawned in a region already taken
            if random_region_improvement.name != None:
                continue
           
            # no uranium mines and ree mines may spawn randomly at the start of the game
            if random_region.resource == 'Rare Earth Elements':
                continue
            
            # there cannot be other improvements within a radius of two regions
            nearby_improvement_found = False
            for region_id in random_region.get_regions_in_radius(2):
                temp = Improvement(region_id, self.game_id)
                if temp.name != None:
                    nearby_improvement_found = True
                    break
            if nearby_improvement_found:
                continue
            
            # place improvement
            count += 1
            match random_region.resource:
                case 'Coal':
                    random_region_improvement.set_improvement('Coal Mine')
                case 'Oil':
                    random_region_improvement.set_improvement('Oil Well')
                case 'Basic Materials':
                    random_region_improvement.set_improvement('Industrial Zone')
                case 'Common Metals':
                    random_region_improvement.set_improvement('Common Metals Mine')
                case 'Advanced Metals':
                    random_region_improvement.set_improvement('Advanced Metals Mine')
                case 'Uranium':
                    random_region_improvement.set_improvement('Uranium Mine')
                case _:
                    capital_roll = 0
                    if random_region.is_significant:
                        capital_roll = random.randint(1, 6)
                    if capital_roll <= 2:
                        improvement_name = random.sample(improvement_candidates_list, 1)[0]
                        improvement_health = improvement_data_dict[improvement_name]["Health"]
                        if improvement_health == 99:
                            random_region_improvement.set_improvement(improvement_name)
                        else:
                            random_region_improvement.set_improvement(improvement_name, 1)
                    else:
                        random_region_improvement.set_improvement('Capital', 1)

    def populate_resource_map(self) -> None:
        """
        Assigns a resource to each map region. Should only be called at the start of the game.
        """
        
        # create resource list
        resource_list = []
        for resource, resource_count in self.map_config_dict["resourceCounts"].items():
            resource_list += [resource] * resource_count
        resource_list = random.sample(resource_list, len(resource_list))

        # update regdata.json
        with open(f"gamedata/{self.game_id}/regdata.json", 'r') as json_file:
            regdata_dict = json.load(json_file)
        for region_id in regdata_dict:
            region = Region(region_id, self.game_id)
            region.set_resource(resource_list.pop())

    def _init_images(self) -> None:
        
        image_resources_filepath = f"app/static/images/map_images/{self.map_str}/image_resources"
        self.filepath_background = f"{image_resources_filepath}/background.png"
        self.filepath_magnified = f"{image_resources_filepath}/magnified.png"
        self.filepath_main = f"{image_resources_filepath}/main.png"
        self.filepath_text = f"{image_resources_filepath}/text.png"
        
        self.main_map = Image.open(self.filepath_main).convert("RGBA")
        self.resource_map = Image.open(self.filepath_main).convert("RGBA")
        self.control_map = Image.open(self.filepath_main).convert("RGBA")
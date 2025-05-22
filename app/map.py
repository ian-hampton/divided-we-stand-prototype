import json
import random

from PIL import Image, ImageDraw, ImageFont

from app import core
from app import palette
from app.region import Region
from app.improvement import Improvement
from app.unit import Unit
from app.nationdata import NationTable


MAP_OPACITY = 0.75
DO_NOT_SPAWN = {'Capital', 'Military Base', 'Missile Defense Network', 'Missile Silo', 'Oil Refinery',
                'Research Institute', 'Surveillance Center', 'Nuclear Power Plant'}

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
        Exports updated maps to game files.
        """
        
        # get game data
        nation_table = NationTable(self.game_id)
        improvement_data_dict = core.get_scenario_dict(self.game_id, "Improvements")
        unit_data_dict = core.get_scenario_dict(self.game_id, "Units")
        with open(f'gamedata/{self.game_id}/regdata.json', 'r') as json_file:
            regdata_dict = json.load(json_file)

        # initialize map images
        self._init_images()

        for region_id in regdata_dict:
            region = Region(region_id, self.game_id)
            improvement = Improvement(region_id, self.game_id)

            # color region using ownership
            fill_color = self._get_fill_color(nation_table, region)
            if fill_color is not None:
                if not region.is_magnified:
                    x = improvement.coords[0] + 25
                    y = improvement.coords[1] + 25
                    ImageDraw.floodfill(self.main_map, (x, y), fill_color, border=(0, 0, 0, 255))
                    ImageDraw.floodfill(self.control_map, (x, y), fill_color, border=(0, 0, 0, 255))
                for coords in region.additional_region_coordinates:
                    ImageDraw.floodfill(self.main_map, tuple(coords), fill_color, border=(0, 0, 0, 255))
                    ImageDraw.floodfill(self.control_map, tuple(coords), fill_color, border=(0, 0, 0, 255))
            
            # color region using resource
            if region.resource != "Empty":
                fill_color = palette.resource_colors[region.resource]
                if not region.is_magnified:
                    x = improvement.coords[0] + 25
                    y = improvement.coords[1] + 25
                    coords = (x, y)
                    ImageDraw.floodfill(self.resource_map, coords, fill_color, border=(0, 0, 0, 255))
                for coords in region.additional_region_coordinates:
                    ImageDraw.floodfill(self.resource_map, tuple(coords), fill_color, border=(0, 0, 0, 255))

            # apply background texture
            background_img = Image.open(self.filepath_background)
            background_img = background_img.convert("RGBA")
            self.main_map = Image.blend(background_img, self.main_map, MAP_OPACITY)
            self.resource_map = Image.blend(background_img, self.resource_map, MAP_OPACITY)
            self.control_map = Image.blend(background_img, self.control_map, MAP_OPACITY)

            # magnified regions
            magnified_img = Image.open(self.filepath_magnified)
            self.main_map = Image.alpha_composite(self.main_map, magnified_img)
            for region_id in regdata_dict:
                region = Region(region_id, self.game_id)
                improvement = Improvement(region_id, self.game_id)

                # skip non-magnified or unclaimed
                fill_color = self._get_fill_color(nation_table, region)
                if not region.is_magnified or fill_color is None:
                    continue

                # color magnified box using ownership
                x = improvement.coords[0] + 25
                y = improvement.coords[1] + 25
                ImageDraw.floodfill(self.main_map, (x, y), fill_color, border=(0, 0, 0, 255))
                x = improvement.coords[0] + 55
                ImageDraw.floodfill(self.main_map, (x, y), fill_color, border=(0, 0, 0, 255))
                x = improvement.coords[0] + 70
                ImageDraw.floodfill(self.main_map, (x, y), fill_color, border=(0, 0, 0, 255))

            # add text
            text_img = Image.open(self.filepath_text)
            self.resource_map = Image.alpha_composite(self.resource_map, text_img)
            self.control_map = Image.alpha_composite(self.control_map, text_img)

            # place units and improvements
            for region_id in regdata_dict:
                region = Region(region_id, self.game_id)
                improvement = Improvement(region_id, self.game_id)
                unit = Unit(region_id, self.game_id)
                
                if unit.name is not None:
                    
                    # place unit image
                    nation = nation_table.get(str(region.occupier_id))
                    fill_color = palette.hex_to_tup(nation.color, alpha=True)
                    unit_img = Image.open(self.filepath_unit_back)
                    ImageDraw.floodfill(unit_img, (1, 1), fill_color, border=(0, 0, 0, 255))

                    # place unit symbol
                    fill_color = palette.normal_to_occupied[nation.color]
                    fill_color = palette.hex_to_tup(fill_color, alpha=True)
                    symb_back_img = Image.open(self.filepath_unit_symb_back)
                    ImageDraw.floodfill(symb_back_img, (1, 1), fill_color, border=(0, 0, 0, 255))
                    symb_img = Image.open(f"{self.images_filepath}/units/{unit.name.lower()}.png")
                    symb_img = Image.alpha_composite(symb_img, symb_back_img)
                    unit_img.paste(symb_img, (9, 16))

                    # place unit name
                    font = ImageFont.truetype("app/fonts/LeelawUI.ttf", size=12)
                    ImageDraw.Draw(unit_img).text(xy=(24, 4), text=unit.abbrev(), fill=(0, 0, 0, 255), font=font, align="center")

                    # place unit health
                    max_health = unit_data_dict[unit.name]["Health"]
                    ImageDraw.Draw(unit_img).text(xy=(24, 35), text=f"{unit.health}/{max_health}", fill=(0, 0, 0, 255), font=font, align="center")
                    
                    # place unit on map
                    x = unit.coords[0]
                    y = unit.coords[1]
                    self.main_map.paste(unit_img, (x, y))

                if region.fallout:
                    # place nuclear explosion
                    # TODO: make shadow blend properly
                    mask = self.nuke_img.split()[3]
                    self.main_map.paste(self.nuke_img, improvement.coords, mask)
                    continue
            
                if improvement.name is not None:
                    
                    # place improvement image
                    pass
                    
                    # place improvement health
                    pass

            # save images
            match self.turn_num:
                case "Starting Region Selection in Progress" | "Nation Setup in Progress":
                    self.main_map.save(f"gamedata/{self.game_id}/images/0.png")
                case _:
                    self.main_map.save(f"gamedata/{self.game_id}/images/{self.turn_num - 1}.png")
            self.resource_map.save(f"gamedata/{self.game_id}/images/resourcemap.png")
            self.control_map.save(f"gamedata/{self.game_id}/images/controlmap.png")

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
        
        map_images_filepath = f"app/static/images/map_images/{self.map_str}/image_resources"
        self.filepath_background = f"{map_images_filepath}/background.png"
        self.filepath_magnified = f"{map_images_filepath}/magnified.png"
        self.filepath_main = f"{map_images_filepath}/main.png"
        self.filepath_text = f"{map_images_filepath}/text.png"
        
        self.main_map = Image.open(self.filepath_main).convert("RGBA")
        self.resource_map = Image.open(self.filepath_main).convert("RGBA")
        self.control_map = Image.open(self.filepath_main).convert("RGBA")

        self.images_filepath = "app/static/images"
        self.filepath_unit_back = f"{self.images_filepath}/units/back.png"
        self.filepath_unit_symb_back = f"{self.images_filepath}/units/back_symb.png"
        self.nuke_img = Image.open(f"{self.images_filepath}/nuke.png")

    def _get_fill_color(self, nation_table: NationTable, region: Region) -> tuple | None:
        
        if region.occupier_id != 0:
            nation = nation_table.get(str(region.occupier_id))
            fill_color = palette.normal_to_occupied[nation.color]
            return palette.hex_to_tup(fill_color, alpha=True)
        
        if region.owner_id != 0:
            nation = nation_table.get(str(region.owner_id))
            return palette.hex_to_tup(nation.color, alpha=True)
        
        return None
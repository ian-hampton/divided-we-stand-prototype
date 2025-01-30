# STANDARD IMPORTS
import csv
from datetime import datetime
import json
import random

# ENVIROMENT IMPORTS
from PIL import Image, ImageDraw

# GAME IMPORTS
from app import core
from app.region import Region
from app.improvement import Improvement
from app.unit import Unit


class MainMap:

    """Creates and updates the main map for Divided We Stand games."""

    def __init__(self, game_id: str, map_name: str, current_turn_num):
        self.game_id = game_id
        self.map_name = map_name
        self.turn_num = current_turn_num

    def place_random(self) -> None:
        """
        This function populates the map with random improvements.
        """
        
        # get filepaths and lists
        playerdata_location = f'gamedata/{self.game_id}/playerdata.csv'
        playerdata_list = core.read_file(playerdata_location, 1)
        with open(f'gamedata/{self.game_id}/regdata.json', 'r') as json_file:
            regdata_dict = json.load(json_file)
        region_id_list = list(regdata_dict.keys())
        EXCLUSION_SET = {'Capital', 'Military Base', 'Missile Defense Network', 'Missile Silo', 'Oil Refinery', 'Research Institute', 'Surveillance Center', 'Nuclear Power Plant'}
        improvement_candidates_list = []
        improvement_data_dict = core.get_scenario_dict(self.game_id, "Improvements")
        for improvement_name in improvement_data_dict:
            if improvement_data_dict[improvement_name]['Required Resource'] == None and improvement_name not in EXCLUSION_SET:
                improvement_candidates_list.append(improvement_name)
        
        # place improvements randomly
        count = 0
        placement_quota = 2 * len(playerdata_list)
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
                region_improvement = Improvement(region_id, self.game_id)
                if region_improvement.name != None:
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
    
    def update(self) -> None:
        """
        Updates the main map.
        """

        print("Updating main map...")
        
        # get filepaths
        playerdata_location = f'gamedata/{self.game_id}/playerdata.csv'
        match self.turn_num:
            case "Starting Region Selection in Progress" | "Nation Setup in Progress":
                main_map_save_location = f'gamedata/{self.game_id}/images/0.png'
            case _:
                main_map_save_location = f'gamedata/{self.game_id}/images/{self.turn_num - 1}.png'
        map_str = get_map_str(self.map_name)
        image_resources_filepath = f"app/static/images/map_images/{map_str}/image_resources"
        background_filepath = f"{image_resources_filepath}/background.png"
        magnified_filepath = f"{image_resources_filepath}/magnified.png"
        main_filepath = f"{image_resources_filepath}/main.png"
        text_filepath = f"{image_resources_filepath}/text.png"
        texture_filepath = f"{image_resources_filepath}/texture.png"
        
        
        # get game data
        playerdata_list = core.read_file(playerdata_location, 1)
        nation_info_masterlist = core.get_nation_info(playerdata_list)
        player_color_list = generate_player_color_list(playerdata_location)
        improvement_data_dict = core.get_scenario_dict(self.game_id, "Improvements")
        unit_data_dict = core.get_scenario_dict(self.game_id, "Units")
        with open('active_games.json', 'r') as json_file:
            active_games_dict = json.load(json_file)
        with open(f'gamedata/{self.game_id}/regdata.json', 'r') as json_file:
            regdata_dict = json.load(json_file)
        

        # Color Regions in Map Image
        main_image = Image.open(main_filepath)
        main_image = main_image.convert("RGBA")
        for region_id in regdata_dict:
            region = Region(region_id, self.game_id)
            region_improvement = Improvement(region_id, self.game_id)
            # only color a region if it is owned or occupied
            if region.owner_id  != 0 or region.occupier_id != 0:
                cord_x = (region_improvement.cords[0] + 25)
                cord_y = (region_improvement.cords[1] + 25)
                start_cords_updated = (cord_x, cord_y)
                if region.cords is not None:
                    start_cords_updated = region.cords
                map_color_fill(region.owner_id, region.occupier_id, player_color_list, region_id, start_cords_updated, main_image, self.game_id, active_games_dict)
        
        # add texture and background to temp image
        if map_str == "united_states":
            main_image = apply_textures_old(main_image, texture_filepath, background_filepath)
        else:
            main_image = apply_textures(main_image, background_filepath)
       
        # add magnified regions
        magnified_image = Image.open(magnified_filepath)
        main_image = Image.alpha_composite(main_image, magnified_image)
       
        # color magnified regions
        for region_id in regdata_dict:
            region = Region(region_id, self.game_id)
            region_improvement = Improvement(region_id, self.game_id)
            if region.cords is not None and (region.owner_id != 0 or region.occupier_id != 0):
                fill_color = determine_region_color(region.owner_id, region.occupier_id, player_color_list, self.game_id, active_games_dict)
                cord_x = (region_improvement.cords[0] + 25)
                cord_y = (region_improvement.cords[1] + 25)
                improvement_box_start_cords = (cord_x, cord_y)
                cord_x = (region_improvement.cords[0] + 55)
                cord_y = (region_improvement.cords[1] + 25)
                main_box_start_cords = (cord_x, cord_y)
                cord_x = (region_improvement.cords[0] + 70)
                cord_y = (region_improvement.cords[1] + 25)
                unit_box_start_cords = (cord_x, cord_y)
                ImageDraw.floodfill(main_image, improvement_box_start_cords, fill_color, border=(0, 0, 0, 255))
                ImageDraw.floodfill(main_image, main_box_start_cords, fill_color, border=(0, 0, 0, 255))
                ImageDraw.floodfill(main_image, unit_box_start_cords, fill_color, border=(0, 0, 0, 255))
        

        # Place Improvements
        main_image = main_image.convert("RGBA")
        nuke_image = Image.open('app/static/images/nuke.png')
        for region_id in regdata_dict:
            region = Region(region_id, self.game_id)
            region_improvement = Improvement(region_id, self.game_id)
            nuke = region.fallout
            # place nuclear explosion
            if nuke:
                mask = nuke_image.split()[3]
                main_image.paste(nuke_image, region_improvement.cords, mask)
                continue
            # check for fautasian bargan case lease
            if "Faustian Bargain" in active_games_dict[self.game_id]["Active Events"]:
                if region_id in active_games_dict[self.game_id]["Active Events"]["Faustian Bargain"]["Leased Regions List"]:
                    print(region_id)
                    lease_filepath = 'app/static/images/lease.png'
                    lease_image = Image.open(lease_filepath)
                    mask = lease_image.split()[3]
                    main_image.paste(lease_image, region_improvement.cords, mask)
                    continue
            # place improvement if present
            if region_improvement.name is not None:
                # place improvement image
                improvement_filepath = f'app/static/images/improvements/{region_improvement.name}.png'
                improvement_image = Image.open(improvement_filepath)
                main_image.paste(improvement_image, region_improvement.cords)
                # place improvement health
                if region_improvement.health != 99:
                    cord_x = (region_improvement.cords[0] - 13)
                    cord_y = (region_improvement.cords[1] + 54)
                    health_start_cords = (cord_x, cord_y)
                    ten_health_improvements = set()
                    for improvement_name, improvement_dict in improvement_data_dict.items():
                        if improvement_dict["Health"] == 10:
                            ten_health_improvements.add(improvement_name)
                    if region_improvement.name in ten_health_improvements:
                        health_filepath = f'app/static/images/health/{region_improvement.health}-10.png'
                    else:
                        health_filepath = f'app/static/images/health/{region_improvement.health}-5.png'
                    health_image = Image.open(health_filepath)
                    main_image.paste(health_image, health_start_cords)
        

        # Place Units
        for region_id in regdata_dict:
            region_improvement = Improvement(region_id, self.game_id)
            region_unit = Unit(region_id, self.game_id)
            # get cords of unit if present
            if region_unit.name is not None:
                if region_unit.cords is None:
                    # unit placement is the standard 15 pixels to the right of improvement
                    cord_x = (region_improvement.cords[0] + 65)
                    cord_y = (region_improvement.cords[1])
                    unit_cords = (cord_x, cord_y)
                else:
                    # unit placement is custom
                    cord_x = (region_unit.cords[0])
                    cord_y = (region_unit.cords[1] - 20)
                    unit_cords = (cord_x, cord_y)
                # get unit color
                if region_unit.owner_id != 0 and region_unit.owner_id != 99:
                    player_color_str = nation_info_masterlist[region_unit.owner_id - 1][1]
                elif region_unit.owner_id == 0 and "Foreign Invasion" in active_games_dict[self.game_id]["Active Events"]:
                    player_color_str = active_games_dict[self.game_id]["Active Events"]["Foreign Invasion"]["Invasion Color"]
                unit_filepath = f'app/static/images/units/{region_unit.abbrev()}{player_color_str}.png'
                # place unit
                unit_image = Image.open(unit_filepath)
                mask = unit_image.split()[3]
                main_image.paste(unit_image, unit_cords, mask)
                # place unit health
                health_filepath = f"app/static/images/health/U{region_unit.health}-{unit_data_dict[region_unit.name]['Health']}.png"
                health_image = Image.open(health_filepath)
                health_temp = Image.new("RGBA", main_image.size)
                mask = health_image.split()[3]
                health_temp.paste(health_image, unit_cords, mask)
                main_image = Image.alpha_composite(main_image, health_temp)
        
        main_image.save(main_map_save_location)


class ResourceMap:
    
    """Creates and updates the resource map for Divided We Stand games."""

    def __init__(self, game_id: str, map_name: str):
        self.game_id = game_id
        self.map_name = map_name

    def create(self) -> None:
        """
        Populates regdata.json with resource map data.
        """
        
        # get map info
        map_str = get_map_str(self.map_name)
        map_config_filepath = f"maps/{map_str}/map_config.json"
        with open(map_config_filepath, 'r') as json_file:
            map_config_dict = json.load(json_file)
        
        # create resource list
        resource_list = []
        for resource, resource_count in map_config_dict["resourceCounts"].items():
            resource_list += [resource] * resource_count
        resource_list = random.sample(resource_list, len(resource_list))
        
        # update regdata.json
        with open(f'gamedata/{self.game_id}/regdata.json', 'r') as json_file:
            regdata_dict = json.load(json_file)
        for i, region_id in enumerate(regdata_dict):
            region = Region(region_id, self.game_id)
            region.set_resource(resource_list[i])

    def update(self) -> None:
        """
        Updates the resource map.
        """

        print("Updating resource map...")

        # get filepaths
        map_str = get_map_str(self.map_name)
        resource_map_save_location = f'gamedata/{self.game_id}/images/resourcemap.png'
        image_resources_filepath = f"app/static/images/map_images/{map_str}/image_resources"
        background_filepath = f"{image_resources_filepath}/background.png"
        magnified_filepath = f"{image_resources_filepath}/magnified.png"
        main_filepath = f"{image_resources_filepath}/main.png"
        text_filepath = f"{image_resources_filepath}/text.png"
        texture_filepath = f"{image_resources_filepath}/texture.png"
        
        # get game data
        with open(f'gamedata/{self.game_id}/regdata.json', 'r') as json_file:
            regdata_dict = json.load(json_file)
        
        # color regions
        main_image = Image.open(main_filepath)
        main_image = main_image.convert("RGBA")
        for region_id in regdata_dict:
            region = Region(region_id, self.game_id)
            region_improvement = Improvement(region_id, self.game_id)
            # if region has a resource color it
            if region.resource != 'Empty':
                cord_x = (region_improvement.cords[0] + 25)
                cord_y = (region_improvement.cords[1] + 25)
                start_cords_updated = (cord_x, cord_y)
                if region.cords is not None:
                    start_cords_updated = region.cords
                main_image = silly_placeholder(main_image, region_id, core.resource_colors[region.resource])
                ImageDraw.floodfill(main_image, start_cords_updated, core.resource_colors[region.resource], border=(0, 0, 0, 255))
        
        # add background textures and text
        if map_str == "united_states":
            main_image = apply_textures_old(main_image, texture_filepath, background_filepath)
        else:
            main_image = apply_textures(main_image, background_filepath)
        main_image = text_over_map_new(main_image, text_filepath)
        
        main_image.save(resource_map_save_location)


class ControlMap:

    """Creates and updates the control map for Divided We Stand games."""

    def __init__(self, game_id: str, map_name: str):
        self.game_id = game_id
        self.map_name = map_name

    def update(self) -> None:
        """
        Updates the control map.
        """

        print("Updating control map...")
        
        # get map data
        map_str = get_map_str(self.map_name)
        control_map_save_location = f'gamedata/{self.game_id}/images/controlmap.png'
        image_resources_filepath = f"app/static/images/map_images/{map_str}/image_resources"
        background_filepath = f"{image_resources_filepath}/background.png"
        magnified_filepath = f"{image_resources_filepath}/magnified.png"
        main_filepath = f"{image_resources_filepath}/main.png"
        text_filepath = f"{image_resources_filepath}/text.png"
        texture_filepath = f"{image_resources_filepath}/texture.png"
       
        # get game data
        playerdata_location = f'gamedata/{self.game_id}/playerdata.csv'
        player_color_list = generate_player_color_list(playerdata_location)
        with open('active_games.json', 'r') as json_file:
            active_games_dict = json.load(json_file)
        with open(f'gamedata/{self.game_id}/regdata.json', 'r') as json_file:
            regdata_dict = json.load(json_file)

        # color regions
        main_image = Image.open(main_filepath)
        main_image = main_image.convert("RGBA")
        for region_id in regdata_dict:
            region = Region(region_id, self.game_id)
            region_improvement = Improvement(region_id, self.game_id)
            # only color region if it is owned or occupied
            if region.owner_id != 0 or region.occupier_id != 0:
                cord_x = (region_improvement.cords[0] + 25)
                cord_y = (region_improvement.cords[1] + 25)
                start_cords_updated = (cord_x, cord_y)
                if region.cords is not None:
                    start_cords_updated = region.cords
                map_color_fill(region.owner_id, region.occupier_id, player_color_list, region_id, start_cords_updated, main_image, self.game_id, active_games_dict)
        
        # add background textures and text
        if map_str == "united_states":
            main_image = apply_textures_old(main_image, texture_filepath, background_filepath)
        else:
            main_image = apply_textures(main_image, background_filepath)
        main_image = text_over_map_new(main_image, text_filepath)
        
        main_image.save(control_map_save_location)


def generate_player_color_list(playerdata_location: str) -> list:
    """
    Gets a list of all player colors in RGB form.

    Params:
        playerdata_location (str): Filepath to playerdata.csv.
    """

    player_color_list = []

    with open(playerdata_location, 'r') as file:
        reader = csv.reader(file)
        next(reader,None)
        for row in reader:
            if row != []:
                player_color_hex = row[2]
                player_color_rgb = core.player_colors_conversions[player_color_hex]
                player_color_list.append(player_color_rgb)

    return player_color_list

def map_color_fill(owner_id: int, occupier_id: int, player_color_list: list, region_id: str, start_cords_updated: tuple, main_image: Image, full_game_id: str, active_games_dict: dict) -> None:
    """
    Determines what fill color to use for main map and control map generation, depending on region ownership and occupation.
    """

    fill_color = determine_region_color(owner_id, occupier_id, player_color_list, full_game_id, active_games_dict)
    main_image = silly_placeholder(main_image, region_id, fill_color)
    ImageDraw.floodfill(main_image, start_cords_updated, fill_color, border=(0, 0, 0, 255))

def determine_region_color(owner_id: int, occupier_id: int, player_color_list: list, full_game_id: str, active_games_dict: dict) -> tuple:
    """
    Cheap solution for determing region color.
    Future Ian if you allow this code to survive the next refactoring I will strangle you.
    """
    
    if owner_id != 99:
        fill_color = player_color_list[owner_id - 1]
    elif owner_id == 99 and "Foreign Invasion" in active_games_dict[full_game_id]["Active Events"]:
        fill_color = active_games_dict[full_game_id]["Active Events"]["Foreign Invasion"]["Invasion Color"]
        fill_color = core.player_colors_conversions[fill_color]
    if occupier_id != 0 and occupier_id != 99:
        fill_color = player_color_list[occupier_id -1]
        fill_color = core.player_colors_normal_to_occupied[fill_color]
    elif occupier_id == 99 and "Foreign Invasion" in active_games_dict[full_game_id]["Active Events"]:
        fill_color = active_games_dict[full_game_id]["Active Events"]["Foreign Invasion"]["Invasion Color"]
        fill_color = core.player_colors_conversions[fill_color]
        fill_color = core.player_colors_normal_to_occupied[fill_color]
        
    return fill_color

def apply_textures_old(main_image: Image, texture_filepath: str, background_filepath: str) -> Image:
    """
    Overlays the map image onto the textured background.

    Params:
        main_image (Image): Map image.
        texture_filepath (str): Filepath to land texture image.
        background_filepath (str): Filepath to background image (texture + water).

    Returns:
        Image: Map image.
    """
    
    texture_image = Image.open(texture_filepath)
    temp_image = Image.blend(texture_image, main_image, 0.75)
    main_image = temp_image

    background_image = Image.open(background_filepath)
    background_image = background_image.convert("RGBA")
    mask = main_image.split()[3]
    background_image.paste(main_image, (0,0), mask)
    main_image = background_image

    return main_image

def text_over_map_new(main_image: Image, text_filepath: str) -> Image:
    """
    Overlays text layer onto the map image.

    Params:
        main_image (Image): Map image.
        texture_filepath (str): Filepath to text image.

    Returns:
        Image: Map image.
    """

    text_image = Image.open(text_filepath)
    main_image = Image.alpha_composite(main_image, text_image)

    return main_image

def get_map_str(proper_map_name: str) -> str:
    
    match proper_map_name:
        case "United States 2.0":
            map_name_str = "united_states"
        case "China 2.0":
            map_name_str = "china"
        case _:
            map_name_str = 'united_states'

    return map_name_str

def apply_textures(main_image: Image, background_filepath: str) -> Image:
    """
    """

    background_image = Image.open(background_filepath)
    background_image = background_image.convert("RGBA")
    main_image = Image.blend(background_image, main_image, 0.75)

    return main_image

def silly_placeholder(main_image, region_id, fill_color):
    # to do - move this hardcoded crap to the regdata.json file
    match region_id:
        case "HAMPT":
            ImageDraw.floodfill(main_image, (4430, 1520), fill_color, border=(0, 0, 0, 255))
        case "ZHANJ":
            ImageDraw.floodfill(main_image, (4200, 4521), fill_color, border=(0, 0, 0, 255))
        case "YANGJ":
            ImageDraw.floodfill(main_image, (4369, 4432), fill_color, border=(0, 0, 0, 255))
        case "GUANG":
            ImageDraw.floodfill(main_image, (4548, 4255), fill_color, border=(0, 0, 0, 255))
            ImageDraw.floodfill(main_image, (4559, 4274), fill_color, border=(0, 0, 0, 255))
        case "NINGD":
            ImageDraw.floodfill(main_image, (5270, 3659), fill_color, border=(0, 0, 0, 255))
            ImageDraw.floodfill(main_image, (5254, 3675), fill_color, border=(0, 0, 0, 255))
        case "NINGB":
            ImageDraw.floodfill(main_image, (5441, 3178), fill_color, border=(0, 0, 0, 255))
        case "YANGZ":
            ImageDraw.floodfill(main_image, (5147, 2952), fill_color, border=(0, 0, 0, 255))
        case "SHANG":
            ImageDraw.floodfill(main_image, (5345, 2990), fill_color, border=(0, 0, 0, 255))
        case "YONGJ":
            ImageDraw.floodfill(main_image, (5375, 3450), fill_color, border=(0, 0, 0, 255))
        case "HONGK":
            ImageDraw.floodfill(main_image, (4659, 4302), fill_color, border=(0, 0, 0, 255))
            ImageDraw.floodfill(main_image, (4609, 4327), fill_color, border=(0, 0, 0, 255))
            ImageDraw.floodfill(main_image, (4643, 4322), fill_color, border=(0, 0, 0, 255))
    return main_image
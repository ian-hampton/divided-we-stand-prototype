import json
import random

from PIL import Image, ImageDraw, ImageFont

from app import palette
from app.game.games import Games
from app.game.game import GameStatus
from app.scenario.scenario import ScenarioInterface as SD
from app.nation.nations import Nations
from app.region.region import Region
from app.region.regions import Regions

MAP_OPACITY = 0.75
DO_NOT_SPAWN = {"Capital", "City", "Colony", "Military Base", "Missile Defense System", "Missile Silo",
                "Nuclear Power Plant", "Research Institute", "Solar Farm", "Surveillance Center"}

class GameMaps:
    """
    Class used for generating and updating map images.

    Important methods:
        update_all() - updates all maps and exports them as images
        populate_main_map() - spawns random improvements on random regions
        populate_resource_map() - handles resource generation
    """

    def __init__(self, game_id: str):

        game = Games.load(game_id)

        self.game_id = game_id
        self.map_str = game.get_map_string()
        with open(f"maps/{self.map_str}/config.json", 'r') as json_file:
            self.map_config: dict = json.load(json_file)

    def _get_fill_color(self, region: Region) -> tuple | None:
    
        if region.data.occupier_id != "0":
            nation = Nations.get(str(region.data.occupier_id))
            fill_color = palette.normal_to_occupied[nation.color]
            return palette.hex_to_tup(fill_color, alpha=True)
        
        if region.data.owner_id != "0":
            nation = Nations.get(str(region.data.owner_id))
            return palette.hex_to_tup(nation.color, alpha=True)
        
        return None  

    def init_images(self) -> None:
        """
        Takes care of map image initialization.
        """

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

    def color_regions(self) -> None:
        """
        Iterates through all map regions, coloring them as needed for each individual map.
        - Main and Control maps use region ownership and occupation. If region is occupied, that occupation color will show instead of the ownership color.
        - Resource map uses region resource (duh).
        """

        for region in Regions:

            # color region using ownership
            fill_color = self._get_fill_color(region)
            if fill_color is not None and region.graph.improvement_coordinates is not None:
                if not region.graph.is_magnified:
                    x = region.graph.improvement_coordinates[0] + 25
                    y = region.graph.improvement_coordinates[1] + 25
                    ImageDraw.floodfill(self.main_map, (x, y), fill_color, border=(0, 0, 0, 255))
                    ImageDraw.floodfill(self.control_map, (x, y), fill_color, border=(0, 0, 0, 255))
                for coords in region.graph.additional_region_coordinates:
                    ImageDraw.floodfill(self.main_map, tuple(coords), fill_color, border=(0, 0, 0, 255))
                    ImageDraw.floodfill(self.control_map, tuple(coords), fill_color, border=(0, 0, 0, 255))
            
            # color region using resource
            if region.data.resource != "Empty":
                fill_color = palette.resource_colors[region.data.resource]
                if not region.graph.is_magnified and region.graph.improvement_coordinates is not None:
                    x = region.graph.improvement_coordinates[0] + 25
                    y = region.graph.improvement_coordinates[1] + 25
                    coords = (x, y)
                    ImageDraw.floodfill(self.resource_map, coords, fill_color, border=(0, 0, 0, 255))
                for coords in region.graph.additional_region_coordinates:
                    ImageDraw.floodfill(self.resource_map, tuple(coords), fill_color, border=(0, 0, 0, 255))

    def apply_background(self) -> None:
        """
        Applies background raster layer to all maps. 
        - Uses MAP_OPACITY constant to set transparency of map layers.
        """
        background_img = Image.open(self.filepath_background)
        background_img = background_img.convert("RGBA")
        self.main_map = Image.blend(background_img, self.main_map, MAP_OPACITY)
        self.resource_map = Image.blend(background_img, self.resource_map, MAP_OPACITY)
        self.control_map = Image.blend(background_img, self.control_map, MAP_OPACITY)

    def apply_magnified(self) -> None:
        """
        Adds magnified boxes layer to maps that need it.
        """

        magnified_img = Image.open(self.filepath_magnified)
        self.main_map = Image.alpha_composite(self.main_map, magnified_img)
        
        for region in Regions:

            # skip non-magnified or unclaimed
            fill_color = self._get_fill_color(region)
            if not region.graph.is_magnified or fill_color is None:
                continue

            # color magnified box using ownership
            x = region.graph.improvement_coordinates[0] + 25
            y = region.graph.improvement_coordinates[1] + 25
            ImageDraw.floodfill(self.main_map, (x, y), fill_color, border=(0, 0, 0, 255))
            x = region.graph.improvement_coordinates[0] + 55
            ImageDraw.floodfill(self.main_map, (x, y), fill_color, border=(0, 0, 0, 255))
            x = region.graph.improvement_coordinates[0] + 70
            ImageDraw.floodfill(self.main_map, (x, y), fill_color, border=(0, 0, 0, 255))

    def apply_text(self) -> None:
        """
        Adds text layer to maps that need it.
        """
        text_img = Image.open(self.filepath_text)
        self.resource_map = Image.alpha_composite(self.resource_map, text_img)
        self.control_map = Image.alpha_composite(self.control_map, text_img)

    def render_improvement(self, region: Region) -> None:
        """
        Improvement rendering logic is handled here.
        - Places an improvement if able.
        - If the region has been nuked recently, display nuclear explosion instead of improvement (although there should not be one).

        Params:
            region (Region) - Region to render the improvement on.
        """
        
        if region.data.fallout and region.graph.improvement_coordinates is not None:
            # place nuclear explosion
            # TODO: make shadow blend properly
            mask = self.nuke_img.split()[3]
            self.main_map.paste(self.nuke_img, region.graph.improvement_coordinates, mask)
            return
    
        if region.improvement.name is not None and region.graph.improvement_coordinates is not None:
            
            # place improvement on map
            improvement_img = Image.open(f"{self.images_filepath}/improvements/{region.improvement.name.lower()}.png")
            x = region.graph.improvement_coordinates[0]
            y = region.graph.improvement_coordinates[1]
            self.main_map.paste(improvement_img, (x, y))

            # place improvement health
            if region.improvement.health != 99:
                max_health = SD.improvements[region.improvement.name].health
                health_img = Image.open(f"{self.images_filepath}/health/{region.improvement.health}-{max_health}.png")
                x = region.graph.improvement_coordinates[0] - 12
                y = region.graph.improvement_coordinates[1] + 52
                self.main_map.paste(health_img, (x, y))

    def render_unit(self, region: Region) -> None:
        """
        Unit rendering logic is handled here.
        - Places a unit if able.

        Params:
            region (Region) - Region to render the unit on.
        """

        if region.unit.name is None or region.graph.unit_coordinates is None:
            return
            
        # place unit image
        nation = Nations.get(region.unit.owner_id)
        fill_color = palette.hex_to_tup(nation.color, alpha=True)
        unit_img = Image.open(self.filepath_unit_back).convert("RGBA")
        ImageDraw.floodfill(unit_img, (1, 1), fill_color, border=(0, 0, 0, 255))

        # place unit symbol
        fill_color = palette.normal_to_occupied[nation.color]
        fill_color = palette.hex_to_tup(fill_color, alpha=True)
        symb_back_img = Image.open(self.filepath_unit_symb_back).convert("RGBA")
        ImageDraw.floodfill(symb_back_img, (1, 1), fill_color, border=(0, 0, 0, 255))
        symb_img = Image.open(f"{self.images_filepath}/units/{region.unit.name.lower()}.png")
        symb_img = Image.alpha_composite(symb_back_img, symb_img)
        unit_img.paste(symb_img, (9, 16))

        # place unit name
        font = ImageFont.truetype("app/fonts/LeelaUIb.ttf", size=10)
        ImageDraw.Draw(unit_img).text(xy=(25, 5), text=region.unit.full_name, fill=(0, 0, 0, 255), font=font, anchor="mt", align="center")

        # place unit health
        max_health = SD.units[region.unit.name].health
        status = f"{region.unit.health}/{max_health}"
        ImageDraw.Draw(unit_img).text(xy=(25, 37), text=status, fill=(0, 0, 0, 255), font=font, anchor="mt", align="center")
        
        # place unit on map
        x = region.graph.unit_coordinates[0]
        y = region.graph.unit_coordinates[1]
        self.main_map.paste(unit_img, (x, y))

    def export(self) -> None:
        """
        Exports maps generated by this class as images.
        """
        
        game = Games.load(self.game_id)
        
        if game.status.is_setup():
            self.main_map.save(f"gamedata/{self.game_id}/images/0.png")
        elif game.status == GameStatus.ACTIVE_PENDING_EVENT:
            self.main_map.save(f"gamedata/{self.game_id}/images/{game.turn}.png")
        else:
            self.main_map.save(f"gamedata/{self.game_id}/images/{game.turn - 1}.png")
        
        self.resource_map.save(f"gamedata/{self.game_id}/images/resourcemap.png")
        self.control_map.save(f"gamedata/{self.game_id}/images/controlmap.png")

    def update_all(self) -> None:
        """
        Exports updated maps to game files.
        """

        print("Updating game maps...")

        self.init_images()
        self.color_regions()
        self.apply_background()
        self.apply_magnified()
        self.apply_text()

        for region in Regions:
            self.render_improvement(region)
            self.render_unit(region)

        self.export()

    def populate_main_map(self) -> None:
        """
        Spawns random improvements on random regions. Should only be called at the start of the game.
        """
        
        region_id_list = Regions.ids()
        
        # get list of improvements that can spawn
        improvement_candidates_list = []
        for improvement_name, improvement_data in SD.improvements:
            if improvement_data.required_resource is None and improvement_name not in DO_NOT_SPAWN:
                improvement_candidates_list.append(improvement_name)
        
        # place improvements randomly
        count = 0
        placement_quota = int(len(Regions) * 0.1) - len(Nations)
        while count < placement_quota and len(region_id_list) != 0:
            random_region_id = random.choice(region_id_list)
            region_id_list.remove(random_region_id)
            random_region = Regions.load(random_region_id)
            
            # improvement cannot be spawned in a region already taken
            if random_region.improvement.name != None:
                continue
            
            # there cannot be other improvements within a radius of two regions
            nearby_improvement_found = False
            for region_id in random_region.get_regions_in_radius(2):
                temp = Regions.load(region_id)
                if temp.improvement.name is not None:
                    nearby_improvement_found = True
                    break
            if nearby_improvement_found:
                continue
            
            # place improvement
            match random_region.data.resource:
                
                case "Coal":
                    # always spawn coal mine on region with coal
                    random_region.improvement.set("Coal Mine")
                
                case "Oil":
                    # always spawn oil well on region with oil
                    random_region.improvement.set("Oil Well")
                
                case "Basic Materials":
                    # always spawn industrial zone on region with basic materials
                    random_region.improvement.set("Industrial Zone")
                
                case "Common Metals":
                    # always spawn cmm on region with common metals
                    random_region.improvement.set("Common Metals Mine")
                
                case "Advanced Metals":
                    # never spawn am mines
                    continue
                
                case "Uranium":
                    # never spawn uranium mines
                    continue

                case "Rare Earth Elements":
                    # never spawn ree mines
                    continue
                
                case _:
                    # determine if random improvement or capital will spawn
                    improvement_name = random.sample(improvement_candidates_list, 1)[0]
                    if random_region.graph.is_significant and random.randint(1, 10) > 5:
                        improvement_name = "City"
                    # add health bar if needed
                    if SD.improvements[improvement_name].health == 99:
                        random_region.improvement.set(improvement_name)
                    else:
                        random_region.improvement.set(improvement_name, 1)
            
            count += 1

    def populate_resource_map(self) -> None:
        """
        Assigns a resource to each map region. Should only be called at the start of the game.
        """

        def is_resource_allowed(resource_name) -> bool:
            for adj_region in region.graph.iter_adjacent_regions():
                if adj_region.data.resource == resource_name:
                    return False
            return True

        PRIORITY = {"Advanced Metals", "Uranium", "Rare Earth Elements"}
        region_id_list = Regions.ids()
        
        # get resource distribution data for this specific game
        game = Games.load(self.game_id)
        scenario_name = game.info.scenario.lower()
        map_resources: dict = self.map_config["mapResources"][scenario_name]

        # determine resource quantities
        priority_resources = []
        general_resources = []
        for key, value in map_resources.items():
            target = priority_resources if key in PRIORITY else general_resources
            target.extend([key] * value)

        # place priority resources
        for resource in priority_resources:
            while len(region_id_list) != 0:
                random_region_id = random.choice(region_id_list)
                region = Regions.load(random_region_id)
                # rare resources are not allowed to be adjacent another of its kind
                if not is_resource_allowed(resource):
                    continue
                # place resource
                region.data.resource = resource
                region_id_list.remove(random_region_id)
                break

        # place all other resources
        for resource in general_resources:
            random_region_id = random.choice(region_id_list)
            region = Regions.load(random_region_id)
            region.data.resource = resource
            region_id_list.remove(random_region_id)
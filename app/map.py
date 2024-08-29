#STANDARD IMPORTS
import ast
import csv
from datetime import datetime
import json
import os
import random
import shutil

#UWS ENVIROMENT IMPORTS
from PIL import Image, ImageDraw

#UWS SOURCE IMPORTS
from app import core

#THE MAP CLASSES
class MainMap:
    
    '''Creates and updates the main map for United We Stood games.'''

    #INITIALIZE
    def __init__(self, game_id, map_name, current_turn_num):
        self.game_id = game_id
        self.map_name = map_name
        self.turn_num = current_turn_num


    #PLACE RANDOM IMPROVEMENTS
    def place_random(self):
        
        #get filepaths and lists
        regdata_location = f'gamedata/game{self.game_id}/regdata.csv'
        regdata_list = core.read_file(regdata_location, 2)
        improvement_exclusion_list = ['Capital', 'Missile Defense System', 'Missile Defense Network', 'Oil Refinery', 'Advanced Metals Refinery', 'Uranium Refinery', 'Nuclear Power Plant', 'Surveillance Center']
        improvement_candidates_list = []
        for improvement_name in core.improvement_data_dict:
            if core.improvement_data_dict[improvement_name]['Required Resource'] == None and improvement_name not in improvement_exclusion_list:
                improvement_candidates_list.append(improvement_name)
        
        #update regdata.csv
        count = 0
        placement_quota = 5
        placement_odds = 5
        while count < placement_quota:
            for region in regdata_list:
                placement_roll = random.randint(1, 100)
                if placement_roll <= placement_odds:
                    control_data = ast.literal_eval(region[2])
                    resource_name = region[3]
                    improvement_data = ast.literal_eval(region[4])
                    contains_regional_capital = ast.literal_eval(region[10])
                    if control_data[0] == 0 and improvement_data == [None, 99]:
                        match resource_name:
                            case 'Coal':
                                region[4] = ['Coal Mine', 99]
                            case 'Oil':
                                region[4] = ['Oil Well', 99]
                            case 'Basic Materials':
                                region[4] = ['Industrial Zone', 99]
                            case 'Common Metals':
                                region[4] = ['Common Metals Mine', 99]
                            case 'Advanced Metals':
                                region[4] = ['Advanced Metals Mine', 99]
                            case 'Uranium':
                                region[4] = ['Uranium Mine', 99]
                            case 'Rare Earth Elements':
                                region[4] = ['Rare Earth Elements Mine', 99]
                            case _:
                                if contains_regional_capital:
                                    improvement_candidates_list.append('Capital')
                                improvement_roll = random.randint(0, len(improvement_candidates_list) - 1)
                                improvement_name = improvement_candidates_list[improvement_roll]
                                if core.improvement_data_dict[improvement_name]['Health'] != 99:
                                    region[4] = [improvement_name, 1]
                                else:
                                    region[4] = [improvement_name, 99]
                                if contains_regional_capital:
                                    improvement_candidates_list.remove('Capital')
                        count += 1
                                
        #save regdata.csv
        with open(regdata_location, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(core.regdata_header_a)
            writer.writerow(core.regdata_header_b)
            writer.writerows(regdata_list)
    
    
    #UPDATE
    def update(self):
        print("Updating main map...")
        
        #Get Filepaths
        full_game_id = f'game{self.game_id}'
        match self.turn_num:
            case "Starting Region Selection in Progress" | "Nation Setup in Progress":
                main_map_save_location = f'gamedata/{full_game_id}/images/mainmap.png'
            case _:
                main_map_save_location = f'gamedata/{full_game_id}/images/{self.turn_num - 1}.png'
        regdata_location = f'gamedata/{full_game_id}/regdata.csv'
        playerdata_location = f'gamedata/{full_game_id}/playerdata.csv'
        background_filepath, magnified_filepath, main_filepath, text_filepath, texture_filepath = get_map_filepaths(self.map_name)
        
        #Build Needed Lists
        playerdata_list = core.read_file(playerdata_location, 1)
        nation_info_masterlist = core.get_nation_info(playerdata_list)
        regdata_list = core.read_file(regdata_location, 2)
        player_color_list = generate_player_color_list(playerdata_location)
        with open('active_games.json', 'r') as json_file:
            active_games_dict = json.load(json_file)

        #Get Cordinate Dictionaries
        match self.map_name:
            case "United States 2.0":
                cords_filepath = "maps/united_states"
            case _ :
                cords_filepath = "maps/united_states"
        with open(f'{cords_filepath}/improvement_cords.json', 'r') as json_file:
            improvement_cords_dict = json.load(json_file)
        with open(f'{cords_filepath}/unit_cords.json', 'r') as json_file:
            unit_cords_dict = json.load(json_file)
        
        #Color Regions in Map Image
        main_image = Image.open(main_filepath)
        for region in regdata_list:
            region_id = region[0]
            control_data_list = ast.literal_eval(region[2])
            owner_id = control_data_list[0]
            occupier_id = control_data_list[1]
            start_cords = improvement_cords_dict[region_id]
            if start_cords != () and owner_id != 0:
                cord_x = (start_cords[0] + 25)
                cord_y = (start_cords[1] + 25)
                start_cords_updated = (cord_x, cord_y)
                start_cords_finalized = check_region_fill_exceptions(region_id, self.map_name, start_cords_updated)
                map_color_fill(owner_id, occupier_id, player_color_list, region_id, start_cords_finalized, main_image, full_game_id, active_games_dict)
        #add texture and background to temp image
        main_image = apply_textures_new(main_image, texture_filepath, background_filepath)
        #add magnified regions
        magnified_image = Image.open(magnified_filepath)
        main_image = Image.alpha_composite(main_image, magnified_image)
        #color magnified regions
        for region in regdata_list:
            region_id = region[0]
            control_data_list = ast.literal_eval(region[2])
            owner_id = control_data_list[0]
            occupier_id = control_data_list[1]
            improvement_start_cords = improvement_cords_dict[region_id]
            if self.map_name == "United States 2.0":
                magnified_regions_list = ["LOSAN", "FIRCT", "TAMPA", "GACST", "HAMPT", "EASMD", "DELEW", "RHODE", "NTHMA", "STHMA"]
            if improvement_start_cords != () and owner_id != 0 and region_id in magnified_regions_list:
                fill_color = determine_region_color(owner_id, occupier_id, player_color_list, full_game_id, active_games_dict)
                cord_x = (improvement_start_cords[0] + 25)
                cord_y = (improvement_start_cords[1] + 25)
                improvement_box_start_cords = (cord_x, cord_y)
                cord_x = (improvement_start_cords[0] + 55)
                cord_y = (improvement_start_cords[1] + 25)
                main_box_start_cords = (cord_x, cord_y)
                cord_x = (improvement_start_cords[0] + 70)
                cord_y = (improvement_start_cords[1] + 25)
                unit_box_start_cords = (cord_x, cord_y)
                ImageDraw.floodfill(main_image, improvement_box_start_cords, fill_color, border=(0, 0, 0, 255))
                ImageDraw.floodfill(main_image, main_box_start_cords, fill_color, border=(0, 0, 0, 255))
                ImageDraw.floodfill(main_image, unit_box_start_cords, fill_color, border=(0, 0, 0, 255))
        
        #Place Improvements
        main_image = main_image.convert("RGBA")
        nuke_image = Image.open('app/static/nuke.png')
        for region in regdata_list:
            region_id = region[0]
            improvement_data_list = ast.literal_eval(region[4])
            improvement_name = improvement_data_list[0]
            improvement_health = improvement_data_list[1]
            nuke_data = ast.literal_eval(region[6])
            nuke = nuke_data[0]
            improvement_start_cords = improvement_cords_dict[region_id]
            #place nuclear explosion
            if nuke:
                mask = nuke_image.split()[3]
                main_image.paste(nuke_image, improvement_start_cords, mask)
                continue
            #check for fautasian bargan case lease
            if "Faustian Bargain" in active_games_dict[full_game_id]["Active Events"]:
                if region_id in active_games_dict[full_game_id]["Active Events"]["Faustian Bargain"]["Leased Regions List"]:
                    lease_filepath = 'app/static/lease.png'
                    lease_image = Image.open(lease_filepath)
                    main_image.paste(lease_image, improvement_start_cords)
                    continue
            #place improvement if present
            if improvement_start_cords != () and improvement_name is not None:
                #place improvement image
                if improvement_name != "Embassy":
                    improvement_filepath = f'app/static/improvements/{improvement_name}.png'
                else:
                    partner_player_id = improvement_data_list[2]
                    if partner_player_id != 0:
                        embassy_color_str = nation_info_masterlist[partner_player_id - 1][1]
                        improvement_filepath = f'app/static/improvements/{improvement_name}{embassy_color_str}.png'
                    else:
                        improvement_filepath = f'app/static/improvements/{improvement_name}.png'
                improvement_image = Image.open(improvement_filepath)
                main_image.paste(improvement_image, improvement_start_cords)
                #place improvement health
                if improvement_health != 99:
                    cord_x = (improvement_start_cords[0] - 13)
                    cord_y = (improvement_start_cords[1] + 54)
                    health_start_cords = (cord_x, cord_y)
                    if improvement_name in core.ten_health_improvements_list:
                        health_filepath = f'app/static/health/{improvement_health}-10.png'
                    else:
                        health_filepath = f'app/static/health/{improvement_health}-5.png'
                    health_image = Image.open(health_filepath)
                    main_image.paste(health_image, health_start_cords)
        
        #Place Units
        for region in regdata_list:
            region_id = region[0]
            unit_data_list = ast.literal_eval(region[5])
            unit_abbr = unit_data_list[0]
            unit_name = next((unit for unit, data in core.unit_data_dict.items() if data.get('Abbreviation') == unit_abbr), None)
            if unit_name is not None:
                unit_health = unit_data_list[1]
                unit_owner_id = unit_data_list[2]
                #get cords
                if region_id not in unit_cords_dict:
                    #unit placement is the standard 15 pixels to the right of improvement
                    improvement_cords = improvement_cords_dict[region_id]
                    cord_x = (improvement_cords[0] + 65)
                    cord_y = (improvement_cords[1])
                    unit_cords = (cord_x, cord_y)
                else:
                    #unit placement is custom
                    unit_cords = unit_cords_dict[region_id]
                    cord_x = (unit_cords[0])
                    cord_y = (unit_cords[1] - 20)
                    unit_cords = (cord_x, cord_y)
                #get unit color
                player_color_str = nation_info_masterlist[unit_owner_id - 1][1]
                unit_filepath = f'app/static/units/{unit_abbr}{player_color_str}.png'
                #place unit
                unit_image = Image.open(unit_filepath)
                mask = unit_image.split()[3]
                main_image.paste(unit_image, unit_cords, mask)
                #place unit health
                health_filepath = f"app/static/health/U{unit_health}-{core.unit_data_dict[unit_name]['Health']}.png"
                health_image = Image.open(health_filepath)
                health_temp = Image.new("RGBA", main_image.size)
                mask = health_image.split()[3]
                health_temp.paste(health_image, unit_cords, mask)
                main_image = Image.alpha_composite(main_image, health_temp)
        main_image.save(main_map_save_location)

class ResourceMap:
    
    '''Creates and updates the resource map for United We Stood games.'''

    #INITIALIZE
    def __init__(self, game_id, map_name):
        self.game_id = game_id
        self.map_name = map_name

    #CREATE RESOURCE MAP DATA
    def create(self):
        
        #Create Resource List
        resource_list = []
        if self.map_name == "United States 2.0":
            coal_count = 18
            oil_count = 18
            basic_count = 50
            common_count = 30
            advanced_count = 10
            uranium_count = 10
            rare_count = 5
            empty_count = 67
        resource_list += ["Coal"] * coal_count
        resource_list += ["Oil"] * oil_count
        resource_list += ["Basic Materials"] * basic_count
        resource_list += ["Common Metals"] * common_count
        resource_list += ["Advanced Metals"] * advanced_count
        resource_list += ["Uranium"] * uranium_count
        resource_list += ["Rare Earth Elements"] * rare_count
        resource_list += ["Empty"] * empty_count
        resource_list = random.sample(self.resource_list, len(self.resource_list))
        
        #Update regdata.csv
        regdata_location = f'gamedata/game{self.game_id}/regdata.csv'
        regdata_list = core.read_file(regdata_location, 0)
        resource_list.insert(0, "Resource Name")
        resource_list.insert(0, "Resource Data")
        for i, region in enumerate(regdata_list):
            region[3] = resource_list[i]
        
        #Save regdata.csv
        with open(regdata_location, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerows(regdata_list)

    #UPDATE
    def update(self):
        print("Updating resource map...")

        #Get Filepaths
        full_game_id = f'game{self.game_id}'
        resource_map_save_location = f'gamedata/{full_game_id}/images/resourcemap.png'
        regdata_location = f'gamedata/{full_game_id}/regdata.csv'
        playerdata_location = f'gamedata/{full_game_id}/playerdata.csv'
        background_filepath, magnified_filepath, main_filepath, text_filepath, texture_filepath = get_map_filepaths(self.map_name)
        
        #Build Needed Lists
        regdata_list = core.read_file(regdata_location, 2)
        
        #Get Cordinate Dictionaries
        match self.map_name:
            case "United States 2.0":
                cords_filepath = "maps/united_states"
            case _ :
                cords_filepath = "maps/united_states"
        with open(f'{cords_filepath}/improvement_cords.json', 'r') as json_file:
            improvement_cords_dict = json.load(json_file)
        
        #Color Regions in Map Image
        main_image = Image.open(main_filepath)
        for region in regdata_list:
            region_id = region[0]
            resource_type = region[3]
            start_cords = improvement_cords_dict[region_id]
            if start_cords != () and resource_type != 'Empty':
                cord_x = (start_cords[0] + 25)
                cord_y = (start_cords[1] + 25)
                start_cords_updated = (cord_x, cord_y)
                start_cords_finalized = check_region_fill_exceptions(region_id, self.map_name, start_cords_updated)
                if region_id == "HAMPT" and self.map_name == "United States 2.0":
                    ImageDraw.floodfill(main_image, (4430, 1520), core.resource_colors[resource_type], border=(0, 0, 0, 255))
                ImageDraw.floodfill(main_image, start_cords_finalized, core.resource_colors[resource_type], border=(0, 0, 0, 255))
        
        #Add Textures and Text
        background_image = Image.open(background_filepath)
        background_image = background_image.convert("RGBA")
        mask = main_image.split()[3]
        background_image.paste(main_image, (0,0), mask)
        main_image = background_image
        main_image = text_over_map_new(main_image, text_filepath)
        main_image.save(resource_map_save_location)

class ControlMap:

    '''Creates and updates the control map for United We Stood games.'''

    #INITIALIZE
    def __init__(self, game_id, map_name):
        self.game_id = game_id
        self.map_name = map_name

    #GENERATE CONTROL MAP IMAGE
    def update(self):
        print("Updating control map...")
        
        #Get Filepaths
        full_game_id = f'game{self.game_id}'
        control_map_save_location = f'gamedata/{full_game_id}/images/controlmap.png'
        regdata_location = f'gamedata/{full_game_id}/regdata.csv'
        playerdata_location = f'gamedata/{full_game_id}/playerdata.csv'
        background_filepath, magnified_filepath, main_filepath, text_filepath, texture_filepath = get_map_filepaths(self.map_name)
       
        #Build Needed Lists
        regdata_list = core.read_file(regdata_location, 2)
        player_color_list = generate_player_color_list(playerdata_location)
        with open('active_games.json', 'r') as json_file:
            active_games_dict = json.load(json_file)

        #Get Cordinate Dictionaries
        match self.map_name:
            case "United States 2.0":
                cords_filepath = "maps/united_states"
            case _ :
                cords_filepath = "maps/united_states"
        with open(f'{cords_filepath}/improvement_cords.json', 'r') as json_file:
            improvement_cords_dict = json.load(json_file)

        #Color Regions in Map Image
        main_image = Image.open(main_filepath)
        for region in regdata_list:
            region_id = region[0]
            control_data_list = ast.literal_eval(region[2])
            owner_id = control_data_list[0]
            occupier_id = control_data_list[1]
            start_cords = improvement_cords_dict[region_id]
            if start_cords != () and owner_id != 0:
                cord_x = (start_cords[0] + 25)
                cord_y = (start_cords[1] + 25)
                start_cords_updated = (cord_x, cord_y)
                start_cords_finalized = check_region_fill_exceptions(region_id, self.map_name, start_cords_updated)
                map_color_fill(owner_id, occupier_id, player_color_list, region_id, start_cords_finalized, main_image, full_game_id, active_games_dict)
        
        #Add Textures and Text
        main_image = apply_textures_new(main_image, texture_filepath, background_filepath)
        main_image = text_over_map_new(main_image, text_filepath)
        main_image.save(control_map_save_location)

#MAP GENERATION HELPER FUNCTIONS
def get_map_filepaths(map_name):
    '''Returns a series of variables representing the filepaths of the map generation image based on the map type.'''
    if map_name == "United States 2.0":
        map_name = "united_states"
    background_file = f'maps/{map_name}/image_resources/background.png'
    magnified_file = f'maps/{map_name}/image_resources/magnified.png'
    main_file = f'maps/{map_name}/image_resources/main.png'
    text_file = f'maps/{map_name}/image_resources/text.png'
    texture_file = f'maps/{map_name}/image_resources/texture.png'
    return background_file, magnified_file, main_file, text_file, texture_file

def generate_player_color_list(playerdata_location):
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

def check_region_fill_exceptions(region_id, map_name, start_cords_updated):
    '''Changes start_cords_updated for maginified regions.'''
    if map_name == "United States 2.0":
        if region_id == "LOSAN":
            start_cords_updated = (563, 1866)
        elif region_id == "FIRCT":
            start_cords_updated = (4040, 2489)
        elif region_id == "TAMPA":
            start_cords_updated = (3997, 2697)
        elif region_id == "GACST":
            start_cords_updated = (4014, 2297)
        elif region_id == "HAMPT":
            start_cords_updated = (4358, 1590)
        elif region_id == "EASMD":
            start_cords_updated = (4413, 1447)
        elif region_id == "DELEW":
            start_cords_updated = (4410, 1379)
        elif region_id == "RHODE":
            start_cords_updated = (4676, 995)
        elif region_id == "NTHMA":
            start_cords_updated = (4660, 923)
        elif region_id == "STHMA":
            start_cords_updated = (4700, 960)
    return start_cords_updated

def map_color_fill(owner_id, occupier_id, player_color_list, region_id, start_cords_updated, main_image, full_game_id, active_games_dict):
    '''
    Determines what fill color to use for main map and control map generation, depending on region ownership and occupation.
    '''

    fill_color = determine_region_color(owner_id, occupier_id, player_color_list, full_game_id, active_games_dict)
    if region_id == "HAMPT":
        ImageDraw.floodfill(main_image, (4430, 1520), fill_color, border=(0, 0, 0, 255))
    ImageDraw.floodfill(main_image, start_cords_updated, fill_color, border=(0, 0, 0, 255))

def determine_region_color(owner_id, occupier_id, player_color_list, full_game_id, active_games_dict):
    '''
    Cheap solution for determing region color. Future Ian if you allow this code to survive the next refactoring I will strangle you.
    '''
    
    if owner_id != 99:
        fill_color = player_color_list[owner_id - 1]
    elif owner_id == 99 and "Foreign Invasion" in active_games_dict[full_game_id]["Active Events"]:
        fill_color = active_games_dict[full_game_id]["Active Events"]["Foreign Invasion"]["Invasion Color"]
    if occupier_id != 0 and occupier_id != 99:
        fill_color = player_color_list[occupier_id -1]
        fill_color = core.player_colors_normal_to_occupied[fill_color]
    elif occupier_id == 99 and "Foreign Invasion" in active_games_dict[full_game_id]["Active Events"]:
        fill_color = core.player_colors_normal_to_occupied[active_games_dict[full_game_id]["Active Events"]["Foreign Invasion"]["Invasion Color"]]
        
    return fill_color

def apply_textures_new(main_image, texture_filepath, background_filepath):
    '''
    '''
    
    texture_image = Image.open(texture_filepath)
    temp_image = Image.blend(texture_image, main_image, 0.75)
    main_image = temp_image

    background_image = Image.open(background_filepath)
    background_image = background_image.convert("RGBA")
    mask = main_image.split()[3]
    background_image.paste(main_image, (0,0), mask)
    main_image = background_image

    return main_image

def text_over_map_new(main_image, text_filepath):
    '''
    '''
    text_image = Image.open(text_filepath)
    main_image = Image.alpha_composite(main_image, text_image)

    return main_image
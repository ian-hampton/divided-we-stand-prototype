import json
import os
import sys

from PIL import Image, ImageDraw

# This script tests region coloring and unit/improvement placement by outputting a fully populated map.
# Does not use any of the custom classes to do this
# Last updated 5/16/2025

# TODO: Use new map code functions instead for this test

MAP_STR = "china"
REGDATA_FILEPATH = f"../../maps/{MAP_STR}/regdata.json"
FILL_COLOR = (0, 150, 255, 255)
IMPROVEMENT_IMAGE = "../../app/static/images/improvements/industrial zone.png"
UNIT_IMAGE = "../../app/static/images/units/new-unit-test.png"

def color_test():

    print("Running map test...")
        
    # get filepaths
    image_resources_filepath = f"../../app/static/images/map_images/{MAP_STR}/image_resources"
    background_filepath = f"{image_resources_filepath}/background.png"
    magnified_filepath = f"{image_resources_filepath}/magnified.png"
    main_filepath = f"{image_resources_filepath}/main.png"
    text_filepath = f"{image_resources_filepath}/text.png"
    with open(REGDATA_FILEPATH, 'r') as json_file:
        regdata_dict = json.load(json_file)
    
    # color regions in map image
    main_image = Image.open(main_filepath)
    main_image = main_image.convert("RGBA")
    for region_id in regdata_dict:
        region_cords = regdata_dict[region_id]["regionData"].get("coordinates")
        improvement_cords = regdata_dict[region_id]["improvementData"]["coordinates"]
        cord_x = improvement_cords[0] + 25
        cord_y = improvement_cords[1] + 25
        start_cords_updated = (cord_x, cord_y)
        if region_cords is not None:
            start_cords_updated = region_cords
        ImageDraw.floodfill(main_image, start_cords_updated, FILL_COLOR, border=(0, 0, 0, 255))
    
    # add texture and background to temp image (copy paste from map.py)
    background_image = Image.open(background_filepath)
    background_image = background_image.convert("RGBA")
    main_image = Image.blend(background_image, main_image, 0.75)

    # add magnified regions
    magnified_image = Image.open(magnified_filepath)
    main_image = Image.alpha_composite(main_image, magnified_image)
    
    # color magnified regions
    for region_id in regdata_dict:
        region_cords = regdata_dict[region_id]["regionData"].get("coordinates")
        if region_cords is not None:
            improvement_cords = regdata_dict[region_id]["improvementData"]["coordinates"]
            cord_x = improvement_cords[0] + 25
            cord_y = improvement_cords[1] + 25
            improvement_box_start_cords = (cord_x, cord_y)
            cord_x = improvement_cords[0] + 55
            cord_y = improvement_cords[1] + 25
            main_box_start_cords = (cord_x, cord_y)
            cord_x = improvement_cords[0] + 70
            cord_y = improvement_cords[1] + 25
            unit_box_start_cords = (cord_x, cord_y)
            ImageDraw.floodfill(main_image, improvement_box_start_cords, FILL_COLOR, border=(0, 0, 0, 255))
            ImageDraw.floodfill(main_image, main_box_start_cords, FILL_COLOR, border=(0, 0, 0, 255))
            ImageDraw.floodfill(main_image, unit_box_start_cords, FILL_COLOR, border=(0, 0, 0, 255))

    # Place Improvements
    main_image = main_image.convert("RGBA")
    for region_id in regdata_dict:
        # place improvement image
        improvement_cords = regdata_dict[region_id]["improvementData"]["coordinates"]
        improvement_image = Image.open(IMPROVEMENT_IMAGE)
        main_image.paste(improvement_image, improvement_cords)

    # Place Units
    for region_id in regdata_dict:
        # get cords of unit if present
        unit_cords = regdata_dict[region_id]["unitData"].get("coordinates")
        if unit_cords is None:
            # unit placement is the standard 15 pixels to the right of improvement
            improvement_cords = regdata_dict[region_id]["improvementData"]["coordinates"]
            cord_x = (improvement_cords[0] + 65)
            cord_y = (improvement_cords[1])
            unit_cords = (cord_x, cord_y)
        else:
            # unit placement is custom
            cord_x = (unit_cords[0])
            cord_y = (unit_cords[1] - 20)
            unit_cords = (cord_x, cord_y)
        # place unit
        unit_image = Image.open(UNIT_IMAGE)
        main_image.paste(unit_image, unit_cords)
    
    main_image.save("../../map_color_test.png")
    print(f"Done!")

color_test()
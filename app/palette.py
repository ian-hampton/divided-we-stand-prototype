from app import core

def color_nation_names(string, game_id):
    """
    Adds html span tags around all nation names in given string
    """

    playerdata_filepath = f'gamedata/{game_id}/playerdata.csv'
    playerdata_list = core.read_file(playerdata_filepath, 1)

    color_dict = {}
    for playerdata in playerdata_list:
        color_dict[playerdata[1]] = playerdata[2]

    bad_primary_colors_set = {"#603913", "#105500", "#8b2a1a"}

    for nation_name, color in color_dict.items():
        if color in bad_primary_colors_set:
            color = normal_to_occupied[color]
        html_nation_name = f"""<span style="color: {color}">{nation_name}</span>"""
        string = string.replace(nation_name, html_nation_name)

    return string

def str_to_hex(color_str):
    """
    Retrives a hexadecimal color value that corresponds to a string name.
    """

    color_str = color_str.lower().strip()
    
    return player_colors_hex.get(color_str)

player_colors_hex = {
    "brown": "#603913",
    "coral": "#ff974e",
    "dark blue": "#003b84",
    "dark green": "#105500",
    "dark purple": "#5a009d",
    "dark red": "#b30000",
    "light blue": "#0096ff",
    "light green": "#5bb000",
    "light purple": "#b654ff",
    "light red": "#ff3d3d",
    "maroon": "#8b2a1a",
    "metallic gold": "#9f8757",
    "orange": "#ff9600",
    "pink": "#f384ae",
    "terracotta": "#b66317",
    "yellow": "#ffd64b",
}

normal_to_occupied = {
    "#603913": "#905721",
    "#ff974e": "#ffaa6f",
    "#003b84": "#004eae",
    "#105500": "#187e00",
    "#5a009d": "#7e00dd",
    "#b30000": "#d40000",
    "#0096ff": "#57baff",
    "#5bb000": "#6ed400",
    "#b654ff": "#c87fff",
    "#ff3d3d": "#ff6666",
    "#8b2a1a": "#b83823",
    "#9f8757": "#af9a6e",
    "#ff9600": "#ffaf3d",
    "#f384ae": "#f4a0c0",
    "#b66317": "#c57429",
    "#ffd64b": "#ffe68e" 
}
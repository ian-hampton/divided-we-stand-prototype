from app import core
from app.nationdata import NationTable

from PIL import ImageColor

BAD_PRIMARY_COLORS = {"#603913", "#105500", "#8b2a1a"}

def color_nation_names(string: str, game_id: str):
    """
    Adds html span tags around all nation names in given string
    """
    nation_table = NationTable(game_id)
    color_dict = {}
    for nation in nation_table:
        color_dict[nation.name] = nation.color

    for nation_name, color in color_dict.items():
        if color in BAD_PRIMARY_COLORS:
            color = normal_to_occupied[color]
        html_nation_name = f"""<span style="color:{color}">{nation_name}</span>"""
        string = string.replace(nation_name, html_nation_name)

    return string

def str_to_hex(color_str: str):
    """
    Retrives a hexadecimal color value that corresponds to a string name.
    """

    color_str = color_str.lower().strip()
    
    return player_colors_hex.get(color_str)

def tup_to_hex(color_tuple: tuple) -> str:
    """
    Converts RBG or RGBA color to a hexadecimal string.
    """

    result = None
    if len(color_tuple) == 3:
        result = f"#{color_tuple[0]:02x}{color_tuple[1]:02x}{color_tuple[2]:02x}"
    elif len(color_tuple) == 4:
        result = f"#{color_tuple[0]:02x}{color_tuple[1]:02x}{color_tuple[2]:02x}{color_tuple[3]:02x}"

    return result.lower()

def hex_to_tup(color_hex: str, alpha=False) -> tuple:
    """
    Converts hexadecimal string to RGB or RGBA.
    """

    result = ImageColor.getrgb(color_hex)

    if alpha:
        result = list(result)
        result.append(255)
        return tuple(result)
    
    return result

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
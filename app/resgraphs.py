#STANDARD IMPORTS
import ast
import copy

#UWS SOURCE IMPORTS
from app import core

#UWS ENVIROMENT IMPORTS
from PIL import Image

def update_research_graphic(research_type, completed_research_dictionary, player_colors_list, game_id):
    '''
    Updates a research graphic using pillow.

    Parameters:
    - research_type: The research tree type.
    - completed_research_dictionary: A dictionary of research names and corresponding player ids.
    - player_colors_list: A list in player id order of nation colors.
    - game_id: The full game_id of the active game.
    '''

    #get data from scenario
    agenda_data_dict = core.get_scenario_dict(game_id, "Agendas")
    research_data_dict = core.get_scenario_dict(game_id, "Technologies")

    #variables for star placement
    ORIGIN = [74, 264]
    COL_DISTANCE = 465
    ROW_DISTANCE = 244
    STAR_DISTANCE = 24

    #get correct file name and research dictionary
    match research_type:
        case 'Agenda':
            filename = '0-Agenda'
            research_dict = agenda_data_dict
        case 'Energy':
            filename = '1-Energy'
            research_dict = research_data_dict
        case 'Infrastructure':
            filename = '2-Infrastructure'
            research_dict = research_data_dict
        case 'Military':
            filename = '3-Military'
            research_dict = research_data_dict
        case 'Defense':
            filename = '4-Defense'
            research_dict = research_data_dict

    #populate the chosen research graphic with stars    
    research_graphic = Image.open(f'app/static/{filename}.png')
    for research_name in research_dict:
        if completed_research_dictionary[research_name] == []:
            continue
        if research_type != 'Agenda':
            if research_dict[research_name]['Research Type'] != research_type:
                continue
        #calculate initial star position for a specific research
        research_position_str = research_dict[research_name]['Location']
        x = (int(research_position_str[1]) - 1) * COL_DISTANCE
        y = (ord(research_position_str[0]) - 65) * ROW_DISTANCE
        cords = [x, y]
        starting_star_cords = [a + b for a, b in zip(ORIGIN, cords)]
        #place stars
        for player_id in completed_research_dictionary[research_name]:
            star_cords = copy.deepcopy(starting_star_cords)
            x_offset = (player_id - 1) * STAR_DISTANCE
            star_cords[0] += x_offset
            color_hex = player_colors_list[player_id - 1]
            for key, value in core.player_colors_hex.items():
                if value == color_hex:
                    color = key
            star_image = Image.open(f'app/static/stars/{color}.png')
            mask = star_image.split()[3]
            research_graphic.paste(star_image, star_cords, mask)
    research_graphic.save(f'gamedata/{game_id}/images/{filename}.png')

def update_all(game_id):
    '''
    Updates all research graphics for a given game.

    Parameters:
    - game_id: The full game_id of the active game.
    '''

    #define core lists
    playerdata_filepath = f'gamedata/{game_id}/playerdata.csv'
    playerdata_list = core.read_file(playerdata_filepath, 1)
    player_colors_list = []

    #get data from scenario
    agenda_data_dict = core.get_scenario_dict(game_id, "Agendas")
    research_data_dict = core.get_scenario_dict(game_id, "Technologies")

    #create research dictionary
    keys = set(agenda_data_dict.keys()).union(research_data_dict.keys())
    completed_research_dictionary = {key: [] for key in keys}
    for index, playerdata in enumerate(playerdata_list):
        player_colors_list.append(playerdata[2])
        player_research_list = ast.literal_eval(playerdata[26])
        for research_name in player_research_list:
            completed_research_dictionary[research_name].append(index + 1)

    #update all graphics
    research_types = ['Agenda', 'Energy', 'Infrastructure', 'Military', 'Defense']
    for research_type in research_types:
        update_research_graphic(research_type, completed_research_dictionary, player_colors_list, game_id)

def update_one(game_id, research_type):
    
    #define core lists
    playerdata_filepath = f'gamedata/{game_id}/playerdata.csv'
    playerdata_list = core.read_file(playerdata_filepath, 1)
    player_colors_list = []

    #get data from scenario
    agenda_data_dict = core.get_scenario_dict(game_id, "Agendas")
    research_data_dict = core.get_scenario_dict(game_id, "Technologies")

    #create research dictionary
    keys = set(agenda_data_dict.keys()).union(research_data_dict.keys())
    completed_research_dictionary = {key: [] for key in keys}
    for index, playerdata in enumerate(playerdata_list):
        player_colors_list.append(playerdata[2])
        player_research_list = ast.literal_eval(playerdata[26])
        for research_name in player_research_list:
            completed_research_dictionary[research_name].append(index + 1)

    #update graphic
    update_research_graphic(research_type, completed_research_dictionary, player_colors_list, game_id)
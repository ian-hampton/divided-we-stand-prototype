import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import core
import map

def run():
    game_id = input("Enter Full Game ID: ")
    map_name = core.get_map_name(int(game_id[-1]))
    current_turn_num = core.get_current_turn_num(int(game_id[-1]))

    main_map = map.MainMap(game_id, map_name, current_turn_num)
    main_map.update()
    resource_map = map.ResourceMap(game_id, map_name)
    resource_map.update()
    control_map = map.ControlMap(game_id, map_name)
    control_map.update()

# TO UTILIZE TEST ADD THESE LINES TO INTERFACE.PY
# from testing import map_tests
# map_tests.run()
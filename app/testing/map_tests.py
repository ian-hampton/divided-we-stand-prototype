import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import core
import map

def run():
    full_game_id = input("Enter Full Game ID: ")
    map_name = core.get_map_name(full_game_id)
    current_turn_num = core.get_current_turn_num(full_game_id)

    main_map = map.MainMap(full_game_id, map_name, current_turn_num)
    main_map.update()
    resource_map = map.ResourceMap(full_game_id, map_name)
    resource_map.update()
    control_map = map.ControlMap(full_game_id, map_name)
    control_map.update()

# TO UTILIZE TEST ADD THESE LINES TO INTERFACE.PY
# from testing import map_tests
# map_tests.run()
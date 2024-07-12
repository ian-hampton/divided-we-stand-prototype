import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import core
import resgraphs

full_game_id = input("Enter gameid to generate research graphics for: ")
choice = input("Would you like to generate all research graphics? (Y/N) ")
if choice == 'Y':
    resgraphs.update_all(full_game_id)
else:
    print(['Agenda', 'Energy', 'Infrastructure', 'Military', 'Defense'])
    research_type = input("Select one of the above options: ")
    resgraphs.update_one(full_game_id, research_type)
print("Task complete.")

# TO USE THIS TEST YOU MUST ADD ../ TO THE FRONT OF ALL FILEPATHS IN RESGRAPHICS.PY BECAUSE RELATIVE FILEPATHS ARE STUPID
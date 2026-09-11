from app.game.games import Games
from app.scenario.scenario import ScenarioInterface as SD
from app.nation.nations import Nations
from app.war.wars import Wars

def _is_first_event(game_id: str) -> bool:

    game = Games.load(game_id)
    
    already_chosen_events = set(game.inactive_events) | set(key for key in game.active_events)

    if len(already_chosen_events) != 0:
        return False
    
    return True

def _no_major_events(game_id: str) -> bool:

    game = Games.load(game_id)
    
    already_chosen_events = set(game.inactive_events) | set(key for key in game.active_events)
   
    for event_name, event_data in SD.events:
        if event_name in already_chosen_events and event_data.type == "Major Event":
            return False
        
    return True

def _no_ranking_tie(game_id: str, ranking: str) -> bool:

    top_three = Nations.get_top_three(ranking)
    if top_three[0][1] == top_three[1][1]:
        return False
    
    return True

def _at_least_x_ongoing_wars(game_id: str, count: int) -> bool:

    ongoing_war_count = 0
    for war in Wars:
        if war.outcome == "TBD":
            ongoing_war_count += 1
    
    if ongoing_war_count < count:
        return False
    
    return True

def _at_least_x_nations_at_peace_for_y_turns(game_id: str, nation_count: int, turn_count: int) -> bool:

    at_peace_count = 0
    for nation in Nations:
        if Wars.at_peace_for_x(nation.id) >= turn_count:
            at_peace_count += 1
    
    if at_peace_count < nation_count:
        return False
    
    return True

def _global_count_of_x_improvement_at_least_y(game_id: str, improvement_name: str, count: int) -> bool:

    global_total = 0
    for nation in Nations:
        global_total += nation.improvement_counts[improvement_name]
    
    if global_total < count:
        return False
    
    return True
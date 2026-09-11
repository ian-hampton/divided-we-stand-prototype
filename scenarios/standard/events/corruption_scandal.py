from scenarios.standard import event_tools
from app.event.event import Event, EventState
from app.nation.nations import Nations
from app.notifications import Notifications

EVENT_NAME = "Corruption Scandal"

class CorruptionScandal(Event):
    
    def __init__(self, game_id: str, event_name: str, event_data: dict):
        Event.__init__(self, game_id, event_name, event_data)

    def activate(self):
        
        top_three_economy = Nations.get_top_three("net_income")
        victim_nation_name = top_three_economy[0][0]
        victim_nation = Nations.get(victim_nation_name)
        Notifications.add(f"{victim_nation.name} has been randomly selected as the target for the {self.name} event!", 3)

        new_tag = {
            "Dollars Rate": -20,
            "Political Power Rate": -20,
            "Expire Turn": self.game.turn + self.duration + 1
        }
        victim_nation.tags["Corruption Scandal"] = new_tag

        self.state = EventState.ACTIVE
        self.expire_turn = self.game.turn + self.duration + 1

    def has_conditions_met(self) -> bool:

        if not event_tools._no_ranking_tie(self.game_id, "net_income"):
            return False
        
        return True
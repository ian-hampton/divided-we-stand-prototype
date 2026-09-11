from app.event.event import Event, EventState
from app.nation.nations import Nations
from app.notifications import Notifications

EVENT_NAME = "Embargo"

class Embargo(Event):
    
    def __init__(self, game_id: str, event_name: str, event_data: dict):
        Event.__init__(self, game_id, event_name, event_data)

    def activate(self):
        
        Notifications.add(f"New Event: {self.name}!", 3)
        for nation in Nations:
            self.targets.append(nation.id)
        
        self.state = EventState.PENDING

    def resolve(self):

        print("""Available Options: "# Nation Name" or "Abstain" """)
        self.vote_tally = self._get_votes_nation()
        nation_name = self._determine_vote_winner()

        if nation_name is None:
            Notifications.add(f"Vote tied. No nation has been embargoed.", 3)
            self.state = EventState.FINISHED
            return
        
        nation = Nations.get(nation_name)
        new_tag = {
            "Expire Turn": self.game.turn + self.duration + 1
        }
        nation.tags["Embargo"] = new_tag
        
        Notifications.add(f"Having received {self.vote_tally[nation_name]} votes, {nation_name} has been embargoed", 3)
        
        self.state = EventState.ACTIVE
        self.expire_turn = self.game.turn + self.duration + 1     

    def has_conditions_met(self) -> bool:
        return True

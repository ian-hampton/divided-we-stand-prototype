from app.event.event import Event, EventState
from app.nation.nations import Nations
from app.notifications import Notifications

EVENT_NAME = "Threat Containment"

class ThreatContainment(Event):
    
    def __init__(self, game_id: str, event_name: str, event_data: dict):
        Event.__init__(self, game_id, event_name)
        self.type = "Voting Event"
        self.duration = 8
        self.targets: list = event_data.get("Targets", [])
        self.expire_turn: int = event_data.get("Expiration", -1)

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
            Notifications.add(f"Vote tied. No nation has been sanctioned.", 3)
            self.state = EventState.FINISHED
            return
        
        nation = Nations.get(nation_name)
        new_tag = {
            "Military Capacity Rate": -20,
            "Trade Fee Modifier": -1,
            "Expire Turn": self.game.turn + self.duration + 1
        }
        nation.tags["Threat Containment"] = new_tag

        Notifications.add(f"Having received {self.vote_tally[nation_name]} votes, {nation_name} has been sanctioned.", 3)

        self.state = EventState.ACTIVE
        self.expire_turn = self.game.turn + self.duration + 1

    def has_conditions_met(self) -> bool:
        return True
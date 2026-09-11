from app.event.event import Event, EventState
from app.nation.nations import Nations
from app.notifications import Notifications

EVENT_NAME = "Shared Fate"

class SharedFate(Event):
    
    def __init__(self, game_id: str, event_name: str, event_data: dict):
        Event.__init__(self, game_id, event_name)
        self.type = "Voting Event"
        self.duration = 99999
        self.targets: list = event_data.get("Targets", [])
        self.expire_turn: int = event_data.get("Expiration", -1)

    def activate(self):
        
        Notifications.add(f"New Event: {self.name}!", 3)
        for nation in Nations:
            self.targets.append(nation.id)
        
        self.state = EventState.PENDING

    def resolve(self):

        self.choices = ["Cooperation", "Conflict", "Abstain"]
        print(f"Available Options: {" or ".join(self.choices)}")
        self.vote_tally = self._get_votes_option()
        option_name = self._determine_vote_winner()

        if option_name is None:
            Notifications.add(f"Vote tied. No option was resolved.", 3)
            self.state = EventState.FINISHED
            return

        if option_name == "Cooperation":
            for nation in Nations:
                new_tag = {
                    "Alliance Limit Modifier": 1,
                    "Expire Turn": 99999
                }
                nation.tags["Shared Fate"] = new_tag
            Notifications.add(f"Cooperation won in a {self.vote_tally.get("Cooperation")} - {self.vote_tally.get("Conflict")} decision.", 3)

        elif option_name == "Conflict":
            for nation in Nations:
                new_tag = {
                    "Improvement Income": {
                        "Boot Camp": {
                            "Military Capacity": 1
                        }
                    },
                    "Expire Turn": 99999
                }
                nation.tags["Shared Fate"] = new_tag
            Notifications.add(f"Conflict won in a {self.vote_tally.get("Conflict")} - {self.vote_tally.get("Cooperation")} decision.", 3)

        self.state = EventState.ACTIVE
        self.duration = 99999

    def has_conditions_met(self) -> bool:
        return True
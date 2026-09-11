from app.event.event import Event, EventState
from app.nation.nations import Nations
from app.notifications import Notifications

EVENT_NAME = "Assassination"

class Assassination(Event):
    
    def __init__(self, game_id: str, event_name: str, event_data: dict):
        Event.__init__(self, game_id, event_name)
        self.type = "Standard Event"
        self.duration = 8
        self.targets: list = event_data.get("Targets", [])
        self.expire_turn: int = event_data.get("Expiration", -1)

    def activate(self):

        victim_player_id = Nations.get_random_id()
        victim_nation = Nations.get(victim_player_id)
        self.targets.append(victim_nation.id)

        Notifications.add(f"{victim_nation.name} has been randomly selected as the target for the {self.name} event!", 3)

        self.state = EventState.PENDING

    def resolve(self):
        
        self.choices = ["Find the Perpetrator", "Find a Scapegoat"]
        print(f"Available Options: {" or ".join(self.choices)}")
        decision_dict = self._collect_basic_decisions()

        for nation_id, decision in decision_dict.items():
            
            nation = Nations.get(nation_id)
            
            if decision == "Find the Perpetrator":
                nation.update_stockpile("Political Power", 5)
                self.state = EventState.FINISHED
            
            elif decision == "Find a Scapegoat":
                while True:
                    scapegoat_nation_name = input("Enter the nation name to scapegoat: ")
                    try:
                        scapegoat = Nations.get(scapegoat_nation_name)
                        break
                    except:
                        print("Unrecognized nation name, try again.")
                new_tag = {
                    "Combat Roll Bonus": scapegoat.id,
                    "Expire Turn": self.game.turn + self.duration + 1
                }
                nation.tags["Assassination Scapegoat"] = new_tag
                self.state = EventState.ACTIVE
                self.expire_turn = self.game.turn + self.duration + 1
    
    def has_conditions_met(self) -> bool:
        return True
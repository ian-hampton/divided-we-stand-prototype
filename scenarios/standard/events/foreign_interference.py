from app import actions
from scenarios.standard import event_tools
from app.event.event import Event, EventState
from app.nation.nations import Nations
from app.notifications import Notifications

EVENT_NAME = "Foreign Interference"

class ForeignInterference(Event):
    
    def __init__(self, game_id: str, event_name: str, event_data: dict):
        Event.__init__(self, game_id, event_name)
        self.type = "Standard Event"
        self.duration = 0
        self.targets: list = event_data.get("Targets", [])
        self.expire_turn: int = event_data.get("Expiration", -1)

    def activate(self):
        
        Notifications.add(f"New Event: {self.name}!", 3)
        for nation in Nations:
            self.targets.append(nation.id)
        
        self.state = EventState.PENDING

    def resolve(self):

        self.choices = ["Accept", "Decline"]
        print(f"Available Options: {" or ".join(self.choices)}")
        decision_dict = self._collect_basic_decisions()

        war_actions: list[actions.WarAction] = []
        for nation_id, decision in decision_dict.items():
            
            nation = Nations.get(nation_id)
            
            if decision == "Accept":
                action_valid = False
                while not action_valid:
                    enemy_nation_name = input("Enter nation you wish to declare war on: ")
                    chosen_war_justification = input("Enter desired war justification: ")
                    action_str = f"War {enemy_nation_name} {chosen_war_justification}"
                    war_action = actions.WarAction(self.game_id, nation_id, action_str)
                    if war_action.is_valid():
                        action_valid = True
                new_tag = {
                    "Foreign Interference Target": enemy_nation_name,
                    "Expire Turn": 99999
                }
                for resource_name in nation._resources:
                    if resource_name in ["Political Power", "Military Capacity"]:
                        continue
                    new_tag[f"{resource_name} Rate"] = 10
                nation.tags["Foreign Interference"] = new_tag
            
            elif decision == "Decline":
                nation.update_stockpile("Political Power", 5)

        actions.resolve_war_actions(self.game_id, war_actions)
        self.state = EventState.FINISHED

    def has_conditions_met(self) -> bool:

        if event_tools._is_first_event(self.game_id):
            return False
        
        return True

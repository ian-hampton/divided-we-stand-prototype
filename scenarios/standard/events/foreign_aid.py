from app.event.event import Event, EventState
from app.nation.nations import Nations, LeaderboardRecordNames
from app.notifications import Notifications

EVENT_NAME = "Foreign Aid"

class ForeignAid(Event):
    
    def __init__(self, game_id: str, event_name: str, event_data: dict):
        Event.__init__(self, game_id, event_name)
        self.type = "Standard Event"
        self.duration = 0
        self.targets: list = event_data.get("Targets", [])
        self.expire_turn: int = event_data.get("Expiration", -1)

    def activate(self):
        
        for record in LeaderboardRecordNames:
            top_three = Nations.get_top_three(record)
            for nation_name, score in top_three:
                if score != 0 and nation_name not in self.targets:
                    self.targets.append(nation_name)

        for nation_name in self.targets:
            nation = Nations.get(nation_name)
            count = nation.improvement_counts["Settlement"] + nation.improvement_counts["City"]
            if count > 0:
                amount = count * 5
                nation.update_stockpile("Dollars", amount)
                Notifications.add(f"{nation_name} has received {amount} dollars worth of foreign aid.", 3)

        self.state = EventState.FINISHED

    def has_conditions_met(self) -> bool:
        return True
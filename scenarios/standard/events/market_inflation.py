from app.event.event import Event, EventState

EVENT_NAME = "Market Inflation"

class MarketInflation(Event):
    
    def __init__(self, game_id: str, event_name: str, event_data: dict):
        Event.__init__(self, game_id, event_name)
        self.type = "Standard Event"
        self.duration = 8
        self.targets: list = event_data.get("Targets", [])
        self.expire_turn: int = event_data.get("Expiration", -1)

    def activate(self):
        self.state = EventState.ACTIVE
        self.expire_turn = self.game.turn + self.duration + 1

    def has_conditions_met(self) -> bool:
        return True
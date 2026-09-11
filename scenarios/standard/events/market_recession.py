from app.event.event import Event, EventState

EVENT_NAME = "Market Recession"

class MarketRecession(Event):
    
    def __init__(self, game_id: str, event_name: str, event_data: dict):
        Event.__init__(self, game_id, event_name, event_data)

    def activate(self):
        self.state = EventState.ACTIVE
        self.expire_turn = self.game.turn + self.duration + 1

    def has_conditions_met(self) -> bool:
        return True
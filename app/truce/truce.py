from app.game.games import Games

class Truce:

    def __init__(self, truce_id: str, data: dict, game_id: str):
        self._game_id = game_id
        self._data = data
        self.id = truce_id
        self.start_turn: int = self._data["startTurn"]

    @property
    def end_turn(self) -> int:
        return self._data["endTurn"]
    
    @end_turn.setter
    def end_turn(self, turn: int) -> None:
        self._data["endTurn"] = turn

    @property
    def signatories(self) -> dict[str, bool]:
        return self._data["signatories"]
    
    @signatories.setter
    def signatories(self, value: dict) -> None:
        self._data["signatories"] = value

    @property
    def is_active(self) -> bool:
        game = Games.load(self._game_id)
        return True if self.end_turn > game.turn else False

    def __str__(self):
        from app.nation.nations import Nations

        signatories_list = list(self.signatories.keys())
        
        nations_list = []
        for nation_id in signatories_list:
            nation = Nations.get(nation_id)
            nations_list.append(nation.name)
        
        return " - ".join(nations_list)
from app.nation.nations import Nations

class Combatant:
    
    def __init__(self, d: dict):
        self._data = d
        self.id: str = self._data["id"]
        self.role: str = self._data["role"]

        nation = Nations.get(self.id)
        self.name = nation.name
        # TODO - restructure Combatant and Nation to both pull nationattribute sfrom a parent class
    
    @property
    def target_id(self) -> str:
        return self._data["targetID"]
    
    @target_id.setter
    def target_id(self, value: str):
        self._data["targetID"] = value

    @property
    def justification(self) -> str:
        return self._data["justification"]

    @justification.setter
    def justification(self, value: str):
        self._data["justification"] = value

    @property
    def attacks(self) -> int:
        return self._data["attacks"]

    @attacks.setter
    def attacks(self, value: int):
        self._data["attacks"] = value

    @property
    def destroyed_units(self) -> int:
        return self._data["enemyUnitsDestroyed"]
    
    @destroyed_units.setter
    def destroyed_units(self, value: int):
        self._data["enemyUnitsDestroyed"] = value

    @property
    def destroyed_improvements(self) -> int:
        return self._data["enemyImprovementsDestroyed"]

    @destroyed_improvements.setter
    def destroyed_improvements(self, value: int):
        self._data["enemyImprovementsDestroyed"] = value

    @property
    def lost_units(self) -> int:
        return self._data["friendlyUnitsDestroyed"]

    @lost_units.setter
    def lost_units(self, value: int):
        self._data["friendlyUnitsDestroyed"] = value

    @property
    def lost_improvements(self) -> int:
        return self._data["friendlyImprovementsDestroyed"]

    @lost_improvements.setter
    def lost_improvements(self, value: int):
        self._data["friendlyImprovementsDestroyed"] = value

    @property
    def launched_missiles(self) -> int:
        return self._data["missilesLaunched"]

    @launched_missiles.setter
    def launched_missiles(self, value: int):
        self._data["missilesLaunched"] = value

    @property
    def launched_nukes(self) -> int:
        return self._data["nukesLaunched"]

    @launched_nukes.setter
    def launched_nukes(self, value: int):
        self._data["nukesLaunched"] = value

    @property
    def claims(self) -> dict:
        return self._data["claims"]

    @claims.setter
    def claims(self, value: dict) -> None:
        self._data["claims"] = value
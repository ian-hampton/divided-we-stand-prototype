from app.game.games import Games
from app.scenario.scenario import ScenarioInterface as SD
from app.nation.nation import Nation
from .war_claims import ManageWarClaims
from .combatant import Combatant

class War:

    def __init__(self, war_name: str, data: dict, game_id: str):
        
        self.name = war_name
        self._data = data
        self._game_id = game_id
        self.attackers = WarScoreData(self._data["attackerWarScore"])
        self.defenders = WarScoreData(self._data["defenderWarScore"])

    @property
    def start(self) -> int:
        return self._data["start"]

    @property
    def end(self) -> int:
        return self._data["end"]
    
    @end.setter
    def end(self, turn: int) -> None:
        self._data["end"] = turn

    @property
    def outcome(self) -> str:
        return self._data["outcome"]

    @outcome.setter
    def outcome(self, outcome_str: str) -> None:
        self._data["outcome"] = outcome_str

    @property
    def combatants(self) -> dict:
        return self._data["combatants"]

    @combatants.setter
    def combatants(self, value: dict) -> None:
        self._data["combatants"] = value

    @property
    def log(self) -> list:
        return self._data["warLog"]

    @log.setter
    def log(self, value: list) -> None:
        self._data["warLog"] = value

    def _resolve_war_justification(self, nation_id: str):
        
        from app.nation.nations import Nations
        from app.region.regions import Regions
        game = Games.load(self._game_id)
        
        winner_nation = Nations.get(nation_id)
        winner_combatant_data = self.get_combatant(nation_id)
        war_justification_data = SD.war_justificiations[winner_combatant_data.justification]

        if war_justification_data.has_war_claims:
            for region_id, original_owner_id in winner_combatant_data.claims.items():
                region = Regions.load(region_id)
                
                # do not take over regions that have changed ownership since start of war
                if str(region.data.owner_id) != original_owner_id:
                    continue
                    
                if region.improvement.name is not None:
                    looser_nation = Nations.get(original_owner_id)
                    looser_nation.improvement_counts[region.improvement.name] -= 1
                    winner_nation.improvement_counts[region.improvement.name] += 1
                
                region.data.owner_id = winner_nation.id
                region.data.occupier_id = "0"

        for resource_name, amount in war_justification_data.winner_stockpile_gains:
            winner_nation.update_stockpile(resource_name, amount)

        for resource_name, amount in war_justification_data.looser_stockpile_gains:
            looser_nation = Nations.get(winner_combatant_data.target_id)
            looser_nation.update_stockpile(resource_name, amount)

        if war_justification_data.looser_penalties is not None:
            looser_nation = Nations.get(winner_combatant_data.target_id)
            war_justification_data.looser_penalties["Expire Turn"] = game.turn + war_justification_data.looser_penalty_duration + 1
            looser_nation.tags[f"Defeated by {winner_nation} in {self.name}"] = war_justification_data.looser_penalties

        if war_justification_data.winner_becomes_independent:
            winner_nation.status = "Independent Nation"

        if war_justification_data.looser_releases_all_puppet_states:
            looser_nation = Nations.get(winner_combatant_data.target_id)
            for nation in Nations:
                if looser_nation.name in nation.status:
                    winner_nation.status = "Independent Nation"

        if war_justification_data.looser_becomes_puppet_state:
            looser_nation = Nations.get(winner_combatant_data.target_id)
            looser_nation.status = f"Puppet State of {winner_nation.name}"

    def add_combatant(self, nation: Nation, role: str, target_id: str) -> None:
        
        combatant_data = {
            "id": nation.id,
            "role": role,
            "justification": "TBD",
            "targetID": target_id,
            "claims": {},
            "attacks": 0,
            "enemyUnitsDestroyed": 0,
            "enemyImprovementsDestroyed": 0,
            "friendlyUnitsDestroyed": 0,
            "friendlyImprovementsDestroyed": 0,
            "missilesLaunched": 0,
            "nukesLaunched": 0
        }

        self.combatants[nation.id] = combatant_data

    def get_combatant(self, nation_id: str) -> "Combatant":
        
        if nation_id in self.combatants:
            return Combatant(self.combatants[nation_id])
        
        raise Exception(f"Failed to retrieve nation #{nation_id} combatant data in war {self.name}.")

    def get_role(self, nation_id: str) -> str:
        if nation_id in self.combatants:
            combatant = self.get_combatant(nation_id)
            return combatant.role
        return None

    def get_main_combatant_ids(self) -> tuple[str, str]:
        
        main_attacker_id = ""
        main_defender_id = ""

        for nation_id in self.combatants:
            combatant = self.get_combatant(nation_id)
            if combatant.role == "Main Attacker":
                main_attacker_id = nation_id
            elif combatant.role == "Main Defender":
                main_defender_id = nation_id

        return main_attacker_id, main_defender_id
    
    def is_on_same_side(self, nation_id_1: str, nation_id_2: str) -> bool:
        
        combatant_1 = self.get_combatant(nation_id_1)
        combatant_2 = self.get_combatant(nation_id_2)

        if "Attacker" in combatant_1.role and "Attacker" in combatant_2.role:
            return True
        elif "Defender" in combatant_1.role and "Defender" in combatant_2.role:
            return True
        
        return False

    def add_missing_justifications(self) -> None:
        
        from app.nation.nations import Nations

        for combatant_id in self.combatants:
            
            combatant = self.get_combatant(combatant_id)
            combatant_nation = Nations.get(combatant_id)
            region_claims_list = []

            if combatant.justification != "TBD":
                continue
                
            war_justification = input(f"Please enter {combatant.name} war justification for {self.name} or enter SKIP to postpone: ")
            if war_justification == "SKIP":
                continue

            # process war claims
            if SD.war_justificiations[war_justification].has_war_claims:

                manage_claims = ManageWarClaims(combatant.name, war_justification)
                claim_cost, region_claims_list = manage_claims.get_war_claims()
                if float(combatant_nation.get_stockpile("Political Power")) - claim_cost < 0:
                    combatant_nation.action_log.append(f"Error: Not enough political power for war claims.")
                    continue
                
                combatant.target_id = "N/A"
                combatant_nation.update_stockpile("Political Power", -1 * claim_cost)
                combatant.claims = manage_claims.claim_pairs(region_claims_list)
            
            # OR handle war justification that does not seize territory
            else:
                target_id = input(f"Enter nation_id of nation {combatant.name} is targeting with {war_justification}: ")
                combatant.target_id = str(target_id)
            
            combatant.justification = war_justification

    def update_warscore(self, side: str, category: str, amount: int) -> None:
        """
        This is an ugly solution. Too bad!

        Args:
            side (str): _description_
            category (str): _description_
            amount (WarScore): _description_
        """
        if side == "Attacker":
            match category:
                case "occupation":
                    self.attackers.occupation += amount
                case "decisive_battles":
                    self.attackers.decisive_battles += amount
                case "destroyed_units":
                    self.attackers.destroyed_units += amount
                case "destroyed_improvements":
                    self.attackers.destroyed_improvements += amount
                case "captures":
                    self.attackers.captures += amount
                case "nuclear_strikes":
                    self.attackers.nuclear_strikes += amount
        elif side == "Defender":
            match category:
                case "occupation":
                    self.defenders.occupation += amount
                case "decisive_battles":
                    self.defenders.decisive_battles += amount
                case "destroyed_units":
                    self.defenders.destroyed_units += amount
                case "destroyed_improvements":
                    self.defenders.destroyed_improvements += amount
                case "captures":
                    self.defenders.captures += amount
                case "nuclear_strikes":
                    self.defenders.nuclear_strikes += amount

    def calculate_score_threshold(self) -> tuple:
        
        from app.nation.nations import Nations

        # initial win threshold is a 100 point difference
        attacker_threshold = 100
        defender_threshold = 100

        # check for unyielding and crime syndicate
        for combatant_id in self.combatants:
            combatant = self.get_combatant(combatant_id)
            combatant_nation = Nations.get(combatant_id)
            
            # add modifiers to defender threshold
            if combatant.role == "Main Attacker" and defender_threshold == 100:
                if combatant_nation.gov == "Crime Syndicate":
                    defender_threshold = None
                elif "Unyielding" in combatant_nation.completed_research:
                    defender_threshold += 50
            
            # add modifiers to attacker threshold
            elif combatant.role == "Main Defender" and attacker_threshold == 100:
                if combatant_nation.gov == "Crime Syndicate":
                    attacker_threshold = None
                elif "Unyielding" in combatant_nation.completed_research:
                    attacker_threshold += 50

        # if not crime syndicate compute remaining threshold
        if attacker_threshold is not None:
            attacker_threshold += self.defenders.total
        if defender_threshold is not None:
            defender_threshold += self.attackers.total

        return attacker_threshold, defender_threshold

    def withdraw_units(self) -> None:
        """
        Forces all units in foreign territory to withdraw back to friendly territory if they are not participating in war.
        """
        from app.nation.nations import Nations
        from app.region.regions import Regions

        for region in Regions:
            
            # a unit can only be present in another nation without occupation if a war just ended 
            if region.unit.name is not None and region.unit.owner_id != region.data.owner_id and region.data.occupier_id == "0":
                
                nation = Nations.get(region.unit.owner_id)
                target_id = region.find_suitable_region()
                
                if target_id is not None:
                    nation.action_log.append(f"Withdrew {region.unit.name} {region.id} to {target_id}.")
                    region.move_unit(Regions.load(target_id), withdraw=True)
                else:
                    nation.action_log.append(f"Failed to withdraw {region.unit.name} {region.id}. Unit disbanded!")
                    nation.unit_counts[region.unit.name] -= 1
                    region.unit.clear()

    def end_conflict(self, outcome: str) -> None:
        """
        Ends and resolves this war according to a certain outcome.

        Args:
            outcome (str): Either 'Attacker Victory' or 'Defender Victory' or 'White Peace'
        """
        from app.nation.nations import Nations
        from app.region.regions import Regions
        from app.truce.truces import Truces
        
        game = Games.load(self._game_id)
        truce_length = 4
        
        # resolve war justifications
        match outcome:
            
            case "Attacker Victory":
                for combatant_id in self.combatants:
                    combatant = self.get_combatant(combatant_id)
                    if combatant.justification in ["TBD", "N/A"]:
                        continue
                    if "Attacker" in combatant.role:
                        self._resolve_war_justification(combatant_id)
                    if "Main Attacker" == combatant.role:
                        truce_length = SD.war_justificiations[combatant.justification].truce_duration

            case "Defender Victory":
                for combatant_id in self.combatants:
                    combatant = self.get_combatant(combatant_id)
                    if "Defender" in combatant.role:
                        self._resolve_war_justification(combatant_id)
                    if "Main Defender" == combatant.role:
                        truce_length = SD.war_justificiations[combatant.justification].truce_duration
        
        # add truce periods
        for combatant_id in self.combatants:
            attacker = self.get_combatant(combatant_id)
            if 'Attacker' not in attacker.role:
                continue
            for temp_id in self.combatants:
                defender = self.get_combatant(temp_id)
                if temp_id == combatant_id or 'Defender' not in defender.role:
                    continue
                signatories = [attacker.id, defender.id]
                Truces.create(signatories, truce_length)

        # update war
        self.end = game.turn
        self.outcome = outcome

        # end occupations
        for region in Regions:
            if region.data.owner_id in self.combatants and region.data.occupier_id in self.combatants:
                region.data.occupier_id = "0"

        # withdraw units
        self.withdraw_units()

        # resolve foreign interference tag if applicable (event)
        attacker_id, defender_id = self.get_main_combatant_ids()
        attacker_nation = Nations.get(attacker_id)
        defender_nation = Nations.get(defender_id)
        if "Foreign Interference" in attacker_nation.tags and attacker_nation.tags["Foreign Interference"]["Foreign Interference Target"] == defender_nation.name:
            del attacker_nation.tags["Foreign Interference"]
            if outcome == "Attacker Victory":
                attacker_nation.update_stockpile("Dollars", 50)
                attacker_nation.update_stockpile("Research", 20)
                attacker_nation.update_stockpile("Advanced Metals", 10)

class WarScoreData:
    
    def __init__(self, d: dict):
        self._data = d

    @property
    def total(self) -> int:
        return self._data["total"]
    
    @total.setter
    def total(self, value: int) -> None:
        self._data["total"] = value

    @property
    def occupation(self) -> int:
        return self._data["occupation"]

    @occupation.setter
    def occupation(self, value: int) -> None:
        self._data["occupation"] = value

    @property
    def decisive_battles(self) -> int:
        return self._data["decisiveBattles"]
    
    @decisive_battles.setter
    def decisive_battles(self, value: int) -> None:
        self._data["decisiveBattles"] = value

    @property
    def destroyed_units(self) -> int:
        return self._data["enemyUnitsDestroyed"]

    @destroyed_units.setter
    def destroyed_units(self, value: int) -> None:
        self._data["enemyUnitsDestroyed"] = value

    @property
    def destroyed_improvements(self) -> int:
        return self._data["enemyImprovementsDestroyed"]
    
    @destroyed_improvements.setter
    def destroyed_improvements(self, value: int) -> None:
        self._data["enemyImprovementsDestroyed"] = value

    @property
    def captures(self) -> int:
        return self._data["capitalCaptures"]

    @captures.setter
    def captures(self, value: int) -> None:
        self._data["capitalCaptures"] = value

    @property
    def nuclear_strikes(self) -> int:
        return self._data["nukedEnemyRegions"]

    @nuclear_strikes.setter
    def nuclear_strikes(self, value: int) -> None:
        self._data["nukedEnemyRegions"] = value
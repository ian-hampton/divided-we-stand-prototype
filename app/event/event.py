from app.game.games import Games
from app.scenario.scenario import ScenarioInterface as SD
from app.nation.nation import Nation
from app.nation.nations import Nations

class Event:

    def __init__(self, game_id: str, event_name: str, event_data: dict):

        self.name: str = event_name
        self.type: str = event_data["Type"]
        self.duration: int = event_data["Duration"]
        self.targets: list = event_data.get("Targets", [])
        self.expire_turn: int = event_data.get("Expiration", -1)

        self.game_id = game_id
        self.game = Games.load(self.game_id)
        self.state = -1

        # EVENT STATES
        #  2  event is pending input from players
        #  1  event is active and does not require attention from players
        #  0  event is completed and ready to be archived

    def export(self) -> dict:
        
        return {
            "Name": self.name,
            "Type": self.type,
            "Duration": self.duration,
            "Targets": self.targets,
            "Expiration": self.expire_turn
        }
    
    def run_before(self, actions_dict: dict[str, list]) -> None:
        self.state = 1

    def run_after(self) -> None:
        self.state = 1
    
    def _gain_free_research(self, research_name: str, nation: Nation) -> bool:
        """
        Returns updated playerdata_List and a bool that is True if the research was valid, False otherwise.
        """

        prereq = SD.technologies[research_name].prerequisite
        if prereq is not None and prereq not in nation.completed_research:
            return False

        nation.add_tech(research_name)
        nation.award_research_bonus(research_name)

        return True

    def _collect_basic_decisions(self) -> dict:
        """
        Simple function to collect decisions from players in the terminal.
        """

        decision_dict = {}
        for player_id in self.targets:
            nation = Nations.get(player_id)
            while True:
                decision = input(f"Enter {nation.name} decision: ")
                if decision in self.choices:
                    break
            decision_dict[player_id] = decision
        
        return decision_dict

    def _get_votes_nation(self) -> dict:
        
        vote_tally_dict = {}
    
        for nation_id in self.targets:
            
            nation = Nations.get(nation_id)
            
            while True:
                
                decision = input(f"Enter {nation.name} vote: ")
                decision = decision.strip()
                if decision == "Abstain":
                    break

                decision_data = decision.split()
                vote_count = int(decision_data[0])
                target_name = " ".join(decision_data[1:])

                if vote_count > float(nation.get_stockpile("Political Power")):
                    continue
                try:
                    target_nation = Nations.get(target_name)
                except:
                    continue
                
                if target_name in vote_tally_dict:
                    vote_tally_dict[target_name] += vote_count
                else:
                    vote_tally_dict[target_name] = vote_count
                
                nation.update_stockpile("Political Power", -1 * vote_count)
                break
        
        return vote_tally_dict

    def _get_votes_option(self) -> dict[str, int]:

        vote_tally_dict = {}
        
        for nation_id in self.targets:
            
            nation = Nations.get(nation_id)
            
            while True:
                
                decision = input(f"Enter {nation.name} vote: ")
                decision = decision.strip()
                if decision == "Abstain":
                    break
                
                # expecting something like "# OPTION NAME"
                decision_data = decision.split()
                vote_count = int(decision_data[0])
                option_name = " ".join(decision_data[1:])

                if vote_count > float(nation.get_stockpile("Political Power")):
                    continue
                if option_name not in self.choices:
                    continue
                
                if option_name in vote_tally_dict:
                    vote_tally_dict[option_name] += vote_count
                else:
                    vote_tally_dict[option_name] = vote_count
                
                nation.update_stockpile("Political Power", -1 * vote_count)
                break
        
        return vote_tally_dict

    def _determine_vote_winner(self) -> str | None:

        if len(self.vote_tally) == 0:
            return None

        sorted_vote_tally = dict(sorted(self.vote_tally.items(), key=lambda item: item[1], reverse=True))

        if len(sorted_vote_tally) == 1:
            winning_outcome_data = list(sorted_vote_tally.items())[:1]
            return winning_outcome_data[0][0]

        top_two = list(sorted_vote_tally.items())[:2]
        if top_two[0][1] == top_two[1][1]:
            return None
        
        return top_two[0][0]
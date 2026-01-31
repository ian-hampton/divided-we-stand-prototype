import copy

class SD_WarJustification:
    
    def __init__(self, d: dict):
        
        self.d = d
        self.required_agenda: str = d["Required Agenda"]
        self.truce_duration: int = d["Truce Duraton"]
        
        self.has_war_claims: bool = d.get("War Claims") is not None
        self.free_claims: int = None if not self.has_war_claims else d["War Claims"]["Free"]
        self.max_claims: int = None if not self.has_war_claims else d["War Claims"]["Max"]
        self.claim_cost: int = None if not self.has_war_claims else d["War Claims"]["Cost"]
        
        self.winner_stockpile_gains: dict = d.get("Winner Stockpile Gains", {})
        self.winner_becomes_independent: bool = d.get("Winner Becomes Independent") is not None

        self.looser_stockpile_gains: dict = d.get("Looser Stockpile Gains", {})
        self.looser_penalty_duration: int = d.get("Looser Penalty Duration", None)
        self.looser_releases_all_puppet_states: bool = d.get("Looser Releases All Puppet States") is not None
        self.looser_becomes_puppet_state: bool = d.get("Looser Becomes Puppet State") is not None
        
        self.for_puppet_states: bool = d.get("For Puppet States") is not None
        self.target_requirements: dict = d.get("Target Requirements", {})

    @property
    def looser_penalties(self) -> dict | None:
        return copy.deepcopy(self.d.get("Looser Penalties", None))
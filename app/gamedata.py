import csv
import json
from datetime import datetime
from enum import Enum, IntEnum
from dataclasses import dataclass
from typing import ClassVar, Iterator, Tuple

class GamesMeta(type):

    def __iter__(cls) -> Iterator["Game"]:
        for game_id in cls._data:
            yield Game(game_id)

    def __len__(cls):
        return len(cls._data)

@dataclass
class Games(metaclass=GamesMeta):

    _data: ClassVar[dict[str, dict]]
    _instances: ClassVar[dict[str, "Game"]] = {}
    with open("active_games.json", "r") as json_file:
        _data = json.load(json_file)

    @classmethod
    def save(cls) -> None:
        with open("active_games.json", 'w') as json_file:
            json.dump(cls._data, json_file, indent=4)

    @classmethod
    def create(cls, game_id: str, form_data_dict: dict) -> None:

        GAME_VERSION = "Development"
        current_date = datetime.today().date()

        with open("game_records.json", 'r') as json_file:
            game_records_dict = json.load(json_file)
        
        game_data = {
            "name": form_data_dict["Game Name"],
            "number": len(game_records_dict) + len(cls) + 1,
            "turn": 0,
            "status": 101,
            "information": {
                "version": GAME_VERSION,
                "scenario": form_data_dict["Scenario"],
                "map": form_data_dict["Map"],
                "playerCount": form_data_dict["Player Count"],
                "victoryConditions": form_data_dict["Victory Conditions"],
                "turnLength": form_data_dict["Turn Length"],
                "fogOfWar": form_data_dict["Fog of War"],
                "acceleratedSchedule":form_data_dict["Accelerated Schedule"],
                "weekendDeadlines": form_data_dict["Deadlines on Weekends"]
            },
            "statistics": {
                "regionDisputes": 0,
                "daysElapsed": 0,
                "gameStarted": current_date.strftime("%m/%d/%Y")
            },
            "inactiveEvents": [],
            "activeEvents": {},
            "currentEvent": {}
        }

        cls._data[game_id] = game_data

    @classmethod
    def delete(cls, game_id: str) -> None:
        if game_id in cls._data:
            del cls._data[game_id]

    @classmethod
    def load(cls, game_id: str) -> "Game":
        
        # trying to load a game that does not exist is a critical error
        if game_id not in cls._data:
            raise Exception(f"Error loading Game. {game_id} not recognized as a valid Game ID.")
        
        # reuse cached Game object if it exists
        if game_id not in cls._instances:
            cls._instances[game_id] = Game(game_id)
        return cls._instances[game_id]

class Game:
    
    def __init__(self, game_id: str):

        self._data = Games._data[game_id]
        
        self.id = game_id
        self.info = GameInformation(self._data["information"])
        self.stats = GameStatistics(self._data["statistics"])

    @property
    def name(self) -> str:
        return self._data["name"]
    
    @name.setter
    def name(self, value: str) -> None:
        self._data["name"] = value
        
    @property
    def number(self) -> int:
        return self._data["number"]

    @number.setter
    def number(self, value: int) -> None:
        self._data["number"] = value

    @property
    def turn(self) -> int:
        return self._data["turn"]

    @turn.setter
    def turn(self, value: int) -> None:
        self._data["turn"] = value
    
    @property
    def status(self) -> "GameStatus":
        return GameStatus(self._data["status"])
    
    @status.setter
    def status(self, value: "GameStatus") -> None:
        self._data["status"] = value.value

    @property
    def current_event(self) -> dict:
        return self._data["currentEvent"]
    
    @current_event.setter
    def current_event(self, value: dict) -> None:
        self._data["currentEvent"] = value
    
    @property
    def active_events(self) -> dict:
        return self._data["activeEvents"]
    
    @active_events.setter
    def active_events(self, value: dict) -> None:
        self._data["activeEvents"] = value
    
    @property
    def inactive_events(self) -> list:
        return self._data["inactiveEvents"]
    
    @inactive_events.setter
    def inactive_events(self, value: list) -> None:
        self._data["inactiveEvents"] = value

    def get_season_and_year(self, turn=-1) -> Tuple[str, str]:

        if turn == -1:
            turn = self.turn
        
        match (turn % 4):
            case 0:
                season = 'Winter'
            case 1:
                season = 'Spring'
            case 2:
                season = 'Summer'
            case 3:
                season = 'Fall'

        quotient = turn // 4
        year = 2021 + quotient
        if season == 'Winter':
            year -= 1

        return season, year

    def get_map_string(self) -> str:
        map_name_actual = ""
        for char in self.info.map:
            if char.isalpha():
                map_name_actual += char.lower()
            elif char == " ":
                map_name_actual += "_"
        return map_name_actual.strip("_")
    
    def get_market_data(self, refine=12, include_header=False) -> list:
        """
        Reads rmdata.csv and generates a list of all currently relevant transactions.
        """

        # get list of all transactions
        rmdata_list = []
        with open(f"gamedata/{self.id}/rmdata.csv", 'r') as file:
            reader = csv.reader(file)
            if not include_header:
                next(reader,None)
            for row in reader:
                if row != []:
                    rmdata_list.append(row)

        # refine list as needed
        rmdata_refined_list = []
        for transaction in rmdata_list:
            transaction[0] = int(transaction[0])
            transaction[3] = int(transaction[3])
            if refine and transaction[0] < self.turn - refine:
                continue
            rmdata_refined_list.append(transaction)
        
        return rmdata_refined_list

    def set_startdate(self) -> None:
        current_date = datetime.today().date()
        current_date_string = current_date.strftime("%m/%d/%Y")
        self.stats.date_started = current_date_string
        self.stats.days_elapsed = 0

    def updated_days_ellapsed(self) -> None:
        current_date = datetime.today().date()
        current_date_string = current_date.strftime("%m/%d/%Y")
        current_date_obj = datetime.strptime(current_date_string, "%m/%d/%Y")
        start_date_obj = datetime.strptime(self.stats.date_started, "%m/%d/%Y")
        date_difference = current_date_obj - start_date_obj
        self.stats.days_elapsed = date_difference.days

    def update_market_data(self, new_transactions_list) -> None:
        all_transactions_list = self.get_market_data(refine=0)
        with open(f"gamedata/{self.id}/rmdata.csv", 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(["Turn", "Nation", "Bought/Sold", "Count", "Resource Exchanged"])
            writer.writerows(all_transactions_list)
            writer.writerows(new_transactions_list)

class GameInformation:
    
    def __init__(self, d: dict):
        self._data = d

    @property
    def version(self) -> str:
        return self._data["version"]

    @version.setter
    def version(self, value: str) -> None:
        self._data["version"] = value

    @property
    def scenario(self) -> str:
        return self._data["scenario"]

    @scenario.setter
    def scenario(self, value: str) -> None:
        self._data["scenario"] = value

    @property
    def map(self) -> str:
        return self._data["map"]

    @map.setter
    def map(self, value: str) -> None:
        self._data["map"] = value

    @property
    def player_count(self) -> int:
        return self._data["playerCount"]

    @player_count.setter
    def player_count(self, value: int) -> None:
        self._data["playerCount"] = value

    @property
    def victory_conditions(self) -> str:
        return self._data["victoryConditions"]

    @victory_conditions.setter
    def victory_conditions(self, value: str) -> None:
        self._data["victoryConditions"] = value

    @property
    def turn_length(self) -> str:
        return self._data["turnLength"]

    @turn_length.setter
    def turn_length(self, value: str) -> None:
        self._data["turnLength"] = value

    @property
    def fog_of_war(self) -> bool:
        return self._data["fogOfWar"]

    @fog_of_war.setter
    def fog_of_war(self, value: bool) -> None:
        self._data["fogOfWar"] = value

    @property
    def accelerated_schedule(self) -> bool:
        return self._data["acceleratedSchedule"]

    @accelerated_schedule.setter
    def accelerated_schedule(self, value: bool) -> None:
        self._data["acceleratedSchedule"] = value

    @property
    def weekend_deadlines(self) -> bool:
        return self._data["weekendDeadlines"]

    @weekend_deadlines.setter
    def weekend_deadlines(self, value: bool) -> None:
        self._data["weekendDeadlines"] = value

class GameStatistics:
    
    def __init__(self, d: dict):
        self._data = d

    @property
    def region_disputes(self) -> int:
        return self._data["regionDisputes"]
    
    @region_disputes.setter
    def region_disputes(self, value: int) -> None:
        self._data["regionDisputes"] = value
    
    @property
    def days_elapsed(self) -> int:
        return self._data["daysElapsed"]
    
    @days_elapsed.setter
    def days_elapsed(self, value: int) -> None:
        self._data["daysElapsed"] = value
    
    @property
    def date_started(self) -> str:
        return self._data["gameStarted"]
    
    @date_started.setter
    def date_started(self, value: str) -> None:
        self._data["gameStarted"] = value

class GameStatus(IntEnum):
    REGION_SELECTION = 101
    NATION_SETUP = 102
    ACTIVE = 201
    ACTIVE_PENDING_EVENT = 202
    FINISHED = 301

    def is_setup(self) -> bool:
        return 100 < self.value < 200

    def is_active(self) -> bool:
        return 200 < self.value < 300

    def is_finished(self) -> bool:
        return self is GameStatus.FINISHED
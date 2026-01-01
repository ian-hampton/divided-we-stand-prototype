"""
File: mock_games.py
Author: Ian Hampton
Created Date: 1st January 2026

Mocks the Games class to prevent writes to disk. Required for tests to work.

All of the major dataclasses import Games immediately. This is a problem for testing because Games immediately tries to load active_games.json when imported.
We do not want to use the real active_games.json. We can initialize a fake module to prevent Games from doing any initial loading.
Once loaded, we stuff the fake module with a mocked Games and call it a day.

This file is imported by base.py. You should not need to import it yourself.
"""

import json
import sys
import types

from app.game.game import Game

fake_games_module = types.ModuleType("app.game.games")
with open("tests/mock-files/active_games.json") as f:
    fake_games_data = json.load(f)

class GamesMock:
    _data = fake_games_data
    _instances = {}

    @classmethod
    def load(cls, game_id):
        return Game(game_id, cls._data[game_id])

fake_games_module.Games = GamesMock
sys.modules["app.game.games"] = fake_games_module
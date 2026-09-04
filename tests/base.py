"""
File: base.py
Author: Ian Hampton
Created Date: 1st January 2026

This is the core code required to run any tests on the turn procesor. You must import this before running any tests!
"""

import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from . import mock_games
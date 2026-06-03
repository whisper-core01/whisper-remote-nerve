# tests/conftest.py

"""
Pytest path bootstrap.

Allows tests to be run either from the project root:

    pytest -q

or directly from the tests directory:

    cd tests
    pytest -q test_vault_v01.py

Without this file, running pytest from tests/ prevents Python from seeing
project-level modules such as mce_v01.py, rotor_machine_v01.py and vault_v01.py.
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

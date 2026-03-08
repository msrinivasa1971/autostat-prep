"""
Root conftest — ensures the project root is on sys.path so that
`from app.xxx import yyy` works when pytest is run from the repo root.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

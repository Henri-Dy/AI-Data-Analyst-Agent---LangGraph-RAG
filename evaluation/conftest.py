"""Makes `backend/app` importable from evaluation/*.py, the same sys.path
pattern used by backend/scripts/*.py — evaluation/ is a sibling of backend/,
not a package under it, so pytest run from the repo root wouldn't otherwise
find `app`.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

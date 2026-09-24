"""Load Oracle without using Pool (Pool executes Python decks)."""

from __future__ import annotations

import sys
from functools import lru_cache
from pathlib import Path

SIM_ROOT = Path(__file__).resolve().parents[1] / "simulator"
_ENGINE_DIR = SIM_ROOT / "engine"

if str(_ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(_ENGINE_DIR))
if str(SIM_ROOT) not in sys.path:
    sys.path.insert(0, str(SIM_ROOT))

from oracle import Oracle  # noqa: E402  (lab module; class Oracle only)


@lru_cache(maxsize=1)
def get_oracle() -> Oracle:
    return Oracle()

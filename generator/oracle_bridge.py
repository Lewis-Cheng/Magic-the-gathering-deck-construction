"""Load lab Oracle without using Pool (Pool execs Python decks and defaults Ovika)."""

from __future__ import annotations

import sys
from functools import lru_cache
from pathlib import Path

OVIKA_ROOT = Path(__file__).resolve().parents[1] / "ovika"
_ENGINE_DIR = OVIKA_ROOT / "engine"

if str(_ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(_ENGINE_DIR))
if str(OVIKA_ROOT) not in sys.path:
    sys.path.insert(0, str(OVIKA_ROOT))

from oracle import Oracle  # noqa: E402  (lab module; class Oracle only)


@lru_cache(maxsize=1)
def get_oracle() -> Oracle:
    return Oracle()

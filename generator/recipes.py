"""Load theme recipes from JSON. Not Ovika 28-land / convoke shape."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

RECIPES_DIR = Path(__file__).resolve().parent / "recipes"


@lru_cache(maxsize=32)
def load_recipe(theme: str) -> dict[str, Any]:
    path = RECIPES_DIR / f"{theme}.json"
    if not path.exists():
        raise FileNotFoundError(f"no recipe for theme: {theme}")
    return json.loads(path.read_text(encoding="utf-8"))

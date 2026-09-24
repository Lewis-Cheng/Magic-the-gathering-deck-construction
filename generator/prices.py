"""Local USD prices. Missing is None, never 0. Optional Scryfall only if enabled."""

from __future__ import annotations

import json
import os
import urllib.request
from functools import lru_cache
from pathlib import Path
from typing import Optional

PRICES_PATH = Path(__file__).resolve().parents[1] / "ovika" / "rulebook" / "data" / "card_prices.json"
PRICES_AS_OF = "2026-09-13-local-card_prices.json"
USER_AGENT = "mtg-edh-generator/1.0 (local V1; contact: lab)"


@lru_cache(maxsize=1)
def _table() -> dict[str, Optional[float]]:
    raw = json.loads(PRICES_PATH.read_text(encoding="utf-8"))
    out: dict[str, Optional[float]] = {}
    for k, v in raw.items():
        if v is None:
            out[k] = None
            continue
        try:
            out[k] = float(v)
        except (TypeError, ValueError):
            out[k] = None
    return out


def prices_as_of() -> str:
    return PRICES_AS_OF


def lookup(name: str, *, fetch_scryfall: Optional[bool] = None) -> Optional[float]:
    """Return USD or None. Never coerce missing to 0.0."""
    table = _table()
    if name in table:
        return table[name]
    if " // " in name:
        front = name.split(" // ", 1)[0]
        if front in table:
            return table[front]
    enabled = fetch_scryfall
    if enabled is None:
        enabled = os.environ.get("GENERATOR_SCRYFALL") == "1"
    if enabled:
        fetched = _scryfall_usd(name)
        if fetched is not None:
            return fetched
    return None


def _scryfall_usd(name: str) -> Optional[float]:
    q = urllib.parse.quote(name)
    url = f"https://api.scryfall.com/cards/named?exact={q}"
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception:
        return None
    prices = (data.get("prices") or {})
    usd = prices.get("usd") or prices.get("usd_foil")
    if usd is None:
        return None
    try:
        return float(usd)
    except (TypeError, ValueError):
        return None


# Imported lazily to keep urllib.parse available
import urllib.parse  # noqa: E402

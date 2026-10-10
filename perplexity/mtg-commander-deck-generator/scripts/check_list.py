#!/usr/bin/env python3
"""Validate a research-layer Commander JSON written by the Agent API skill.

Usage: python scripts/check_list.py deck.json
Exit 0 only if the file is structurally sellable or an explicit short collection draft.
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

BASICS = {
    "Plains",
    "Island",
    "Swamp",
    "Mountain",
    "Forest",
    "Wastes",
    "Snow-Covered Plains",
    "Snow-Covered Island",
    "Snow-Covered Swamp",
    "Snow-Covered Mountain",
    "Snow-Covered Forest",
}


def fail(msg: str) -> None:
    print(f"FAIL: {msg}", file=sys.stderr)
    raise SystemExit(1)


def main() -> None:
    if len(sys.argv) != 2:
        fail("usage: python scripts/check_list.py deck.json")
    path = Path(sys.argv[1])
    if not path.is_file():
        fail(f"missing file {path}")
    data = json.loads(path.read_text(encoding="utf-8"))

    commander = data.get("commander")
    if not commander or not isinstance(commander, str):
        fail("commander must be a non-empty string")

    confidence = data.get("confidence")
    if confidence != "research-only":
        fail('confidence must be "research-only" (no win_rate in this skill)')
    if "win_rate" in data:
        fail("win_rate is forbidden")

    cards = data.get("cards")
    if not isinstance(cards, list):
        fail("cards must be a list")

    missing = data.get("missing_slots")
    finished = missing in (None, [], 0)

    if finished and len(cards) != 99:
        fail(f"finished list must have 99 cards, got {len(cards)}")
    if not finished and len(cards) > 99:
        fail("short draft cannot exceed 99 cards")

    names = []
    new_count = 0
    total = 0.0
    for i, row in enumerate(cards):
        if not isinstance(row, dict):
            fail(f"card {i} is not an object")
        name = row.get("name")
        if not name:
            fail(f"card {i} missing name")
        names.append(name)
        src = row.get("source")
        if src not in ("collection", "new"):
            fail(f"{name}: source must be collection or new")
        if src == "new":
            new_count += 1
        price = row.get("price_usd")
        if price is None:
            if src == "new":
                fail(f"{name}: new card missing price (null is not $0)")
        else:
            if not isinstance(price, (int, float)) or price < 0:
                fail(f"{name}: bad price_usd")
            if src != "collection":
                total += float(price)

    counts = Counter(names)
    for name, n in counts.items():
        if n > 1 and name not in BASICS:
            fail(f"singleton violation: {name} x{n}")

    allowed = data.get("new_cards_allowed")
    commander_owned = data.get("commander_owned", True)
    billed_new = new_count + (0 if commander_owned else 1)
    if allowed is not None:
        if not isinstance(allowed, int) or allowed < 0:
            fail("new_cards_allowed must be int >= 0 or omitted")
        if billed_new > allowed:
            fail(f"new cards {billed_new} exceed allowance {allowed}")

    budget = data.get("budget_usd")
    if not isinstance(budget, (int, float)) or budget <= 0:
        fail("budget_usd must be > 0")
    stamped = data.get("total_usd")
    if stamped is not None and abs(float(stamped) - total) > 0.06:
        fail(f"total_usd {stamped} != summed new prices {total:.2f}")
    if total - 1e-6 > float(budget):
        fail(f"summed new prices {total:.2f} exceed budget {budget}")

    for key in ("ban_list_version", "prices_as_of", "win_condition"):
        if not data.get(key):
            fail(f"missing stamp {key}")

    print("ok", path)
    print(f"cards={len(cards)} new={billed_new} total_usd={total:.2f} finished={finished}")


if __name__ == "__main__":
    main()

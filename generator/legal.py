"""Commander legality: count, singleton, CI both faces, dated ban list, MDFC flags."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable

from generator.load import canonical_name, is_spell_front_mdfc, require_card

_BAN_PATH = Path(__file__).resolve().parent / "data" / "ban_list.json"

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
    "Snow-Covered Wastes",
}


def load_ban_list() -> dict[str, Any]:
    return json.loads(_BAN_PATH.read_text(encoding="utf-8"))


def ban_list_version() -> str:
    return str(load_ban_list()["version"])


def banned_names() -> set[str]:
    return set(load_ban_list()["banned"])


def color_identity(name: str) -> set[str]:
    card = require_card(name)
    return set(card.color_identity)


def is_basic_land(name: str) -> bool:
    key = canonical_name(name)
    if key in BASICS:
        return True
    card = require_card(key)
    return "Basic" in card.supertypes and card.is_land


def check_deck(commander: str, card_names: Iterable[str]) -> dict[str, Any]:
    """card_names is the 99. Commander is separate. Total must be 100."""
    violations: list[str] = []
    names = [canonical_name(n) for n in card_names]
    cmd = canonical_name(commander)

    if len(names) != 99:
        violations.append(f"expected 99 cards plus commander, got {len(names)} plus commander")

    all_cards = [cmd] + names
    if len(all_cards) != 100:
        violations.append(f"expected 100 objects (99 + commander), got {len(all_cards)}")

    try:
        cmd_card = require_card(cmd)
    except KeyError:
        violations.append(f"unknown commander: {commander}")
        return {"ok": False, "violations": violations, "ban_list_version": ban_list_version()}

    cmd_ci = set(cmd_card.color_identity)
    bans = banned_names()

    counts: dict[str, int] = {}
    for n in all_cards:
        counts[n] = counts.get(n, 0) + 1

    for n, c in counts.items():
        if c > 1 and not is_basic_land(n):
            violations.append(f"singleton violation: {n} x{c}")

    if cmd in bans:
        violations.append(f"banned commander: {cmd}")

    for n in names:
        try:
            card = require_card(n)
        except KeyError:
            violations.append(f"unknown card: {n}")
            continue
        if n in bans:
            violations.append(f"banned: {n}")
        ci = set(card.color_identity)
        if not ci.issubset(cmd_ci):
            violations.append(
                f"color identity: {n} is {''.join(sorted(ci)) or 'C'} not subset of commander {''.join(sorted(cmd_ci)) or 'C'}"
            )
        if is_spell_front_mdfc(n):
            violations.append(f"spell-front MDFC flagged avoid: {n}")

    return {
        "ok": len(violations) == 0,
        "violations": violations,
        "ban_list_version": ban_list_version(),
    }

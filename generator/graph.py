"""Theme-family graph suggestions. No {U,R} filter. Never auto-applied."""

from __future__ import annotations

from typing import Any

from generator.index import get_index
from generator.models import CardRow
from generator.prices import lookup


FAMILY_TAGS = {
    "tokens": ("token", "wipe"),
    "spellslinger": ("spell", "draw", "counter"),
    "enchantress": ("enchantment", "draw", "aura"),
    "voltron": ("aura", "equipment", "protection"),
    "reanimator": ("tutor", "ramp"),
    "stax": ("stax", "rock", "ramp"),
    "midrange": ("ramp", "draw", "removal", "counter"),
}


def suggestions_for(commander: str, theme: str, ci: set[str], cards: list[CardRow], limit: int = 5) -> list[dict[str, Any]]:
    family = FAMILY_TAGS.get(theme, FAMILY_TAGS["midrange"])
    index = get_index()
    present = {c.name for c in cards} | {commander}
    thin: list[CardRow] = []
    for row in cards:
        if row.slot == "land":
            continue
        ic = index.by_name.get(row.name)
        if ic is None:
            thin.append(row)
            continue
        if not set(ic.roles) & set(family):
            thin.append(row)
    out: list[dict[str, Any]] = []
    for row in thin[:8]:
        hits = index.search(ci, row.slot, f"tag:{family[0]}", limit=40)
        for h in hits:
            if h.name in present:
                continue
            price = lookup(h.name)
            if price is None:
                continue
            out.append(
                {
                    "cut": row.name,
                    "add": h.name,
                    "slot": row.slot,
                    "price_usd": price,
                    "reason": "theme-family graph suggestion (not auto-applied)",
                }
            )
            present.add(h.name)
            break
        if len(out) >= limit:
            break
    return out

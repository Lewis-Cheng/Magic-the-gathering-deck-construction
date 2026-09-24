"""Same-slot cheaper substitutes. Suggestions only."""

from __future__ import annotations

from typing import Any

from generator.budget import substitute
from generator.fill import _candidates
from generator.index import get_index
from generator.legal import color_identity
from generator.models import Intake
from generator.recipes import load_recipe


def cheaper_swaps(
    intake: Intake,
    deck: dict[str, Any],
    cut: str,
    budget_remaining: float,
    limit: int = 12,
) -> list[dict[str, Any]]:
    cards = deck.get("cards") or []
    row = next((c for c in cards if c.get("name") == cut), None)
    if row is None:
        return []
    slot = row.get("slot") or "flex"
    recipe = load_recipe(intake.theme)
    query = (recipe.get("queries") or {}).get(slot) or recipe.get("fallback_query") or "*"
    skip = {intake.commander} | {c.get("name") for c in cards} | set(intake.exclude)
    ci = color_identity(intake.commander)
    cand = _candidates(get_index(), ci, slot, query, skip=skip, intake=intake, recipe=recipe, remaining=budget_remaining)
    ordered: list[dict[str, Any]] = []
    skip2 = set(skip)
    remaining = float(budget_remaining)
    for _ in range(limit):
        pick = substitute([(n, p) for n, p, _r in cand], remaining=remaining, per_card_cap=intake.per_card_cap_usd, skip=skip2)
        if pick is None:
            break
        name, price = pick
        skip2.add(name)
        ordered.append({"name": name, "slot": slot, "price_usd": price, "reason": f"cheaper {slot} substitute"})
    return ordered

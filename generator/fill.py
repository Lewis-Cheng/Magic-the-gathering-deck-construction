"""Fill 99 from empty list: lands then slots with reasons. Fail closed on empty pools."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from generator.budget import effective_price, substitute, sum_known, within_caps
from generator.index import CardIndex, get_index
from generator.lands import build_lands
from generator.load import require_card
from generator.models import CardRow, Intake
from generator.prices import lookup
from generator.recipes import load_recipe

_POWER = json.loads((Path(__file__).resolve().parent / "data" / "power_filters.json").read_text(encoding="utf-8"))

SLOT_REASONS = {
    "ramp": "mana development",
    "draw": "card advantage",
    "interaction": "answers on the stack or board",
    "protection": "protects commander or key permanents",
    "seed": "enables the theme engine",
    "payoff": "theme payoff",
    "enabler": "supports the theme line",
    "flex": "on-color flexible role",
    "land": "mana base",
}


def _power_blocked(name: str, roles: tuple[str, ...], power_level: str, recipe: dict) -> bool:
    banned_roles = (recipe.get("banned_roles") or {}).get(power_level) or []
    if any(r in banned_roles for r in roles):
        return True
    if power_level in {"precon", "casual"}:
        if name in _POWER["fast_mana"] or name in _POWER["heavy_tutors"] or name in _POWER["game_changers"]:
            return True
        if "extra-turn" in roles:
            return True
        if power_level == "precon" and name in _POWER["hard_stax"]:
            return True
        if power_level == "casual" and "stax" in (recipe.get("banned_roles") or {}).get("casual", []):
            if name in _POWER["hard_stax"]:
                return True
    if power_level == "casual" and recipe.get("theme") == "tokens":
        if "extra-turn" in roles or name in _POWER["hard_stax"]:
            return True
    return False


def _candidates(
    index: CardIndex,
    ci: set[str],
    slot: str,
    query: str,
    *,
    skip: set[str],
    intake: Intake,
    recipe: dict,
    remaining: float,
) -> list[tuple[str, Optional[float], tuple[str, ...]]]:
    found = index.search(ci, slot, query, limit=400)
    rows = []
    for ic in found:
        if ic.name in skip:
            continue
        if ic.spell_front_mdfc:
            continue
        if _power_blocked(ic.name, ic.roles, intake.power_level, recipe):
            continue
        p = effective_price(ic.name, lookup(ic.name), intake.owned_cards, intake.proxies)
        if p is None:
            continue
        if not within_caps(p, remaining=remaining + 50, per_card_cap=intake.per_card_cap_usd):
            # keep slightly over remaining so substitute can still sort cheapest
            if intake.per_card_cap_usd is not None and p > intake.per_card_cap_usd:
                continue
        rows.append((ic.name, p, ic.roles))
    # owned first, then cheap
    owned = set(intake.owned_cards)
    rows.sort(key=lambda r: (0 if r[0] in owned else 1, r[1] if r[1] is not None else 9999, r[0]))
    return rows


def fill_deck(intake: Intake, cmd_ci: set[str]) -> tuple[list[CardRow], dict, list[str]]:
    recipe = load_recipe(intake.theme)
    index = get_index()
    land_count = intake.land_count or int(recipe["lands"])
    skip = set(intake.exclude) | {intake.commander}
    notes: list[str] = []
    missing: list[str] = []

    cmd_price = effective_price(intake.commander, lookup(intake.commander), intake.owned_cards, intake.proxies)
    remaining = float(intake.budget_usd)
    if cmd_price is None:
        notes.append("commander price unknown; excluded from budget sum (not treated as $0)")
    else:
        remaining -= cmd_price

    land_names, remaining = build_lands(
        cmd_ci,
        land_count,
        remaining=remaining,
        per_card_cap=intake.per_card_cap_usd,
        power_level=intake.power_level,
        owned=intake.owned_cards,
        proxies=intake.proxies,
        theme=intake.theme,
        exclude=skip,
    )
    skip |= set(land_names)

    cards: list[CardRow] = [
        CardRow(name=n, slot="land", price_usd=effective_price(n, lookup(n), intake.owned_cards, intake.proxies), reason=SLOT_REASONS["land"])
        for n in land_names
    ]

    slots: dict[str, int] = dict(recipe["slots"])
    queries: dict[str, str] = dict(recipe["queries"])

    # must_include occupies a matching slot or flex
    for name in intake.must_include:
        if name in skip:
            continue
        try:
            require_card(name)
        except KeyError:
            notes.append(f"must_include unknown, skipped: {name}")
            continue
        p = effective_price(name, lookup(name), intake.owned_cards, intake.proxies)
        if p is None or not within_caps(p, remaining=remaining, per_card_cap=intake.per_card_cap_usd):
            notes.append(f"must_include failed budget/price: {name}")
            continue
        ic = index.by_name.get(name)
        slot = "flex"
        if ic:
            for s, q in queries.items():
                if s in slots and slots[s] > 0 and any(r in (ic.roles) for r in (s, "token", "counter", "draw", "ramp")):
                    slot = s if s in slots else "flex"
                    break
        if slot not in slots or slots.get(slot, 0) <= 0:
            slot = "flex" if slots.get("flex", 0) > 0 else next((s for s, n in slots.items() if n > 0), "flex")
        cards.append(CardRow(name=name, slot=slot, price_usd=p, reason="must_include"))
        skip.add(name)
        remaining -= p
        if slot in slots and slots[slot] > 0:
            slots[slot] -= 1

    fallback_q = recipe.get("fallback_query") or "tag:ramp OR tag:draw OR tag:rock"

    for slot, need in list(slots.items()):
        q = queries.get(slot, fallback_q)
        for _ in range(need):
            cand = _candidates(index, cmd_ci, slot, q, skip=skip, intake=intake, recipe=recipe, remaining=remaining)
            pick = substitute([(n, p) for n, p, _r in cand], remaining=remaining, per_card_cap=intake.per_card_cap_usd, skip=skip)
            if pick is None:
                # documented fallback: more on-color rocks / lands
                fb = _candidates(
                    index, cmd_ci, "flex", fallback_q, skip=skip, intake=intake, recipe=recipe, remaining=remaining
                )
                pick = substitute([(n, p) for n, p, _r in fb], remaining=remaining, per_card_cap=intake.per_card_cap_usd, skip=skip)
                if pick is None:
                    missing.append(slot)
                    break
                notes.append(f"fallback fill for slot {slot}: {pick[0]}")
            name, price = pick
            ic = index.by_name.get(name)
            reason = SLOT_REASONS.get(slot, slot)
            if ic and ic.roles:
                reason = f"{reason} ({', '.join(ic.roles[:3])})"
            cards.append(CardRow(name=name, slot=slot, price_usd=price, reason=reason))
            skip.add(name)
            remaining -= price

    basic_map = {"W": "Plains", "U": "Island", "B": "Swamp", "R": "Mountain", "G": "Forest"}
    basics_cycle = [basic_map[c] for c in "WUBRG" if c in cmd_ci] or ["Wastes"]
    i = 0
    while len(cards) < 99:
        b = basics_cycle[i % len(basics_cycle)]
        cards.append(CardRow(name=b, slot="land", price_usd=effective_price(b, lookup(b), intake.owned_cards, intake.proxies), reason="basic land padding"))
        i += 1
        notes.append("padded with basics to reach 99")
        missing.append("count-pad")

    cards = cards[:99]
    theme_fill = {"ok": len(missing) == 0, "missing_slots": sorted(set(missing))}
    return cards, theme_fill, notes

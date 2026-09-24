"""Construct a 100-card list from empty JSON. Never reads deck_v12.py."""

from __future__ import annotations

from typing import Any

from generator import BAN_LIST_VERSION, TAGGER_VERSION
from generator.budget import effective_price, sum_known
from generator.fill import fill_deck
from generator.graph import suggestions_for
from generator.intake import IntakeError, parse
from generator.legal import check_deck, color_identity
from generator.models import DeckList, Intake
from generator.prices import lookup, prices_as_of


def generate(body: dict[str, Any]) -> dict[str, Any]:
    intake = parse(body)
    return generate_from_intake(intake)


def generate_from_intake(intake: Intake) -> dict[str, Any]:
    sim_on = bool((intake.sim or {}).get("enabled"))
    if sim_on:
        # V1: do not run pods; honest coverage-blocked (E1, E2, Phase 3 stub)
        return {
            "commander": intake.commander,
            "theme": intake.theme,
            "budget_usd": intake.budget_usd,
            "cards": [],
            "confidence": "coverage-blocked",
            "coverage": {"not_probed": True, "named_hook": 0, "generic": 0, "simplified": 0, "unimplemented": 0},
            "detail": "V1 does not run pods at checkout",
            "notes": ["Not a real Magic win rate. Engine coverage is incomplete."],
            "prices_as_of": prices_as_of(),
            "ban_list_version": BAN_LIST_VERSION,
        }

    cards: list = []  # empty-list constructor (A3)
    cmd_ci = color_identity(intake.commander)
    filled, theme_fill, notes = fill_deck(intake, cmd_ci)
    cards.extend(filled)

    names_99 = [c.name for c in cards]
    legality = check_deck(intake.commander, names_99)

    prices = []
    cmd_p = effective_price(intake.commander, lookup(intake.commander), intake.owned_cards, intake.proxies)
    prices.append(cmd_p)
    prices.extend(c.price_usd for c in cards)
    total, unknown = sum_known(prices)
    if unknown:
        notes.append(f"{unknown} unknown prices excluded from total (not treated as $0)")
        legality["violations"] = list(legality.get("violations") or []) + ["unknown prices present"]
        legality["ok"] = False

    if total > intake.budget_usd + 1e-6:
        legality["violations"] = list(legality.get("violations") or []) + [f"over budget: {total:.2f} > {intake.budget_usd}"]
        legality["ok"] = False

    ok_all = bool(legality.get("ok")) and bool(theme_fill.get("ok")) and total <= intake.budget_usd + 1e-6
    if not ok_all:
        notes.append("generate scoring = legal + theme_fill + budget (no pod win rate)")

    graph_sugs = suggestions_for(intake.commander, intake.theme, cmd_ci, cards)

    deck = DeckList(
        commander=intake.commander,
        theme=intake.theme,
        budget_usd=intake.budget_usd,
        power_level=intake.power_level,
        cards=cards,
        total_usd=round(total, 2),
        lands=sum(1 for c in cards if c.slot == "land"),
        legality=legality,
        theme_fill=theme_fill,
        coverage={"not_probed": True, "named_hook": 0, "generic": 0, "simplified": 0, "unimplemented": 0},
        confidence="generator-only",
        notes=notes,
        tagger_version=TAGGER_VERSION,
        prices_as_of=prices_as_of(),
        ban_list_version=BAN_LIST_VERSION,
        graph_suggestions=graph_sugs,
    )
    data = deck.to_json()
    if "win_rate" in data:
        del data["win_rate"]
    return data

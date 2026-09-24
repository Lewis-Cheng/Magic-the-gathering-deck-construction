"""Reject incomplete jobs. No Ovika / $1000 / convoke defaults."""

from __future__ import annotations

from typing import Any

from generator.models import THEMES_V1, POWER_LEVELS, Intake
from generator.oracle_bridge import get_oracle


class IntakeError(ValueError):
    def __init__(self, message: str, code: str = "invalid_intake"):
        super().__init__(message)
        self.code = code
        self.message = message

    def to_json(self) -> dict[str, Any]:
        return {"error": self.code, "detail": self.message}


def parse(body: dict[str, Any]) -> Intake:
    if not isinstance(body, dict):
        raise IntakeError("body must be a JSON object")

    commander = body.get("commander")
    theme = body.get("theme")
    budget = body.get("budget_usd")

    if not commander or not str(commander).strip():
        raise IntakeError("commander is required (no default)", "missing_commander")
    if not theme or not str(theme).strip():
        raise IntakeError("theme is required (no default)", "missing_theme")
    if budget is None:
        raise IntakeError("budget_usd is required (no default of 1000)", "missing_budget")
    try:
        budget_f = float(budget)
    except (TypeError, ValueError):
        raise IntakeError("budget_usd must be a number", "invalid_budget")
    if budget_f <= 0:
        raise IntakeError("budget_usd must be > 0", "invalid_budget")

    theme_s = str(theme).strip().lower()
    if theme_s.startswith("other:"):
        raise IntakeError("theme other:<slug> requires a written recipe in the request (V1: pick a shipped theme)", "unknown_theme")
    if theme_s not in THEMES_V1:
        raise IntakeError(f"unknown theme: {theme}", "unknown_theme")

    power = str(body.get("power_level") or "casual").strip().lower()
    if power not in POWER_LEVELS:
        raise IntakeError(f"unknown power_level: {power}", "invalid_power_level")

    oracle = get_oracle()
    card = oracle.get(str(commander).strip())
    if card is None:
        raise IntakeError(f"commander not in Oracle: {commander}", "unknown_commander")
    if not card.is_legendary:
        raise IntakeError(f"commander must be legendary: {commander}", "invalid_commander")
    if not (card.is_creature or card.is_planeswalker):
        raise IntakeError(f"commander must be a legendary creature or planeswalker: {commander}", "invalid_commander")

    per_cap = body.get("per_card_cap_usd")
    per_cap_f = float(per_cap) if per_cap is not None and per_cap != "" else None
    if per_cap_f is not None and per_cap_f <= 0:
        raise IntakeError("per_card_cap_usd must be > 0 when set", "invalid_per_card_cap")

    owned = [str(x) for x in (body.get("owned_cards") or [])]
    exclude = [str(x) for x in (body.get("exclude") or [])]
    must = [str(x) for x in (body.get("must_include") or [])]
    sim = body.get("sim") if isinstance(body.get("sim"), dict) else {"enabled": False}

    land_count = body.get("land_count")
    land_i = int(land_count) if land_count is not None else None

    return Intake(
        commander=card.name if " // " not in card.name else card.name.split(" // ", 1)[0],
        theme=theme_s,
        budget_usd=budget_f,
        power_level=power,
        per_card_cap_usd=per_cap_f,
        owned_cards=owned,
        proxies=bool(body.get("proxies", False)),
        land_count=land_i,
        exclude=exclude,
        must_include=must,
        sim=sim,
    )

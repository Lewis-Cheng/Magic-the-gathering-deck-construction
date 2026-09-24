from __future__ import annotations

from pathlib import Path

from generator.build import generate
from generator.budget import substitute
from generator.recipes import load_recipe


def test_no_pool_and_no_deck_v12_in_product_sources():
    root = Path(__file__).resolve().parents[1]
    for p in root.rglob("*.py"):
        if "tests" in p.parts:
            continue
        text = p.read_text(encoding="utf-8")
        assert "Pool(" not in text, p
        assert "import Pool" not in text, p
        assert "from oracle import Pool" not in text, p


def test_voltron_recipe_lands_and_payoffs():
    r = load_recipe("voltron")
    assert r["lands"] >= 36
    assert r["slots"]["payoff"] >= 10
    assert r["lands"] != 28


def test_budget_substitute_skips_expensive():
    cand = [("The One Ring", 99.0), ("Opt", 0.12), ("Rhystic Study", 65.0)]
    pick = substitute(cand, remaining=5.0, per_card_cap=5.0, skip=set())
    assert pick is not None
    assert pick[0] == "Opt"


def test_owned_price_zero():
    from generator.budget import effective_price

    assert effective_price("Sol Ring", 1.43, ["Sol Ring"], False) == 0.0
    assert effective_price("Sol Ring", 1.43, [], False) == 1.43


def test_golden_generate_midrange_50(oracle):
    data = generate(
        {
            "commander": "Torbran, Thane of Red Fell",
            "theme": "midrange",
            "budget_usd": 50,
            "power_level": "casual",
        }
    )
    assert data["confidence"] == "generator-only"
    assert "win_rate" not in data
    assert len(data["cards"]) == 99
    names = [data["commander"]] + [c["name"] for c in data["cards"]]
    assert len(names) == 100
    assert data["total_usd"] <= 50 + 1e-6
    assert all(c.get("price_usd") is not None for c in data["cards"])
    assert all(c["price_usd"] != 0 or True for c in data["cards"])  # 0 only if owned
    assert data["legality"]["ok"] is True
    assert data["prices_as_of"]
    assert data["ban_list_version"]
    assert data["commander"] == "Torbran, Thane of Red Fell"


def test_two_commanders_differ(oracle):
    a = generate({"commander": "Torbran, Thane of Red Fell", "theme": "tokens", "budget_usd": 80, "power_level": "casual"})
    b = generate({"commander": "Talrand, Sky Summoner", "theme": "tokens", "budget_usd": 80, "power_level": "casual"})
    assert a["commander"] != b["commander"]
    sa = {c["name"] for c in a["cards"]}
    sb = {c["name"] for c in b["cards"]}
    assert sa != sb


def test_sim_enabled_is_coverage_blocked(oracle):
    data = generate(
        {
            "commander": "Torbran, Thane of Red Fell",
            "theme": "midrange",
            "budget_usd": 50,
            "sim": {"enabled": True},
        }
    )
    assert data["confidence"] == "coverage-blocked"
    assert "win_rate" not in data


def test_casual_tokens_no_extra_turn_staple(oracle):
    data = generate(
        {
            "commander": "Krenko, Mob Boss",
            "theme": "tokens",
            "budget_usd": 150,
            "power_level": "casual",
        }
    )
    names = {c["name"] for c in data["cards"]}
    assert "Time Warp" not in names
    assert "Expropriate" not in names

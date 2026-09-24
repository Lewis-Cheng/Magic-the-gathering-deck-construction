from __future__ import annotations

from pathlib import Path

from generator.lab_convert import lab_py_to_names
from generator.legal import check_deck
from generator.models import DeckList, CardRow
from generator.oracle_bridge import get_oracle


def test_oracle_require_not_tuple_tags(oracle):
    c = oracle.require("Counterspell")
    assert "Instant" in c.types
    assert c.mana_cost.cmc() == 2


def test_wand_of_the_worldsoul_fails_ur(oracle):
    cmd = "Ovika, Enigma Goliath"
    ninety_nine = ["Island"] * 49 + ["Mountain"] * 49 + ["Wand of the Worldsoul"]
    result = check_deck(cmd, ninety_nine)
    assert result["ok"] is False
    assert any("color identity" in v.lower() or "Wand" in v for v in result["violations"])


def test_extra_card_fails(oracle):
    cmd = "Torbran, Thane of Red Fell"
    too_many = ["Mountain"] * 100
    result = check_deck(cmd, too_many)
    assert result["ok"] is False
    assert any("99" in v or "100" in v for v in result["violations"])


def test_legal_mono_red_basics(oracle):
    cmd = "Torbran, Thane of Red Fell"
    names = ["Mountain"] * 99
    result = check_deck(cmd, names)
    assert result["ok"] is True
    assert result["ban_list_version"]


def test_json_names_only_not_python_tuples():
    deck = DeckList(
        commander="Torbran, Thane of Red Fell",
        theme="midrange",
        budget_usd=50,
        power_level="casual",
        cards=[CardRow("Mountain", "land", 0.07, "basic")] * 99,
        total_usd=7.0,
        lands=99,
        legality={"ok": True, "violations": []},
        theme_fill={"ok": True, "missing_slots": []},
        coverage={"not_probed": True},
        confidence="generator-only",
    )
    blob = deck.to_json()
    assert "win_rate" not in blob
    assert all(isinstance(c["name"], str) for c in blob["cards"])


def test_lab_convert_is_ast_not_pool():
    path = Path(__file__).resolve().parents[2] / "ovika" / "deck_v12.py"
    if not path.exists():
        return
    data = lab_py_to_names(path)
    assert data["commander"]
    assert data["cards"]
    assert all(isinstance(n, str) for n in data["cards"])

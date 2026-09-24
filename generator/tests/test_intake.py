from __future__ import annotations

import pytest

from generator.intake import IntakeError, parse


def test_missing_budget_does_not_default():
    with pytest.raises(IntakeError) as ei:
        parse({"commander": "Torbran, Thane of Red Fell", "theme": "midrange"})
    assert ei.value.code == "missing_budget"


def test_missing_theme():
    with pytest.raises(IntakeError) as ei:
        parse({"commander": "Torbran, Thane of Red Fell", "budget_usd": 50})
    assert ei.value.code == "missing_theme"


def test_missing_commander():
    with pytest.raises(IntakeError) as ei:
        parse({"theme": "midrange", "budget_usd": 50})
    assert ei.value.code == "missing_commander"


def test_unknown_theme():
    with pytest.raises(IntakeError) as ei:
        parse({"commander": "Torbran, Thane of Red Fell", "theme": "convoke", "budget_usd": 50})
    assert ei.value.code == "unknown_theme"


def test_budget_non_positive():
    with pytest.raises(IntakeError) as ei:
        parse({"commander": "Torbran, Thane of Red Fell", "theme": "midrange", "budget_usd": 0})
    assert ei.value.code == "invalid_budget"


def test_ok_intake(oracle):
    inn = parse(
        {
            "commander": "Torbran, Thane of Red Fell",
            "theme": "midrange",
            "budget_usd": 50,
            "power_level": "casual",
        }
    )
    assert inn.commander == "Torbran, Thane of Red Fell"
    assert inn.budget_usd == 50

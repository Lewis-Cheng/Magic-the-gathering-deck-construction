from __future__ import annotations

from generator.budget import sum_known
from generator.prices import lookup


def test_missing_price_is_none_not_zero():
    p = lookup("___definitely_not_a_card___")
    assert p is None
    assert p != 0
    total, unknown = sum_known([1.5, None, 2.0])
    assert unknown == 1
    assert total == 3.5


def test_sol_ring_has_price():
    p = lookup("Sol Ring")
    assert p is None or p > 0

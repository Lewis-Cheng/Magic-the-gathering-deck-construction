"""Budget solver: cap from request, never default 1000; missing price excluded; owned = 0."""

from __future__ import annotations

from typing import Iterable, Optional, Sequence


def effective_price(name: str, listed: Optional[float], owned: Iterable[str], proxies: bool) -> Optional[float]:
    owned_set = set(owned)
    if (not proxies) and name in owned_set:
        return 0.0
    return listed


def within_caps(
    price: Optional[float],
    *,
    remaining: float,
    per_card_cap: Optional[float],
) -> bool:
    if price is None:
        return False
    if per_card_cap is not None and price > per_card_cap:
        return False
    return price <= remaining


def substitute(
    candidates: Sequence[tuple[str, Optional[float]]],
    *,
    remaining: float,
    per_card_cap: Optional[float],
    skip: set[str],
) -> Optional[tuple[str, float]]:
    """Next-cheapest same-slot name with a known price under remaining + per-card cap."""
    priced: list[tuple[str, float]] = []
    for name, p in candidates:
        if name in skip or p is None:
            continue
        if within_caps(p, remaining=remaining, per_card_cap=per_card_cap):
            priced.append((name, p))
    if not priced:
        return None
    priced.sort(key=lambda x: (x[1], x[0]))
    return priced[0]


def sum_known(prices: Iterable[Optional[float]]) -> tuple[float, int]:
    """Sum known prices only. None is not 0. Returns (sum, unknown_count)."""
    total = 0.0
    unknown = 0
    for p in prices:
        if p is None:
            unknown += 1
        else:
            total += p
    return total, unknown

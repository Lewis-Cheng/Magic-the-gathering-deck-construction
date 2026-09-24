"""Same-engine 1-for-1 retain protocol (novel lab contribution).

Stubs the decision procedure used to reject Ovika v12.2: graph/ping
density is not a retain signal unless locked-schedule wins improve.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Literal, Sequence


Slot = Literal[
    "land",
    "ramp",
    "draw/filter",
    "interaction",
    "protection",
    "seed/engine",
    "payoff/finisher",
    "enabler/synergy",
    "flex",
]


@dataclass(frozen=True)
class FactorLock:
    """Locked measurement factors; any change invalidates A/B."""

    engine_stamp: str
    opponent_modules: tuple[str, str, str]
    seeds: tuple[int, ...]
    turn_cap: int
    workers: int
    ai_version: str


@dataclass(frozen=True)
class PodOutcome:
    candidate_wins: int
    games: int
    cap_no_winner: int
    csv_path: str


def state_signature_noop_is_pass(sig_before: str, sig_after: str) -> bool:
    """CR 117: an action that changes no state is a pass, not a re-grant."""
    return sig_before == sig_after


def workers_in_bounds(workers: int, cores: int = 4) -> bool:
    """Never run more than 4-5 pod workers on 4 cores."""
    return 1 <= workers <= min(5, cores + 1)


def same_slot_swap(parent: Sequence[str], child: Sequence[str]) -> bool:
    """Exactly one add and one cut (multiset difference size 2)."""
    a, b = set(parent), set(child)
    return len(a.symmetric_difference(b)) == 2 and len(a) == len(b)


def retain_candidate(
    parent: PodOutcome,
    child: PodOutcome,
    lock_parent: FactorLock,
    lock_child: FactorLock,
    *,
    graph_edges_increased: bool = False,
) -> Literal["adopt", "reject", "invalid-comparison"]:
    """Retain only on same-lock win improvement.

    `graph_edges_increased` is recorded but never sufficient (v12.2).
    """
    if lock_parent != lock_child:
        return "invalid-comparison"
    if parent.games != child.games:
        return "invalid-comparison"
    if child.candidate_wins > parent.candidate_wins:
        return "adopt"
    _ = graph_edges_increased
    return "reject"


def deal_damage_must_be_unified(damage_paths: Iterable[str]) -> bool:
    """Every damage source name must route through Game.deal_damage."""
    allowed = {"combat", "burn", "etb_ping", "on_cast_ping", "activated"}
    return set(damage_paths).issubset(allowed)

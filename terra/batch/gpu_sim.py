"""GPU-accelerated statistical layer (PyTorch).

Full-rules games are sequential, so they run on CPU (multiprocessing);
this module uses the laptop GPU for what is genuinely parallel:
- 1M+ hand/mulligan Monte Carlo (vectorized sampling)
- Wilson confidence intervals for batch results
- large-N abstraction-level win-rate sweeps for sensitivity analysis

Falls back to CPU tensors if CUDA is unavailable.
"""

from __future__ import annotations

import math
from typing import List, Optional

try:
    import torch
except ImportError:  # pragma: no cover
    torch = None


def device() -> str:
    if torch is not None and torch.cuda.is_available():
        return "cuda"
    return "cpu"


def _deck_tensors(deck: List[str], commander: str, oracle) -> tuple:
    """Feature tensors per deck card: [is_land, is_ramp, cmc, is_ovika]."""
    lands = []
    ramps = []
    cmcs = []
    for name in deck:
        c = oracle.require(name)
        lands.append(1 if c.is_land else 0)
        ramps.append(1 if ("ramp" in c.tags or c.name in (
            "Sol Ring", "Arcane Signet", "Wayfarer's Bauble", "Mind Stone",
            "Fellwar Stone", "Everflowing Chalice", "Chromatic Lantern",
            "Commander's Sphere", "Thran Dynamo", "Pristine Talisman",
            "The Eternity Elevator", "Myriad Landscape", "Terramorphic Expanse")) else 0)
        cmcs.append(c.mana_cost.cmc() if not c.is_land else 0)
    return (torch.tensor(lands, device=device()),
            torch.tensor(ramps, device=device()),
            torch.tensor(cmcs, device=device()))


def hand_mc(deck: List[str], commander: str, n: int = 200_000, chunk: int = 20_000,
            oracle=None) -> dict:
    """Vectorized Monte Carlo of opening hands + mulligan policy + land curve.

    Uses exact without-replacement sampling (argsort of random keys over a
    full deck permutation per hand, in chunks to bound memory).
    """
    if oracle is None:
        from engine.oracle import Oracle
        oracle = Oracle()
    dev = device()
    land_t, ramp_t, cmc_t = _deck_tensors(deck, commander, oracle)
    D = len(deck)
    acc = {"lands": 0.0, "ramp": 0.0, "keep": 0, "p25": 0, "screw": 0, "flood": 0}
    n_done = 0
    while n_done < n:
        b = min(chunk, n - n_done)
        keys = torch.rand(b, D, device=dev)
        order = torch.argsort(keys, dim=1)          # full deck permutation per hand
        hand = order[:, :7]
        lands = land_t[hand].sum(dim=1)             # lands in opening 7
        ramp = ramp_t[hand].sum(dim=1)
        cheap = (cmc_t[hand] > 0).sum(dim=1) > 0    # any nonland card in hand
        keep = ((lands >= 2) & (lands <= 5) & ((ramp > 0) | cheap))
        keep |= ((lands == 1) & (ramp > 0) & cheap)
        acc["lands"] += lands.sum().item()
        acc["ramp"] += ramp.sum().item()
        acc["keep"] += keep.sum().item()
        acc["p25"] += ((lands >= 2) & (lands <= 5)).sum().item()
        acc["screw"] += (lands < 2).sum().item()
        acc["flood"] += (lands > 5).sum().item()
        n_done += b
    # land curve: cards drawn by turn t = 7 + t; cumulative lands in prefix
    pref_lands = torch.cumsum(land_t[order], dim=1)  # per hand cumulative
    lands_turn = {}
    for t in (1, 3, 5, 7, 9):
        idx = min(7 + t, D) - 1
        lands_turn[f"t{t}"] = float(pref_lands[:, idx].float().mean().item())
    return {
        "avg_lands": acc["lands"] / n_done,
        "avg_ramp": acc["ramp"] / n_done,
        "keep_pct": 100 * acc["keep"] / n_done,
        "p_2_5": acc["p25"] / n_done,
        "p_screw": acc["screw"] / n_done,
        "p_flood": acc["flood"] / n_done,
        "lands_by_turn": lands_turn,
        "device": dev,
    }


def aggregate_gpu(wins: List[int], z: float = 1.96) -> dict:
    """Wilson score interval for a batch win rate, computed on the GPU."""
    if torch is None:
        raise RuntimeError("torch not installed; run without --gpu")
    dev = device()
    t = torch.tensor(wins, dtype=torch.float32, device=dev)
    n = t.numel()
    p = t.mean().item()
    if n == 0:
        return {"p": 0.0, "lo": 0.0, "hi": 0.0, "n": 0}
    z2 = z * z
    denom = 1 + z2 / n
    center = (p + z2 / (2 * n)) / denom
    margin = z * math.sqrt((p * (1 - p) + z2 / (4 * n)) / n) / denom
    return {"p": p, "lo": max(0.0, center - margin), "hi": min(1.0, center + margin), "n": n}


def fast_sweep(commander_name: str, n: int = 100_000, turns: int = 10,
               wipe_p: float = 0.12, remove_p: float = 0.20, die_p: float = 0.30,
               win_n: int = 30) -> dict:
    """GPU-vectorized abstraction-level win estimate (heuristic baseline,
    similar to the original sim.py): used for large-N sensitivity sweeps,
    NOT a substitute for the full-rules engine."""
    if torch is None:
        raise RuntimeError("torch not installed; run without --gpu")
    dev = device()
    r = lambda *a, **k: torch.rand(*a, device=dev, **k)
    # --- opening 7 (with replacement approximation at this abstraction layer)
    n_land = 26
    lands = torch.zeros(n, device=dev)
    mana = torch.zeros(n, device=dev)
    ovika_turn = torch.full((n,), turns + 1, device=dev)
    tokens = torch.zeros(n, device=dev)
    won = torch.zeros(n, dtype=torch.bool, device=dev)
    hand = (r((n, 7), ) < n_land / 99).sum(dim=1)
    keep = (hand >= 2) & (hand <= 5)
    lands = hand.clone()
    mana = hand.clone().float()
    for t in range(1, turns + 1):
        # draw step
        draw_land = (r((n,), ) < n_land / 99) & (t > 1)
        lands += draw_land
        mana = lands + (mana - lands).clamp(min=0)  # rocks keep previous float
        # rock ramp: each rock ~ +1.3
        rock_draw = (r((n,), ) < 0.13)  # ramp density approx
        mana += rock_draw * 1.3
        # cast Ovika
        just_ovika = (~(ovika_turn <= t)) & (mana >= 7)
        ovika_turn = torch.where(just_ovika, torch.full_like(ovika_turn, t), ovika_turn)
        active = ovika_turn <= t
        # spells per turn with engines (abstraction: mv ~ 4.5, mult ~ 2.4)
        spells = torch.where(active, (mana / 4.5).floor().clamp(max=8), torch.zeros(n, device=dev))
        gained = spells * 4.5 * 2.4
        tokens = tokens + gained
        # wipe chance
        wiped = (r((n,), ) < wipe_p) & active
        tokens = torch.where(wiped, torch.zeros(n, device=dev), tokens)
        # Ovika removed
        removed = (r((n,), ) < remove_p) & active
        ovika_turn = torch.where(removed, torch.full_like(ovika_turn, turns + 1), ovika_turn)
        # end-of-turn attrition
        survivors = (tokens * (1 - die_p)).floor()
        won |= (survivors >= win_n) & active
    wins = won.sum().item()
    agg = aggregate_gpu([1] * wins + [0] * (n - wins))
    return {**agg, "n": n, "device": dev}

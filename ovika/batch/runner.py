"""Batch 4-player Commander simulation runner (CPU multiprocessing + GPU stats).

Usage:
  python ovika/batch/runner.py --games 40 --seeds 101-140 --turns 14 --workers 8 --gpu
  python ovika/batch/runner.py --games 20 --gpu --hand-mc 1000000

Full-rules games are sequential by nature, so they are distributed across
CPU cores; the GPU is used for (a) vectorized 1M-hand Monte Carlo,
(b) win-rate confidence intervals, and (c) large-N abstraction-level
sensitivity sweeps (see gpu_sim.py).
"""

import argparse
import json
import os
import sys
import time
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(os.path.join(__file__, ".."))))

from engine.oracle import Oracle, Pool
from engine.game import Game
from engine.ai import AI

CSV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "results_engine.csv")


def play_seed(seed: int, deck_path: str, turns: int) -> dict:
    oracle = Oracle()
    pool = Pool(oracle, deck_path)
    deck = pool.decklist()
    commander = pool.commander
    game = Game(deck, commander, seed=seed,
                ais=[AI("A"), AI("B"), AI("C"), AI("D")],
                max_turns=turns, log_fn=None, oracle=oracle)
    r = game.run_game()
    return {
        "seed": seed,
        "winner": r["winner"],
        "win_turn": r["win_turn"],
        "turns": r["turns"],
        "life": r["life"],
        "lost": [x["name"] for x in r["lost"]],
        "reasons": [x["reason"] for x in r["lost"]],
        "commander_damage": {k: max(v.values()) if v else 0 for k, v in r["commander_damage"].items()},
    }


def parse_seeds(arg: str) -> list:
    out = []
    for part in arg.split(","):
        part = part.strip()
        if "-" in part:
            a, b = part.split("-")
            out.extend(range(int(a), int(b) + 1))
        elif part:
            out.append(int(part))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--games", type=int, default=20)
    ap.add_argument("--seeds", type=str, default="")
    ap.add_argument("--deck", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "deck_v11.py"))
    ap.add_argument("--turns", type=int, default=14)
    ap.add_argument("--workers", type=int, default=0)
    ap.add_argument("--gpu", action="store_true")
    ap.add_argument("--hand-mc", type=int, default=0, help="GPU hand Monte Carlo sample count (0=off)")
    ap.add_argument("--fast-n", type=int, default=0, help="GPU fast-model sweep size (0=off)")
    ap.add_argument("--csv", default=CSV_PATH)
    args = ap.parse_args()

    seeds = parse_seeds(args.seeds) or list(range(1, args.games + 1))
    workers = args.workers or min(8, os.cpu_count() or 4)

    t0 = time.time()
    results = []
    from concurrent.futures import ProcessPoolExecutor
    with ProcessPoolExecutor(max_workers=workers) as ex:
        futs = [ex.submit(play_seed, s, args.deck, args.turns) for s in seeds]
        for i, f in enumerate(futs, 1):
            r = f.result()
            results.append(r)
            tag = r["winner"] or "-"
            print(f"[{i}/{len(seeds)}] seed {r['seed']:>3}: winner={tag} turn={r['win_turn']} "
                  f"turns={r['turns']} life={ {k: v for k, v in r['life'].items()} }", flush=True)

    # ---- stats (CPU first; GPU aggregation when --gpu) ----
    wins = sum(1 for r in results if r["winner"])
    completed = sum(1 for r in results if r["winner"])
    n = len(results)
    print(f"\nFull-rules 4-player: {wins}/{n} completed wins ({100*wins/n:.1f}%) "
          f"over {time.time()-t0:.1f}s with {workers} workers")

    if args.gpu:
        from batch.gpu_sim import aggregate_gpu, hand_mc, fast_sweep
        agg = aggregate_gpu([1 if r["winner"] else 0 for r in results])
        print(f"GPU Wilson CI: p={agg['p']:.3f} [{agg['lo']:.3f}, {agg['hi']:.3f}]")
        if args.hand_mc:
            from engine.oracle import Oracle as O
            pool = Pool(O(), args.deck)
            hm = hand_mc([c.name for c in pool.decklist()], pool.commander.name,
                         n=args.hand_mc)
            print(f"GPU hand MC (n={args.hand_mc:,}): avg lands={hm['avg_lands']:.2f} "
                  f"avg ramp={hm['avg_ramp']:.2f} keep%={hm['keep_pct']:.1f} "
                  f"P(2-5 lands)={hm['p_2_5']:.3f} P(mana screw)={hm['p_screw']:.3f}")
        if args.fast_n:
            fs = fast_sweep(pool.commander, args.fast_n)
            print(f"GPU fast-model win estimate (n={args.fast_n:,}): {100*fs['p']:.1f}% "
                  f"[{100*fs['lo']:.1f}, {100*fs['hi']:.1f}]")

    # save CSV
    import csv
    with open(args.csv, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["seed", "winner", "win_turn", "turns",
                                          "life_p1", "life_p2", "life_p3", "life_p4"])
        w.writeheader()
        for r in results:
            w.writerow({
                "seed": r["seed"], "winner": r["winner"] or "", "win_turn": r["win_turn"] or "",
                "turns": r["turns"],
                "life_p1": r["life"].get("P1", ""), "life_p2": r["life"].get("P2", ""),
                "life_p3": r["life"].get("P3", ""), "life_p4": r["life"].get("P4", ""),
            })
    print("saved", args.csv)


if __name__ == "__main__":
    main()

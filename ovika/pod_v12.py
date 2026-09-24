"""4-deck pod: Ovika v12 convoke + the three EDHREC decks (Nekusar, Kuja, Minstrel).

Usage:
  python ovika/pod_v12.py --seeds 1-36 --turns 14 --workers 4 [--deck deck_v12.py]
"""

import argparse
import csv
import os
import sys
import time
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from engine.oracle import Oracle, Pool
from engine.game import Game
from engine.ai import AI

POD = [
    ("ovika deck", "deck_v12.py", "Ovika, Enigma Goliath"),
    ("nekusar deck", "decks/edhrec_nekusar.py", "Nekusar, the Mindrazer"),
    ("kuja deck", "decks/edhrec_kuja.py", "Kuja, Genome Sorcerer"),
    ("minstrel deck", "decks/edhrec_minstrel.py", "The Wandering Minstrel"),
]

HERE = os.path.dirname(os.path.abspath(__file__))


def play_pod_seed(seed: int, turns: int, log_fn=None, ovika_deck: str = "deck_v12.py") -> dict:
    oracle = Oracle()
    decks, commanders = [], []
    for label, deck_file, cname in POD:
        deck_file = ovika_deck if label == "ovika deck" else deck_file
        pool = Pool(oracle, os.path.join(HERE, deck_file))
        decks.append(pool.decklist())
        commanders.append(pool.commander)
    game = Game(decks[0], commanders[0], seed=seed,
                ais=[AI("A"), AI("B"), AI("C"), AI("D")],
                max_turns=turns, log_fn=log_fn, oracle=oracle,
                decks=decks, commanders=commanders)
    r = game.run_game()
    # who sits where
    seat = {p.name: i for i, p in enumerate(game.players)}
    return {
        "seed": seed,
        "winner": r["winner"],
        "win_turn": r["win_turn"],
        "turns": r["turns"],
        "life": r["life"],
        "seat": seat,
        "deck_of": {p.name: POD[i][0] for p, i in ((pl, seat[pl.name]) for pl in game.players)},
        "commander_of": {p.name: POD[i][2] for p, i in ((pl, seat[pl.name]) for pl in game.players)},
        "simplified": sum(1 for ln in r["logs"] if "(simplified spell" in ln),
        "unresolved": sum(1 for ln in r["logs"] if "unimplemented spell" in ln or "!! priority loop guard" in ln),
        "commander_damage": r["commander_damage"],
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--games", type=int, default=12)
    ap.add_argument("--seeds", type=str, default="")
    ap.add_argument("--turns", type=int, default=14)
    ap.add_argument("--workers", type=int, default=0)
    ap.add_argument("--csv", default=None)
    ap.add_argument("--log1", action="store_true", help="print the full log of the first game")
    ap.add_argument("--deck", default="deck_v12.py", help="Ovika deck file to test (default deck_v12.py)")
    args = ap.parse_args()

    if args.seeds:
        seeds = []
        for part in args.seeds.split(","):
            part = part.strip()
            if "-" in part:
                a, b = part.split("-")
                seeds.extend(range(int(a), int(b) + 1))
            elif part:
                seeds.append(int(part))
    else:
        seeds = list(range(1, args.games + 1))
    workers = args.workers or min(4, os.cpu_count() or 4)
    csv_path = args.csv or os.path.join(
        HERE, "results_" + os.path.splitext(os.path.basename(args.deck))[0] + ".csv")

    t0 = time.time()
    if workers <= 1:
        results = [play_pod_seed(s, args.turns,
                                 log_fn=(lambda line: print(line)) if (args.log1 and s == seeds[0]) else None,
                                 ovika_deck=args.deck)
                   for s in seeds]
    else:
        from concurrent.futures import ProcessPoolExecutor
        results = []
        with ProcessPoolExecutor(max_workers=workers) as ex:
            futs = [ex.submit(play_pod_seed, s, args.turns, None, args.deck) for s in seeds]
            for i, f in enumerate(futs, 1):
                r = f.result()
                results.append(r)
                print(f"[{i}/{len(seeds)}] seed {r['seed']:>3}: winner={r['winner']} "
                      f"deck={r['deck_of'].get(r['winner'], '-')} turn={r['win_turn']} "
                      f"simplified={r['simplified']}", flush=True)

    # ---- stats ----
    wins = Counter(r["deck_of"].get(r["winner"]) for r in results if r["winner"])
    n = len(results)
    print(f"\nPod {n} games ({time.time()-t0:.1f}s, {workers} workers):")
    for label, deck_file, cname in POD:
        w = wins.get(label, 0)
        print(f"  {label:16s} {cname:24s} {w:3d}/{n} wins ({100*w/n:.0f}%)")
    avg_turn = sum(r["win_turn"] or r["turns"] for r in results) / n
    print(f"  avg game end: turn {avg_turn:.1f} | avg simplified-spell logs/game: "
          f"{sum(r['simplified'] for r in results)/n:.1f}")

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["seed", "winner", "winner_deck", "win_turn", "turns",
                                          "life_p1", "life_p2", "life_p3", "life_p4"])
        w.writeheader()
        for r in results:
            w.writerow({
                "seed": r["seed"], "winner": r["winner"] or "",
                "winner_deck": r["deck_of"].get(r["winner"], ""),
                "win_turn": r["win_turn"] or "", "turns": r["turns"],
                "life_p1": r["life"].get("P1", ""), "life_p2": r["life"].get("P2", ""),
                "life_p3": r["life"].get("P3", ""), "life_p4": r["life"].get("P4", ""),
            })
    print("saved", csv_path)


if __name__ == "__main__":
    main()

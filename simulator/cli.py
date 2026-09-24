"""Run one rules-legal 4-player Commander game and print a readable log.

Usage:
  python simulator/cli.py --deck PATH --seed 1 [--quiet] [--turns 20]
"""

import argparse
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from engine.oracle import Oracle, Pool
from engine.game import Game
from engine.ai import AI


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--deck", required=True, help="deck module with COMMANDER and DECK")
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--turns", type=int, default=20)
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    oracle = Oracle()
    pool = Pool(oracle, args.deck)
    deck = pool.decklist()
    commander = pool.commander

    log_fn = None if args.quiet else (lambda line: print(line))
    game = Game(deck, commander, seed=args.seed,
                ais=[AI("A"), AI("B"), AI("C"), AI("D")],
                max_turns=args.turns, log_fn=log_fn, oracle=oracle)
    res = game.run_game()
    print()
    print("RESULT:", res["winner"], "turn", res["win_turn"], "| turns:", res["turns"])
    for p in res["alive"]:
        print("  alive:", p, "life", res["life"][p])
    for l in res["lost"]:
        print("  lost:", l["name"], "-", l["reason"])


if __name__ == "__main__":
    main()

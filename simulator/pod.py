"""4 bot players, one Commander game or a seeded pod.

Seat 0 is the candidate. The other seats use --opponents, or the sample
fixture when none are given. Default turn cap is 18.

  python simulator/pod.py --deck simulator/fixtures/sample_deck.py --seed 1 --json
  python simulator/pod.py --deck DECK.py --seeds 1-36 --turns 18
"""

from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from engine.ai import AI
from engine.game import Game
from engine.oracle import Oracle, Pool

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_TURNS = 18
FIXTURE = os.path.join(HERE, "fixtures", "sample_deck.py")


def parse_seeds(text: str) -> list[int]:
    seeds: list[int] = []
    for part in text.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            a, b = part.split("-", 1)
            seeds.extend(range(int(a), int(b) + 1))
        else:
            seeds.append(int(part))
    return seeds


def load_seat(oracle: Oracle, path: str):
    if os.path.isabs(path):
        full = path
    elif os.path.exists(path):
        full = path
    else:
        full = os.path.join(HERE, path)
    pool = Pool(oracle, full)
    return pool.decklist(), pool.commander


def play_seed(seed: int, turns: int, deck_files: list[str], log: bool = False) -> dict:
    """One game. Four heuristic bot pilots. Same seed replays the same game."""
    oracle = Oracle()
    decks, commanders = [], []
    for path in deck_files:
        deck, commander = load_seat(oracle, path)
        decks.append(deck)
        commanders.append(commander)
    lines: list[str] = []
    game = Game(
        decks[0], commanders[0], seed=seed,
        ais=[AI("A"), AI("B"), AI("C"), AI("D")],
        max_turns=turns,
        log_fn=(lines.append if log else None),
        oracle=oracle,
        decks=decks,
        commanders=commanders,
    )
    result = game.run_game()
    winner = result["winner"]
    seat = {p.name: i for i, p in enumerate(game.players)}
    # setup() rotates turn order. P1 is still the candidate deck.
    return {
        "seed": seed,
        "turns": result["turns"],
        "turn_cap": turns,
        "winner": winner,
        "winner_seat_after_rotation": None if winner is None else seat.get(winner),
        "candidate_won": winner == "P1",
        "life": result["life"],
        "commanders": [c.name for c in commanders],
        "simplified": sum(1 for ln in game.log_lines if "(simplified" in ln),
        "log_tail": lines[-40:] if log else [],
        "label": "heuristic-baseline",
    }


def play_pod(deck: str, seeds: list[int], turns: int = DEFAULT_TURNS, opponents: list[str] | None = None, log_first: bool = False, workers: int = 1) -> dict:
    seats = [deck] + list(opponents or [])
    while len(seats) < 4:
        seats.append(FIXTURE if deck != FIXTURE else deck)
    seats = seats[:4]
    if workers <= 1 or len(seeds) == 1:
        games = [play_seed(s, turns, seats, log=(log_first and s == seeds[0])) for s in seeds]
    else:
        from concurrent.futures import ProcessPoolExecutor, as_completed
        games = [None] * len(seeds)
        with ProcessPoolExecutor(max_workers=workers) as ex:
            futs = {ex.submit(play_seed, s, turns, seats, False): i for i, s in enumerate(seeds)}
            for fut in as_completed(futs):
                games[futs[fut]] = fut.result()
    wins = sum(1 for g in games if g["candidate_won"])
    return {
        "deck": deck,
        "opponents": seats[1:],
        "seeds": seeds,
        "turns": turns,
        "games": len(games),
        "wins": wins,
        "win_rate": wins / len(games) if games else 0.0,
        "passed_25": bool(games) and (wins / len(games)) > 0.25,
        "seat": "turn order rotated by seed; candidate is P1",
        "bots": ["A", "B", "C", "D"],
        "label": "heuristic-baseline",
        "games_detail": games,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--deck", required=True)
    ap.add_argument("--opponents", nargs="*", default=[])
    ap.add_argument("--seeds", default="")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--turns", type=int, default=DEFAULT_TURNS)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--log", action="store_true", help="keep a log tail on the first game")
    ap.add_argument("--workers", type=int, default=1)
    args = ap.parse_args()
    if args.seed:
        seeds = [args.seed]
    elif args.seeds:
        seeds = parse_seeds(args.seeds)
    else:
        seeds = [1]
    report = play_pod(args.deck, seeds, args.turns, args.opponents, log_first=args.log or args.json, workers=args.workers)
    if args.json or len(seeds) == 1:
        if len(seeds) == 1:
            one = report["games_detail"][0]
            print(json.dumps(one, indent=2))
        else:
            slim = {k: v for k, v in report.items() if k != "games_detail"}
            print(json.dumps(slim, indent=2))
    else:
        print(f"candidate wins {report['wins']}/{report['games']} in {report['turns']} turns ({report['label']})")


if __name__ == "__main__":
    main()

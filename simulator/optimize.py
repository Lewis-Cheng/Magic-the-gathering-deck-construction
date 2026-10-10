"""Optimize a deck: tight synergy graph first, then win-rate vs a pod.

Phase 1 clears degree < 3 under the theme-aware graph (must-include kept).
Phase 2 runs four bot pilots until target win rate or max iterations.
Default target is >25% on 36 seeds; Terra runs use --target 0.50 --seeds 1-200.

  python simulator/optimize.py --deck DECK.py --target 0.5 --seeds 1-200 --turns 18
"""

from __future__ import annotations

import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, ROOT)

from engine.oracle import Oracle, Pool
from graph import report, roles
from pod import DEFAULT_TURNS, parse_seeds, play_pod



# Prefer cutting these when chasing win rate (off-plan / high MV / weak in engine)
_CUT_PRIORITY = [
    "Teferi, Hero of Dominaria",
    "Whirlwind of Thought",
    "The Wandering Emperor",
    "Elesh Norn, Grand Cenobite",
    "Martial Coup",
    "Heroes of the Revel",
    "Cryptic Command",
    "Ajani, Caller of the Pride",
    "Clever Concealment",
    "Dusk // Dawn",
    "Herald's Horn",
    "Hungry Lynx",
    "Highcliff Felidar",
    "Fleetfoot Panther",
    "Showdown of the Skalds",
    "Vanquisher's Banner",
    "Spirited Companion",
    "Summon: Leviathan",
    "Summon: Titan",
    "Demon of Fate's Design",
    "The Master of Keys",
    "Victor, Valgavoth's Seneschal",
    "Spark Double",
    "Anger",
    "The Eldest Reborn",
    "Binding the Old Gods",
    "Culling Ritual",
    "Neoform",
    "Eldritch Evolution",
    "The Apprentice's Folly",
    "Amphibian Downfall",
    "Amphibian Downpour",
    "Dauthi Voidwalker",
    "Archon of Sun's Grace",
    "Yenna, Redtooth Regent",
]


def clears_win_rate(wins: int, games: int, target: float) -> bool:
    return games > 0 and (wins / games) >= target


def read_rows(deck_path: str):
    oracle = Oracle()
    pool = Pool(oracle, deck_path)
    rows = []
    for card in pool.decklist():
        rows.append((card.name, list(card.tags or [])))
    return pool.commander.name, rows


def write_rows(deck_path: str, commander: str, rows: list[tuple[str, list]]) -> None:
    lines = [f"COMMANDER = {commander!r}", "DECK = ["]
    for name, tags in rows:
        kind = "land" if "land" in tags or name in {"Plains", "Island", "Swamp", "Mountain", "Forest", "Wastes"} else "spell"
        lines.append(f"    ({name!r}, 0, {kind!r}, 0, 0, {tags!r}),")
    lines.append("]")
    lines.append("")
    with open(deck_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def replacement(commander: str, rows: list[tuple[str, list]], cut: str) -> str | None:
    from generator.legal import color_identity

    present = {name for name, _ in rows} | {commander}
    ci = set(color_identity(commander) or set())
    oracle = Oracle()

    # Lantern: nearest live card on Deckmates to the current list.
    # What it does, then Combos, only when no seed sits on the earlier plane.
    try:
        from generator.atlas import get_atlas
        from generator.index import get_index
        atlas = get_atlas()
        index = get_index()
        from collections import Counter
        from graph import _strong
        seeds = [n for n, _tags in rows] + [commander]
        role_counts: Counter[str] = Counter()
        for name in seeds:
            try:
                role_counts.update(_strong(roles(oracle.require(name))))
            except KeyError:
                continue
        for lens in ("synergy", "textual", "combo"):
            hits = atlas.neighbors(seeds, ci=ci, limit=80, lens=lens, exclude=present)
            if not hits:
                continue
            for name, _dist in hits:
                if name == cut:
                    continue
                ic = index.by_name.get(name)
                if ic is None or ic.is_land or ic.spell_front_mdfc:
                    continue
                try:
                    card = oracle.require(name)
                except KeyError:
                    continue
                strong = _strong(roles(card))
                if not any(role_counts[r] >= 3 for r in strong):
                    continue
                return name
            break
    except Exception:
        pass
    return None


def swap_name(rows: list[tuple[str, list]], cut: str, add: str) -> list[tuple[str, list]] | None:
    out = []
    found = False
    oracle = Oracle()
    try:
        tags = sorted(roles(oracle.require(add))) or ["enchantment"]
    except Exception:
        tags = ["enchantment"]
    for name, t in rows:
        if not found and name == cut:
            out.append((add, tags))
            found = True
        else:
            out.append((name, t))
    return out if found else None


def _open_thin(deck_path: str, protected: set[str], min_degree: int = 3) -> list[str]:
    graph = report(deck_path, min_degree=min_degree)
    return [t["name"] for t in graph["thin"] if t["name"] not in protected]


def _pick_cut(rows, protected: set[str], basics: set[str], thin: list[str] | None = None) -> str | None:
    names = [n for n, tags in rows if n not in protected and n not in basics and "land" not in tags]
    if thin:
        for n in thin:
            if n in names:
                return n
    for n in _CUT_PRIORITY:
        if n in names:
            return n
    return names[0] if names else None


def _try_graph_swap(deck_path: str, commander: str, rows, cut: str):
    add = replacement(commander, rows, cut)
    if add is None:
        return None
    trial = swap_name(rows, cut, add)
    if trial is None:
        return None
    write_rows(deck_path, commander, trial)
    return add, trial


def optimize(deck_path: str, must_include: list[str], max_iterations: int = 8,
             seeds: list[int] | None = None, turns: int = DEFAULT_TURNS,
             opponents: list[str] | None = None, target: float = 0.25,
             workers: int = 1, min_degree: int = 3) -> dict:
    seeds = seeds or list(range(1, 37))
    protected = set(must_include)
    history: list[dict] = []
    commander, rows = read_rows(deck_path)
    basics = {"Plains", "Island", "Swamp", "Mountain", "Forest", "Wastes"}

    # Protect core Terra enchantress engines
    for core in ("Sythis, Harvest's Hand", "Enchantress's Presence", "Sanctum Weaver",
                 "Eidolon of Blossoms", "Opalescence", "Starfield of Nyx", "Destiny Spinner",
                 "Sol Ring", "Arcane Signet", "Smothering Tithe",
                 "Jetmir, Nexus of Revels", "Jinnie Fay, Jetmir's Second", "Anointed Procession",
                 "Maskwood Nexus", "Doubling Season", "Mondrak, Glory Dominus",
                 "Ojer Taq, Deepest Foundation // Temple of Civilization", "Craterhoof Behemoth",
                 "Beastmaster Ascension", "Shared Animosity", "Cathars' Crusade",
                 "Ghostly Prison", "Norn's Annex", "Blind Obedience", "Thalia, Guardian of Thraben",
                 "Winter Orb", "Sphere of Resistance", "Deafening Silence",
                 "Teferi, Time Raveler", "Grasp of Fate",
                 "Lightstall Inquisitor", "Urabrask the Hidden",
                 "Skrelv's Hive", "Oketra's Monument", "White Sun's Zenith",
                 "White Sun's Twilight", "Impact Tremors", "Felidar Retreat",
                 "Lingering Souls", "Secure the Wastes", "Shark Typhoon",
                 "Path to Exile", "Swords to Plowshares", "Akroma's Will", "Skullclamp",
                 "Impact Tremors", "Felidar Retreat"):
        if any(n == core for n, _ in rows):
            protected.add(core)

    blocked: list[str] = []
    for step in range(60):
        ginfo = report(deck_path, min_degree=min_degree)
        open_thin = [n for n in _open_thin(deck_path, protected, min_degree) if n not in blocked]
        history.append({
            "phase": "graph", "step": step, "thin": open_thin,
            "avg_degree": ginfo.get("avg_degree"), "edges": ginfo.get("edges"),
            "passed_graph": not open_thin and not blocked,
        })
        if not open_thin:
            break
        cut = open_thin[0]
        swapped = _try_graph_swap(deck_path, commander, rows, cut)
        if swapped is None:
            blocked.append(cut)
            history.append({"phase": "graph", "blocked_card": cut, "reason": "no replacement"})
            continue
        add, trial = swapped
        still = [n for n in _open_thin(deck_path, protected, min_degree) if n not in blocked]
        if cut in still or len(still) >= len(open_thin):
            write_rows(deck_path, commander, rows)
            blocked.append(cut)
            history.append({"phase": "graph", "reverted": cut, "tried": add, "reason": "swap did not clear thin"})
            continue
        rows = trial
        history.append({"phase": "graph", "applied": {"cut": cut, "add": add}, "thin_remaining": still})

    open_thin = _open_thin(deck_path, protected, min_degree)
    if open_thin:
        return {
            "deck": deck_path,
            "commander": commander,
            "turns": turns,
            "seeds": seeds,
            "target": target,
            "wins": None,
            "games": 0,
            "passed_wins": False,
            "passed_graph": False,
            "simulation": "not started",
            "thin": open_thin,
            "graph": report(deck_path, min_degree=min_degree),
            "history": history,
            "label": "heuristic-baseline",
            "note": "Graph is not clear, so the four bot pilots did not play.",
        }

    pod = None
    best_rows = list(rows)
    best_wins = -1
    for step in range(max_iterations):
        pod = play_pod(deck_path, seeds, turns, opponents, log_first=False, workers=workers)
        rate = pod["wins"] / pod["games"] if pod["games"] else 0.0
        ok_wins = clears_win_rate(pod["wins"], pod["games"], target)
        print(f"[sim {step}] wins={pod['wins']}/{pod['games']} rate={rate:.3f} target={target}", flush=True)
        if pod["wins"] > best_wins:
            best_wins = pod["wins"]
            best_rows = list(rows)
            write_rows(deck_path + ".best", commander, best_rows)
        history.append({
            "phase": "simulation",
            "step": step,
            "wins": pod["wins"],
            "games": pod["games"],
            "win_rate": round(rate, 4),
            "target": target,
            "passed_wins": ok_wins,
            "passed_graph": True,
            "graph": report(deck_path, min_degree=min_degree),
        })
        if ok_wins:
            break
        cut = _pick_cut(rows, protected, basics, thin=_open_thin(deck_path, protected, min_degree) or None)
        if cut is None:
            history.append({"phase": "simulation", "stop": "no legal cut"})
            break
        swapped = _try_graph_swap(deck_path, commander, rows, cut)
        if swapped is None:
            protected.add(cut)
            history.append({"phase": "simulation", "skip": cut, "reason": "no replacement"})
            continue
        add, trial = swapped
        if _open_thin(deck_path, protected, min_degree):
            write_rows(deck_path, commander, rows)
            history.append({"phase": "simulation", "reverted": cut, "tried": add, "reason": "swap broke the graph"})
            protected.add(cut)
            continue
        pod2 = play_pod(deck_path, seeds, turns, opponents, workers=workers)
        if pod2["wins"] < pod["wins"]:
            write_rows(deck_path, commander, rows)
            history.append({
                "phase": "simulation", "reverted": cut, "tried": add,
                "reason": "swap lowered wins", "wins_before": pod["wins"], "wins_after": pod2["wins"],
            })
            protected.add(cut)
            continue
        rows = trial
        history.append({
            "phase": "simulation", "applied": {"cut": cut, "add": add},
            "wins": pod2["wins"], "win_rate": round(pod2["wins"] / pod2["games"], 4),
        })
        pod = pod2

    # Restore best-seen list
    if best_wins >= 0:
        rows = best_rows
        write_rows(deck_path, commander, rows)
        pod = play_pod(deck_path, seeds, turns, opponents, log_first=False, workers=workers)
        print(f"[best] wins={pod['wins']}/{pod['games']} rate={pod['wins']/pod['games']:.3f}", flush=True)

    final_thin = _open_thin(deck_path, protected, min_degree)
    gfinal = report(deck_path, min_degree=min_degree)
    wins = None if pod is None else pod["wins"]
    games = 0 if pod is None else pod["games"]
    rate = (wins / games) if games else 0.0
    return {
        "deck": deck_path,
        "commander": commander,
        "turns": turns,
        "seeds": f"{seeds[0]}-{seeds[-1]}" if seeds else "",
        "seed_count": len(seeds),
        "target": target,
        "wins": wins,
        "games": games,
        "win_rate": round(rate, 4),
        "passed_wins": clears_win_rate(wins or 0, games, target),
        "passed_graph": not final_thin,
        "simulation": "finished",
        "thin": final_thin,
        "graph": gfinal,
        "history": history,
        "label": "heuristic-baseline",
        "note": "Graph cleared first. Four heuristic bots. Not a real Magic win rate.",
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--deck", required=True)
    ap.add_argument("--must-include", default="")
    ap.add_argument("--opponents", nargs="*", default=[])
    ap.add_argument("--seeds", default="1-36")
    ap.add_argument("--turns", type=int, default=DEFAULT_TURNS)
    ap.add_argument("--max-iterations", type=int, default=8)
    ap.add_argument("--target", type=float, default=0.25)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--min-degree", type=int, default=3)
    args = ap.parse_args()
    must = [p.strip() for p in args.must_include.split(",") if p.strip()]
    result = optimize(
        args.deck, must, args.max_iterations, parse_seeds(args.seeds),
        args.turns, args.opponents, target=args.target, workers=args.workers,
        min_degree=args.min_degree,
    )
    # Slim history for readability
    slim = dict(result)
    hist = []
    for h in result.get("history", []):
        h2 = {k: v for k, v in h.items() if k != "graph"}
        hist.append(h2)
    slim["history"] = hist
    print(json.dumps(slim, indent=2))


if __name__ == "__main__":
    main()

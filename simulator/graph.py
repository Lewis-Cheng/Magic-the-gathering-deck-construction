"""Synergy graph for any deck module.

Edges come from shared roles on Oracle text, not from a fixed tribe or color pair.
Degree under 3 is reported. Suggestions are not applied.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from engine.oracle import Oracle, Pool


def roles(card) -> set:
    text = (card.text or "").lower()
    out = set()
    if "{t}: add" in text or "add {" in text:
        out.add("ramp")
    if "draw " in text:
        out.add("draw")
    if "create " in text and "token" in text:
        out.add("token")
    if "counter target" in text or "destroy target" in text or "exile target" in text:
        out.add("removal")
    return out


def analyze(deck_path: str) -> None:
    oracle = Oracle()
    pool = Pool(oracle, deck_path)
    cards = [c for c in pool.decklist() if not c.is_land]
    commander = pool.commander
    by = {c.name: c for c in cards}
    by[commander.name] = commander
    names = list(by)
    adj = {n: set() for n in names}
    for i, a in enumerate(names):
        ra = roles(by[a])
        for b in names[i + 1:]:
            if ra & roles(by[b]):
                adj[a].add(b)
                adj[b].add(a)
    print("commander:", commander.name)
    print("nodes:", len(names))
    thin = [(n, len(adj[n])) for n in names if n != commander.name and len(adj[n]) < 3]
    thin.sort(key=lambda t: t[1])
    print("degree under 3:")
    if not thin:
        print("  none")
    for n, d in thin:
        print(f"  {d}  {n}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit("usage: python simulator/graph.py DECK.py")
    analyze(sys.argv[1])

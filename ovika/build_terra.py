"""Validate a Terra deck module: Oracle names, count, singleton, color identity, prices."""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from engine.oracle import Oracle, Pool

DECK_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "deck_terra_v1.py")
oracle = Oracle()
pool = Pool(oracle, DECK_PATH)
deck = pool.decklist()
print("deck rows:", len(deck), "| commander:", pool.commander.name,
      "| commander CI:", sorted(pool.commander.color_identity))

names = [c.name for c in deck]
from collections import Counter
dupes = {n: k for n, k in Counter(names).items() if k > 1 and "Basic" not in oracle.require(n).supertypes}
print("illegal duplicates:", dupes or "none")
print("total incl commander:", len(deck) + 1)

bad_ci = [c.name for c in deck
          if not set(c.color_identity) <= set(pool.commander.color_identity)]
print("color-identity violations:", bad_ci or "none")

prices = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                     "rulebook/data/card_prices.json"), encoding="utf-8"))
total = 0.0
missing = []
for c in deck:
    v = prices.get(c.name)
    if v is None:
        missing.append(c.name)
    else:
        total += float(v)
cv = prices.get(pool.commander.name)
if cv is None:
    missing.append(pool.commander.name)
else:
    total += float(cv)
print("total price (99 + commander): $" + ("%.2f" % total))
print("missing prices:", missing or "none")

for c in deck:
    oracle.require(c.name)
print("all", len(deck), "deck names verified in local AtomicCards")

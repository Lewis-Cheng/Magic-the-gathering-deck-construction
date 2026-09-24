"""Validate deck_v12 names against Oracle + compute total price."""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from engine.oracle import Oracle, Pool

oracle = Oracle()
pool = Pool(oracle, os.path.join(os.path.dirname(os.path.abspath(__file__)), "deck_v12.py"))
deck = pool.decklist()
print("deck rows:", len(deck), "| commander:", pool.commander.name)

prices = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "rulebook/data/card_prices.json"), encoding="utf-8"))

def price_of(name):
    if name in prices and prices[name] is not None:
        return float(prices[name])
    return None

total = 0.0
rows = []
for c in deck:
    p = price_of(c.name)
    if p is None:
        p = 0.0
        rows.append((c.name, c.mana_cost_str or "", "MISSING", None))
    else:
        total += p
        rows.append((c.name, c.mana_cost_str or "", f"{p:.2f}", p))

cp = price_of(pool.commander.name)
if cp is None:
    cp = 0.0
    print("COMMANDER PRICE MISSING")
total += cp

for r in sorted(rows, key=lambda x: -(x[3] or 0)):
    print(f"  {r[0]:<46} {r[1]:<10} ${r[2]}")
print(f"\ncommander: Ovika, Enigma Goliath ${cp:.2f}")
print(f"TOTAL (99 + commander): ${total:.2f}")
print("BUDGET OK" if total <= 1000 else "OVER BUDGET")

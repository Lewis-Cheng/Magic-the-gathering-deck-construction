import json, os, sys
sys.path.insert(0, os.path.join(os.getcwd(), "ovika"))
from engine.oracle import Oracle, Pool

oracle = Oracle()
pool = Pool(oracle, os.path.join("ovika", "deck_v12.py"))
prices = json.load(open("ovika/rulebook/data/card_prices.json", encoding="utf-8"))
def price_of(n):
    v = prices.get(n)
    return float(v) if v is not None else 0.0

deck = pool.decklist()
total = sum(price_of(c.name) for c in deck) + price_of(pool.commander.name)
lines = ["# Ovika Convoke Engine (v12) - 99 cards + Commander", ""]
lines.append(f"- Commander: **Ovika, Enigma Goliath** (${price_of(pool.commander.name):.2f})")
lines.append(f"- Total (100 cards): **${total:.2f}** (budget $1000)")
lines.append("")
def kind(c):
    if c.is_land: return "land"
    if c.is_creature: return "creature"
    return "spell"
by_kind = {}
for c in deck:
    by_kind.setdefault(kind(c), []).append(c)
for kk, label in [("land", "Lands"), ("spell", "Noncreature spells"), ("creature", "Creatures")]:
    items = by_kind.get(kk, [])
    lines.append(f"## {label} ({len(items)})")
    lines.append("")
    lines.append("| Card | Cost | Price |")
    lines.append("|---|---|---|")
    for c in sorted(items, key=lambda x: x.mana_cost.cmc()):
        lines.append(f"| {c.name} | {c.mana_cost_str or '-'} | ${price_of(c.name):.2f} |")
    lines.append("")
open("ovika/decklist_v12.md", "w", encoding="utf-8").write("\n".join(lines))
print("written decklist_v12.md,", len(deck), "cards, total $%.2f" % total)

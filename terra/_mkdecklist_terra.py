import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from engine.oracle import Oracle, Pool

HERE = os.path.dirname(os.path.abspath(__file__))
oracle = Oracle()
pool = Pool(oracle, os.path.join(HERE, "deck_terra.py"))
prices = json.load(open(os.path.join(HERE, "rulebook/data/card_prices.json"), encoding="utf-8"))

def price_of(n):
    v = prices.get(n)
    return float(v) if v is not None else 0.0

deck = pool.decklist()
total = sum(price_of(c.name) for c in deck) + price_of(pool.commander.name)

# MTGO text
mtgo = [pool.commander.name] + [c.name for c in deck]
open(os.path.join(HERE, "decklist_terra_mtgo.txt"), "w", encoding="utf-8").write("\n".join(mtgo) + "\n")

lines = ["# Terra, Magical Adept // Esper Terra - Combo (99 + Commander)", ""]
lines.append(f"- Commander: **{pool.commander.name}** (${price_of(pool.commander.name):.2f})")
lines.append(f"- Total (100 cards): **${total:.2f}**")
lines.append(f"- Strategy: Esper Terra + The Apprentice's Folly / Mirrormade copy loop (no convoke/token combat plan)")
lines.append("")

def kind(c):
    if c.is_land:
        return "land"
    if c.is_creature:
        return "creature"
    return "spell"

by_kind = {}
for c in deck:
    by_kind.setdefault(kind(c), []).append(c)

for kk, label in [("creature", "Creatures"), ("spell", "Noncreature spells"), ("land", "Lands")]:
    items = by_kind.get(kk, [])
    lines.append(f"## {label} ({len(items)})")
    lines.append("")
    lines.append("| Card | Cost | Price |")
    lines.append("|---|---|---|")
    for c in sorted(items, key=lambda x: (x.mana_cost.cmc(), x.name)):
        lines.append(f"| {c.name} | {c.mana_cost_str or '-'} | ${price_of(c.name):.2f} |")
    lines.append("")

open(os.path.join(HERE, "decklist_terra.md"), "w", encoding="utf-8").write("\n".join(lines))
print("written decklist_terra.md + decklist_terra_mtgo.txt |", len(deck), "cards | total $%.2f" % total)

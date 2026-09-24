import sys, os
sys.path.insert(0, os.path.join("ovika", "engine"))
from oracle import Oracle
o = Oracle()
for n in ["Rhystic Study", "Delighted Halfling", "Arid Mesa", "Serra's Sanctum"]:
    c = o.get(n)
    if c is None:
        print("MISSING", n)
    else:
        print(f"{c.name:28s} {c.mana_cost_str:8s} CI={sorted(c.color_identity)} | {c.text[:80]}")

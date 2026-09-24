import sys
sys.path.insert(0, ".")
from engine.oracle import Oracle
o = Oracle()
for n in ["Estrid's Invocation", "Copy Enchantment", "Misty Rainforest", "Moonmist", "The Apprentice's Folly", "Demon of Fate's Design"]:
    c = o.get(n)
    print(repr(n), "->", ("MISSING" if c is None else (sorted(c.types), c.mana_cost_str, (c.text or "")[:70])))

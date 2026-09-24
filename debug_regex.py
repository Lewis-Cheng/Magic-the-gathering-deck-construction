import re
t = '{T}, Pay 1 life, Sacrifice this land: Search your library for a Mountain or Plains card, put it onto the battlefield, then shuffle.'
t = t.lower()
print("sacrifice" in t, "search your library" in t)
m = re.search(r"search your library for (?:a |an |up to two |up to three )?(basic [a-z ]+?|[a-z]+ card)", t)
print("regex:", m)
if m: print("want:", m.group(1))

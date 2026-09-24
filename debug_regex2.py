import re
t = 'search your library for a mountain or plains card, put it onto the battlefield, then shuffle.'
pats = [
 r"search your library for (?:a |an |up to two |up to three )?(basic [a-z ]+?|[a-z]+ card)",
 r"search your library for a [a-z]+ card",
 r"search your library for .*card",
 r"[a-z]+ card",
]
for p in pats:
    m = re.search(p, t)
    print(repr(p), "->", m)

import json
fetch = json.load(open("ovika/rulebook/data/terra_prices_fetch.json", encoding="utf-8"))
print(len(fetch), "keys")
for k in sorted(fetch):
    if any(s in k for s in ("Breeding","Terra","Forest","Plains","Godless","Lotus")):
        print(repr(k), fetch[k])

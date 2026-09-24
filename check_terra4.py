import sys, os, gzip, json
with gzip.open(os.path.join("ovika","rulebook","data","AtomicCards.json.gz"), "rt", encoding="utf-8") as f:
    data = json.load(f)["data"]
for name, ps in data.items():
    if "esper terra" in name.lower() or name == "Esper Terra":
        p = ps[0]
        print("KEY:", name)
        print(" cost:", p.get("manaCost"), "| types:", p.get("types"), p.get("subtypes"), "| P/T:", p.get("power"), p.get("toughness"))
        print(" text:", repr(p.get("text")))
        print(" kw:", p.get("keywords"), "| CI:", p.get("colorIdentity"))

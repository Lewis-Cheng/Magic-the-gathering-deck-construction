import json, os
for p in ["ovika/collection_cards.json", "ovika/ur_pool.json"]:
    try:
        with open(p, encoding="utf-8") as f:
            d = json.load(f)
        if isinstance(d, list):
            hits = [x for x in d if isinstance(x, dict) and "terra" in json.dumps(x).lower()][:5]
            print(p, "LIST len", len(d), "hits:", [h.get("name") for h in hits])
        elif isinstance(d, dict):
            keys = list(d.keys())[:5]
            print(p, "DICT keys sample:", keys, "len", len(d))
            hits = [k for k in d if "terra" in k.lower()][:10]
            print(" terra keys:", hits)
    except Exception as e:
        print(p, "ERR", e)

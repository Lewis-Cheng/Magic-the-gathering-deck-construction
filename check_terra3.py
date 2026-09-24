import sys, os
sys.path.insert(0, os.path.join("ovika", "engine"))
from oracle import Oracle
o = Oracle()
k = [n for n in o._by_name if n.lower().startswith("terra, magical")]
print("KEYS:", k)
c = o.get("Terra, Magical Adept // Esper Terra")
print("FRONT:", repr(c.text))
# back face: MTGJSON key is front//back; need otherFace text
import gzip, json
with gzip.open(os.path.join("ovika","rulebook","data","AtomicCards.json.gz"), "rt", encoding="utf-8") as f:
    data = json.load(f)["data"]
for kk in k:
    for printing in data[kk]:
        faces = printing.get("otherFaceIds") or []
        break
print("face data:", data[k[0]][0].get("otherFaceIds"))
# find the back face via otherFaceIds
fid = data[k[0]][0].get("otherFaceIds")
if fid:
    for name, printings in data.items():
        for p in printings:
            if p.get("identifiers", {}).get("mtgjsonV4Id") in fid:
                print("BACK FACE:", name, "|", p.get("manaCost"), "|", p.get("text"), "|", p.get("power"), p.get("toughness"), "|", p.get("types"), p.get("subtypes"), p.get("keywords"))

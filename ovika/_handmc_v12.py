import sys, os, json
sys.path.insert(0, os.path.join(os.getcwd(), "ovika"))
from engine.oracle import Oracle, Pool
from batch.gpu_sim import hand_mc, device
oracle = Oracle()
pool = Pool(oracle, os.path.join("ovika", "deck_v12.py"))
names = [c.name for c in pool.decklist()]
print("device:", device(), "deck size:", len(names))
r = hand_mc(names, pool.commander.name, n=200000, oracle=oracle)
print(json.dumps(r, indent=1))

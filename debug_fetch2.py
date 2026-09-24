import sys, os
sys.path.insert(0, "ovika")
from engine.oracle import Oracle
o = Oracle()
for n in ["Arid Mesa", "Marsh Flats", "Windswept Heath", "Wooded Foothills"]:
    c = o.require(n)
    print(n, "->", repr(c.text))

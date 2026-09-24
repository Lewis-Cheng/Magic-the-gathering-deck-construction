import json, os
base = "ovika/rulebook/data/card_prices.json"
prices = json.load(open(base, encoding="utf-8"))
fetch = json.load(open("ovika/rulebook/data/terra_prices_fetch.json", encoding="utf-8"))
for k, v in fetch.items():
    prices[k] = float(v) if v is not None else None
json.dump(prices, open(base, "w", encoding="utf-8"))
print("merged", len(fetch), "->", len(prices))

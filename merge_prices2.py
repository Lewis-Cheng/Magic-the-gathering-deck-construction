import json
prices = json.load(open("ovika/rulebook/data/card_prices.json", encoding="utf-8"))
fetch = json.load(open("ovika/rulebook/data/terra_prices_fetch2.json", encoding="utf-8"))
for k, v in fetch.items():
    prices[k] = float(v) if v is not None else None
json.dump(prices, open("ovika/rulebook/data/card_prices.json", "w", encoding="utf-8"))
print("merged", len(fetch))

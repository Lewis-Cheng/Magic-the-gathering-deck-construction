# Examples

## Pass — generate (no sim)

Intake:

```json
{
  "commander": "Sythis, Harvest's Hand",
  "theme": "enchantress",
  "budget_usd": 150,
  "power_level": "casual"
}
```

Agent:

1. `Oracle.require("Sythis, Harvest's Hand")` → CI GW.
2. Load enchantress recipe (36 lands, enchantress seed/payoff queries).
3. Build a GW land base for ~$150 casual (no shock/fetch requirement).
4. Search Oracle for GW cards matching seed/payoff/ramp/draw/interaction; tag from text.
5. Drop unpriced cards; drop Game Changers / extra turns (casual).
6. Fill 99; each nonland has slot + reason.
7. Return JSON `confidence: "generator-only"`, `legality.ok` true, `total_usd <= 150`. No `win_rate`.

Do not start from Terra or Ovika files even though Sythis appears in Terra AI lists.

## Fail closed — missing budget

Intake `{ "commander": "Ovika, Enigma Goliath", "theme": "tokens" }` → error: `budget_usd` required. Do not assume 1000. Do not emit `deck_v12.py`.

## Fail closed — empty retrieval

If the index returns no token-makers in that CI, do not invent “Goblin Rabblemaster.” Set `theme_fill.ok false` / refuse a sellable list.

## Collection first — stop before shop cards

File `binder.txt`:

```
20 Forest
20 Plains
1 Sol Ring
1 Sythis, Harvest's Hand
1 Enchantress's Presence
```

Intake adds `"collection_file": "binder.txt"`, `"win_condition": "enchantress draw into auras"`, `"must_include": ["Enchantress's Presence"]`.

First draft uses only those names, up to counts. It will be short of 99. `Enchantress's Presence` is in the file, so it is in the draft. Do not add `Argothian Enchantress` yet.

Ask in Traditional Chinese how many cards outside the file may be added. If the user says 8, add at most 8 `source: "new"` cards. If they say 0, return the short draft and do not run the 36-game loop.

## Lab-only (wrong skill)

“Replay seed 7 of Ovika vs Nekusar and patch `deal_damage`” → simulator skill, not this one.

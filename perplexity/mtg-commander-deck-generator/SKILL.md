---
name: mtg-commander-deck-generator
description: >-
  Load when the user asks the Agent API (preset medium / Deep Research) to
  generate, rebuild, or optimize a Magic Commander / EDH 99, names a
  commander, a win condition, a budget, or pastes a collection. Do not load
  for rules-only questions, limited, Modern, Standard, or Perplexity
  Computer. Do not load to run a local simulator or quote a win rate.
---

# Commander 99 — Perplexity Agent API (Deep Research)

**Runtime is the Agent API with `preset: "medium"` only.** This skill is not for Perplexity Computer. If the host is Computer, stop and say the list must be built with the Agent API Deep Research preset, not Computer.

Do not invent a local `AskQuestion` tool, `AtomicCards`, `generator/atlas.py`, or `simulator/optimize.py`. Those exist in the Cursor repo, not here.

Card **names** stay English. User-facing prose may be Traditional Chinese if the user writes Chinese.

## Hard stop: intake before any search

Before Scryfall, EDHREC, Lantern, a draft, or a swap, collect intake. A pasted list is `seed_list` / collection, not intake.

Ask **all** of these in one message. Wait. Do not infer `win_condition`, `budget_usd`, or `power_level`. Do not default budget to 1000.

Required:

1. `commander` — exact English Oracle name
2. `win_condition` — the user’s sentence; do not rewrite it
3. `budget_usd` — number > 0
4. `power_level` — `precon` | `casual` | `focused` | `high` | `cedh`
5. `interaction_density` — `low` | `medium` | `high` (instants and flash)
6. `stax_density` — `none` | `light` | `medium` | `heavy`
7. `must_include` — names or none
8. `exclude` — names or none
9. `collection` — pasted names or none
10. `back_face_plan` — if the commander is MDFC/DFC/transform; otherwise “not a transform commander”

Missing any required field → stop. Do not draft.

After answers, echo intake JSON once (see `schemas.md`).

`new_cards_allowed` is asked **only after** a collection-first draft, integer ≥ 0, no default.

## Tools

Use the request’s **`web_search`** (and page fetch if the API exposes it) for every card fact: Oracle text, color identity, commander legality, Commander banned list, USD prices.

Do **not** curl Scryfall or EDHREC from the sandbox. Sandbox is only for writing the JSON/MTGO files and running `python scripts/check_list.py`.

Cite sources. Prefer:

- Scryfall named / commander-legality
- Official Commander banned list (Wizards / format page as dated)
- Cardmarket / TCGPlayer / Scryfall USD as `prices_as_of`
- [Lantern](https://stoken.games/stack/lantern/lantern.html), [Endless Atlas](https://stoken.games/stack/card-atlas.html), [methodology](https://stoken.games/stack/methodology.html)

Do **not** copy an EDHREC average 99 as the list. EDHREC may be a citation for popularity, not a constructor.

## Card discovery (Lantern order)

Every nonland name must come from a search neighborhood, not from walking a dump or copying a staple list.

1. Start from cards already chosen (commander, collection, must-includes).
2. Nearest neighbors on the **Deckmates** plane (Lantern / Atlas).
3. If that slot is empty, **What it does**, then **Combos**.
4. Filter neighbors by color identity ⊆ commander CI (both faces) and by `recipes.md` `tag:` queries. Queries filter; they do not pick the neighborhood.
5. Empty neighborhood → fail closed. Do not invent names.

If Atlas coordinates cannot be fetched this run, say so, use the same three-lens *order* with cited synergy/combo pages, and stamp `atlas_fetch: failed`. Still refuse uncited names.

## Pipeline

```
intake wait
  → web_search commander, both faces, CI, ban/format
  → collection-only first draft (if collection given)
  → wait for new_cards_allowed
  → fill slots from Lantern neighborhoods
  → densities, back_face_plan, budget
  → write deck JSON + MTGO
  → python scripts/check_list.py
```

### Collection

One English name per line; optional `4 Mountain` or `Mountain,4`. Unknown names: list them and drop them.

First draft: only owned names, up to counts. Collection cards `source: "collection"` and `price_usd: 0` toward budget. Holes stay holes (`missing_slots`). Then ask how many **new** cards. Each new name (and an unowned commander) counts as 1. `must_include` missing from the collection spends the allowance first.

### Recipe

`recipes.md`. Match `win_condition` heading; else midrange shell + payoff queries from the user’s sentence. Apply density modifiers. Lands + slots = 99.

### Tagger (from Oracle text only)

| Signal | Tag |
|---|---|
| `{T}: Add` / add mana | `ramp` / `rock` if artifact |
| counter target spell | `counter` |
| draw | `draw` |
| search library | `tutor` |
| destroy/exile all | `wipe` |
| create token | `token` |
| hexproof / indestructible / protection / cannot be countered | `protection` |
| extra turn | `extra-turn` |
| skip untap / tax / orbs | `stax` |
| Instant or Flash | `interaction` |

### Price

Missing price is `null`, never `$0`. Exclude or substitute. Sum only known prices. Collection = 0 toward budget. Stamp `prices_as_of`.

### Power

Below `focused`, strip extra turns, listed fast mana, Game Changers, hard stax from `recipes.md`, unless `must_include` or `stax_density` is medium/heavy (keep the stax they asked for).

### Audit (hard fail)

- Finished 100 = commander + 99. Collection-only draft may be shorter.
- `source: "new"` ≤ allowance
- Singleton except basics
- CI ⊆ commander CI (both faces)
- On dated Commander ban list → fail
- Spell-front MDFC lands: do not include as lands
- `total_usd <= budget_usd` (null prices not treated as 0)
- Interaction / stax meet densities
- Transform: some nonlands serve `back_face_plan`
- `check_list.py` must exit 0 before returning a sellable list

## Simulation — forbidden here

Set `confidence: "research-only"`. Do not quote `wins/36`, `win_rate`, or heuristic-baseline. Graph degree and pod sims run only in the Cursor repo after the user pastes this 100 there.

Do not silently strip interaction or stax to make the list “tighter.”

## Output

1. Intake echo
2. Deck JSON per `schemas.md` (`confidence: "research-only"`)
3. MTGO plaintext derived from that JSON
4. Citations
5. `atlas_fetch` ok or failed
6. If collection-only: `missing_slots` and the new-card question, not a fake 100

---
name: mtg-commander-deck-generator
description: >-
  Constructs a legal Commander 99 from commander, win condition, budget, and
  an optional collection file. First draft uses only cards in that file, then
  asks how many new cards may be added. Use when generating an EDH list the
  user can build from cards they own. Do not use pod_v12 as the constructor.
---

# Commander deck generator

This is the **product** skill. The user chooses the commander and the win condition. Any legal commander is in scope. Lab files such as `deck_v12.py` are one old experiment, not a template and not a limit.

**Website construction is forbidden until** [website-gate.md](website-gate.md) is fully checked. If the user asks for a site and the gate is open on any item, finish this skill set first and say so.

## When this skill applies

User names a commander, a win condition, a budget, or “generate an EDH deck.” The commander string is whatever they typed. Do **not** replace it with a lab commander, and do **not** open `ovika/deck_v12.py` or `ovika/deck_terra_*.py`.

## Non-negotiables

1. Required intake: `commander`, `win_condition`, `budget_usd`, `power_level`. Missing any → stop. Do not fill a missing commander or win condition from a previous deck. Do not default the budget to $1000. `theme` is optional and only a slot-count hint; if it conflicts with `win_condition`, follow `win_condition`.
2. Every nonland name from `Oracle.require` + recipe search. Empty pool → fail closed. Do not invent names.
3. Deck JSON is **names only**. CMC/types/text/CI from AtomicCards. Roles from the tagger, not handwritten tuples.
4. Missing price is `null`, never `$0`. Exclude the card or substitute.
5. If `collection_file` is present, the first draft uses **only** names in that file. Do not add shop cards, and do not run the 25% loop, until the user answers how many new cards are allowed (0 is valid).
6. Accept a finished 100 only if legal, on win-condition, on budget, must-includes kept, new-card count ≤ allowance, and (when coverage allows) simulator ≥ 10/36 with the graph rule below.
7. No naked `win_rate` marketed as real Magic. Quote `wins/36` only as `heuristic-baseline` after coverage passes. Otherwise `coverage-blocked` and do not optimize.
8. Do not import `Pool` (executes Python tuples; defaults commander to Ovika).

Details: [schemas.md](schemas.md), [recipes.md](recipes.md), [issues.md](issues.md), [examples.md](examples.md).

## Pipeline (run in order)

```
intake + collection file
      → Oracle commander + both-face CI → ban/format
      → FIRST DRAFT from collection only (stop and ask new-card count)
      → add at most N shop cards
      → coverage gate on the win condition
      → if covered: graph + 36-game sim (deadlock relaxes graph, not the win rate)
```

### 1. Intake

Reject: commander name not in Oracle, `win_condition` empty, or `budget_usd <= 0`.

`commander` is the exact English name the user gave. Look it up. Use that card’s color identity (both faces). Any identity is legal: mono-color, two-color, three-color, four-color, five-color, or colorless. Do not refuse a commander because it is not in the lab decks.

`win_condition` is the user’s own sentence: what the deck is trying to do. Examples the user might type: tokens, enchantress, mill, commander damage, reanimate, spellslinger, +1/+1 counters, aristocrats, or a named combo. Build the 99 to that sentence. Do not rewrite it into a convoke or goblin plan unless the user wrote that.

Optional: `per_card_cap_usd`, `collection_file`, `new_cards_allowed` (only after the user answers), `land_count`, `exclude`, `must_include`, `theme`.

### 1b. Collection file (hard stop)

Accept `.txt` or `.csv`. One English Oracle name per line. Optional count: `4 Mountain` or `Mountain,4`. Ignore blank lines and a header row named `name` or `card`.

Resolve every name with `Oracle.require`. Unknown names are listed back to the user and are not in the pool.

**First draft:** lands and spells may use only cards in the file, up to owned counts. Basics may repeat only up to the owned count. Do not fill holes with shop cards. A short collection produces a short list plus `missing_slots`. Cards in the file get `source: "collection"` and `price_usd: 0` toward `budget_usd`.

If the commander is not in the file, leave it as the commander but mark `commander_owned: false`. It will consume 1 new-card slot later. Do not pretend it is owned.

`must_include` names absent from the file are **not** in the first draft. They wait for the new-card allowance.

Then stop and ask, in Traditional Chinese, how many cards **outside the file** may be added. Wait for an integer ≥ 0. Do not assume a number. Do not start simulator optimization on the partial draft.

**After the answer:** add at most that many new names (each copy counts as one). New cards pay market price, must pass color identity, ban list, and budget, and are tagged `source: "new"`. `must_include` not in the collection consumes this allowance first. If the allowance is too small to fit required must-includes plus a legal 100, return the draft and the shortfall. Do not silently buy more.

### 2. Commander

`Oracle.require` on the user’s name. Color identity = both faces of that card. If that card is banned as a commander, fail. Otherwise proceed, whatever the colors are.

### 3. Recipe

Pick slot counts from [recipes.md](recipes.md) only when a heading matches the user’s `win_condition`. If none match, use the midrange counts as a neutral shell and set payoff/seed queries from the user’s sentence. Lands + slots = 99. Never copy a lab list’s land count or payoff package.

### 4. Lands

Target `recipe.lands` (or `land_count` if set). Basics and duals must match **this** commander’s colors, not a fixed pair. Order: one basic per color in the identity → budget duals in those colors → shocks/fetches only if budget and `power_level` is `high` or `cedh` → utility lands if they fit the identity, the price, and the user’s win condition.

While drafting from a collection, take lands only from the file, up to owned counts. If that cannot reach the land target, leave the hole and report it. Do not add duals the user does not own until `new_cards_allowed` is set.

### 5. Retrieve

Search local AtomicCards: `CI ⊆ commander CI`, recipe query, tagger role. Cap ~80 per slot.

If a collection file was given, the first-draft pool is the **intersection** of that search and the file. Shop cards enter the pool only after the user sets `new_cards_allowed`, and only up to that count. Empty intersection → `missing_slots`, not invented names.

### 6. Tagger (`tagger_version: 1`)

From Oracle text only:

| Signal | Tag |
|---|---|
| `{T}: Add` / “add one mana” | `ramp` / `rock` if artifact |
| “counter target spell” | `counter` |
| “draw” on instant/sorcery or “draw a card” engine | `draw` |
| search library for card | `tutor` |
| destroy/exile all | `wipe` |
| create token | `token` |
| hexproof/indestructible/protection / “cannot be countered” | `protection` |
| extra turn | `extra-turn` |
| skip untap / tax spells / orbs | `stax` |

### 7. Price

Local `ovika/rulebook/data/card_prices.json`. Optional Scryfall only if explicitly enabled (`User-Agent` + `Accept: application/json`). Sum only known prices. Collection cards count as 0. New cards use the market price. Missing price on a new card excludes it (never treat as $0). No default cap of 1000.

### 8. Power level

Below `focused`, strip [recipes.md](recipes.md) power filters (extra turns, listed fast mana, Game Changers, hard stax) unless `must_include`.

### 9. Fill

Start `cards = []`. First pass: collection only, lands then slots, `must_include` only when that name is in the file. Honor `exclude`. Each row: `name`, `slot`, `source` (`collection` or `new`), `price_usd`, `reason`. Stop if `new_cards_allowed` is unset. Second pass: spend the allowance, must-includes outside the file first.

### 10. Audit (hard fail)

- Finished list: 99 cards + commander = 100. The collection-only draft may be shorter; that is not a failure.
- `source: "new"` count ≤ `new_cards_allowed` (commander counts as 1 if not owned)
- Singleton except basics
- Each card CI ⊆ commander CI (both faces)
- On dated ban list → fail ([issues.md](issues.md) B3)
- MDFC lands: front-face key; spell-front MDFC → do not include
- `total_usd <= budget_usd`; per-card cap if set
- `legality.ok` false ⇒ do not return a sellable list

### 11. Coverage, graph, and 25% (only on a finished 100)

Any commander is allowed. If the win-condition cards are not implemented in the engine, set `confidence: "coverage-blocked"`, do not quote a win rate, and do not swap cards to chase one.

When coverage passes, both gates apply on seeds 1–36, turn cap 14:

- Simulator: at least 10 wins out of 36 (over 25%). Label `heuristic-baseline`. This is not a real Magic win rate.
- Graph: nonland degree under 3 must be swapped, same slot, still inside the collection plus the new-card allowance. Pair rules come from **this** commander and **this** `win_condition`. Do not reuse another deck’s pair rules, and do not drop a card for being outside a fixed color pair.

Deadlock: if every swap that clears a degree-under-3 card drops the deck below 10/36, **keep the card** (and every `must_include`). The graph gate relaxes. The 10/36 gate does not. Record the kept thin nodes.

Do not run this loop on the collection-only draft before the user sets `new_cards_allowed`.

### 12. Output

JSON per [schemas.md](schemas.md) plus MTGO plaintext derived from JSON. Stamp `ban_list_version`, `prices_as_of`, `tagger_version`, `confidence: "generator-only"`. Coverage: `"not_probed": true` until a real coverage gate exists.

## Lab vs product

| | Product (this skill) | Lab |
|---|---|---|
| Start | Empty JSON 99 | `deck_v12.py` / Terra modules |
| Fitness | Legal + theme + budget | 36-seed Nekusar pod |
| AI / tags | Oracle tagger | Handwritten tuple tags |
| Sim | Off; or `coverage-blocked` | `pod_v12.py`, GPU hand MC |

If asked to **tune Ovika inside the engine**, use the lab skills. If asked to **make a list a customer could buy**, stay here.

## After each issue-shaped change

Append `agent-work/flexibility-productization/ISSUE-LOG.md`: code, **skill audit** (this file + lab SKILL.md), **simulator audit** (`pod_v12.py`, `ai.py`, `generic.py`, `Oracle.require` / `Pool`). Do not use the pod as constructor.

## Website (only after the gate)

When [website-gate.md](website-gate.md) is all checked: FastAPI `POST /v1/decks` + `POST /v1/swap` + `GET /v1/commanders`; React form with **no** default commander/theme/$1000; names+slots only (no card images); Generate disabled until required fields; sim button disabled or `coverage-blocked`; claims copy from `agent-work/flexibility-productization/CLAIMS.md`.

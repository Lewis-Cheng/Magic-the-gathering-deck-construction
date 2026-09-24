# How this skill closes the 43 issues

Operational rules. Lab code may still have the bug; the **generator agent** must obey the close.

## A Generator

| ID | Close |
|---|---|
| A1 | Retrieve from Oracle index + recipe query. Never memorize staples. Empty → fail. |
| A2 | [recipes.md](recipes.md) slot quotas per theme. Not Ovika 28/11/12. |
| A3 | Start `cards = []`. Never clone `deck_v12.py` / Terra. |
| A4 | Required JSON intake. No silent defaults. |
| A5 | Graph from this recipe + this CI. Suggestions only. No auto-swap. |
| A6 | This skill is product. Lab skills are engine-only. |
| A7 | Accept = legal + theme_fill + budget. Not Nekusar 36-seed wins. |

## B Data

| ID | Close |
|---|---|
| B1 | Tagger on Oracle text. Ignore tuple tags. |
| B2 | One legality gate (count, singleton, CI, MDFC). |
| B3 | Dated ban list; banned name fails. Snapshot in `generator/data/ban_list.json` when present. |
| B4 | Missing price `null`, never 0. Exclude or substitute. |
| B5 | Cap from intake only. No hardcoded 1000. |
| B6 | Both-face CI; land MDFC front face; no spell-front MDFC. |
| B7 | JSON names, not Python tuples (comma-merge). |
| B8 | Replacements not filtered to UR. |

## C Engine (honest; not checkout)

| ID | Close |
|---|---|
| C1 | Generate does not require hooks. Sim without coverage → `coverage-blocked`, no win table. |
| C2 | Do not use shared Ovika AI to pick the 99. Future sim stamps `ai_version` / `shared-pilot abstraction`. |
| C3 | Counters from tagger (`counter target spell`), not `"counter"` in a tuple. |
| C4 | Mulligan is recipe/commander-curve when sim exists. Not 2–5 lands + CMC≤3 as product policy. |
| C5 | Turn cap disclosed; cap-loss ≠ “cannot win.” Generate ignores turn cap. |
| C6 | If sim: rotate seats or label `seat-0-only`. Generate does not seat. |
| C7 | If sim: Wilson CI; do not churn 1-win swaps. Generate does not use n=36. |
| C8 | Lab pod is preset `lab-ovika-pod` only. Not default meta. |
| C9 | Disclose perf guards if sim. Do not clip generate. |
| C10 | Disclose partial combat/PW/copy if sim. |
| C11 | Lab: new damage via `deal_damage`. Not a generate rule. |
| C12 | Never quote `sim.py` or `fast_sweep` as product. No `win_rate` on generate. |
| C13 | Hand MC is lands-only; not theme consistency. |
| C14 | Sim may log `pilot` misses. Do not blame the 99 for AI. |
| C15 | Simplified logs by card on the critical path, not a raw count. |

## D Flexibility

| ID | Close |
|---|---|
| D1 | Generate needs no `engine/<commander>.py`. Sim may be blocked. Partial by design. |
| D2 | Theme ontology in [recipes.md](recipes.md). |
| D3 | Land builder from identity + budget + power. |
| D4 | Same-slot cheaper substitutes. Swap API later. |
| D5 | Power filters below `focused`. |
| D6 | `owned_cards` preferred at price 0. |
| D7 | Opponents not used in generate. |

## E Product / site

| ID | Close |
|---|---|
| E1 | No win-rate marketing. See CLAIMS.md. |
| E2 | Generate = seconds CPU. Pods = future queue. |
| E3 | No bulk card images; dated snapshots; MTGJSON/Scryfall ToS. |
| E4 | Illegal/off-budget/off-theme ⇒ `ok: false`, not a sale. |
| E5 | Every card `reason`; cheaper same-slot swap. |
| E6 | Pinned service Python. Not Codex PATH or laptop CUDA. |

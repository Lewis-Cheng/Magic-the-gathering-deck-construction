# Model / artifact configs

## Commander
- **Value**: Ovika, Enigma Goliath (UR)
- **Rationale**: Lab target; every noncreature with Ovika on board makes X Phyrexian Goblins (X = MV)
- **Search range**: Terra is a separate family (`terra/`)
- **Sensitivity**: high
- **Source**: CONTEXT.md; REPORT.md §4

## Live deck module
- **Value**: `ovika/deck_v12.py` (v12.1 FINAL)
- **Rationale**: Adopted after v12.0 3/36 and v12.2 8/36
- **Search range**: `deck_v1.py`–`deck_v11.py` archive
- **Sensitivity**: high
- **Source**: CONTEXT.md Key files

## Deck shape (99 + commander)
- **Value**: 28 lands · 11 ramp · 10 draw · 12 convoke payoffs · 15 creatures/convoke bodies · 6 token spells · 9 burst/velocity · 5 protection · 3 utility
- **Rationale**: Convoke chain + rituals + amplifiers
- **Search range**: Not specified as a sweep; v12.2 changed creature/ping mix
- **Sensitivity**: high
- **Source**: REPORT.md §4

## List price v12.1
- **Value**: $533.00
- **Rationale**: Under $1,000 cap; `build_convoke.py` BUDGET OK
- **Search range**: Cap $1,000 (REPORT.md)
- **Sensitivity**: medium
- **Source**: REPORT.md §1

## List price v12.2 (rejected)
- **Value**: $546.04
- **Rationale**: Pinger variant cost
- **Search range**: Not adopted
- **Sensitivity**: medium
- **Source**: REPORT.md §1; CONTEXT.md

## Synergy graph v12.1
- **Value**: 72 nodes, 712 tight edges, 1 component, 3 communities; no node degree < 3; deg-3 tail = 7 draw/velocity spells
- **Rationale**: Audit lens
- **Search range**: Pair rules are handwritten
- **Sensitivity**: high (misuse as retain criterion)
- **Source**: CONTEXT.md graph_analysis.py bullet

## Phase verifier
- **Value**: 21/21
- **Rationale**: Must stay green after engine edits
- **Search range**: Not specified
- **Sensitivity**: high
- **Source**: CONTEXT.md; engine README

## CR corpus
- **Value**: 1,414 numbered rules, effective 2025-02-07
- **Rationale**: Official sequencing source
- **Search range**: Not specified
- **Sensitivity**: low
- **Source**: engine README Data sources

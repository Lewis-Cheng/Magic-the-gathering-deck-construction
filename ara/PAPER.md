---
title: "Heuristic 4-player Commander simulation for Ovika convoke: comparable pods, disclosed abstractions, and a rejected connectivity swap"
authors: [Lewis]
year: 2026
venue: "Local lab notebook (ovika/ REPORT.md + CONTEXT.md, dated 2026-09-03)"
doi: "Not specified in paper"
ara_version: "1.0"
domain: "Magic: The Gathering Commander simulation / experimental deck iteration"
keywords:
  - Commander
  - Ovika Enigma Goliath
  - rules engine
  - pod benchmark
  - synergy graph
  - heuristic baseline
  - GPU hand Monte Carlo
claims_summary:
  - "On the locked 36-seed, turn-cap-14, 4-deck schedule, live deck v12.1 recorded 9/36 Ovika wins (25%) at $533.00."
  - "Same-engine A/B of v12.2 (pinger/connectivity swap) recorded 8/36 Ovika wins (22%) and was not adopted."
  - "A pod share is a product of list × Oracle coverage × heuristic AI × opponents × seat/order × turn cap × engine version, not a real Magic win rate."
abstract: "This artifact compiles the Ovika, Enigma Goliath (UR) Commander lab: a CR-structured 4-player Python engine with MTGJSON Oracle text, a GPU hand-Monte-Carlo layer, and a 36-seed confirmation pod against fixed EDHREC Nekusar/Kuja/Wandering Minstrel lists. Adopted build v12.1 matches the archived v11 storm list at 9/36 on that schedule with better GPU opener stats, under a $1,000 budget ($533.00). Variant v12.2 raised synergy-graph ping density but lost 9/36 → 8/36 and is archived. Engine work in the same window routed damage through Game.deal_damage and treated no-op actions as CR 117 passes after 8-minute priority spins on large boards. Claims are scoped as heuristic baselines, not rules-complete Magic."
---

# Heuristic 4-player Commander simulation for Ovika convoke

## Overview

The `ovika/` tree is a from-scratch Commander rules engine plus one iterated convoke deck. Full games are sequential CPU multiprocessing; CUDA (RTX-4060 Laptop, 8 GB) is used only for parallel hand Monte Carlo and related statistics. Card text comes from local MTGJSON `AtomicCards.json.gz`. Unsupported effects log `(simplified ...)` rather than silent invention.

This ARA binds the 2026-09-03 final report, working CONTEXT, result CSVs, engine README, and the v4 deckbuilding skill into a traversable package: falsifiable claims, directional experiment plans, exact evidence tables, and the exploration DAG that includes the rejected v12.2 branch.

**Confidence label for the live deck:** `heuristic baseline` (skill ladder). Material cards are hooked or generic-patterned; AI is heuristic; turn cap 14; opponents locked. Do not quote these numbers as a real Magic win rate.

## Layer Index

### Cognitive Layer (`/logic`)

| File | Description |
|------|-------------|
| [problem.md](logic/problem.md) | Observations → gaps → key insight |
| [claims.md](logic/claims.md) | 6 falsifiable claims (C01–C06) |
| [concepts.md](logic/concepts.md) | Core terms (pod, heuristic baseline, slots, etc.) |
| [experiments.md](logic/experiments.md) | 5 declarative verification plans (E01–E05) |
| [related_work.md](logic/related_work.md) | CR, MTGJSON, EDHREC, Scryfall, graph modularity |
| [solution/architecture.md](logic/solution/architecture.md) | Engine + deck + stats + graph components |
| [solution/algorithm.md](logic/solution/algorithm.md) | Turn loop, retain rule, hand MC |
| [solution/constraints.md](logic/solution/constraints.md) | Abstractions and comparison bans |
| [solution/heuristics.md](logic/solution/heuristics.md) | Hard-won implementation tricks (H01–H06) |

### Physical Layer (`/src`)

| File | Description | Claims |
|------|-------------|--------|
| [configs/training.md](src/configs/training.md) | Pod schedule, workers, turn cap, hand-MC N | C01, C02, C03 |
| [configs/model.md](src/configs/model.md) | Deck shape, engine family, graph stats | C01, C05 |
| [execution/comparable_pod.py](src/execution/comparable_pod.py) | Same-engine 1-for-1 retain protocol | C02, C05 |
| [environment.md](src/environment.md) | Interpreters, CUDA, seeds | C01–C04 |

### Exploration Graph (`/trace`)

| File | Description |
|------|-------------|
| [exploration_tree.yaml](trace/exploration_tree.yaml) | 12-node research DAG including v12.0 dead end and v12.2 rejection |

### Evidence (`/evidence`)

| File | Description |
|------|-------------|
| [README.md](evidence/README.md) | Index of source tables transcribed from REPORT.md / CONTEXT.md / CSVs |

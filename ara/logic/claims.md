# Claims

## C01: Locked-schedule v12.1 Ovika share
- **Statement**: Under seeds 1–36, turn cap 14, 4 CPU workers, and the three locked EDHREC opponent decks, live list `deck_v12.py` (v12.1 FINAL, $533.00) recorded 9 Ovika wins out of 36 games (25%).
- **Status**: supported
- **Falsification criteria**: Re-run `ovika/pod_v12.py --seeds 1-36 --turns 14 --workers 4` on the same engine and deck file; if Ovika winner_deck count ≠ 9, this claim is false for that engine stamp (baselines must be re-run after engine changes).
- **Proof**: [E01]
- **Evidence basis**: REPORT.md §1 table column “v12.1 FINAL”; CONTEXT.md “9/36 (25%)”; CSV `results_pod_v12.csv` Ovika winner rows.
- **Interpretation**: This is a heuristic-baseline pod share, not a real Magic win rate (see C04).
- **Dependencies**: C04
- **Tags**: pod, v12.1, confirmation, heuristic-baseline

## C02: v12.2 same-engine swap did not improve Ovika wins
- **Statement**: On the same 36-seed, T14, 4-deck schedule, v12.2 (Guttersnipe, Coruscation Mage, Seething Song in; Will-Forged Golem, Thunderhead Squadron, Interdisciplinary Mascot out) recorded 8/36 Ovika wins (22%) at $546.04 and was not adopted.
- **Status**: supported
- **Falsification criteria**: Re-run `pod_v12.py --deck` pointing at the archived v12.2 module on the same engine; if Ovika wins ≥ v12.1 wins on that stamp, the “no improvement / not adopted” historical decision would need revision (the archived CSV would still stand as a past measurement).
- **Proof**: [E02]
- **Evidence basis**: REPORT.md §1 v12.2 column; CONTEXT.md “8/36 (22%), not adopted”; `results_deck_v12_2.csv`.
- **Interpretation**: Static synergy/ping density was not a sufficient retain signal for this swap.
- **Dependencies**: C01, C05
- **Tags**: ablation, rejected-variant, v12.2

## C03: GPU hand MC opener metrics favor v12.1 over archived v11
- **Statement**: On 200k CUDA hand Monte Carlo, v12.1 reported keep rate 82.1%, P(2–5 lands opener) 0.640, mana screw rate 0.359, mean lands by turn 5 3.39, versus v11 79.0%, 0.592, 0.406, 3.16.
- **Status**: supported
- **Falsification criteria**: Re-run `ovika/_handmc_v12.py` (200k) on the live deck and the archived v11 list with the same shuffle model; if the four metrics do not preserve the reported direction (v12.1 better keep, higher P(2–5), lower screw, higher T5 lands), the claim is false.
- **Proof**: [E03]
- **Evidence basis**: REPORT.md §1 GPU hand MC rows only. No v12.2 hand-MC numbers are in source (“—”).
- **Interpretation**: Better opening-hand statistics can coexist with an unchanged 9/36 pod share versus an old-engine v11 archive (do not treat that pod equality as same-engine A/B).
- **Dependencies**: none
- **Tags**: hand-mc, gpu, openers

## C04: Pod share is a composite measurement, not a real Magic win rate
- **Statement**: A quoted Ovika pod fraction is the product of a legal 100-card list, Oracle-backed defs, implemented effect coverage, shared heuristic AI, fixed 3-opponent pod, seat/turn order, turn cap, and engine version; the lab forbids labeling it a real MTG win rate or fully rules-accurate Magic.
- **Status**: supported
- **Falsification criteria**: Exhibit a documented run where unsupported=0 for every material effect and decision path, verifier 21/21, and the report still calls the number a real Magic win rate without those disclosures — or, conversely, a source that claims rules-complete while listing remaining simplifications. The skill’s `rules-complete` ladder would have to be met and used honestly.
- **Proof**: [E01, E04]
- **Evidence basis**: Skill v4 “What is actually being measured”; REPORT.md Known approximations; engine README Reliability caveats; 11/36 cap no-winners in the v12.1 CSV summary.
- **Interpretation**: Website or agent copy that says “25% win rate” without the factor list is a claims violation, not an extra experiment.
- **Dependencies**: C01
- **Tags**: epistemology, labeling, product-safety

## C05: Synergy-graph connectivity is not a sufficient retain criterion
- **Statement**: A candidate that improves static pairwise connectivity (or ping-engine density) can still record fewer locked-schedule Ovika wins than the parent list; measured pods override graph-only swaps.
- **Status**: supported
- **Falsification criteria**: On a same-engine locked schedule, adopt a graph-only swap that strictly increases Ovika wins versus parent (predeclared secondary metrics and Wilson interval disclosed). Until then, v12.2 is a counterexample to “higher connectivity ⇒ keep.”
- **Proof**: [E02, E05]
- **Evidence basis**: CONTEXT/REPORT v12.2 8/36 vs v12.1 9/36; graph audit 72 nodes / 712 tight edges, 1 component, 3 communities, no node degree < 3, deg-3 tail = 7 draw/velocity spells.
- **Interpretation**: Draw/velocity cards can be structurally thin yet carry dynamic consistency value.
- **Dependencies**: C02
- **Tags**: graph, retain-rule, dead-end

## C06: No-op actions must count as passes or large-board games hang
- **Statement**: If `priority_loop` re-grants priority when `action.execute()` changes no game state, games on large boards can spin for minutes (observed: 8+ min on a 68-permanent board during v12.2 work); treating no-ops as CR 117 passes made the confirmation schedule runnable.
- **Status**: supported
- **Falsification criteria**: Remove no-op detection, replay a documented large-board seed, and observe completion without spinning to the 5000-guard within a comparable wall-clock bound — or show the hang was caused by a different loop. Source does not provide a timed before/after table beyond the 8-min qualitative report.
- **Proof**: [E02]
- **Evidence basis**: CONTEXT.md “8-min hang”; REPORT.md Reliability item 2; simulator skill history of silent cast failures.
- **Interpretation**: This is an engine-correctness/liveness fix, not a claim that v12.2’s 8/36 is caused by the hang (the hang blocked completing games; the CSV is the completed schedule after the fix window).
- **Dependencies**: none
- **Tags**: priority, CR-117, liveness

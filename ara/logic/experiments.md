# Experiments

Plans are directional. Exact numerators, prices, and MC rates live in `evidence/`.

## E01: Locked 36-seed confirmation pod (v12.1 live)
- **Verifies**: C01, C04
- **Setup**:
  - Model: `ovika/deck_v12.py` vs `decks/edhrec_{nekusar,kuja,minstrel}.py`
  - Hardware: 4 CPU workers (do not exceed 4–5 on 4 cores); GPU unused for full games
  - Dataset: seeds 1–36, turn cap 14
  - System: deterministic `Game.__init__` reseeds `random`; engine stamp locked
- **Procedure**:
  1. Confirm verifier green if engine files changed (see E04).
  2. Run `pod_v12.py --seeds 1-36 --turns 14 --workers 4`.
  3. Write winner deck/seat/turn per seed to CSV.
  4. Count Ovika wins and no-winner (cap) games; disclose perf guards.
- **Metrics**: Ovika win count / 36; opponent win counts; cap no-winner count; win-turn distribution for Ovika wins
- **Expected outcome**:
  - Candidate share is well-defined only on this factor list
  - Cap no-winners remain a large residual (do not relabel them as losses to the deck’s “inability to win forever”)
- **Baselines**: Archived v11 storm 9/36 is an old-engine reference only, not a same-stamp A/B
- **Dependencies**: E04 when engine changed

## E02: Same-engine A/B of v12.2 pinger variant
- **Verifies**: C02, C05, C06
- **Setup**:
  - Model: v12.2 module via `pod_v12.py --deck` (adds Guttersnipe, Coruscation Mage, Seething Song; cuts three 6–8 MV convoke creatures)
  - Hardware: same as E01
  - Dataset: same seeds 1–36, T14
  - System: same engine stamp as the v12.1 confirmation used for retain
- **Procedure**:
  1. Keep opponents, seeds, workers, cap, AI version identical to E01.
  2. Run the pod; auto-named CSV (`results_deck_v12_2.csv` in the lab).
  3. Retain only if Ovika wins rise or a predeclared secondary metric improves with overlapping interval disclosed.
- **Metrics**: Ovika win count vs E01 parent; total price; qualitative liveness (no multi-minute priority spin)
- **Expected outcome**:
  - Graph/ping-motivated list does not automatically beat parent wins
  - Large-board games complete only if no-op passes remain in `priority_loop`
- **Baselines**: v12.1 live list on the same engine
- **Dependencies**: E01

## E03: GPU opening-hand Monte Carlo (200k)
- **Verifies**: C03
- **Setup**:
  - Model: live v12.1 list vs archived v11 list as reported
  - Hardware: CUDA venv, RTX-4060 Laptop 8 GB
  - Dataset: 200k hands, without-replacement shuffle model
  - System: `ovika/_handmc_v12.py` / `batch/gpu_sim.py::hand_mc`
- **Procedure**:
  1. Run 200k hands on each list.
  2. Record keep rate, P(2–5 lands), screw rate, mean lands by turn 5.
- **Metrics**: keep rate; P(2–5); screw rate; mean lands by T5
- **Expected outcome**:
  - Opener metrics can improve without implying a higher pod share on a T14 FFA
  - Land-curve numbers are exact for the shuffle model, not for full-game mana
- **Baselines**: v11 hand-MC column in REPORT.md
- **Dependencies**: none

## E04: Rules-conformance suite (21 checks)
- **Verifies**: C04
- **Setup**:
  - Model: `ovika/scripts/verify_phases.py`
  - Hardware: CPU python
  - Dataset: scripted fixtures (phase order, stack, tax, SBA, London mulligan, cleanup)
  - System: must stay 21/21 after engine edits
- **Procedure**:
  1. Run the suite after any `engine/` change.
  2. Fail the change if any check is red.
- **Metrics**: pass count / 21
- **Expected outcome**:
  - Sequencing/priority/SBA/mulligan invariants hold
  - Passing does not imply full-card coverage or optimal AI
- **Baselines**: none (regression suite)
- **Dependencies**: none

## E05: Synergy-graph audit of v12.1
- **Verifies**: C05
- **Setup**:
  - Model: `ovika/graph_analysis.py` over non-land cards + commander hub
  - Hardware: `.venv` with networkx + matplotlib
  - Dataset: live v12.1 names
  - System: documented pair rules only (no universal edges)
- **Procedure**:
  1. Build undirected graph; write `graph_deck_v12.json` / `.png`.
  2. Report nodes, edges, components, greedy-modularity communities, degree < 3 set, weakest tail.
  3. Optionally score UR replacements by edges added; do not adopt without E02-style pod.
- **Metrics**: |V|, |E|, component count, community count, size of deg < 3 set, identity of deg-3 tail
- **Expected outcome**:
  - Graph may look healthy (single component, no deg < 3) while a connectivity-increasing swap still loses the pod
  - Deg-3 tail may be draw/velocity rather than “useless”
- **Baselines**: none
- **Dependencies**: none

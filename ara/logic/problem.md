# Problem Specification

## Observations

### O1: A 36-game FFA share is easy to misread as deck strength
- **Statement**: On seeds 1–36, turn cap 14, four decks, live v12.1 recorded Ovika 9/36 (25%), Nekusar 6/36 (17%), Kuja 7/36 (19%), Minstrel 3/36 (8%), 11 no-winner (31%) (`REPORT.md` §1; `results_pod_v12.csv`).
- **Evidence**: REPORT.md Result summary table and pod opponent paragraph; CSV winner column.
- **Implication**: Cap-losses (31%) and seat/turn order are first-class outcomes. Calling 25% a “win rate at Magic” overclaims the measurement.

### O2: Engine version confounds list comparison
- **Statement**: Archived v11 storm also shows 9/36 (25%) but CONTEXT.md labels those “old-engine numbers.” Simulator skill forbids comparing results across engine versions.
- **Evidence**: CONTEXT.md Deck history; `mtg-commander-simulator-v1` “Never compare results across engine versions.”
- **Implication**: Equal numerators are not a same-experiment A/B unless the engine, AI, opponents, seeds, and cap are locked.

### O3: Graph connectivity and pod wins can disagree
- **Statement**: v12.2 added Guttersnipe / Coruscation Mage / Seething Song and cut three slow 6–8 MV convoke creatures; measured 8/36 (22%) at $546.04 and was not adopted. Skill text: graph “outliers” were the velocity layer that made v12.1 consistent.
- **Evidence**: REPORT.md §1; CONTEXT.md v12.2 bullet; results_deck_v12_2.csv.
- **Implication**: Static pairwise synergy is a hypothesis generator, not a retain criterion.

### O4: Large boards can livelock the priority loop
- **Statement**: Silent cast/payment failures used to re-grant priority until a 5000-action guard; v12.2 exposed ~8-minute hangs on a 68-permanent board.
- **Evidence**: CONTEXT.md Engine reliability; REPORT.md Reliability item 2; simulator skill Guardrails.
- **Implication**: Throughput and completeness of the pod schedule depend on treating no-op actions as passes (CR 117).

### O5: GPU opener stats can move while pod share stays flat
- **Statement**: GPU hand MC (200k, CUDA): v11 keep 79.0%, P(2–5 lands) 0.592, screw 0.406, lands by T5 mean 3.16 vs v12.1 keep 82.1%, P(2–5) 0.640, screw 0.359, lands by T5 3.39. Pod Ovika wins both 9/36 vs their respective (not necessarily same-engine) archives.
- **Evidence**: REPORT.md §1 table.
- **Implication**: Hand quality is a separate measurement from FFA elimination under a 14-turn cap.

### O6: Productization pressure collides with lab metrics
- **Statement**: ISSUES-poor-deck-performance.md (2026-09-13) records that retaining cards only if they win seeds 1–36 vs Nekusar/Kuja/Minstrel selects for that pod, AI, and cap — not a customer Golgari $150 theme.
- **Evidence**: ISSUES-poor-deck-performance.md A7, A5 (v12.2 25% → 22%).
- **Implication**: Lab retain rules must not be silently reused as a generator quality metric.

## Gaps

### G1: No implicit “real win rate”
- **Statement**: Reports historically risk quoting pod fractions without the factor list (coverage × AI × opponents × cap × engine).
- **Caused by**: O1, O2
- **Existing attempts**: Skill prohibited-claims list; CLAIMS.md for the website.
- **Why they fail**: Agents still cargo-cult `pod_v12.py` numbers into unrelated commanders unless the measurement definition is in a structured artifact.

### G2: Graph-only optimization
- **Statement**: Synergy-graph thin-node swaps can cut velocity cards that look poorly connected.
- **Caused by**: O3, O6
- **Existing attempts**: Graph audit with pair rules; skill caveat to trust the pod.
- **Why they fail**: Without a bound claim, a later agent will “improve” v12.1 the same way v12.2 did.

### G3: Incomplete Oracle coverage vs. claimed rules-completeness
- **Statement**: Engine is rules-structured for implemented cards; generic layer and `(simplified ...)` logs remain.
- **Caused by**: O4 (complexity of full boards), engine README caveats
- **Existing attempts**: Coverage gate in skill v4.1; verifier 21/21 for core sequencing
- **Why they fail**: 21/21 phase suite does not imply every deck card is modeled.

## Key Insight
- **Insight**: Treat every quoted number as an experiment object with a locked factor list; retain list changes only on same-engine measured pods; use graphs and hand-MC as auxiliary, labeled measurements.
- **Derived from**: O1–O5
- **Enables**: Falsifiable retain/reject of candidates (v12.2), honest product copy, and engine invariants that keep the schedule runnable.

## Assumptions
- A1: Opponent modules `edhrec_nekusar.py`, `edhrec_kuja.py`, `edhrec_minstrel.py` stay fixed for Ovika A/B.
- A2: Candidate remains in the seats encoded in the CSVs for those runs (not a seat-rotated confirmation unless labeled).
- A3: Turn cap 14 measures fast decks; cap-losses are not “cannot ever win.”
- A4: AI is a versioned heuristic pilot, not optimal play.
- A5: Prices are Scryfall cheapest non-foil USD as of the 2026-09-03 price pass (`$533.00` / `$546.04`).

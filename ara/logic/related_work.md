# Related Work

Works with a technical delta relative to this lab get full RW blocks. Remaining sources from the notebooks are listed briefly so the neighborhood is preserved.

## RW01: Wizards of the Coast Comprehensive Rules (effective 2025-02-07)
- **DOI**: Not specified in paper (local `ovika/rulebook/CR.txt`, 1,414 numbered rules, 939 KB)
- **Type**: imports
- **Delta**:
  - What changed: Engine implements CR 117, 405, 500–514, 603, 608, 704, 800/802/806, 903 rather than a simplified “phases” toy.
  - Why: Truthful sequencing is the difference between a heuristic combat script and a disclosed rules engine.
- **Claims affected**: C04, C06
- **Adopted elements**: Phase/step order, priority, SBA, London mulligan, commander tax/damage

## RW02: MTGJSON AtomicCards
- **DOI**: Not specified in paper (local `AtomicCards.json.gz`)
- **Type**: imports
- **Delta**:
  - What changed: Card properties are required from Oracle JSON; no name-inferred mana costs or identity.
  - Why: Fabricated Oracle text was a prohibited failure mode in the skill.
- **Claims affected**: C01, C04
- **Adopted elements**: `Oracle.require()`, MDFC front-face keys

## RW03: Scryfall pricing API
- **DOI**: Not specified in paper
- **Type**: imports
- **Delta**:
  - What changed: Cheapest non-foil USD with `User-Agent` + `Accept: application/json` (400s otherwise).
  - Why: Budget checks after every list change ($533.00 / $546.04).
- **Claims affected**: C01, C02
- **Adopted elements**: `card_prices.json` cache + fetch-on-miss

## RW04: EDHREC / Moxfield / Archidekt opponent lists
- **DOI**: Not specified in paper
- **Type**: baseline
- **Delta**:
  - What changed: Three converted 99s (Nekusar, Kuja, Wandering Minstrel) as a locked threat model.
  - Why: A/B needs frozen opponents; not claimed as the competitive meta.
- **Claims affected**: C01, C02, C04
- **Adopted elements**: `ovika/decks/edhrec_*.py` (URLs in engine README)

## RW05: Wilson score interval (GPU `aggregate_gpu`)
- **DOI**: Not specified in paper
- **Type**: extends
- **Delta**:
  - What changed: Skill v4.1 requires Wilson 95% CI on confirmation (9/36 has a wide interval).
  - Why: Point estimates overstate precision.
- **Claims affected**: C01, C04
- **Adopted elements**: Tensor CI in `batch/gpu_sim.py`; **interval endpoints are not in REPORT.md 2026-09-03 table**

## RW06: NetworkX greedy modularity communities
- **DOI**: Not specified in paper
- **Type**: baseline
- **Delta**:
  - What changed: Graph audit reports 3 communities on v12.1; still insufficient to retain v12.2.
  - Why: Static community structure is a lens, not a pod.
- **Claims affected**: C05
- **Adopted elements**: `graph_analysis.py` pipeline

## Additional sources (brief)
- **London mulligan (CR 103.5)** — imported by verifier check 5.
- **CR 614 replacement effects** — amplifiers on the unified damage path (H02).
- **edh-combos.com combo 6575-6617** — Terra report only; out of scope for Ovika claims.
- **ISSUES-poor-deck-performance.md (2026-09-13)** — product/generator gap analysis; bounds using this lab as a website quality metric (G1, O6).

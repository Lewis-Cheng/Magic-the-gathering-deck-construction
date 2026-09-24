# Product claims policy (E1)

Generator output is a **suggested Commander list**, not a match result.

## Required on every deck JSON

- `confidence` is always present.
- Website generate uses `confidence: "generator-only"`.
- Optional sim (V1 stub) uses `confidence: "coverage-blocked"` and `coverage.not_probed: true`.
- Never emit a naked `win_rate` field on generate. A win fraction is allowed only if `sim.enabled` is true **and** the label is `heuristic-baseline` with coverage, seeds, and turn cap. V1 does not run that path.

## Banned marketing phrases

Do not use these in UI copy, API `notes`, or README:

- “real win rate”
- “real Magic win rate”
- “fully rules accurate”
- “rules-complete” (unless the lab verifier and full coverage actually apply — they do not on this product)
- “cEDH proven”
- implying checkout lists were selected by `pod_v12` / Nekusar seeds

## Allowed phrases

- “Legal, on-theme, on-budget suggestion”
- “Not a real Magic win rate. Engine coverage is incomplete.”
- “Prices and ban list are dated snapshots”
- “Simulation is optional / not offered at checkout (V1)”

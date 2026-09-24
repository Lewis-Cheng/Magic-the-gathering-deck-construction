# Service shape (E2, E6)

Pinned product Python: `C:\Users\lewis\Documents\ChatGPT\mtg\.venv\Scripts\python.exe`  
(Not Codex runtime PATH. Generate does not require CUDA.)

## Generate (checkout path)

- **Sync HTTP** `POST /v1/decks` on CPU.
- Pipeline: intake → Oracle.require → recipe → lands → index search → tagger → budget solver → fill.
- **Zero GPU.** **Zero 36-seed pods.** Do not import or call `ovika/pod_v12.py` to keep/reject cards.
- Target: p95 generate under a few seconds without network price fetch (local `card_prices.json` only).
- Website V1 stays **offline-local** for prices unless `GENERATOR_SCRYFALL=1` is set.

## Simulation (not checkout)

- Default `sim.enabled = false`.
- If a client sets `sim.enabled`, V1 returns `{ "confidence": "coverage-blocked", "detail": "V1 does not run pods at checkout" }` and does not quote a win rate.
- Future: async job queue. Worker caps from the simulator skill (≤4–5 pod workers) apply **only** on that queue, never on generate.

## Do not use

- Laptop CUDA as a product dependency
- Codex `<cpu-py>` PATH as the documented service runtime
- `Pool(...)` (executes Python deck tuples; defaults commander to Ovika)

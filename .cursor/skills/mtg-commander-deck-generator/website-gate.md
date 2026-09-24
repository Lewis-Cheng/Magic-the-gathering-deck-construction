# Website construction gate

Do **not** build FastAPI, Vite/React, or checkout UX until every box is true.

This file is the definition of “skill set completely ready.”

## Skill pack present

- [x] `.cursor/skills/mtg-commander-deck-generator/SKILL.md` has YAML `name` + `description`, pipeline, non-negotiables.
- [x] `schemas.md` intake + output (no `win_rate`).
- [x] `recipes.md` has quotas for v1 themes and land fill order.
- [x] `issues.md` maps all 43 IDs (A1–A7, B1–B8, C1–C15, D1–D7, E1–E6) to a rule.
- [x] `examples.md` has a pass example and a fail-closed example.
- [x] Lab skills point here for **customer lists** and still own engine work.

## Agent can execute without a site

- [x] Given `{commander, theme, budget_usd, power_level}`, an agent following SKILL.md can emit deck JSON + MTGO text.
- [x] Agent knows to use `Oracle.require` and local prices, fail on missing intake, fail on unknown price-as-zero, fail on empty retrieval.
- [x] Agent will not open `deck_v12.py` as a template or call `pod_v12.py` to choose cards.

## Product claims locked

- [x] CLAIMS.md bans “real win rate” / “fully rules accurate” / “cEDH proven.”
- [x] SERVICE.md: generate is CPU sync; sim is not checkout.
- [x] LICENSING.md: no bulk images; dated ban/price stamps.

## Known remaining (allowed)

These do **not** block declaring the **skill** ready. They block calling the **website** done:

- Engine coverage / AI / pods (C1–C15) stay lab + `coverage-blocked`.
- D1 remains partial (no per-commander engine module required to sell a list).
- Python `generator/` package may exist as a draft; the skill is the source of truth until tests match it.

## When all skill boxes are checked

Then, and only then: implement `POST /v1/decks`, `POST /v1/swap`, `GET /v1/commanders`, and a React form with Generate **disabled** until required fields, no default $1000, names+slots only, sim disabled or stubbed.

**Status 2026-09-13:** skill set ready. Website not started under this gate.

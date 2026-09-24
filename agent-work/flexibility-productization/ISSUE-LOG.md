# ISSUE-LOG (generator V1)

Ritual: after each issue ID closes, acceptance test, then this section (code / skill audit / simulator audit), then tick. Next issue only after that.

Lab skills (pointer only — do not rewrite the Ovika lab):

- `C:\Users\lewis\.codex\skills\mtg-commander-deckbuilding-simulation-v4\SKILL.md`
- `C:\Users\lewis\.codex\skills\mtg-commander-simulator-v1\SKILL.md`

Product skill: `.cursor/skills/mtg-commander-deck-generator/SKILL.md`

Simulator greps: `ovika/pod_v12.py`, `ovika/engine/ai.py`, `ovika/engine/generic.py`, `ovika/engine/oracle.py` (`Pool`, `Oracle.require`).

---

## A6 — Split product vs lab skills

- **Status:** closed
- **Code changed:** pointers at top of both lab skills; this folder’s CLAIMS/SERVICE/LICENSING; `generator/` is the product package (does not open `deck_v12.py` as a template).
- **Skill audit:** Lab skill still describes mutating Ovika / $1000 / pod constructor for **lab** work. One-line product pointer added: customer lists use `generator_deck_skill.md`; do not use `pod_v12` as the constructor. Product skill is the construction path.
- **Simulator audit:** `Oracle.require` unchanged. Generate does not import `Pool` or call `pod_v12` / `ai.py` / `generic.py` for keep/reject.

## E1 — No win-rate marketing

- **Status:** closed
- **Code changed:** `CLAIMS.md`; generate JSON uses `confidence` and omits naked `win_rate`; React copy “Not a real Magic win rate.”
- **Skill audit:** Lab skill still documents pod win rates for research. Product claims file bans those phrases on the website.
- **Simulator audit:** No generate path quotes `pod_v12` win fraction. Sim stub returns `coverage-blocked`.

## E2 — Generate is sync CPU

- **Status:** closed
- **Code changed:** `SERVICE.md`; `generator/api.py` `POST /v1/decks` is in-process CPU; sim is not a pod.
- **Skill audit:** Lab still uses CUDA for hand MC. Product generate documents zero GPU.
- **Simulator audit:** API does not spawn `pod_v12.py`. `Oracle.require` still used for names.

## E3 — Licensing / no bulk images

- **Status:** closed
- **Code changed:** `LICENSING.md`; React shows names + slots, not card scans; dated `ban_list_version` / `prices_as_of`.
- **Skill audit:** Lab uses MTGJSON locally; product does not add Scryfall image shipping.
- **Simulator audit:** Unchanged.

## E6 — Pinned runtime, not Codex PATH

- **Status:** closed
- **Code changed:** `SERVICE.md`, `generator/README.md` pin `.venv\Scripts\python.exe`.
- **Skill audit:** Simulator skill still documents Codex `<cpu-py>` for **lab** pods. Product runbook does not.
- **Simulator audit:** Unchanged.

---

<!-- Phase 1+ sections appended below as issues close -->

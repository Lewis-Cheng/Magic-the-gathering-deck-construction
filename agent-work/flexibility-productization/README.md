# Agent work folder — flexibility & productization

This folder is the dump for the Cursor agent session that turns the
Commander skill + `ovika/` simulator into a **flexible deck generator**
(any commander, theme, and budget) and later a **paid website**.

Do not scatter new notes across `ovika/` or the Codex skill dirs.
Put session artifacts here.

| File | What it is |
|---|---|
| `README.md` | This index |
| `ISSUES-poor-deck-performance.md` | Full issue catalog (why generated decks play poorly) |
| `CHANGELOG.md` | What this agent changed, in order |
| `generator_deck_skill.md` | Pointer to the canonical Cursor skill |
| Canonical skill | `.cursor/skills/mtg-commander-deck-generator/` (`SKILL.md` + schemas/recipes/issues/examples/website-gate) |
| `CLAIMS.md` | Banned marketing phrases; no naked `win_rate` |
| `SERVICE.md` | Sync CPU generate; sim is not checkout |
| `LICENSING.md` | MTGJSON/Scryfall; no bulk card images in V1 |
| `ISSUE-LOG.md` | Per-issue close ritual (skill + simulator audit) |

Related (outside this folder):

- Product skill: `C:\Users\lewis\Documents\ChatGPT\mtg\.cursor\skills\mtg-commander-deck-generator\SKILL.md`
- Lab deckbuilding: `C:\Users\lewis\.codex\skills\mtg-commander-deckbuilding-simulation-v4\SKILL.md`
- Lab simulator: `C:\Users\lewis\.codex\skills\mtg-commander-simulator-v1\SKILL.md`
- Engine: `C:\Users\lewis\Documents\ChatGPT\mtg\ovika\`

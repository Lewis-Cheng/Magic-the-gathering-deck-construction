# Changelog (this agent)

## 2026-09-13

- Added **Improvement protocol (v4.1)** to
  `mtg-commander-deckbuilding-simulation-v4/SKILL.md`
  (commander-agnostic onboarding, coverage gate, slot map, failure
  taxonomy, Wilson CI, seat rotation, confidence ladder).
- Created this folder as the persistent store for subsequent agent work.
- Wrote `ISSUES-poor-deck-performance.md`: 43 issues that make generated
  decks weak or that block theme / commander / price flexibility and a
  paid site.
- Canvas: `edh-generator-failure-audit.canvas.tsx` (open beside chat).
- Wrote `generator_deck_skill.md`: product generator skill (JSON in/out,
  retrieval, recipes, budget solver) and a 29-step plan that maps each
  of the 43 issues to an acceptance test.
- Replaced that spec with a Cursor skill pack at
  `.cursor/skills/mtg-commander-deck-generator/` (procedure + recipes +
  43-issue rules + website gate). Website construction stays blocked
  until the gate is used; skill set is marked ready.
- Locked optimization policy into the generator skill: any commander,
  coverage-blocked when the win condition is unimplemented, both graph
  degree under 3 and at least 10/36, deadlock keeps the card (graph relaxes).
- Collection constraint: first draft uses only the uploaded card file;
  then ask how many new cards may be added before any shop card or sim loop.

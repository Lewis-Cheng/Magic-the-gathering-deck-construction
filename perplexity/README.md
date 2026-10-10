# Perplexity Agent API bundle (Deep Research only)

This folder is a custom skill for the **Perplexity Agent API** with the **`medium` preset** (multi-step web research). It is **not** for Perplexity Computer.

Do **not** upload this zip to Computer Skills. Do **not** start a Computer task with this skill. Computer has a different sandbox, different upload path, and this workflow is written for `POST /v1/agent` with `preset: "medium"`.

## What this skill does

Research-layer Commander construction: intake, Scryfall / Commander ban list / prices, Lantern-style neighbor search, a legal 100, citations.

It does **not** run this repo’s Python simulator, graph, or optimize loop. Those stay in Cursor. Output `confidence` is always `research-only`. Never report a heuristic win rate.

## Build the zip

From the repository root (PowerShell):

```powershell
Compress-Archive -Path .\perplexity\mtg-commander-deck-generator -DestinationPath .\perplexity\mtg-commander-deck-generator.zip -Force
```

The archive must contain exactly one `SKILL.md`. Files live under one top-level folder named `mtg-commander-deck-generator` (same as the skill `name`).

## Upload and call (Agent API)

```bash
curl https://api.perplexity.ai/v1/skills \
  -H "Authorization: Bearer $PERPLEXITY_API_KEY" \
  -F "file=@perplexity/mtg-commander-deck-generator.zip;type=application/zip"
```

Save the returned `skill_id` (`skill_...`). Then:

```json
{
  "preset": "medium",
  "max_steps": 32,
  "background": true,
  "skills": [{ "type": "custom", "id": "skill_REPLACE", "version": "latest" }],
  "input": "Generate a Commander 99. I will answer intake in this thread. Do not use Perplexity Computer."
}
```

`max_steps` must be large enough for `load_skill` plus research. A one-step request can load the skill and never draft.

## Cursor vs this bundle

| | Cursor skill | This bundle |
|---|---|---|
| Host | Local agent + `generator/` + `simulator/` | Agent API `medium` |
| Oracle | AtomicCards | Scryfall via `web_search` |
| Card search | `generator/atlas.py` | Lantern / Endless Atlas URLs, then citations |
| Win rate | `heuristic-baseline` after coverage | Forbidden |
| Computer | n/a | Forbidden |

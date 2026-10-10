# Magic: the Gathering deck construction

Commander deck construction for any legal commander. The product path is the skill in `.cursor/skills/mtg-commander-deck-generator/`. It asks for the commander, how the deck wins, a budget, and a power level before it drafts. A collection file, when given, is used first. New cards are added only after you say how many are allowed.

## What is here

- `.cursor/skills/mtg-commander-deck-generator/` — intake, recipes, and the construction rules (Cursor).
- `perplexity/mtg-commander-deck-generator/` — the same intake and Lantern rules as an Agent API Deep Research skill (`preset: medium` only). **Not for Perplexity Computer.** See `perplexity/README.md`.
- `generator/` — legal 99 construction, prices, and Lantern-map card search (`generator/atlas.py`).
- `simulator/` — heuristic four-player games, the functional synergy graph, and the optimize loop.

Card names are resolved from a local AtomicCards file. Missing prices stay missing. They are never treated as $0.

## Synergy graph

`simulator/graph.py` connects two nonland cards only when they share a function read from Oracle text (tokens, stax, ramp, removal, and similar). Type labels such as creature, instant, or enchantment do not create a link by themselves. A second coplay score records when one card's text names another. That score does not change degree and does not drive swaps.

A card with functional degree under 3 is thin. The optimize loop swaps thin cards before it simulates.

## Simulation

The pod is four heuristic bots. It is not a real Magic win rate. The default bar is at least 10 wins in 36 games, seeds 1–36, 18-turn cap.

```text
python simulator/graph.py simulator/decks/DECK.py
python simulator/pod.py --deck simulator/decks/DECK.py --seeds 1-36 --turns 18 --workers 6
python simulator/optimize.py --deck simulator/decks/DECK.py --seeds 1-36 --turns 18 --target 0.25 --workers 6
```

## Lantern search

New-card search walks nearest neighbors on the Endless Atlas Deckmates map shipped in `generator/data/atlas_map.json` (the same positions as [Lantern](https://stoken.games/stack/lantern/lantern.html)). If that neighborhood has no card for the slot, search moves to the What-it-does plane, then Combos. Scryfall is used for prices, not for picking names.

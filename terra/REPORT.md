# Terra, Magical Adept // Esper Terra - Combo Build Report

Engine: terra/engine (forked from Ovika rules engine, 2026-09-05). Verifier: 21/21.
Label: **heuristic baseline** (all material cards modeled; the Folly loop is a
bounded perf-guard abstraction, disclosed in logs as `(simplified ...)`).

## Deck
- Commander: Terra, Magical Adept // Esper Terra
- 99 main + commander = 100 legal cards, singleton, WUBRG identity, all names verified in AtomicCards.
- Total price (Scryfall cheapest nonfoil): **$2,159.17**, no missing prices.
- Files: terra/decklist_terra_mtgo.txt, terra/decklist_terra.md

## Strategy
Esper Terra + The Apprentice's Folly / Mirrormade copy loop (source:
edh-combos.com/combo/6575-6617). The engine models the loop as a bounded burst of
24 hasty 6/6 flying Esper Terra Reflections that spread for a table kill. The 4
existing tutors (Enlightened, Idyllic, Demonic Counsel, Entomb) fetch the combo
pieces; no tutors were added. Moonmist gives a 2-mana transform; Delighted
Halfling fixes R/G and makes the commander uncounterable.

## Changes vs submitted list
- + Rhystic Study, Arid Mesa (legality fill for duplicate Offer/Counterspell)
- + Delighted Halfling, Moonmist (from sideboard -> main)
- + Estrid's Invocation (enabler redundancy)
- + Ponder, Preordain, Brainstorm (card selection, not tutors)
- - Summon: Leviathan (bounces your own Terra), Anger (haste off-plan)
- - The Eldest Reborn (slow), Dauthi Voidwalker, Victor, Summon: Titan (off-plan)
- - Lumbering Falls -> Misty Rainforest; one Island -> one Forest; one Island -> one Mountain

## Pod results (36 seeds, 4 workers, turn cap 14)
| Deck | Wins | Rate |
|---|---|---|
| terra deck | 14 | 39% |
| kuja deck | 15 | 42% |
| nekusar deck | 4 | 11% |
| minstrel deck | 0 | 0% |
| no winner by cap | 3 | 8% |

Terra win turns (wins only): 4,5,5,6,6,7,7,8,8,9,9,11,13 (mean ~7.5).

## Diagnostic failure taxonomy (seeds 1-10)
- 4 wins, 0 mana-screw in the winning games.
- Primary loss causes: opponent race (Nekusar/Kuja lethal turn 8-13), commander
  removed repeatedly, and occasional R/G color-screw before commander cast.
- Combo fires in the winning seeds (1-3 loops), and loses fire 0 loops.

## Hand Monte Carlo (GPU, 200k hands, cuda)
- opening hand: 2.33 lands, 1.48 ramp, keep rate 92.3%
- P(2-5 lands) 74.1%, screw 25.4%, flood 0.5%
- lands by turn: t1 2.68, t3 3.34, t5 4.00, t7 4.67, t9 5.33

## Synergy graph
- 67 nonland nodes, 324 tight edges. Hub cluster = combo assembly
  (Terra <-> Folly/Mirrormade/Estrid's, tutors, cantrips, protection) plus
  enchantress engine and ramp.
- Thin nodes: interaction (removal/counters) and graveyard value (Reanimate,
  Sevinne's, Six) are structurally thin but add dynamic consistency; not cut.
- PNG/JSON: terra/graph_terra.png, terra/graph_terra.json

## Disclosed simplifications
- Folly/Mirrormade loop bounded to 24 Reflections + 3 loops/game; intermediate
  Folly tokens and enchantress ETB/death triggers folded.
- Ponder/Preordain scry and Brainstorm put-back simplified to draws.
- Moonmist lore counter applied at draw step instead of precombat main.
- Esper Terra token chapter IV mana empties at phase end in engine.

## Retained/rejected
- Retained: combo engine, tutor AI, Trance gating, lethal attack spread, Terra
  land/fetch sequencing, commander protection counters, Moonmist + cantrips.
- Rejected: full v2 bundle (2/10), +Opt/+Consider (12/36 vs 14/36).
- Next: try Copy Enchantment or a second counterspell; tune mulligan keep rule.

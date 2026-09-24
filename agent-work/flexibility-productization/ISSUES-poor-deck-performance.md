# Issues that produce poor deck performance

Date: 2026-09-13
Scope: `mtg-commander-deckbuilding-simulation-v4` + `ovika/` engine
Product target: generate a legal Commander list for **any commander**, **any
theme**, **any total price**, then sell that as a website.

A “poor deck” here means any of: illegal list, wrong theme, over/under
budget, cards that do not function in the engine, cards the AI never
casts, or a measured win rate that does not match how the deck would
play for a human. The current stack is a **lab for one Ovika convoke
list** (and a second Terra family). It is not a generator.

Severity:

- **Blocker** — cannot ship flexible generation; output is systematically wrong
- **High** — often produces a weak or misleading list
- **Medium** — biases results; fix before charging money
- **Product** — not a gameplay bug, but will kill a paid site

---

## A. The skill does not generate decks

These are the root causes of “the model built a bad 99.”

### A1. Blocker — No card retrieval by theme
The skill tells the agent to use Oracle data and then iterate. It does
not give a searchable pool (EDHREC, Scryfall `q=`, tagger, or a local
theme index). The model therefore **recalls cards from training data**.
That produces: outdated reprints, missing new-set staples, color-identity
leaks, and “goodstuff piled onto the commander name” instead of a theme.

### A2. Blocker — No commander → theme → slot recipe
There is no table of: commander identity, default land count, ramp/draw/
interaction quotas, win-condition class (combat, combo, stax, mill, …).
Ovika’s 28 lands / 11 rocks / 12 convoke payoffs is treated as the
shape of Commander. A voltron, lands-matter, or stax commander built
on that template will be a poor deck.

### A3. Blocker — Construction is “edit Ovika / Terra”
Versioned modules (`deck_v12.py`, `deck_terra_v2.py`) plus 1-for-1
swaps assume a **starting list already exists**. Empty-list generation
is not specified. On a website, every new commander would start from
the wrong skeleton.

### A4. High — Intake is a human interview, not parameters
Required intake (commander, budget, theme, opponents) lives in prose.
There is no schema `{commander, theme, budget_usd, power_level,
owned_cards?, proxies?}`. An LLM will fill gaps with Ovika defaults
(UR, $1000, convoke, Nekusar pod).

### A5. High — Synergy graph is a handwritten Ovika overlay
`ovika/graph_analysis.py` pair rules name Ovika, goblin tokens, convoke,
Mana Echoes, Torbran. Replacement search even filters non-UR identity.
A “thin node” swap for any other commander is nonsense and can cut the
velocity layer (already observed: v12.2 connectivity up, wins 25% → 22%).

### A6. High — Two skills, one lab notebook
Deckbuilding v4 still reads as the Ovika 2026-09-03 project. Simulator
v1 maps paths and CUDA python. A generation agent will cargo-cult
`pod_v12.py`, `$1000`, and goblin-convoke cuts into unrelated decks.

### A7. Medium — Optimization loop rewards the lab, not the player
“Retain only if wins improve on seeds 1–36 vs Nekusar/Kuja/Minstrel”
selects for **that pod, that AI, that turn cap**. A paid customer
asked for a fun Golgari graveyard theme at $150. The loop will reject
on-theme cards that lose the Ovika-shaped experiment.

---

## B. Data, legality, and price (bad lists before they even play)

### B1. Blocker — Deck rows are tagged tuples, not Oracle cards
`DECK = [("Sol Ring", 1, "spell", 0, 0, ["ramp", "rock", "+2"]), ...]`.
Mana value, kind, and tags are **author metadata**. The AI and
`sim.py` read tags (`ramp`, `counter`, `convoke`). Oracle `text` is
not the source of role. A generated list that omits tags (or copies
the wrong tags) will mulligan badly, never counter, and never ramp.

### B2. High — No shared legality gate
Terra’s `build_terra.py` checks count, singleton, color identity,
prices. `build_convoke.py` checks names + a hard `$1000` total.
There is no one function that enforces: 100 cards, commander identity
(both faces), format legality, ban list, companion/partner, MDFC face
rules. The skill *says* to audit; the generator can skip it.

### B3. High — Commander ban list is not in code
A website that emits a banned card is a refund. The engine will still
load the name if it is in AtomicCards.

### B4. High — Missing prices become $0
`build_convoke.py`: if Scryfall/local price is missing, add `$0.00`
and still print a total. Budget-capped generation will **prefer
unpriced cards** (they look free). That is the opposite of a shop.

### B5. High — Budget is a single hard cap of $1000
`BUDGET OK if total <= 1000`. No per-card cap, no “$50 precon”, no
currency, no foil/condition, no “use cards I own.” Cheapest non-foil
USD snapshot also ignores availability (reserved list, out of print).

### B6. Medium — Color identity and MDFC traps
Skill already records: Wand of the Worldsoul is white; spell-front
MDFCs resolve as instants in this engine. A flexible generator will
re-hit these constantly without an automated CI + MDFC checker.

### B7. Medium — Duplicate-row / missing-comma loader bugs
A missing trailing comma merges tuples and breaks loading. A generator
that writes Python modules (current format) will ship silent syntax
corruption. Website output should be JSON names, not Python.

### B8. Medium — Graph replacement pool is UR-locked
Replacement candidates with `color_identity - {U, R}` are dropped.
Useless for five-color Terra, mono-green, etc.

---

## C. Engine + AI: why a “correct” list still plays poorly in the loop

If the website uses simulation as quality control, these issues make
**good human decks look bad** and **engine-friendly piles look good**.
The model will then generate piles that game the engine.

### C1. Blocker — Coverage is a whitelist, not Magic
`cards.py` is named hooks for the Ovika-era list. `terra.py` is a
second whitelist. `generic.py` regex-handles a subset of tutor /
wipe / damage / draw / token text. Anything else logs
`(simplified spell: Name)` and **does nothing**. The agent learns:
do not put unimplemented theme cards in the 99, even if they are the
theme. Result: generic goodstuff that happens to have hooks.

### C2. Blocker — One AI piloting four commanders
`AI` in `engine/ai.py` is a shared heuristic with **name-keyed
priorities** for Ovika goblins/convoke and Terra enchantress/combo.
Generic fallback is tag-based (`ramp` 8, `wheel` 7, `removal` 4).
Nekusar, Kuja, and Minstrel do not play like themselves. The candidate
is measured against **misplayed opponents** and a pilot that will
ignore a new theme’s lines unless those names are added.

### C3. High — Counters only if tagged `"counter"`
`decide_with_stack` looks at `c.tags`. Oracle text “counter target
spell” is not enough. Generated interaction sits in hand.

### C4. High — Mulligan is not commander-aware
Keep: 2–5 lands plus ramp or CMC≤3. Ovika is 7 mana. A combo
commander that needs a specific seed, or a 2-land fetch-heavy hand,
is kept or dumped with an Ovika-shaped rule. GPU hand MC uses a
similar land model, so “keep rate” can look healthy while the
commander never comes down.

### C5. High — Turn cap 14
Confirmation uses `--turns 14`. Fast combo/convoke can finish.
Control, stax, and many themes cannot. The optimizer will cut
slow theme cards to chase cap-wins.

### C6. High — Seat 0 every seed
`pod_v12.py` always puts the candidate first. Turn order in 4p FFA
is a large effect. Lists can be kept or rejected from seating luck.

### C7. High — n=36 is a noisy fitness function
9/36 = 25% has a wide Wilson interval. The skill already forbids
optimizing from one game, but 1–2 extra wins is still noise. The
model will churn 1-for-1 swaps that do not generalize.

### C8. High — Fixed opponents are not a meta
EDHREC Nekusar / Kuja / Minstrel is one threat model (wheels, midrange,
lands). Tribal, infect, stax, extra turns, and hard combo are absent.
A deck built to beat that pod is not a “good EDH deck.”

### C9. High — Perf guards clip the strategy
150 casts/turn, Mana Echoes +30/trigger, log budget ~3k, attacker-log
collapse. Token/storm/echoes themes hit the cap and look weaker than
they are — or the AI never takes the real line.

### C10. Medium — Combat and objects are partial
Skill/simulator already disclose: first-blocker damage assignment,
partial planeswalkers, partial copy/clone, partial triggers. Voltron,
flicker, and clone themes are systematically under-simulated.

### C11. Medium — Damage must go through `deal_damage`
A new hook that subtracts life skips City on Fire / Torbran. Theme
finishers can be “implemented” wrong and underperform.

### C12. Medium — Two simulators
`sim.py` is the old heuristic (wipe p=0.12, win = 30 creatures).
`pod_v12.py` is the rules engine. `batch/runner.py --gpu` can quote
`fast_sweep`. An agent (or a website) can report the wrong number.

### C13. Medium — GPU hand MC is lands only
200k hands → keep rate, P(2–5 lands). It cannot see “did we have the
theme piece.” A $80 mana base can pass MC and still be off-theme.

### C14. Medium — Pilot-visible lines vs taken lines
Failure code `pilot` (v4.1) is not computed by `pod_v12.py`. Logs can
contain a win the AI did not take. The list gets blamed.

### C15. Medium — No-op / simplified on the critical path
Pod CSV stores a simplified-spell **count**, not whether the
commander’s payoff was the thing simplified. A theme card that no-ops
once per game is enough to tank the theme and still look “supported.”

---

## D. Flexibility gaps (commander / theme / price)

These are why “choose a different theme” will still emit Ovika-shaped
UR piles.

### D1. Blocker — New commander = new Python module
Terra required `engine/terra.py`, AI name lists, `pod_terra.py`,
`build_terra.py`. A site with thousands of commanders cannot hire a
rules engineer per listing. Until effects are data-driven (or the
product **does not** use the engine as the generator), flexibility
is fake.

### D2. Blocker — No theme ontology
Needed as first-class input, for example: tokens, spellslinger,
enchantress, aristocrats, voltron, lands, reanimator, stax, superfriends,
tribal, +1/+1 counters, mill, group hug. Each implies different slot
quotas, land counts, and “do not cut this role” rules. None of that
exists except convoke/enchantress in code comments.

### D3. Blocker — Land base is copied, not built
`deck_v12.py` is a UR duals + basics list. There is no generator for
2–5 color identity, shock/fetch/budget duals, or utility lands by
theme (e.g. Cabal Coffers only if the theme and budget allow). Wrong
mana is the fastest way to a poor EDH deck.

### D4. High — Price is not a solver
True budget construction is: maximize theme density subject to
`sum(price) <= cap` and `price(card) <= per_card_cap`, with substitutes
in the same slot (Sol Ring → cheaper rock). Today: sum prices after
the fact, missing = 0, cap = 1000. Cheap replacements are not searched.

### D5. High — Power level is prompt-only
“Casual vs cEDH” is intake text. The card pool is not stratified
(Game Changers, extra turns, fast mana, tutors). A $400 “casual tokens”
list can still emit Rhystic + Dockside-equivalents if the model
knows they are “good.”

### D6. Medium — Owned-cards / collection not modeled
A paid site’s best feature is “build from my binder.” No input for
that, so generated decks assume an infinite shop.

### D7. Medium — Opponent policy not parameterized
Skill wants “exact opponent lists.” A website user will not paste
three 99s. Defaulting to the lab pod makes every theme look like it
was built to beat Nekusar.

---

## E. Website / money (quality + legal + trust)

Charging for the current loop without a product layer will churn.

### E1. Product — Marketing a “win rate” is a prohibited claim
The skill forbids calling this a real MTG win rate. A landing page
that says “25% pod win rate” will be both **misleading** and a
support nightmare when humans play the list.

### E2. Product — Latency and cost
Confirmation is ~1–2 minutes, 4 CPU workers; GPU MC is extra.
Users expect a list in seconds. You cannot run a 36-game pod per
checkout without a queue, a cheaper proxy scorer, or precomputed
catalogs.

### E3. Product — Wizards / Scryfall / MTGJSON terms
Oracle text, names, and card images are not a free storefront.
A commercial site needs a licensing plan (and usually no full-card
image dump). The local `AtomicCards.json.gz` + Scryfall fetches are
fine for a personal lab, not an unreviewed SaaS.

### E4. Product — Refunds follow legality and “this isn’t my theme”
Without A2/B2/D2, the typical paid output is: slightly illegal, off
theme, or a $1000 Ovika clone with the commander name swapped. That
is not a business.

### E5. Product — No explanation / swap UI
Paid deck tools live on “why is this card here” and “give me a $5
replacement.” The skill’s adds/cuts table is for the lab notebook,
not a customer. Graph PNG is Ovika-only.

### E6. Product — Python PATH / CUDA venv is not a service
Simulator skill: `python` is not on PATH; CPU python is a Codex
runtime; CUDA is `.venv` on an RTX 4060 laptop. None of that is a
multi-tenant backend.

---

## What the model will actually do today

Given `{commander: X, theme: Y, budget: Z}` and this skill:

1. Clone the Ovika or Terra skeleton.
2. Swap in remembered staples that share colors with X.
3. Miss tags → AI plays the list badly.
4. Include unimplemented theme cards → simplified no-ops → low pod score.
5. Cut those cards, keep hooked staples → off-theme pile.
6. Sum prices with missing = $0, maybe over a $1000 default.
7. Report a 36-seed number vs Nekusar that is not X’s real power.

That is the poor-performance machine. Fix order for the product:

1. **JSON deck + shared legality/price solver** (B2–B5, B7, D4)
2. **Theme recipes + land-base builder + card retrieval** (A1–A4, D2–D3)
3. **Coverage gate: never score unimplemented win-condition cards** (C1, v4.1)
4. **Commander-specific or tag-from-Oracle AI** (C2–C4, B1)
5. Only then: simulation as an optional “stress test,” never as the
   generator’s objective for a paid casual deck.
6. Website: precomputed catalogs, seconds-latency, no win-rate claims,
   licensed data (E1–E6)

---

## Issue index

| ID | Sev | Layer | One-line |
|---|---|---|---|
| A1 | Blocker | Generator | No theme/card retrieval; model memorizes staples |
| A2 | Blocker | Generator | No commander/theme slot recipe |
| A3 | Blocker | Generator | Only mutates Ovika/Terra modules |
| A4 | High | Generator | Intake is prose; defaults to Ovika |
| A5 | High | Generator | Graph rules UR/Ovika-only |
| A6 | High | Generator | Skills are a lab notebook |
| A7 | Medium | Generator | Fitness = beat lab pod |
| B1 | Blocker | Data | Hand-written tags drive play, not Oracle |
| B2 | High | Data | No single legality function |
| B3 | High | Data | Ban list not enforced |
| B4 | High | Data | Missing price = $0 |
| B5 | High | Data | Budget hardcoded $1000 |
| B6 | Medium | Data | CI / MDFC traps |
| B7 | Medium | Data | Python tuple decks corrupt easily |
| B8 | Medium | Data | Graph replacements UR-only |
| C1 | Blocker | Engine | Unimplemented cards no-op |
| C2 | Blocker | Engine | Shared name-keyed AI |
| C3 | High | Engine | Counters need tags |
| C4 | High | Engine | Mulligan not commander-aware |
| C5 | High | Engine | Turn cap 14 |
| C6 | High | Engine | Seat 0 confounder |
| C7 | High | Engine | n=36 noisy |
| C8 | High | Engine | Three fixed opponents |
| C9 | High | Engine | Cast/trigger caps |
| C10 | Medium | Engine | Partial combat/PW/copy |
| C11 | Medium | Engine | Wrong damage path |
| C12 | Medium | Engine | Three different “win rates” |
| C13 | Medium | Engine | Hand MC ignores theme |
| C14 | Medium | Engine | AI misses visible lines |
| C15 | Medium | Engine | Simplified count ≠ critical path |
| D1 | Blocker | Flex | New commander = new Python |
| D2 | Blocker | Flex | No theme ontology |
| D3 | Blocker | Flex | Land base not generated |
| D4 | High | Flex | Price is not a substitute solver |
| D5 | High | Flex | Power level is prompt-only |
| D6 | Medium | Flex | No collection constraint |
| D7 | Medium | Flex | Opponents not parameterized |
| E1 | Product | Site | Cannot sell “win rate” |
| E2 | Product | Site | Pod too slow/expensive |
| E3 | Product | Site | IP / data licenses |
| E4 | Product | Site | Refunds if off-theme/illegal |
| E5 | Product | Site | No why-this-card UX |
| E6 | Product | Site | Laptop runtime ≠ SaaS |

# Algorithm

## Mathematical formulation

Locked-schedule share:

\[
\hat{p} = \frac{1}{n}\sum_{i=1}^{n} \mathbf{1}[\text{winner}(\text{Game}(E, L, P, \pi, T; \sigma_i)) = \text{candidate}]
\]

with \(n=36\), \(\sigma_i = i\), \(T=14\). Cap games contribute \(0\) to the candidate indicator (no-winner).

Retain rule for a same-slot swap \(L \to L'\):

\[
\text{retain}(L') \iff w(L') > w(L)
\quad\text{or (predeclared) secondary metric improves with CI disclosed.}
\]

Priority no-op:

\[
\text{if } \mathrm{sig}(s) = \mathrm{sig}(\mathrm{execute}(a,s))\ \text{then treat } a \text{ as a pass.}
\]

Hand MC keep probability is an empirical mean over \(N=200000\) without-replacement opening hands under the lab’s keep predicate (2–4 lands or fast-mana equivalent, etc. — exact keep predicate lives in `_handmc_v12.py`, not restated with invented thresholds here).

## Pseudocode — confirmation pod

```
function confirm(deck_module, engine E):
  assert workers in {1..5}  # 4 typical; never >> cores
  csv <- []
  for seed in 1..36:
    g <- Game(E, decks=[deck_module, nekusar, kuja, minstrel], seed, T=14)
    csv.append(record(g))
  w <- count(csv.winner_deck == ovika)
  return w, csv
```

## Pseudocode — 1-for-1 retain

```
function maybe_adopt(parent L, candidate L', slot s):
  require same_engine_stamp
  require one_add_one_cut_in_slot(L, L', s)
  w0, w1 <- confirm(L), confirm(L')
  if w1 > w0: return adopt
  else: archive L' as rejected  # v12.2 pattern
```

## Complexity

- One game: sequential in board/stack size; token engines hit disclosed caps (150 casts/turn, Mana Echoes +30/trigger, log ~3000 lines).
- Pod: \(O(n)\) games, \(n=36\), 4-way process pool ~60–90s on the lab machine (CONTEXT.md).
- Hand MC: vectorized GPU, \(N=2\cdot10^5\) (report) up to \(10^6\) in README examples.

## Step-by-step explanation

1. Legality + `Oracle.require` on every name.
2. Diagnostic 10 seeds + failure taxonomy if iterating.
3. Confirmation 36 seeds on locked factors.
4. Optional graph audit — never override step 3.
5. Re-run confirmation after any engine change (`stale` otherwise).

import { useEffect, useMemo, useState } from "react";
import { generateDeck, searchCommanders, swapCard, toMtgo, type CardRow, type Deck } from "./api";

const THEMES = ["midrange", "tokens", "spellslinger", "enchantress", "voltron", "reanimator", "stax"] as const;

export default function App() {
  const [q, setQ] = useState("");
  const [hits, setHits] = useState<{ name: string; color_identity: string[] }[]>([]);
  const [commander, setCommander] = useState("");
  const [theme, setTheme] = useState("");
  const [budget, setBudget] = useState<number | "">("");
  const [perCard, setPerCard] = useState<number | "">("");
  const [power, setPower] = useState("casual");
  const [exclude, setExclude] = useState("");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");
  const [deck, setDeck] = useState<Deck | null>(null);
  const [cut, setCut] = useState<CardRow | null>(null);
  const [swaps, setSwaps] = useState<CardRow[]>([]);
  const [copied, setCopied] = useState(false);

  const ready = Boolean(commander && theme && budget && Number(budget) > 0);

  useEffect(() => {
    if (q.trim().length < 2) {
      setHits([]);
      return;
    }
    const t = setTimeout(() => {
      searchCommanders(q)
        .then((r) => setHits(r.results))
        .catch(() => setHits([]));
    }, 200);
    return () => clearTimeout(t);
  }, [q]);

  async function onGenerate() {
    setErr("");
    setBusy(true);
    setCut(null);
    try {
      const body: Record<string, unknown> = {
        commander,
        theme,
        budget_usd: Number(budget),
        power_level: power,
      };
      if (perCard !== "" && Number(perCard) > 0) body.per_card_cap_usd = Number(perCard);
      const ex = exclude
        .split(",")
        .map((s) => s.trim())
        .filter(Boolean);
      if (ex.length) body.exclude = ex;
      const d = await generateDeck(body);
      setDeck(d);
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }

  async function onCut(row: CardRow) {
    if (!deck) return;
    setCut(row);
    const remaining = Math.max(0, deck.budget_usd - deck.total_usd + (row.price_usd || 0));
    const r = await swapCard({
      commander: deck.commander,
      theme: deck.theme,
      budget_usd: deck.budget_usd,
      power_level: deck.power_level,
      deck,
      cut: row.name,
      budget_remaining: remaining,
    });
    setSwaps(r.candidates);
  }

  function applySwap(add: CardRow) {
    if (!deck || !cut) return;
    const cards = deck.cards.map((c) => (c.name === cut.name ? { ...add, slot: cut.slot, reason: add.reason } : c));
    const total = cards.reduce((s, c) => s + (c.price_usd || 0), 0);
    setDeck({ ...deck, cards, total_usd: Math.round(total * 100) / 100 });
    setCut(null);
  }

  const grouped = useMemo(() => {
    if (!deck) return [];
    const map = new Map<string, CardRow[]>();
    for (const c of deck.cards) {
      map.set(c.slot, [...(map.get(c.slot) || []), c]);
    }
    return [...map.entries()];
  }, [deck]);

  return (
    <div className="app">
      <h1>Commander list generator</h1>
      <p className="sub">Legal, on-theme, on-budget suggestions. Not a real Magic win rate. Engine coverage is incomplete.</p>

      <div className="form">
        <label>
          Commander
          <div className="typeahead">
            <input
              value={q || commander}
              placeholder="Start typing a legendary creature…"
              onChange={(e) => {
                setQ(e.target.value);
                setCommander("");
              }}
            />
            {hits.length > 0 && !commander && (
              <ul>
                {hits.map((h) => (
                  <li
                    key={h.name}
                    onClick={() => {
                      setCommander(h.name);
                      setQ(h.name);
                      setHits([]);
                    }}
                  >
                    {h.name} ({h.color_identity.join("") || "C"})
                  </li>
                ))}
              </ul>
            )}
          </div>
        </label>

        <div>
          Theme
          <div className="chips">
            {THEMES.map((t) => (
              <button key={t} className={theme === t ? "on" : ""} type="button" onClick={() => setTheme(t)}>
                {t}
              </button>
            ))}
          </div>
        </div>

        <label>
          Budget USD (required, no default)
          <input
            type="number"
            min={1}
            placeholder="e.g. 150"
            value={budget}
            onChange={(e) => setBudget(e.target.value === "" ? "" : Number(e.target.value))}
          />
        </label>
        <label>
          Optional per-card cap
          <input
            type="number"
            min={0}
            placeholder="none"
            value={perCard}
            onChange={(e) => setPerCard(e.target.value === "" ? "" : Number(e.target.value))}
          />
        </label>
        <label>
          Power level
          <select value={power} onChange={(e) => setPower(e.target.value)}>
            <option value="precon">precon</option>
            <option value="casual">casual</option>
            <option value="focused">focused</option>
            <option value="high">high</option>
            <option value="cedh">cedh</option>
          </select>
        </label>
        <label>
          Exclude (comma-separated names)
          <input value={exclude} onChange={(e) => setExclude(e.target.value)} />
        </label>
        <button className="primary" disabled={!ready || busy} onClick={onGenerate}>
          {busy ? "Generating…" : "Generate"}
        </button>
        {!ready && <span>Generate stays off until commander, theme, and budget are set. No Ovika / $1000 default.</span>}
        {err && <div className="error">{err}</div>}
      </div>

      {deck && (
        <section>
          <h2>
            {deck.commander} · {deck.theme} · ${deck.total_usd} / ${deck.budget_usd}
          </h2>
          <div className={deck.legality?.ok ? "banner ok" : "banner bad"}>
            legality {deck.legality?.ok ? "ok" : "fail"} {deck.legality?.violations?.join("; ")}
          </div>
          <div className={deck.theme_fill?.ok ? "banner ok" : "banner bad"}>
            theme fill {deck.theme_fill?.ok ? "ok" : "missing: " + (deck.theme_fill?.missing_slots || []).join(", ")}
          </div>
          <p>
            confidence={deck.confidence} · prices_as_of={deck.prices_as_of} · ban_list_version={deck.ban_list_version}
          </p>
          <button
            className="ghost"
            type="button"
            onClick={() => {
              navigator.clipboard.writeText(toMtgo(deck));
              setCopied(true);
            }}
          >
            {copied ? "Copied MTGO text" : "Copy MTGO plaintext"}
          </button>
          <button className="ghost" type="button" disabled title="Not a real Magic win rate. Engine coverage is incomplete.">
            Simulate (disabled)
          </button>

          {grouped.map(([slot, rows]) => (
            <div key={slot}>
              <h3>{slot}</h3>
              <table className="table">
                <thead>
                  <tr>
                    <th>Card</th>
                    <th>USD</th>
                    <th>Reason</th>
                  </tr>
                </thead>
                <tbody>
                  {rows.map((row) => (
                    <tr key={row.name + slot} className="clickable" onClick={() => onCut(row)}>
                      <td>{row.name}</td>
                      <td>{row.price_usd ?? "unknown"}</td>
                      <td>{row.reason}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ))}
        </section>
      )}

      {cut && (
        <div className="drawer">
          <h3>Cheaper {cut.slot} swaps for {cut.name}</h3>
          <button className="ghost" type="button" onClick={() => setCut(null)}>
            Close
          </button>
          <ul>
            {swaps.map((s) => (
              <li key={s.name}>
                <button type="button" className="ghost" onClick={() => applySwap(s)}>
                  {s.name} (${s.price_usd})
                </button>
              </li>
            ))}
            {swaps.length === 0 && <li>No cheaper same-slot candidates under remaining budget.</li>}
          </ul>
        </div>
      )}

      <p className="footer">
        Suggestion-only lists. Legality uses a dated Commander ban snapshot. Prices are a local USD snapshot. Not affiliated
        with Wizards of the Coast. No full-card images in V1.
      </p>
    </div>
  );
}

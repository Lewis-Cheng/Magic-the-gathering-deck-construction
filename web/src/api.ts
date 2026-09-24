export type CardRow = {
  name: string;
  slot: string;
  price_usd: number | null;
  reason: string;
};

export type Deck = {
  commander: string;
  theme: string;
  budget_usd: number;
  power_level?: string;
  cards: CardRow[];
  total_usd: number;
  lands: number;
  legality: { ok: boolean; violations: string[] };
  theme_fill: { ok: boolean; missing_slots: string[] };
  confidence: string;
  notes: string[];
  prices_as_of?: string;
  ban_list_version?: string;
  graph_suggestions?: { cut: string; add: string; slot: string; price_usd: number; reason: string }[];
  detail?: string;
};

const base = "";

export async function searchCommanders(q: string) {
  const r = await fetch(`${base}/v1/commanders?q=${encodeURIComponent(q)}`);
  if (!r.ok) throw new Error("commander search failed");
  return (await r.json()) as { results: { name: string; color_identity: string[] }[] };
}

export async function generateDeck(body: Record<string, unknown>) {
  const r = await fetch(`${base}/v1/decks`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const data = await r.json();
  if (!r.ok) throw new Error(data.detail?.detail || data.detail || r.statusText);
  return data as Deck;
}

export async function swapCard(body: Record<string, unknown>) {
  const r = await fetch(`${base}/v1/swap`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const data = await r.json();
  if (!r.ok) throw new Error(data.detail?.detail || r.statusText);
  return data as { cut: string; candidates: CardRow[] };
}

export function toMtgo(deck: Deck): string {
  const counts = new Map<string, number>();
  for (const c of deck.cards) {
    counts.set(c.name, (counts.get(c.name) || 0) + 1);
  }
  const deckLines = [...counts.entries()].map(([n, k]) => `${k} ${n}`);
  return `1 ${deck.commander}\n${deckLines.join("\n")}\n`;
}

"""Card search on the Endless Atlas / Lantern map.

Positions are the TRUE UMAP coordinates from stoken Lantern
(https://stoken.games/stack/lantern/lantern.html), the same map as
card-atlas.html. Search walks nearest neighbors of the cards already in
the deck. It does not scan the Oracle file in dump order and it does not
copy an EDHREC average list.

Lenses:
- synergy: Deckmates (what commanders actually play together)
- textual: What it does (rules-text neighborhood)
- combo: Combos (Commander Spellbook islands)

A card with no data on a lens is parked and is not a result on that lens.
Distance is Euclidean on [0, 1] coordinates. Lower is tighter.
"""

from __future__ import annotations

import base64
import json
from array import array
from functools import lru_cache
from pathlib import Path

MAP_PATH = Path(__file__).resolve().parent / "data" / "atlas_map.json"
LENSES = ("synergy", "textual", "combo")
# WUBRG bit order used by the atlas idn mask.
_BITS = ("W", "U", "B", "R", "G")


def _u8(blob: str) -> bytes:
    return base64.b64decode(blob)


def _pairs(blob: str, n: int) -> tuple[list[float], list[float]]:
    raw = base64.b64decode(blob)
    vals = array("H")
    vals.frombytes(raw[: n * 4])
    if vals.itemsize != 2:
        raise RuntimeError("uint16 array size")
    xs = [vals[i] / 65535.0 for i in range(0, n * 2, 2)]
    ys = [vals[i] / 65535.0 for i in range(1, n * 2, 2)]
    return xs, ys


class Atlas:
    def __init__(self, path: Path = MAP_PATH) -> None:
        data = json.loads(path.read_text(encoding="utf-8"))
        self.source = data.get("source", "")
        self.names: list[str] = data["names"]
        self.n = len(self.names)
        self.by_name: dict[str, int] = {}
        for i, name in enumerate(self.names):
            self.by_name.setdefault(name, i)
            if " // " in name:
                self.by_name.setdefault(name.split(" // ", 1)[0], i)
        self.idn = _u8(data["idn"])
        edh_raw = array("H")
        edh_raw.frombytes(base64.b64decode(data["edh"])[: self.n * 2])
        self.edh = edh_raw
        self.xy: dict[str, tuple[list[float], list[float]]] = {}
        self.cid: dict[str, bytes] = {}
        self.nd: dict[str, bytes] = {}
        for lens in LENSES:
            key = f"{lens}_xy"
            if key not in data:
                continue
            self.xy[lens] = _pairs(data[key], self.n)
            self.cid[lens] = _u8(data[f"{lens}_cid"])
            if f"{lens}_nd" in data:
                self.nd[lens] = _u8(data[f"{lens}_nd"])

    def index_of(self, name: str) -> int | None:
        if name in self.by_name:
            return self.by_name[name]
        front = name.split(" // ", 1)[0]
        return self.by_name.get(front)

    def live(self, lens: str, i: int) -> bool:
        nd = self.nd.get(lens)
        if nd is not None and i < len(nd) and nd[i]:
            return False
        if lens in self.cid and self.cid[lens][i] == 255 and lens in ("synergy", "combo"):
            # 255 is noise/parked. Still allow textual/mechanical noise points
            # only when nd did not already reject them. Synergy parked cards
            # sit at the origin of that lens and are not a neighborhood.
            xs, ys = self.xy[lens]
            if abs(xs[i] - 0.5) < 1e-6 and abs(ys[i] - 0.5) < 1e-6:
                return False
        return lens in self.xy

    def identity(self, i: int) -> set[str]:
        mask = self.idn[i]
        return {c for bit, c in enumerate(_BITS) if mask & (1 << bit)}

    def neighbors(
        self,
        seeds: list[str],
        *,
        ci: set[str],
        limit: int = 40,
        lens: str = "synergy",
        exclude: set[str] | None = None,
    ) -> list[tuple[str, float]]:
        """k nearest live cards to the seed centroid on one lens.

        Color identity must be a subset of `ci`. `exclude` drops names already
        in the deck. Returns (name, distance) sorted tightest first.
        """
        if lens not in self.xy:
            return []
        exclude = exclude or set()
        xs, ys = self.xy[lens]
        pts = []
        for name in seeds:
            i = self.index_of(name)
            if i is None or not self.live(lens, i):
                continue
            pts.append((xs[i], ys[i]))
        if not pts:
            return []
        # Distance to the nearest seed, not to the centroid. A centroid of
        # Rhystic and Sythis lands in unrelated space. Lantern steps toward
        # a card you are already standing on.
        ci_f = set(ci)
        ranked: list[tuple[float, str]] = []
        for i, name in enumerate(self.names):
            if name in exclude or not self.live(lens, i):
                continue
            if not self.identity(i).issubset(ci_f):
                continue
            best = min((xs[i] - sx) ** 2 + (ys[i] - sy) ** 2 for sx, sy in pts)
            ranked.append((best, name))
        ranked.sort()
        out = []
        for dist2, name in ranked[:limit]:
            out.append((name, dist2 ** 0.5))
        return out

    def around(
        self,
        seeds: list[str],
        *,
        ci: set[str],
        limit: int = 80,
        exclude: set[str] | None = None,
        lenses: tuple[str, ...] = ("synergy", "textual", "combo"),
    ) -> list[tuple[str, float, str]]:
        """Neighbors on the first lens where any seed is actually on the map.

        Order matches Lantern: start on Deckmates, planeswalk to What it does,
        then Combos. Returns (name, distance, lens).
        """
        for lens in lenses:
            hits = self.neighbors(seeds, ci=ci, limit=limit, lens=lens, exclude=exclude)
            if hits:
                return [(name, dist, lens) for name, dist in hits]
        return []

    def tightness(self, names: list[str], lens: str = "synergy") -> float | None:
        """Mean pairwise distance. None if fewer than two live cards. Lower is tighter."""
        if lens not in self.xy:
            return None
        xs, ys = self.xy[lens]
        pts = []
        for name in names:
            i = self.index_of(name)
            if i is None or not self.live(lens, i):
                continue
            pts.append((xs[i], ys[i]))
        if len(pts) < 2:
            return None
        s = 0.0
        n = 0
        for a in range(len(pts)):
            for b in range(a + 1, len(pts)):
                dx = pts[a][0] - pts[b][0]
                dy = pts[a][1] - pts[b][1]
                s += (dx * dx + dy * dy) ** 0.5
                n += 1
        return s / n


@lru_cache(maxsize=1)
def get_atlas() -> Atlas:
    return Atlas()

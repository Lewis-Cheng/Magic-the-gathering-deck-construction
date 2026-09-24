from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Optional


THEMES_V1 = (
    "midrange",
    "tokens",
    "spellslinger",
    "enchantress",
    "voltron",
    "reanimator",
    "stax",
)

POWER_LEVELS = ("precon", "casual", "focused", "high", "cedh")


@dataclass
class CardRow:
    name: str
    slot: str
    price_usd: Optional[float]
    reason: str

    def to_json(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "slot": self.slot,
            "price_usd": self.price_usd,
            "reason": self.reason,
        }


@dataclass
class DeckList:
    commander: str
    theme: str
    budget_usd: float
    power_level: str
    cards: list[CardRow]
    total_usd: float
    lands: int
    legality: dict[str, Any]
    theme_fill: dict[str, Any]
    coverage: dict[str, Any]
    confidence: str
    notes: list[str] = field(default_factory=list)
    tagger_version: str = "v1"
    prices_as_of: Optional[str] = None
    ban_list_version: str = ""
    graph_suggestions: list[dict[str, Any]] = field(default_factory=list)

    def names(self) -> list[str]:
        return [self.commander] + [c.name for c in self.cards]

    def to_json(self) -> dict[str, Any]:
        d = asdict(self)
        d["cards"] = [c.to_json() if isinstance(c, CardRow) else c for c in self.cards]
        return d


@dataclass
class Intake:
    commander: str
    theme: str
    budget_usd: float
    power_level: str = "casual"
    per_card_cap_usd: Optional[float] = None
    owned_cards: list[str] = field(default_factory=list)
    proxies: bool = False
    land_count: Optional[int] = None
    exclude: list[str] = field(default_factory=list)
    must_include: list[str] = field(default_factory=list)
    sim: dict[str, Any] = field(default_factory=lambda: {"enabled": False})

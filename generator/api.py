"""FastAPI product surface. Generate is CPU-only; no Pool / pod_v12."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from generator.build import generate
from generator.index import commanders_matching, get_index
from generator.intake import IntakeError, parse
from generator.oracle_bridge import get_oracle
from generator.swap import cheaper_swaps

app = FastAPI(title="EDH Generator V1", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def _warmup() -> None:
    get_oracle()
    get_index()


@app.get("/v1/health")
def health() -> dict:
    return {"ok": True, "product": "generator", "sim": "stubbed"}


@app.get("/v1/commanders")
def commanders(q: str = Query("", min_length=0)) -> dict:
    return {"results": commanders_matching(q)}


@app.post("/v1/decks")
def create_deck(body: dict) -> dict:
    try:
        return generate(body)
    except IntakeError as e:
        raise HTTPException(status_code=400, detail=e.to_json()) from e
    except KeyError as e:
        raise HTTPException(status_code=400, detail={"error": "unknown_card", "detail": str(e)}) from e


@app.post("/v1/swap")
def swap(body: dict) -> dict:
    try:
        commander = body.get("commander")
        theme = body.get("theme")
        deck = body.get("deck") or {}
        cut = body.get("cut")
        budget_remaining = float(body.get("budget_remaining") or 0)
        if not commander or not theme or not cut:
            raise IntakeError("commander, theme, and cut are required")
        intake = parse(
            {
                "commander": commander,
                "theme": theme,
                "budget_usd": body.get("budget_usd") or deck.get("budget_usd") or 1,
                "power_level": body.get("power_level") or deck.get("power_level") or "casual",
                "exclude": body.get("exclude") or [],
                "owned_cards": body.get("owned_cards") or [],
            }
        )
        cands = cheaper_swaps(intake, deck, cut, budget_remaining)
        return {"cut": cut, "candidates": cands}
    except IntakeError as e:
        raise HTTPException(status_code=400, detail=e.to_json()) from e


@app.post("/v1/sim")
def sim_stub(body: dict) -> dict:
    return {
        "confidence": "coverage-blocked",
        "detail": "V1 does not run pods at checkout",
        "coverage": {"not_probed": True},
        "notes": ["Not a real Magic win rate. Engine coverage is incomplete."],
    }

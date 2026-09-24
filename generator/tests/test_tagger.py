from __future__ import annotations

from generator.tagger import tag_card, VERSION


def test_tagger_version():
    assert VERSION == "v1"


def test_counterspell(oracle):
    tags = tag_card(oracle.require("Counterspell"))
    assert "counter" in tags


def test_sol_ring(oracle):
    tags = tag_card(oracle.require("Sol Ring"))
    assert "ramp" in tags
    assert "rock" in tags


def test_swords(oracle):
    tags = tag_card(oracle.require("Swords to Plowshares"))
    assert "removal" in tags or "protection" in tags

"""Oracle.require every product name. Ignore lab tuple mv/kind/tags."""

from __future__ import annotations

from typing import Any

from generator.oracle_bridge import get_oracle


def require_card(name: str) -> Any:
    return get_oracle().require(canonical_name(name))


def canonical_name(name: str) -> str:
    name = name.strip()
    if " // " in name:
        front = name.split(" // ", 1)[0].strip()
        oracle = get_oracle()
        if oracle.get(front) is not None:
            return front
        if oracle.get(name) is not None:
            return name
        return front
    return name


def is_spell_front_mdfc(name: str) -> bool:
    raw = get_oracle().get(name) or get_oracle().get(name.split(" // ")[0] if " // " in name else name)
    if raw is None:
        return False
    full = raw.name
    if " // " not in full and " // " not in name:
        keyed = None
        prefix = name + " //"
        for k in get_oracle()._by_name:
            if k.startswith(prefix):
                keyed = k
                break
        if keyed is None:
            return False
        full = keyed
        raw = get_oracle()._by_name[keyed]
    if " // " not in full:
        return False
    return bool(raw.is_instant or raw.is_sorcery) and not raw.is_land

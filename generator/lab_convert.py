"""Test-only: parse lab DECK tuples via AST (does not exec Pool / deck modules)."""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any


def lab_py_to_names(path: str | Path) -> dict[str, Any]:
    tree = ast.parse(Path(path).read_text(encoding="utf-8"))
    commander = None
    names: list[str] = []
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name) and t.id == "COMMANDER":
                    commander = ast.literal_eval(node.value)
                if isinstance(t, ast.Name) and t.id == "DECK":
                    deck = ast.literal_eval(node.value)
                    for row in deck:
                        if row:
                            names.append(str(row[0]))
    return {"commander": commander, "cards": names}

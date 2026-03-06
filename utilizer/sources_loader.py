from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class UtilizerSources:
    constitution: str
    psl_templates: str
    crystals: dict[str, Any]


def load_sources(repo_root: str | Path) -> UtilizerSources:
    root = Path(repo_root)
    base = root / "sources" / "utilizer"

    constitution = (base / "CONSTITUTION_UTILIZER.md").read_text(encoding="utf-8")
    psl_templates = (base / "PSL_TEMPLATES.md").read_text(encoding="utf-8")

    with (base / "CRYSTALS.yaml").open("r", encoding="utf-8") as f:
        crystals = yaml.safe_load(f)

    return UtilizerSources(
        constitution=constitution,
        psl_templates=psl_templates,
        crystals=crystals,
    )


def crystals_index(crystals_yaml: dict[str, Any]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for item in (crystals_yaml or {}).get("crystals", []):
        cid = item.get("id")
        if cid:
            out[cid] = item
    return out

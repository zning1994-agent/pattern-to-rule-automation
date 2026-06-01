from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import tomllib

from .patterns import DEFAULT_PATTERNS


@dataclass(frozen=True)
class Settings:
    """Runtime configuration for scans, proposal generation, and the API."""

    knowledge_base_dir: Path = Path("knowledge")
    output_dir: Path = Path("out")
    db_path: Path = Path("pra.db")
    min_confidence: float = 0.7
    min_frequency: int = 2
    api_host: str = "127.0.0.1"
    api_port: int = 8000
    known_patterns: tuple[str, ...] = tuple(DEFAULT_PATTERNS)


def _section(data: dict[str, Any], name: str) -> dict[str, Any]:
    value = data.get(name, {})
    return value if isinstance(value, dict) else {}


def load_settings(path: str | Path | None = None) -> Settings:
    """Load Settings from an optional TOML file.

    Expected sections are [paths], [thresholds], and [api]. Missing values fall
    back to defaults so the CLI and API remain bootstrappable.
    """

    if path is None:
        return Settings()

    config_path = Path(path)
    data = tomllib.loads(config_path.read_text(encoding="utf-8")) if config_path.exists() else {}
    paths = _section(data, "paths")
    thresholds = _section(data, "thresholds")
    api = _section(data, "api")

    defaults = Settings()
    return Settings(
        knowledge_base_dir=Path(paths.get("knowledge_base_dir", defaults.knowledge_base_dir)),
        output_dir=Path(paths.get("output_dir", defaults.output_dir)),
        db_path=Path(paths.get("db_path", defaults.db_path)),
        min_confidence=float(thresholds.get("min_confidence", defaults.min_confidence)),
        min_frequency=int(thresholds.get("min_frequency", defaults.min_frequency)),
        api_host=str(api.get("host", defaults.api_host)),
        api_port=int(api.get("port", defaults.api_port)),
        known_patterns=tuple(data.get("known_patterns", defaults.known_patterns)),
    )

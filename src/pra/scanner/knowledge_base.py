from __future__ import annotations

from pathlib import Path

from pra.core import PatternAnnotation, scan_path


class KnowledgeBaseScanner:
    """Scan JSON, Markdown, and YAML knowledge-base files for patterns."""

    supported_extensions = {".json", ".md", ".yaml", ".yml"}

    def scan(self, path: str | Path) -> list[PatternAnnotation]:
        return scan_path(path)

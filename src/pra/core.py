from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import yaml

PATTERN_RE = re.compile(
    r"\b(?P<name>(?:system|instruction|memory|error)\.[a-z0-9_.-]+)\b",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class PatternAnnotation:
    id: str
    pattern_type: str
    source_file: str
    line_number: int
    context: str
    frequency: int = 1
    confidence: float = 0.0


@dataclass(frozen=True)
class RuleDraft:
    id: str
    pattern_id: str
    name: str
    description: str
    schema: dict[str, Any]
    confidence: float
    status: str = "proposed"


def _read_text(path: Path) -> str:
    if path.suffix.lower() == ".json":
        return json.dumps(json.loads(path.read_text(encoding="utf-8")), indent=2)
    if path.suffix.lower() in {".yaml", ".yml"}:
        return yaml.safe_dump(yaml.safe_load(path.read_text(encoding="utf-8")) or {})
    return path.read_text(encoding="utf-8")


def detect_patterns(text: str, source_file: str) -> list[PatternAnnotation]:
    found: list[PatternAnnotation] = []
    lines = text.splitlines()
    for index, line in enumerate(lines, start=1):
        for match in PATTERN_RE.finditer(line):
            name = match.group("name").lower()
            context_start = max(0, index - 2)
            context_end = min(len(lines), index + 1)
            context = "\n".join(lines[context_start:context_end]).strip()
            found.append(
                PatternAnnotation(
                    id=f"{Path(source_file).stem}-{index}-{len(found) + 1}",
                    pattern_type=name,
                    source_file=source_file,
                    line_number=index,
                    context=context,
                )
            )
    return found


def scan_path(path: str | Path) -> list[PatternAnnotation]:
    root = Path(path)
    files = [root] if root.is_file() else [
        p for p in root.rglob("*") if p.suffix.lower() in {".json", ".md", ".yaml", ".yml"}
    ]
    patterns: list[PatternAnnotation] = []
    for file_path in files:
        try:
            patterns.extend(detect_patterns(_read_text(file_path), str(file_path)))
        except (OSError, json.JSONDecodeError, yaml.YAMLError, UnicodeDecodeError):
            continue
    return _with_scores(patterns)


def _with_scores(patterns: list[PatternAnnotation]) -> list[PatternAnnotation]:
    counts: dict[str, int] = {}
    for pattern in patterns:
        counts[pattern.pattern_type] = counts.get(pattern.pattern_type, 0) + 1

    scored: list[PatternAnnotation] = []
    for pattern in patterns:
        frequency = counts[pattern.pattern_type]
        context_score = min(0.3, len(pattern.context) / 500)
        confidence = min(1.0, 0.35 + min(0.35, frequency * 0.1) + context_score)
        scored.append(
            PatternAnnotation(
                id=pattern.id,
                pattern_type=pattern.pattern_type,
                source_file=pattern.source_file,
                line_number=pattern.line_number,
                context=pattern.context,
                frequency=frequency,
                confidence=round(confidence, 3),
            )
        )
    return scored


def generate_rule(pattern: PatternAnnotation) -> RuleDraft:
    rule_name = pattern.pattern_type.replace(".", "_").replace("-", "_")
    return RuleDraft(
        id=f"rule-{pattern.id}",
        pattern_id=pattern.id,
        name=rule_name,
        description=f"Draft rule generated from recurring pattern {pattern.pattern_type}.",
        confidence=pattern.confidence,
        schema={
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "title": rule_name,
            "type": "object",
            "properties": {
                "pattern": {"const": pattern.pattern_type},
                "source_file": {"type": "string"},
                "line_number": {"type": "integer", "minimum": 1},
                "recommended_action": {
                    "type": "string",
                    "default": "review_and_promote_to_system_rule",
                },
            },
            "required": ["pattern", "source_file", "line_number"],
            "additionalProperties": True,
        },
    )


def scan_summary(path: str | Path) -> dict[str, Any]:
    patterns = scan_path(path)
    rules = [generate_rule(pattern) for pattern in patterns if pattern.confidence >= 0.7]
    return {
        "patterns": [asdict(pattern) for pattern in patterns],
        "proposals": [asdict(rule) for rule in rules],
        "summary": {
            "patterns_found": len(patterns),
            "proposals_generated": len(rules),
            "high_confidence": sum(1 for p in patterns if p.confidence >= 0.7),
        },
    }

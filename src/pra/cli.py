from __future__ import annotations

import json
from pathlib import Path

import click

from .core import scan_summary


@click.group()
def main() -> None:
    """Pattern-to-rule automation commands."""


@main.command()
@click.argument("path", type=click.Path(exists=True, path_type=Path))
@click.option("--format", "output_format", type=click.Choice(["json", "text"]), default="text")
def scan(path: Path, output_format: str) -> None:
    """Scan a file or directory for promotable pattern annotations."""
    result = scan_summary(path)
    if output_format == "json":
        click.echo(json.dumps(result, indent=2))
        return

    summary = result["summary"]
    click.echo(f"Patterns found: {summary['patterns_found']}")
    click.echo(f"Rule proposals: {summary['proposals_generated']}")
    for pattern in result["patterns"]:
        click.echo(
            f"- {pattern['pattern_type']} "
            f"({pattern['confidence']}) at {pattern['source_file']}:{pattern['line_number']}"
        )


if __name__ == "__main__":
    main()

from pra.core import generate_rule, scan_path


def test_scan_path_detects_patterns(tmp_path):
    kb = tmp_path / "patterns.md"
    kb.write_text(
        "Observed system.async_command_context_missing twice.\n"
        "Again: system.async_command_context_missing needs promotion.\n",
        encoding="utf-8",
    )

    patterns = scan_path(kb)

    assert len(patterns) == 2
    assert patterns[0].pattern_type == "system.async_command_context_missing"
    assert patterns[0].frequency == 2
    assert patterns[0].confidence >= 0.7


def test_generate_rule_returns_json_schema(tmp_path):
    kb = tmp_path / "patterns.md"
    kb.write_text("instruction.session_isolation should become a rule.", encoding="utf-8")
    pattern = scan_path(kb)[0]

    rule = generate_rule(pattern)

    assert rule.status == "proposed"
    assert rule.schema["properties"]["pattern"]["const"] == "instruction.session_isolation"

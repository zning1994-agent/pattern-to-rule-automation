from pra.core import generate_rule, scan_path
from pra.analyzer import ConfidenceAnalyzer
from pra.generator import RuleGenerator
from pra.scanner import KnowledgeBaseScanner
from pra.storage import ProposalStore


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


def test_spec_shaped_modules_work(tmp_path):
    kb = tmp_path / "patterns.md"
    kb.write_text(
        "system.heartbeat_repeated_check happened.\n"
        "system.heartbeat_repeated_check happened again.\n",
        encoding="utf-8",
    )

    patterns = KnowledgeBaseScanner().scan(kb)
    rule = RuleGenerator().generate_rule_draft(patterns[0])
    store = ProposalStore(tmp_path / "pra.db")
    store.add(rule)

    assert ConfidenceAnalyzer().promotion_candidates(patterns)
    assert store.list()[0]["id"] == rule.id

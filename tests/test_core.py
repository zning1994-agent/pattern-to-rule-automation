from pra.core import generate_rule, scan_path
from pra.config import load_settings
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


def test_yaml_scan_and_pattern_annotations(tmp_path):
    kb = tmp_path / "patterns.yaml"
    kb.write_text(
        "notes:\n"
        "  - '@pattern system.heartbeat_repeated_check should be promoted'\n"
        "  - 'instruction.session_isolation needs clearer boundaries'\n",
        encoding="utf-8",
    )

    patterns = KnowledgeBaseScanner().scan(kb)

    assert {pattern.pattern_type for pattern in patterns} == {
        "system.heartbeat_repeated_check",
        "instruction.session_isolation",
    }


def test_toml_settings_override_defaults(tmp_path):
    config = tmp_path / "pra.toml"
    config.write_text(
        "[paths]\n"
        "knowledge_base_dir = 'kb'\n"
        "db_path = 'state/pra.db'\n"
        "[thresholds]\n"
        "min_confidence = 0.8\n"
        "min_frequency = 3\n"
        "[api]\n"
        "host = '0.0.0.0'\n"
        "port = 9000\n",
        encoding="utf-8",
    )

    settings = load_settings(config)

    assert str(settings.knowledge_base_dir) == "kb"
    assert str(settings.db_path) == "state/pra.db"
    assert settings.min_confidence == 0.8
    assert settings.min_frequency == 3
    assert settings.api_host == "0.0.0.0"
    assert settings.api_port == 9000


def test_proposal_lifecycle_transitions(tmp_path):
    kb = tmp_path / "patterns.md"
    kb.write_text("system.async_command_context_missing needs a rule.", encoding="utf-8")
    rule = generate_rule(scan_path(kb)[0])
    store = ProposalStore(tmp_path / "pra.db")
    store.add(rule)

    approved = store.transition(rule.id, "approved", reviewed_by="heartbeat")
    active = store.transition(rule.id, "active")

    assert approved["reviewed_by"] == "heartbeat"
    assert approved["reviewed_at"]
    assert active["status"] == "active"
    assert active["activated_at"]

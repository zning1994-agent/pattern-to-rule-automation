from __future__ import annotations

from pra.core import PatternAnnotation, RuleDraft, generate_rule


class RuleGenerator:
    """Generate JSON Schema rule drafts from detected patterns."""

    def generate_rule_draft(self, pattern: PatternAnnotation) -> RuleDraft:
        return generate_rule(pattern)

    def generate_rules_batch(self, patterns: list[PatternAnnotation]) -> list[RuleDraft]:
        return [self.generate_rule_draft(pattern) for pattern in patterns]

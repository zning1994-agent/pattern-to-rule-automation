from __future__ import annotations

from pra.core import PatternAnnotation


class ConfidenceAnalyzer:
    """Score patterns using frequency and context richness."""

    def calculate_frequency_score(self, frequency: int) -> float:
        return min(1.0, max(0, frequency) / 5)

    def calculate_context_score(self, context: str) -> float:
        return min(1.0, len(context.strip()) / 300)

    def calculate_combined_score(self, pattern: PatternAnnotation) -> float:
        frequency = self.calculate_frequency_score(pattern.frequency)
        context = self.calculate_context_score(pattern.context)
        return round((frequency * 0.6) + (context * 0.4), 3)

    def promotion_candidates(
        self, patterns: list[PatternAnnotation], threshold: float = 0.7
    ) -> list[PatternAnnotation]:
        return [pattern for pattern in patterns if pattern.confidence >= threshold]

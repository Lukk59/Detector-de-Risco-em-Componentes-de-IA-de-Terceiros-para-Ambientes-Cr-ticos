"""Soma e normaliza as notas."""

from app.domain.entities import ComponentInput, CriterionScore
from app.domain.rules import apply_context_penalty


MAX_CRITERIA_SCORE = 60


def calculate_final_score(component: ComponentInput, criteria: list[CriterionScore]) -> int:
    # Converte a soma das notas para uma escala de 0 a 100.
    raw_sum = sum(item.score for item in criteria)
    normalized = round((raw_sum / MAX_CRITERIA_SCORE) * 100)
    final_score = apply_context_penalty(component, normalized)
    return max(0, min(final_score, 100))

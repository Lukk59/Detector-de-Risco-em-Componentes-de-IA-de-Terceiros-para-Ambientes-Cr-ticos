"""Transforma pontuação em nível de risco e recomendação."""

from app.domain.enums import Recommendation, RiskLevel


def classify_risk(score: int) -> RiskLevel:
    # Faixas simples deixam a demo fácil de explicar.
    if score >= 70:
        return RiskLevel.LOW
    if score >= 40:
        return RiskLevel.MEDIUM
    return RiskLevel.HIGH


def recommend_action(risk_level: RiskLevel) -> Recommendation:
    # A recomendação segue o nível de risco.
    if risk_level is RiskLevel.LOW:
        return Recommendation.APPROVE
    if risk_level is RiskLevel.MEDIUM:
        return Recommendation.REVIEW
    return Recommendation.BLOCK

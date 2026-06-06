"""Testa as faixas de classificação."""

from app.domain.classifier import classify_risk
from app.domain.enums import RiskLevel


def test_classify_high():
    # Score baixo indica risco alto.
    assert classify_risk(30) == RiskLevel.HIGH


def test_classify_medium():
    # A faixa intermediária deve ser estável.
    assert classify_risk(62) == RiskLevel.MEDIUM


def test_classify_low():
    # Score forte vira risco baixo.
    assert classify_risk(88) == RiskLevel.LOW

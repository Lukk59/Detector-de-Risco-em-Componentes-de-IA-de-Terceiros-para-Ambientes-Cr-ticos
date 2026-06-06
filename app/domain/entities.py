"""Modelos centrais do projeto.

Os comentários são curtos para deixar o código mais fácil de apresentar.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field, HttpUrl, field_validator

from app.domain.enums import ComponentType, Recommendation, RiskLevel


class ComponentInput(BaseModel):
    """Dados que chegam pela tela de cadastro."""

    name: str = Field(..., min_length=2, max_length=120)
    version: str = Field(..., min_length=1, max_length=40)
    component_type: ComponentType
    license_name: str = Field(..., min_length=2, max_length=80)
    source_url: HttpUrl
    last_update: date
    has_checksum: bool = False
    has_model_card: bool = False
    has_known_dependencies: bool = False
    critical_context: bool = False

    @field_validator("name", "version", "license_name")
    @classmethod
    def strip_text(cls, value: str) -> str:
        # Espaço perdido aqui só atrapalha a validação.
        return value.strip()


class CriterionScore(BaseModel):
    """Nota por critério da análise."""

    label: str
    score: int = Field(..., ge=0, le=10)


class VerificationCheck(BaseModel):
    """Resultado de uma conferência externa por campo."""

    field: str
    status: str
    severity: str
    message: str
    provided_value: Optional[str] = None
    official_value: Optional[str] = None


class VerificationResult(BaseModel):
    """Saída da etapa de verificação externa."""

    ok: bool
    can_continue: bool
    source: str
    normalized_name: Optional[str] = None
    official_version: Optional[str] = None
    official_license: Optional[str] = None
    official_last_update: Optional[date] = None
    official_has_model_card: Optional[bool] = None
    official_source_url: Optional[str] = None
    checks: list[VerificationCheck] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class AnalysisResult(BaseModel):
    """Resultado final mostrado ao usuário."""

    id: Optional[int] = None
    component_name: str
    component_version: str
    component_type: str
    score: int = Field(..., ge=0, le=100)
    risk_level: RiskLevel
    recommendation: Recommendation
    summary_line: str
    justification: str
    criteria_scores: list[CriterionScore]
    created_at: datetime


class AnalysisHistoryItem(BaseModel):
    """Item enxuto para a tela de histórico."""

    id: int
    component_name: str
    component_type: str
    score: int
    risk_level: RiskLevel
    created_at: datetime


class AnalysisOutcome(BaseModel):
    """Empacota a verificação e o resultado da análise."""

    verification: VerificationResult
    result: Optional[AnalysisResult] = None

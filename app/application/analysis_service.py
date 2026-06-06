"""Serviço principal da análise."""

from __future__ import annotations

from datetime import UTC, datetime

from app.domain.classifier import classify_risk, recommend_action
from app.domain.entities import AnalysisOutcome, AnalysisResult, ComponentInput, VerificationResult
from app.domain.justification import build_justification, build_summary_line
from app.domain.rules import evaluate_all
from app.domain.scorer import calculate_final_score
from app.infrastructure.repositories import AnalysisRepository
from app.infrastructure.verifiers.registry_router import ExternalVerificationService


class AnalysisService:
    """Orquestra verificação externa e análise de risco."""

    def __init__(
        self,
        repository: AnalysisRepository | None = None,
        verifier: ExternalVerificationService | None = None,
    ) -> None:
        self.repository = repository or AnalysisRepository()
        self.verifier = verifier or ExternalVerificationService()

    def _apply_verified_values(self, component: ComponentInput, verification: VerificationResult) -> ComponentInput:
        # Quando a fonte oficial devolve um dado melhor, eu prefiro ele.
        updates: dict[str, object] = {}
        if verification.normalized_name:
            updates["name"] = verification.normalized_name
        if verification.official_version:
            updates["version"] = verification.official_version
        if verification.official_license:
            updates["license_name"] = verification.official_license
        if verification.official_last_update:
            updates["last_update"] = verification.official_last_update
        if verification.official_has_model_card is not None:
            updates["has_model_card"] = verification.official_has_model_card
        if verification.official_source_url:
            updates["source_url"] = verification.official_source_url
        if not updates:
            return component
        merged = component.model_dump(mode="json")
        merged.update(updates)
        return ComponentInput.model_validate(merged)

    def analyze(self, component: ComponentInput) -> AnalysisOutcome:
        # Primeiro vem a conferência externa. Sem isso, o score perde valor.
        verification = self.verifier.verify(component)
        if not verification.can_continue:
            return AnalysisOutcome(verification=verification, result=None)

        trusted_component = self._apply_verified_values(component, verification)
        criteria = evaluate_all(trusted_component)
        score = calculate_final_score(trusted_component, criteria)
        risk = classify_risk(score)
        recommendation = recommend_action(risk)
        summary = build_summary_line(trusted_component, criteria)
        justification = build_justification(trusted_component, criteria, risk)

        result = AnalysisResult(
            component_name=trusted_component.name,
            component_version=trusted_component.version,
            component_type=trusted_component.component_type.value,
            score=score,
            risk_level=risk,
            recommendation=recommendation,
            summary_line=summary,
            justification=justification,
            criteria_scores=criteria,
            created_at=datetime.now(UTC),
        )
        result.id = self.repository.save(result)
        return AnalysisOutcome(verification=verification, result=result)

    def get_result(self, analysis_id: int) -> AnalysisResult | None:
        # Busca um resultado já salvo.
        return self.repository.get_by_id(analysis_id)

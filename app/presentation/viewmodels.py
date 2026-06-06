"""Funções auxiliares para as telas."""

from __future__ import annotations

from datetime import datetime, timezone

from app.domain.entities import AnalysisHistoryItem, AnalysisOutcome, AnalysisResult


def relative_date(dt: datetime) -> str:
    # Texto curto para o histórico.
    now = datetime.now(timezone.utc if dt.tzinfo else None)
    delta = now - dt
    days = delta.days
    if days <= 0:
        return "hoje"
    if days == 1:
        return "ontem"
    return f"há {days} dias"


def result_to_export(result: AnalysisResult) -> dict:
    # Estrutura pronta para exportação JSON.
    return result.model_dump(mode="json")


def outcome_to_export(outcome: AnalysisOutcome) -> dict:
    # A API mostra verificação sempre; score só aparece quando liberar.
    payload = {
        "verification": outcome.verification.model_dump(mode="json"),
        "can_continue": outcome.verification.can_continue,
    }
    if outcome.result:
        payload["analysis"] = outcome.result.model_dump(mode="json")
    return payload


def history_item_to_card(item: AnalysisHistoryItem) -> dict:
    # Deixa o template mais simples.
    return {
        "id": item.id,
        "name": item.component_name,
        "type": item.component_type,
        "score": item.score,
        "risk": item.risk_level.value,
        "date_text": relative_date(item.created_at),
    }

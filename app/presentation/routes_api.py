"""Rotas de API para integração e testes."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.application.analysis_service import AnalysisService
from app.application.history_service import HistoryService
from app.domain.entities import ComponentInput
from app.presentation.viewmodels import outcome_to_export, result_to_export

router = APIRouter(prefix="/api", tags=["api"])
analysis_service = AnalysisService()
history_service = HistoryService()


@router.post("/analyze")
def analyze_component(payload: ComponentInput):
    # Aqui a API devolve a verificação e só inclui score quando liberar.
    outcome = analysis_service.analyze(payload)
    return outcome_to_export(outcome)


@router.get("/analyses/{analysis_id}")
def get_analysis(analysis_id: int):
    # Retorna um resultado salvo.
    result = analysis_service.get_result(analysis_id)
    if not result:
        raise HTTPException(status_code=404, detail="Análise não encontrada")
    return result_to_export(result)


@router.get("/history")
def list_history():
    # Lista rápida para consumo externo.
    return [item.model_dump(mode="json") for item in history_service.list_recent()]

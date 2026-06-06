"""Testa o fluxo completo da análise."""

from datetime import date

from app.application.analysis_service import AnalysisService
from app.domain.entities import ComponentInput
from app.domain.enums import ComponentType
from app.infrastructure.database import initialize_database
from app.infrastructure.repositories import AnalysisRepository


def test_analysis_generates_result(monkeypatch, tmp_path):
    # Usa um banco temporário só para este teste.
    temp_db = tmp_path / "analysis.db"
    monkeypatch.setattr("app.config.DB_PATH", temp_db, raising=False)
    monkeypatch.setattr("app.infrastructure.database.DB_PATH", temp_db, raising=False)
    initialize_database()

    service = AnalysisService(repository=AnalysisRepository())
    component = ComponentInput(
        name="transformers",
        version="4.38.2",
        component_type=ComponentType.LIBRARY,
        license_name="Apache 2.0",
        source_url="https://pypi.org/project/transformers/",
        last_update=date(2024, 12, 15),
        has_checksum=True,
        has_model_card=False,
        has_known_dependencies=True,
        critical_context=False,
    )
    outcome = service.analyze(component)

    assert outcome.result is not None
    assert outcome.result.id is not None
    assert 0 <= outcome.result.score <= 100
    assert outcome.result.justification
    assert len(outcome.result.criteria_scores) == 6
    assert outcome.verification.can_continue is True


def test_analysis_blocks_when_verification_fails(monkeypatch, tmp_path):
    # Se a fonte oficial reprovar, o score nem deve existir.
    temp_db = tmp_path / "analysis.db"
    monkeypatch.setattr("app.config.DB_PATH", temp_db, raising=False)
    monkeypatch.setattr("app.infrastructure.database.DB_PATH", temp_db, raising=False)
    initialize_database()

    service = AnalysisService(repository=AnalysisRepository())
    component = ComponentInput(
        name="transformerss",
        version="4.38.2",
        component_type=ComponentType.LIBRARY,
        license_name="Apache 2.0",
        source_url="https://pypi.org/project/transformerss/",
        last_update=date(2024, 12, 15),
    )
    outcome = service.analyze(component)

    assert outcome.result is None
    assert outcome.verification.can_continue is False
    assert outcome.verification.errors

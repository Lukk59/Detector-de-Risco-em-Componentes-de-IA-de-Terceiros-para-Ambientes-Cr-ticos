"""Configura ambiente isolado para os testes."""

from __future__ import annotations

import tempfile
from datetime import date
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.domain.entities import VerificationResult
from app.infrastructure.verifiers.common import finalize_result, make_check


@pytest.fixture(autouse=True)
def fake_external_verification(monkeypatch):
    # Aqui eu simulo a verificação externa para o teste não depender da internet.
    def _fake_verify(self, component):
        if component.name == "transformerss":
            return finalize_result(
                "PyPI",
                [
                    make_check(
                        field="name",
                        status="error",
                        severity="blocking",
                        message="Nome não encontrado na fonte oficial.",
                        provided_value=component.name,
                    )
                ],
            )

        if component.version == "9.99.99":
            return finalize_result(
                "PyPI",
                [
                    make_check(
                        field="version",
                        status="error",
                        severity="blocking",
                        message="Versão informada não existe no registro oficial.",
                        provided_value=component.version,
                    )
                ],
                normalized_name=component.name,
            )

        checks = [
            make_check("name", "ok", "info", "Nome encontrado na fonte oficial.", component.name, component.name),
            make_check("version", "ok", "info", "Versão encontrada na fonte oficial.", component.version, component.version),
            make_check("source_url", "ok", "info", "Origem compatível com a fonte oficial.", str(component.source_url), str(component.source_url)),
        ]

        official_license = component.license_name
        official_date = component.last_update
        official_card = component.has_model_card

        # Este cenário foi feito para forçar score baixo e diferente.
        if component.name == "legacy-ai":
            official_license = "desconhecida"
            official_date = date(2020, 1, 1)
            checks.append(make_check("license", "warning", "warning", "Licença pouco clara na fonte oficial.", component.license_name, official_license))
        else:
            checks.append(make_check("license", "ok", "info", "Licença compatível com a fonte oficial.", component.license_name, official_license))

        return VerificationResult(
            ok=True,
            can_continue=True,
            source="Fake Registry",
            normalized_name=component.name,
            official_version=component.version,
            official_license=official_license,
            official_last_update=official_date,
            official_has_model_card=official_card,
            official_source_url=str(component.source_url),
            checks=checks,
            errors=[],
            warnings=[item.message for item in checks if item.severity == "warning"],
        )

    monkeypatch.setattr("app.infrastructure.verifiers.registry_router.ExternalVerificationService.verify", _fake_verify)


@pytest.fixture()
def client(monkeypatch):
    # Cada teste usa um banco limpo.
    with tempfile.TemporaryDirectory() as tmp:
        temp_db = Path(tmp) / "test.db"
        monkeypatch.setattr("app.config.DB_PATH", temp_db, raising=False)
        monkeypatch.setattr("app.infrastructure.database.DB_PATH", temp_db, raising=False)
        from app.infrastructure.database import initialize_database
        initialize_database()
        from app.main import app
        yield TestClient(app)

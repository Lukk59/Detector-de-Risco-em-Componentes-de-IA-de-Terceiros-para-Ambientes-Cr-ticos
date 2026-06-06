"""Blocos compartilhados pelos verificadores externos."""

from __future__ import annotations

from datetime import date, datetime
from typing import Optional
from urllib.parse import urlparse

import httpx

from app.domain.entities import VerificationCheck, VerificationResult

TIMEOUT = httpx.Timeout(8.0, connect=4.0)
USER_AGENT = "DetectorRiscoIA/1.0"


def build_client() -> httpx.Client:
    # Um client simples já resolve bem para esse MVP.
    return httpx.Client(timeout=TIMEOUT, headers={"User-Agent": USER_AGENT})


def parse_iso_date(value: Optional[str]) -> Optional[date]:
    # Algumas APIs mandam data com hora; aqui eu corto para o dia.
    if not value:
        return None
    cleaned = value.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(cleaned).date()
    except ValueError:
        return None


def host_of(url: str) -> str:
    # O host ajuda muito na comparação da origem.
    return (urlparse(url).hostname or "").lower()


def same_host(left: Optional[str], right: Optional[str]) -> bool:
    # Comparo hosts porque URL completa quase sempre varia.
    if not left or not right:
        return False
    return host_of(left) == host_of(right)


def make_check(
    field: str,
    status: str,
    severity: str,
    message: str,
    provided_value: Optional[str] = None,
    official_value: Optional[str] = None,
) -> VerificationCheck:
    # Esse helper evita repetir muita estrutura.
    return VerificationCheck(
        field=field,
        status=status,
        severity=severity,
        message=message,
        provided_value=provided_value,
        official_value=official_value,
    )


def finalize_result(
    source: str,
    checks: list[VerificationCheck],
    *,
    normalized_name: Optional[str] = None,
    official_version: Optional[str] = None,
    official_license: Optional[str] = None,
    official_last_update: Optional[date] = None,
    official_has_model_card: Optional[bool] = None,
    official_source_url: Optional[str] = None,
) -> VerificationResult:
    # Erro bloqueante corta o fluxo; aviso só fica registrado.
    errors = [item.message for item in checks if item.severity == "blocking"]
    warnings = [item.message for item in checks if item.severity == "warning"]
    can_continue = not errors
    return VerificationResult(
        ok=can_continue,
        can_continue=can_continue,
        source=source,
        normalized_name=normalized_name,
        official_version=official_version,
        official_license=official_license,
        official_last_update=official_last_update,
        official_has_model_card=official_has_model_card,
        official_source_url=official_source_url,
        checks=checks,
        errors=errors,
        warnings=warnings,
    )

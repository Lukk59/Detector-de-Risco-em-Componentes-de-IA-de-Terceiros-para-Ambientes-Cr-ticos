"""Verificador para bibliotecas Python no PyPI."""

from __future__ import annotations

import re
from typing import Any

from app.domain.entities import ComponentInput, VerificationResult
from app.infrastructure.verifiers.common import build_client, finalize_result, make_check, parse_iso_date, same_host


# Padroniza nomes de licença para evitar falso negativo bobo.
def normalize_license(value: str | None) -> str:
    if not value:
        return ""

    text = value.strip().lower()
    text = re.sub(r"[^a-z0-9]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()

    aliases = {
        "apache 2 0": "apache-2.0",
        "apache 2 0 license": "apache-2.0",
        "apache license 2 0": "apache-2.0",
        "apache software license apache 2 0 license": "apache-2.0",
        "apache software license": "apache-2.0",
        "mit": "mit",
        "mit license": "mit",
        "bsd": "bsd",
        "bsd license": "bsd",
        "bsd 3 clause": "bsd-3-clause",
        "bsd 3 clause license": "bsd-3-clause",
        "bsd 3 clause new or revised license": "bsd-3-clause",
        "proprietary": "proprietary",
        "proprietaria": "proprietary",
    }
    return aliases.get(text, text)


# Compara licença com tolerância para nomes equivalentes.
def licenses_match(left: str | None, right: str | None) -> bool:
    left_norm = normalize_license(left)
    right_norm = normalize_license(right)
    if not left_norm or not right_norm:
        return False
    if left_norm == right_norm:
        return True
    # Apache 2.0 vs Apache 2.0 License etc.
    if left_norm.startswith("apache-2.0") and right_norm.startswith("apache-2.0"):
        return True
    return False


class PyPIVerifier:
    """Confere nome, versão e metadados básicos no PyPI."""

    source_name = "PyPI"

    def verify(self, component: ComponentInput) -> VerificationResult:
        checks = []
        with build_client() as client:
            response = client.get(f"https://pypi.org/pypi/{component.name}/json")

        if response.status_code != 200:
            checks.append(
                make_check(
                    field="name",
                    status="error",
                    severity="blocking",
                    message="Nome não encontrado no PyPI.",
                    provided_value=component.name,
                )
            )
            return finalize_result(self.source_name, checks)

        payload: dict[str, Any] = response.json()
        info = payload.get("info", {})
        releases = payload.get("releases", {})
        urls = payload.get("urls", [])

        normalized_name = info.get("name") or component.name
        official_license = info.get("license") or None
        official_source_url = (
            info.get("project_url")
            or info.get("home_page")
            or info.get("package_url")
            or f"https://pypi.org/project/{normalized_name}/"
        )

        latest_upload = None
        for file_info in urls:
            latest_upload = parse_iso_date(file_info.get("upload_time_iso_8601")) or latest_upload

        checks.append(
            make_check(
                field="name",
                status="ok",
                severity="info",
                message="Componente encontrado no PyPI.",
                provided_value=component.name,
                official_value=normalized_name,
            )
        )

        if component.version in releases:
            checks.append(
                make_check(
                    field="version",
                    status="ok",
                    severity="info",
                    message="Versão encontrada no PyPI.",
                    provided_value=component.version,
                    official_value=component.version,
                )
            )
        else:
            checks.append(
                make_check(
                    field="version",
                    status="error",
                    severity="blocking",
                    message="Versão informada não existe no PyPI.",
                    provided_value=component.version,
                )
            )

        if official_license and licenses_match(component.license_name, official_license):
            checks.append(
                make_check(
                    field="license",
                    status="ok",
                    severity="info",
                    message="Licença compatível com a fonte oficial.",
                    provided_value=component.license_name,
                    official_value=official_license,
                )
            )
        elif official_license:
            checks.append(
                make_check(
                    field="license",
                    status="error",
                    severity="blocking",
                    message="Licença divergente da informada no PyPI.",
                    provided_value=component.license_name,
                    official_value=official_license,
                )
            )
        else:
            checks.append(
                make_check(
                    field="license",
                    status="warning",
                    severity="warning",
                    message="PyPI não retornou licença clara para esse pacote.",
                    provided_value=component.license_name,
                )
            )

        if same_host(str(component.source_url), official_source_url) or "pypi.org" in str(component.source_url):
            checks.append(
                make_check(
                    field="source_url",
                    status="ok",
                    severity="info",
                    message="Origem compatível com a fonte oficial.",
                    provided_value=str(component.source_url),
                    official_value=official_source_url,
                )
            )
        else:
            checks.append(
                make_check(
                    field="source_url",
                    status="error",
                    severity="blocking",
                    message="Origem informada não bate com a fonte oficial do pacote.",
                    provided_value=str(component.source_url),
                    official_value=official_source_url,
                )
            )

        if latest_upload and component.last_update == latest_upload:
            checks.append(
                make_check(
                    field="last_update",
                    status="ok",
                    severity="info",
                    message="Data compatível com o release consultado.",
                    provided_value=str(component.last_update),
                    official_value=str(latest_upload),
                )
            )
        elif latest_upload:
            checks.append(
                make_check(
                    field="last_update",
                    status="warning",
                    severity="warning",
                    message="A data informada difere da mais recente retornada pelo PyPI.",
                    provided_value=str(component.last_update),
                    official_value=str(latest_upload),
                )
            )

        return finalize_result(
            self.source_name,
            checks,
            normalized_name=normalized_name,
            official_version=component.version if component.version in releases else None,
            official_license=official_license,
            official_last_update=latest_upload,
            official_source_url=official_source_url,
        )

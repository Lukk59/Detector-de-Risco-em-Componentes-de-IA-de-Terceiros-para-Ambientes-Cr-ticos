"""Verificador do Hugging Face Hub."""

from __future__ import annotations

import re
from typing import Any
from urllib.parse import urlparse

from app.domain.entities import ComponentInput, VerificationResult
from app.infrastructure.verifiers.common import build_client, finalize_result, make_check, parse_iso_date


def normalize_license(value: str | None) -> str:
    """Padroniza texto de licença para evitar falso negativo."""
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
        "apache-2.0": "apache-2.0",
        "mit": "mit",
        "mit license": "mit",
        "bsd 3 clause": "bsd-3-clause",
        "bsd 3 clause license": "bsd-3-clause",
        "bsd 3 clause new or revised license": "bsd-3-clause",
        "cc by sa 4 0": "cc-by-sa-4.0",
        "cc by sa 4 0 license": "cc-by-sa-4.0",
        "cc-by-sa-4.0": "cc-by-sa-4.0",
        "proprietary": "proprietary",
        "proprietaria": "proprietary",
    }
    return aliases.get(text, text)


def licenses_match(left: str | None, right: str | None) -> bool:
    """Compara duas licenças já normalizadas."""
    left_norm = normalize_license(left)
    right_norm = normalize_license(right)
    if not left_norm or not right_norm:
        return False
    if left_norm == right_norm:
        return True
    if left_norm.startswith("apache-2.0") and right_norm.startswith("apache-2.0"):
        return True
    return False


class HuggingFaceVerifier:
    """Confere modelos e datasets no Hugging Face Hub."""

    source_name = "Hugging Face Hub"

    def verify(self, component: ComponentInput) -> VerificationResult:
        checks = []

        component_type_raw = getattr(component.component_type, "value", component.component_type)
        component_type = self._normalize_component_type(str(component_type_raw))

        if component_type == "dataset":
            endpoint = f"https://huggingface.co/api/datasets/{component.name}"
        else:
            endpoint = f"https://huggingface.co/api/models/{component.name}"

        print("TIPO RECEBIDO:", component_type_raw)
        print("TIPO NORMALIZADO:", component_type)
        print("NOME RECEBIDO:", component.name)
        print("URL RECEBIDA:", component.source_url)
        print("ENDPOINT HF:", endpoint)

        try:
            with build_client() as client:
                response = client.get(endpoint, follow_redirects=True)

            print("STATUS HF:", response.status_code)
            print("URL FINAL HF:", str(response.url))
            print("RESPOSTA HF:", response.text[:500])

        except Exception as exc:
            print("ERRO NA REQUISIÇÃO HF:", repr(exc))
            checks.append(
                make_check(
                    field="name",
                    status="error",
                    severity="blocking",
                    message=f"Falha ao consultar o Hugging Face Hub: {str(exc)}",
                    provided_value=component.name,
                )
            )
            return finalize_result(self.source_name, checks)

        if response.status_code != 200:
            checks.append(
                make_check(
                    field="name",
                    status="error",
                    severity="blocking",
                    message="Repositório não encontrado no Hugging Face Hub.",
                    provided_value=component.name,
                )
            )
            return finalize_result(self.source_name, checks)

        try:
            data: dict[str, Any] = response.json()
        except Exception as exc:
            print("ERRO AO LER JSON HF:", repr(exc))
            checks.append(
                make_check(
                    field="name",
                    status="error",
                    severity="blocking",
                    message=f"Resposta inválida do Hugging Face Hub: {str(exc)}",
                    provided_value=component.name,
                )
            )
            return finalize_result(self.source_name, checks)

        official_id = str(data.get("id") or component.name)

        # Ajusta o caminho esperado com base no id oficial canônico.
        if component_type == "dataset":
            expected_path = f"/datasets/{official_id}".lower()
        else:
            expected_path = f"/{official_id}".lower()

        official_license = self._extract_license(data)
        official_last_update = parse_iso_date(data.get("lastModified"))
        official_has_model_card = self._extract_model_card_flag(data)
        official_source_url = f"https://huggingface.co{expected_path}"

        print("OFFICIAL ID:", official_id)
        print("EXPECTED PATH:", expected_path)
        print("OFFICIAL LICENSE:", official_license)
        print("OFFICIAL LAST UPDATE:", official_last_update)
        print("OFFICIAL MODEL CARD:", official_has_model_card)
        print("OFFICIAL SOURCE URL:", official_source_url)

        checks.append(
            make_check(
                field="name",
                status="ok",
                severity="info",
                message="Repositório encontrado no Hugging Face Hub.",
                provided_value=component.name,
                official_value=official_id,
            )
        )

        source_matches = self._source_matches(str(component.source_url), expected_path)
        print("SOURCE MATCHES:", source_matches)

        if source_matches:
            checks.append(
                make_check(
                    field="source_url",
                    status="ok",
                    severity="info",
                    message="Origem compatível com o repositório oficial.",
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
                    message="Origem incompatível com o repositório oficial.",
                    provided_value=str(component.source_url),
                    official_value=official_source_url,
                )
            )

        informed_version = (component.version or "").strip().lower()
        print("INFORMED VERSION:", informed_version)

        if informed_version in {"main", "master"}:
            checks.append(
                make_check(
                    field="version",
                    status="ok",
                    severity="info",
                    message="Versão informada aceita para o repositório.",
                    provided_value=component.version,
                    official_value="main",
                )
            )
            official_version = "main"
        else:
            checks.append(
                make_check(
                    field="version",
                    status="warning",
                    severity="warning",
                    message="A versão informada não pôde ser confirmada diretamente no Hugging Face Hub.",
                    provided_value=component.version,
                    official_value="main",
                )
            )
            official_version = "main"

        if official_license:
            print("LICENSE MATCH:", licenses_match(component.license_name, official_license))
            if licenses_match(component.license_name, official_license):
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
            else:
                checks.append(
                    make_check(
                        field="license",
                        status="error",
                        severity="blocking",
                        message="Licença divergente da informada na fonte oficial.",
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
                    message="Licença não retornada claramente pelo Hugging Face Hub.",
                    provided_value=component.license_name,
                )
            )

        if official_last_update:
            checks.append(
                make_check(
                    field="last_update",
                    status="ok",
                    severity="info",
                    message="Data de atualização obtida na fonte oficial.",
                    provided_value=str(component.last_update),
                    official_value=str(official_last_update),
                )
            )
        else:
            checks.append(
                make_check(
                    field="last_update",
                    status="warning",
                    severity="warning",
                    message="Data de atualização não retornada claramente pela fonte oficial.",
                    provided_value=str(component.last_update),
                )
            )

        if component_type == "model":
            if component.has_model_card and official_has_model_card is False:
                checks.append(
                    make_check(
                        field="model_card",
                        status="error",
                        severity="blocking",
                        message="Model card marcado pelo usuário, mas não confirmado na fonte oficial.",
                        provided_value=str(component.has_model_card),
                        official_value=str(official_has_model_card),
                    )
                )
            elif official_has_model_card:
                checks.append(
                    make_check(
                        field="model_card",
                        status="ok",
                        severity="info",
                        message="Model card identificado na fonte oficial.",
                        provided_value=str(component.has_model_card),
                        official_value=str(official_has_model_card),
                    )
                )
            else:
                checks.append(
                    make_check(
                        field="model_card",
                        status="warning",
                        severity="warning",
                        message="Model card não foi confirmado claramente na fonte oficial.",
                        provided_value=str(component.has_model_card),
                        official_value=str(official_has_model_card),
                    )
                )

        return finalize_result(
            self.source_name,
            checks,
            normalized_name=official_id,
            official_version=official_version,
            official_license=official_license,
            official_last_update=official_last_update,
            official_has_model_card=official_has_model_card,
            official_source_url=official_source_url,
        )

    def _normalize_component_type(self, value: str) -> str:
        text = value.strip().lower()
        if "dataset" in text:
            return "dataset"
        return "model"

    def _source_matches(self, source_url: str, expected_path: str) -> bool:
        try:
            parsed = urlparse(source_url.strip())
            domain = parsed.netloc.lower()
            path = parsed.path.rstrip("/").lower()

            print("SOURCE DOMAIN:", domain)
            print("SOURCE PATH:", path)
            print("EXPECTED SOURCE PATH:", expected_path)

            return domain in {"huggingface.co", "www.huggingface.co"} and path == expected_path
        except Exception as exc:
            print("ERRO NO _source_matches:", repr(exc))
            return False

    def _extract_license(self, data: dict[str, Any]) -> str | None:
        card_data = data.get("cardData") or {}
        if isinstance(card_data, dict):
            license_value = card_data.get("license")
            if license_value:
                return str(license_value)

        license_value = data.get("license")
        if license_value:
            return str(license_value)

        tags = data.get("tags") or []
        for tag in tags:
            if isinstance(tag, str) and tag.startswith("license:"):
                return tag.split(":", 1)[1]

        return None

    def _extract_model_card_flag(self, data: dict[str, Any]) -> bool | None:
        card_data = data.get("cardData")
        if isinstance(card_data, dict) and len(card_data) > 0:
            return True

        siblings = data.get("siblings") or []
        if isinstance(siblings, list):
            for item in siblings:
                if isinstance(item, dict):
                    rfilename = str(item.get("rfilename", "")).lower()
                    if rfilename == "readme.md":
                        return True

        return False
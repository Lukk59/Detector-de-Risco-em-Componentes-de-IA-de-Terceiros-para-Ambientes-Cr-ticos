"""Verificador para modelos e datasets no Hugging Face Hub."""

from __future__ import annotations

from typing import Any

from app.domain.entities import ComponentInput, VerificationResult
from app.domain.enums import ComponentType
from app.infrastructure.verifiers.common import build_client, finalize_result, host_of, make_check, parse_iso_date


class HuggingFaceVerifier:
    """Confere repositório, card e metadados no Hub."""

    source_name = "Hugging Face Hub"

    def verify(self, component: ComponentInput) -> VerificationResult:
        endpoint = "models" if component.component_type is ComponentType.MODEL else "datasets"
        checks = []

        with build_client() as client:
            response = client.get(f"https://huggingface.co/api/{endpoint}/{component.name}")

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

        payload: dict[str, Any] = response.json()
        normalized_name = payload.get("id") or component.name
        official_license = None
        card_data = payload.get("cardData") or {}
        if isinstance(card_data, dict):
            official_license = card_data.get("license")
        last_update = parse_iso_date(payload.get("lastModified"))
        siblings = payload.get("siblings") or []
        has_readme = any((item.get("rfilename") or "").lower() == "readme.md" for item in siblings if isinstance(item, dict))
        official_source_url = f"https://huggingface.co/{normalized_name}"

        checks.append(
            make_check(
                field="name",
                status="ok",
                severity="info",
                message="Repositório encontrado no Hugging Face Hub.",
                provided_value=component.name,
                official_value=normalized_name,
            )
        )

        if component.version and payload.get("sha"):
            checks.append(
                make_check(
                    field="version",
                    status="warning",
                    severity="warning",
                    message="O Hub trabalha mais com revisões e commits; a versão digitada foi mantida só como referência.",
                    provided_value=component.version,
                    official_value=str(payload.get("sha"))[:12],
                )
            )

        if host_of(str(component.source_url)) == "huggingface.co":
            checks.append(
                make_check(
                    field="source_url",
                    status="ok",
                    severity="info",
                    message="Origem compatível com o Hugging Face Hub.",
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
                    message="Origem informada não aponta para o Hugging Face Hub.",
                    provided_value=str(component.source_url),
                    official_value=official_source_url,
                )
            )

        if official_license and component.license_name.strip().lower() == str(official_license).strip().lower():
            checks.append(
                make_check(
                    field="license",
                    status="ok",
                    severity="info",
                    message="Licença compatível com o card do repositório.",
                    provided_value=component.license_name,
                    official_value=str(official_license),
                )
            )
        elif official_license:
            checks.append(
                make_check(
                    field="license",
                    status="error",
                    severity="blocking",
                    message="Licença divergente da encontrada no card do repositório.",
                    provided_value=component.license_name,
                    official_value=str(official_license),
                )
            )
        else:
            checks.append(
                make_check(
                    field="license",
                    status="warning",
                    severity="warning",
                    message="O repositório não expôs licença clara nos metadados do card.",
                    provided_value=component.license_name,
                )
            )

        if component.has_model_card and has_readme:
            checks.append(
                make_check(
                    field="model_card",
                    status="ok",
                    severity="info",
                    message="Card encontrado no repositório.",
                    provided_value="marcado",
                    official_value="README.md presente",
                )
            )
        elif component.has_model_card and not has_readme:
            checks.append(
                make_check(
                    field="model_card",
                    status="error",
                    severity="blocking",
                    message="O usuário marcou card, mas o repositório não expôs README.md.",
                    provided_value="marcado",
                    official_value="não encontrado",
                )
            )
        elif not component.has_model_card and has_readme:
            checks.append(
                make_check(
                    field="model_card",
                    status="warning",
                    severity="warning",
                    message="Existe card no repositório, mas o formulário não marcou esse item.",
                    provided_value="não marcado",
                    official_value="README.md presente",
                )
            )
        else:
            checks.append(
                make_check(
                    field="model_card",
                    status="warning",
                    severity="warning",
                    message="Card não identificado no repositório.",
                    provided_value="não marcado",
                    official_value="não encontrado",
                )
            )

        if last_update and component.last_update == last_update:
            checks.append(
                make_check(
                    field="last_update",
                    status="ok",
                    severity="info",
                    message="Data compatível com a última atualização do Hub.",
                    provided_value=str(component.last_update),
                    official_value=str(last_update),
                )
            )
        elif last_update:
            checks.append(
                make_check(
                    field="last_update",
                    status="warning",
                    severity="warning",
                    message="A data informada difere da última atualização do Hub.",
                    provided_value=str(component.last_update),
                    official_value=str(last_update),
                )
            )

        return finalize_result(
            self.source_name,
            checks,
            normalized_name=normalized_name,
            official_license=str(official_license) if official_license else None,
            official_last_update=last_update,
            official_has_model_card=has_readme,
            official_source_url=official_source_url,
        )

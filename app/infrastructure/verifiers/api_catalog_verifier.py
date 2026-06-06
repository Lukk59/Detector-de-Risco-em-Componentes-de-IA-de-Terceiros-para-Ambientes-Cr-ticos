"""Verificador simples para APIs comerciais conhecidas."""

from __future__ import annotations

from app.domain.entities import ComponentInput, VerificationResult
from app.infrastructure.verifiers.common import finalize_result, host_of, make_check


KNOWN_APIS = {
    "platform.openai.com": {"vendor": "OpenAI", "names": ("gpt", "openai", "embedding", "whisper")},
    "api.anthropic.com": {"vendor": "Anthropic", "names": ("claude", "anthropic")},
    "ai.google.dev": {"vendor": "Google", "names": ("gemini", "google")},
    "generativelanguage.googleapis.com": {"vendor": "Google", "names": ("gemini", "google")},
}


class ApiCatalogVerifier:
    """Usa uma allowlist local quando a API não expõe metadados ricos."""

    source_name = "Catálogo interno de APIs"

    def verify(self, component: ComponentInput) -> VerificationResult:
        checks = []
        host = host_of(str(component.source_url))
        catalog = KNOWN_APIS.get(host)
        if not catalog:
            checks.append(
                make_check(
                    field="source_url",
                    status="error",
                    severity="blocking",
                    message="Domínio da API não está no catálogo interno permitido.",
                    provided_value=str(component.source_url),
                )
            )
            return finalize_result(self.source_name, checks)

        checks.append(
            make_check(
                field="source_url",
                status="ok",
                severity="info",
                message="Domínio da API encontrado no catálogo interno.",
                provided_value=str(component.source_url),
                official_value=host,
            )
        )

        lower_name = component.name.lower()
        if any(token in lower_name for token in catalog["names"]):
            checks.append(
                make_check(
                    field="name",
                    status="ok",
                    severity="info",
                    message="Nome compatível com o fornecedor esperado.",
                    provided_value=component.name,
                    official_value=catalog["vendor"],
                )
            )
        else:
            checks.append(
                make_check(
                    field="name",
                    status="error",
                    severity="blocking",
                    message="Nome da API não parece compatível com o fornecedor informado pela origem.",
                    provided_value=component.name,
                    official_value=catalog["vendor"],
                )
            )

        checks.append(
            make_check(
                field="version",
                status="warning",
                severity="warning",
                message="API comercial não expôs versão verificável automaticamente neste MVP.",
                provided_value=component.version,
            )
        )

        checks.append(
            make_check(
                field="license",
                status="warning",
                severity="warning",
                message="Licença de API comercial exige validação contratual manual.",
                provided_value=component.license_name,
            )
        )

        return finalize_result(
            self.source_name,
            checks,
            normalized_name=component.name,
            official_source_url=str(component.source_url),
        )

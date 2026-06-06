"""Escolhe o verificador externo certo para cada caso."""

from __future__ import annotations

from urllib.parse import urlparse

from app.domain.entities import ComponentInput, VerificationResult
from app.domain.enums import ComponentType
from app.infrastructure.verifiers.api_catalog_verifier import ApiCatalogVerifier
from app.infrastructure.verifiers.github_verifier import GitHubVerifier
from app.infrastructure.verifiers.huggingface_verifier import HuggingFaceVerifier
from app.infrastructure.verifiers.pypi_verifier import PyPIVerifier
from app.infrastructure.verifiers.common import finalize_result, make_check


class ExternalVerificationService:
    """Roteia a checagem conforme tipo e origem."""

    def __init__(self) -> None:
        self.pypi = PyPIVerifier()
        self.huggingface = HuggingFaceVerifier()
        self.github = GitHubVerifier()
        self.api_catalog = ApiCatalogVerifier()

    def verify(self, component: ComponentInput) -> VerificationResult:
        host = (urlparse(str(component.source_url)).hostname or "").lower()

        if component.component_type is ComponentType.LIBRARY:
            if "github.com" in host:
                return self.github.verify(component)
            return self.pypi.verify(component)

        if component.component_type in {ComponentType.MODEL, ComponentType.DATASET}:
            if "huggingface.co" in host:
                return self.huggingface.verify(component)
            return finalize_result(
                "Sem verificador",
                [
                    make_check(
                        field="source_url",
                        status="error",
                        severity="blocking",
                        message="Modelos e datasets deste MVP precisam usar origem do Hugging Face Hub.",
                        provided_value=str(component.source_url),
                    )
                ],
            )

        if component.component_type is ComponentType.API:
            return self.api_catalog.verify(component)

        return finalize_result(
            "Sem verificador",
            [
                make_check(
                    field="component_type",
                    status="error",
                    severity="blocking",
                    message="Tipo de componente sem verificador configurado.",
                    provided_value=component.component_type.value,
                )
            ],
        )

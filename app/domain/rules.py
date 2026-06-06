
"""Regras de pontuação do domínio."""

from __future__ import annotations

from datetime import date
from urllib.parse import urlparse

from app.domain.entities import ComponentInput, CriterionScore
from app.domain.enums import ComponentType


TRUSTED_HOSTS = {
    "huggingface.co",
    "github.com",
    "pypi.org",
    "platform.openai.com",
    "kaggle.com",
    "scikit-learn.org",
    "pytorch.org",
    "tensorflow.org",
}
DOC_HINTS = ("docs", "documentation", "api", "reference", "model", "dataset", "card", "guide")
OPEN_LICENSES = ("apache", "mit", "bsd", "mpl", "gpl", "lgpl", "cc-by", "cc0")
RESTRICTED_LICENSES = ("propriet", "commercial", "custom", "restrit", "internal")
UNKNOWN_LICENSES = ("unknown", "desconhecida", "n/a", "nao informada")


def _host_text(component: ComponentInput) -> tuple[str, str]:
    # Aqui eu reaproveito a URL para enxergar melhor o host e o caminho.
    parsed = urlparse(str(component.source_url))
    return (parsed.hostname or "").lower(), parsed.path.lower()


def _name_text(component: ComponentInput) -> str:
    # Deixo tudo minúsculo porque facilita as comparações.
    return component.name.strip().lower()


def score_provenance(component: ComponentInput) -> CriterionScore:
    # Procedência olha domínio, https e se a URL parece oficial.
    host, path = _host_text(component)
    score = 3

    if component.source_url.scheme == "https":
        score += 2

    if any(host == trusted or host.endswith(f".{trusted}") for trusted in TRUSTED_HOSTS):
        score += 4

    if any(hint in path for hint in DOC_HINTS):
        score += 1

    if component.component_type is ComponentType.API and "openai" in host:
        score += 1
    elif component.component_type is ComponentType.LIBRARY and ("pypi.org" in host or "github.com" in host or "scikit-learn.org" in host):
        score += 1
    elif component.component_type is ComponentType.MODEL and "huggingface.co" in host:
        score += 1
    elif component.component_type is ComponentType.DATASET and ("kaggle.com" in host or "huggingface.co" in host):
        score += 1

    return CriterionScore(label="Procedência", score=max(0, min(score, 10)))


def score_integrity(component: ComponentInput) -> CriterionScore:
    # Hash pesa bastante, mas API costuma ter menos artefato para conferir.
    if component.has_checksum:
        score = 9
    elif component.component_type is ComponentType.API:
        score = 5
    else:
        score = 3
    return CriterionScore(label="Integridade", score=score)


def score_license(component: ComponentInput) -> CriterionScore:
    # Licença aberta ajuda, desconhecida derruba.
    value = component.license_name.strip().lower()
    if any(item in value for item in UNKNOWN_LICENSES):
        score = 2
    elif any(item in value for item in RESTRICTED_LICENSES):
        score = 6 if component.component_type is ComponentType.API else 5
    elif any(item in value for item in OPEN_LICENSES):
        score = 9
    else:
        score = 5
    return CriterionScore(label="Licença", score=score)


def score_ai_docs(component: ComponentInput) -> CriterionScore:
    # Documentação muda bastante conforme o tipo do componente.
    host, path = _host_text(component)
    has_doc_hint = any(hint in path for hint in DOC_HINTS)
    if component.component_type in {ComponentType.MODEL, ComponentType.DATASET}:
        score = 9 if component.has_model_card else 3
        if not component.has_model_card and has_doc_hint:
            score += 1
    elif component.component_type is ComponentType.API:
        score = 8 if has_doc_hint else 6
        if component.has_model_card:
            score += 1
    else:
        score = 7 if has_doc_hint else 5
        if component.has_model_card:
            score += 1
    return CriterionScore(label="Documentação de IA", score=max(0, min(score, 10)))


def score_maintenance(component: ComponentInput) -> CriterionScore:
    # Atualização recente conta mais, mas versão instável tira um pouco da nota.
    days = (date.today() - component.last_update).days
    version_text = component.version.lower()
    if days <= 90:
        score = 10
    elif days <= 365:
        score = 8
    elif days <= 730:
        score = 5
    else:
        score = 2

    if any(tag in version_text for tag in ("alpha", "beta", "rc", "dev")):
        score -= 1

    return CriterionScore(label="Manutenção e atualização", score=max(0, min(score, 10)))


def score_dependencies(component: ComponentInput) -> CriterionScore:
    # Dependências conhecidas ajudam. Alguns nomes famosos costumam ser mais pesados.
    name = _name_text(component)
    heavy_stack = ("transformers", "langchain", "autogen", "diffusers")
    if component.component_type is ComponentType.API:
        score = 8
    elif component.has_known_dependencies:
        score = 7
    else:
        score = 4

    if any(token in name for token in heavy_stack):
        score -= 1

    return CriterionScore(label="Dependências", score=max(0, min(score, 10)))


def apply_context_penalty(component: ComponentInput, base_score: int) -> int:
    # Contexto crítico pede mais conservadorismo mesmo no MVP.
    if component.critical_context:
        return max(0, base_score - 12)
    return base_score


def evaluate_all(component: ComponentInput) -> list[CriterionScore]:
    # A ordem fixa ajuda na leitura da tela e nos testes.
    return [
        score_provenance(component),
        score_integrity(component),
        score_license(component),
        score_ai_docs(component),
        score_maintenance(component),
        score_dependencies(component),
    ]

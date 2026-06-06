"""Testa regras isoladas do domínio."""

from datetime import date, timedelta

from app.domain.entities import ComponentInput
from app.domain.enums import ComponentType
from app.domain.rules import apply_context_penalty, score_ai_docs, score_integrity, score_license


def sample_component(**overrides):
    # Base reaproveitável para os testes.
    data = {
        "name": "transformers",
        "version": "4.38.2",
        "component_type": ComponentType.LIBRARY,
        "license_name": "Apache 2.0",
        "source_url": "https://huggingface.co/docs/transformers",
        "last_update": date.today() - timedelta(days=30),
        "has_checksum": True,
        "has_model_card": False,
        "has_known_dependencies": True,
        "critical_context": False,
    }
    data.update(overrides)
    return ComponentInput(**data)


def test_missing_checksum_lowers_score():
    # Sem hash, a nota precisa cair.
    with_hash = score_integrity(sample_component(has_checksum=True)).score
    without_hash = score_integrity(sample_component(has_checksum=False)).score
    assert with_hash > without_hash


def test_model_card_helps_model_docs():
    # Para modelo, model card pesa bastante.
    with_card = score_ai_docs(sample_component(component_type=ComponentType.MODEL, has_model_card=True)).score
    without_card = score_ai_docs(sample_component(component_type=ComponentType.MODEL, has_model_card=False)).score
    assert with_card > without_card


def test_unknown_license_is_worse():
    # Licença obscura precisa ser penalizada.
    known = score_license(sample_component(license_name="Apache 2.0")).score
    unknown = score_license(sample_component(license_name="desconhecida")).score
    assert known > unknown


def test_critical_context_applies_penalty():
    # Contexto crítico reduz o score final.
    normal = apply_context_penalty(sample_component(critical_context=False), 80)
    critical = apply_context_penalty(sample_component(critical_context=True), 80)
    assert normal > critical

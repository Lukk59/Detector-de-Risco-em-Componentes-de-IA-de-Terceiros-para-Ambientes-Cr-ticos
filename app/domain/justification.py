"""Gera textos explicáveis para a tela de resultado."""

from app.domain.entities import ComponentInput, CriterionScore
from app.domain.enums import RiskLevel


def build_summary_line(component: ComponentInput, criteria: list[CriterionScore]) -> str:
    # Texto curto para o topo do resultado.
    weak = [item.label for item in criteria if item.score <= 5]
    context = "Contexto crítico" if component.critical_context else "Contexto não-crítico"
    if weak:
        return f"{weak[0]} em atenção · {context}"
    return f"Critérios consistentes · {context}"


def build_justification(component: ComponentInput, criteria: list[CriterionScore], risk: RiskLevel) -> str:
    # Monta um texto humano e direto.
    strong = [item.label.lower() for item in criteria if item.score >= 8]
    weak = [item.label.lower() for item in criteria if item.score <= 5]

    parts = []
    if strong:
        parts.append(f"O componente apresenta boa avaliação em {', '.join(strong[:3])}.")
    if weak:
        parts.append(f"Os pontos que mais reduziram a confiança foram {', '.join(weak[:3])}.")
    if component.critical_context:
        parts.append("Como o uso informado é crítico, a análise aplicou uma penalização extra para ser mais conservadora.")
    parts.append(f"No estado atual, o risco foi classificado como {risk.value.lower()}.")
    return " ".join(parts)

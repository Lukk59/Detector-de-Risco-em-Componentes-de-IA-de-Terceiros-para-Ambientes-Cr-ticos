"""Rotas web e renderização das telas."""

from __future__ import annotations

from datetime import date
from json import dumps

from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, Response
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError

from app.application.analysis_service import AnalysisService
from app.application.history_service import HistoryService
from app.config import TEMPLATES_DIR
from app.domain.entities import ComponentInput
from app.domain.enums import ComponentType
from app.presentation.viewmodels import history_item_to_card

router = APIRouter(tags=["web"])
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
analysis_service = AnalysisService()
history_service = HistoryService()


def common_context(request: Request) -> dict:
    # Dados que várias telas usam juntos.
    return {
        "request": request,
        "component_types": [item.value for item in ComponentType],
        "today": date.today().isoformat(),
    }


FORM_LABELS = {
    "name": "Nome do componente",
    "version": "Versão",
    "component_type": "Tipo de componente",
    "license_name": "Licença",
    "source_url": "Origem / repositório",
    "last_update": "Data da última atualização",
}


def _friendly_validation_messages(exc: ValidationError) -> list[str]:
    # Traduz os erros do Pydantic para algo mais apresentável na tela.
    messages: list[str] = []
    for error in exc.errors(include_url=False):
        field_name = error.get("loc", ["campo"])[-1]
        field_label = FORM_LABELS.get(str(field_name), str(field_name))
        error_type = error.get("type", "")

        if error_type == "string_too_short":
            messages.append(f"{field_label} está curto demais.")
        elif error_type == "string_too_long":
            messages.append(f"{field_label} ficou maior do que o permitido.")
        elif error_type in {"url_parsing", "url_scheme", "url_type"}:
            messages.append(f"{field_label} precisa ser uma URL válida começando com http:// ou https://.")
        elif error_type in {"date_from_datetime_parsing", "date_parsing"}:
            messages.append(f"{field_label} precisa estar em uma data válida.")
        elif error_type == "enum":
            messages.append(f"{field_label} precisa ser escolhido na lista.")
        else:
            messages.append(f"Revise o campo {field_label.lower()}.")
    return list(dict.fromkeys(messages))


def _raw_form_data(
    name: str,
    version: str,
    component_type: str,
    license_name: str,
    source_url: str,
    last_update: str,
    has_checksum: str | None,
    has_model_card: str | None,
    has_known_dependencies: str | None,
    critical_context: str | None,
) -> dict:
    # Deixo os dados crus juntos porque isso ajuda no retorno da tela.
    return {
        "name": name,
        "version": version,
        "component_type": component_type,
        "license_name": license_name,
        "source_url": source_url,
        "last_update": last_update,
        "has_checksum": bool(has_checksum),
        "has_model_card": bool(has_model_card),
        "has_known_dependencies": bool(has_known_dependencies),
        "critical_context": bool(critical_context),
    }


@router.get("/", response_class=HTMLResponse)
def cadastro(request: Request):
    # Primeira tela do fluxo.
    context = common_context(request)
    context["form_data"] = {}
    context["error"] = None
    context["validation_details"] = []
    return templates.TemplateResponse(request, "cadastro.html", context)


@router.post("/analisar", response_class=HTMLResponse)
def analisar(
    request: Request,
    name: str = Form(""),
    version: str = Form(""),
    component_type: str = Form(""),
    license_name: str = Form(""),
    source_url: str = Form(""),
    last_update: str = Form(""),
    has_checksum: str | None = Form(None),
    has_model_card: str | None = Form(None),
    has_known_dependencies: str | None = Form(None),
    critical_context: str | None = Form(None),
):
    raw_data = _raw_form_data(
        name,
        version,
        component_type,
        license_name,
        source_url,
        last_update,
        has_checksum,
        has_model_card,
        has_known_dependencies,
        critical_context,
    )
    try:
        component = ComponentInput(**raw_data)
    except ValidationError as exc:
        context = common_context(request)
        context["error"] = "Não foi possível analisar. Corrija os campos destacados abaixo."
        context["form_data"] = raw_data
        context["validation_details"] = _friendly_validation_messages(exc)
        return templates.TemplateResponse(request, "cadastro.html", context)

    try:
        outcome = analysis_service.analyze(component)
    except Exception:
        context = common_context(request)
        context["error"] = "Falha ao consultar a fonte externa. Confira a internet e tente novamente."
        context["form_data"] = raw_data
        context["validation_details"] = []
        return templates.TemplateResponse(request, "cadastro.html", context, status_code=502)

    verification = outcome.verification
    if not verification.can_continue:
        return templates.TemplateResponse(
            request,
            "analise.html",
            {
                "request": request,
                "verification": verification,
                "verification_json": verification.model_dump(mode="json"),
                "result": None,
                "result_id": None,
                "can_continue": False,
                "blocked": True,
            },
        )

    return templates.TemplateResponse(
        request,
        "analise.html",
        {
            "request": request,
            "verification": verification,
            "verification_json": verification.model_dump(mode="json"),
            "result": outcome.result,
            "result_id": outcome.result.id if outcome.result else None,
            "can_continue": True,
            "blocked": False,
        },
    )


@router.get("/analise/{analysis_id}", response_class=HTMLResponse)
def tela_analise(request: Request, analysis_id: int):
    # Se a pessoa voltar na etapa 2, eu mostro uma visão resumida do que já passou.
    result = analysis_service.get_result(analysis_id)
    if not result:
        raise HTTPException(status_code=404, detail="Análise não encontrada")
    checklist = []
    for item in result.criteria_scores:
        status = "ok" if item.score >= 7 else "warning" if item.score >= 4 else "error"
        checklist.append(
            {
                "field": item.label,
                "status": status,
                "severity": "info" if status == "ok" else "warning",
                "message": f"Critério avaliado com nota {item.score}/10.",
                "provided_value": str(item.score),
                "official_value": None,
            }
        )
    return templates.TemplateResponse(
        request,
        "analise.html",
        {
            "request": request,
            "verification": {"source": "Resumo salvo", "checks": checklist, "errors": [], "warnings": []},
            "verification_json": {"ok": True, "source": "Resumo salvo", "checks": checklist, "blocking_errors": [], "warnings": []},
            "result": result,
            "result_id": result.id,
            "can_continue": True,
            "blocked": False,
        },
    )


@router.get("/resultado/{analysis_id}", response_class=HTMLResponse)
def resultado(request: Request, analysis_id: int):
    # Exibe a análise pronta.
    result = analysis_service.get_result(analysis_id)
    if not result:
        raise HTTPException(status_code=404, detail="Análise não encontrada")
    return templates.TemplateResponse(request, "resultado.html", {"request": request, "result": result})


@router.get("/resultado/{analysis_id}/export")
def export_result(analysis_id: int):
    # Exporta o resultado como arquivo baixável.
    result = analysis_service.get_result(analysis_id)
    if not result:
        raise HTTPException(status_code=404, detail="Análise não encontrada")
    payload = dumps(result.model_dump(mode="json"), ensure_ascii=False, indent=2)
    filename = f"analise-{analysis_id}.json"
    headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
    return Response(content=payload, media_type="application/json; charset=utf-8", headers=headers)


@router.get("/historico", response_class=HTMLResponse)
def historico(request: Request):
    # Mostra a lista de análises salvas.
    items = [history_item_to_card(item) for item in history_service.list_recent()]
    return templates.TemplateResponse(
        request,
        "historico.html",
        {"request": request, "items": items, "count": len(items)},
    )

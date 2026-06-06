"""Testa rotas principais da aplicação."""


def test_home_page_loads(client):
    # A tela inicial deve abrir normalmente.
    response = client.get("/")
    assert response.status_code == 200
    assert "Cadastro do componente" in response.text


def test_analyze_route_renders_verification_step(client):
    # Depois do POST, o fluxo cai na etapa 2 com a checagem externa.
    response = client.post(
        "/analisar",
        data={
            "name": "transformers",
            "version": "4.38.2",
            "component_type": "Biblioteca / Framework",
            "license_name": "Apache 2.0",
            "source_url": "https://pypi.org/project/transformers/",
            "last_update": "2024-12-15",
            "has_checksum": "on",
            "has_known_dependencies": "on",
        },
        follow_redirects=False,
    )
    assert response.status_code == 200
    assert "Verificação das informações fornecidas" in response.text
    assert "Ver resultado" in response.text


def test_verification_failure_blocks_next_step(client):
    # Quando o nome não bate com a fonte, a etapa 3 fica bloqueada.
    response = client.post(
        "/analisar",
        data={
            "name": "transformerss",
            "version": "4.38.2",
            "component_type": "Biblioteca / Framework",
            "license_name": "Apache 2.0",
            "source_url": "https://pypi.org/project/transformerss/",
            "last_update": "2024-12-15",
        },
    )
    assert response.status_code == 422
    assert "Voltar e corrigir" in response.text
    assert "Nome não encontrado na fonte oficial" in response.text


def test_invalid_form_returns_error_message(client):
    # Quando a entrada está errada, a tela precisa devolver um erro claro.
    response = client.post(
        "/analisar",
        data={
            "name": "a",
            "version": "",
            "component_type": "",
            "license_name": "x",
            "source_url": "abc",
            "last_update": "data-ruim",
        },
    )
    assert response.status_code == 422
    assert "Não foi possível analisar" in response.text
    assert "URL válida" in response.text or "url válida" in response.text.lower()


def test_history_page_loads(client):
    # O histórico deve responder mesmo vazio.
    response = client.get("/historico")
    assert response.status_code == 200
    assert "Historico" in response.text


def test_export_route_downloads_json(client):
    # Aqui eu gero uma análise e confiro se a exportação vem como arquivo.
    post = client.post(
        "/analisar",
        data={
            "name": "gpt-4o-mini",
            "version": "2024-07-18",
            "component_type": "API de IA",
            "license_name": "Proprietária",
            "source_url": "https://platform.openai.com/docs/models",
            "last_update": "2025-05-01",
            "critical_context": "on",
        },
    )
    assert post.status_code == 200
    assert "/resultado/" in post.text
    marker = '/resultado/'
    analysis_id = post.text.split(marker, 1)[1].split('"', 1)[0].split("/", 1)[0]

    response = client.get(f"/resultado/{analysis_id}/export")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/json")
    assert "attachment;" in response.headers["content-disposition"]
    assert '"component_name": "gpt-4o-mini"' in response.text


def test_api_returns_verification_and_analysis(client):
    # A API agora devolve verificação e análise separadas.
    response = client.post(
        "/api/analyze",
        json={
            "name": "transformers",
            "version": "4.38.2",
            "component_type": "Biblioteca / Framework",
            "license_name": "Apache 2.0",
            "source_url": "https://pypi.org/project/transformers/",
            "last_update": "2024-12-15",
            "has_checksum": True,
            "has_known_dependencies": True,
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["verification"]["can_continue"] is True
    assert "analysis" in payload


def test_api_blocked_case_has_no_analysis(client):
    # Se a verificação bloquear, a API não devolve score.
    response = client.post(
        "/api/analyze",
        json={
            "name": "transformerss",
            "version": "9.99.99",
            "component_type": "Biblioteca / Framework",
            "license_name": "Apache 2.0",
            "source_url": "https://pypi.org/project/transformerss/",
            "last_update": "2024-12-15",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["can_continue"] is False
    assert "analysis" not in payload


def test_different_inputs_generate_different_results(client):
    # Esse teste evita o problema de tudo sair com a mesma cara.
    first = client.post(
        "/api/analyze",
        json={
            "name": "transformers",
            "version": "4.38.2",
            "component_type": "Biblioteca / Framework",
            "license_name": "Apache 2.0",
            "source_url": "https://pypi.org/project/transformers/",
            "last_update": "2024-12-15",
            "has_checksum": True,
            "has_known_dependencies": True,
        },
    )
    second = client.post(
        "/api/analyze",
        json={
            "name": "legacy-ai",
            "version": "0.8-beta",
            "component_type": "Biblioteca / Framework",
            "license_name": "desconhecida",
            "source_url": "https://pypi.org/project/legacy-ai/",
            "last_update": "2020-01-01",
            "critical_context": True,
        },
    )

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["analysis"]["score"] != second.json()["analysis"]["score"]
    assert first.json()["analysis"]["risk_level"] != second.json()["analysis"]["risk_level"]

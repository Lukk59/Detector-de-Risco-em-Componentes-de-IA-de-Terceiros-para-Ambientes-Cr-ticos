"""Verificador para repositórios no GitHub."""

from __future__ import annotations

from typing import Any
from urllib.parse import urlparse

from app.domain.entities import ComponentInput, VerificationResult
from app.infrastructure.verifiers.common import build_client, finalize_result, make_check, parse_iso_date


class GitHubVerifier:
    """Confere existência do repositório e versão por tag/release."""

    source_name = "GitHub"

    def verify(self, component: ComponentInput) -> VerificationResult:
        checks = []
        parts = [piece for piece in urlparse(str(component.source_url)).path.split("/") if piece]
        if len(parts) < 2:
            checks.append(
                make_check(
                    field="source_url",
                    status="error",
                    severity="blocking",
                    message="URL do GitHub precisa apontar para owner/repo.",
                    provided_value=str(component.source_url),
                )
            )
            return finalize_result(self.source_name, checks)

        owner, repo = parts[0], parts[1]
        repo_slug = f"{owner}/{repo}"

        with build_client() as client:
            repo_response = client.get(f"https://api.github.com/repos/{repo_slug}")
        if repo_response.status_code != 200:
            checks.append(
                make_check(
                    field="name",
                    status="error",
                    severity="blocking",
                    message="Repositório não encontrado no GitHub.",
                    provided_value=component.name,
                    official_value=repo_slug,
                )
            )
            return finalize_result(self.source_name, checks)

        repo_payload: dict[str, Any] = repo_response.json()
        official_license = None
        if isinstance(repo_payload.get("license"), dict):
            official_license = repo_payload["license"].get("spdx_id") or repo_payload["license"].get("name")
        last_update = parse_iso_date(repo_payload.get("pushed_at"))
        official_source_url = repo_payload.get("html_url") or str(component.source_url)

        checks.append(
            make_check(
                field="name",
                status="ok",
                severity="info",
                message="Repositório encontrado no GitHub.",
                provided_value=component.name,
                official_value=repo_slug,
            )
        )

        version_ok = False
        with build_client() as client:
            release_response = client.get(f"https://api.github.com/repos/{repo_slug}/releases")
            tag_response = client.get(f"https://api.github.com/repos/{repo_slug}/tags")

        if release_response.status_code == 200:
            releases = release_response.json()
            version_ok = any((item.get("tag_name") or "") == component.version for item in releases if isinstance(item, dict))
        if not version_ok and tag_response.status_code == 200:
            tags = tag_response.json()
            version_ok = any((item.get("name") or "") == component.version for item in tags if isinstance(item, dict))

        if version_ok:
            checks.append(
                make_check(
                    field="version",
                    status="ok",
                    severity="info",
                    message="Versão encontrada entre tags ou releases do GitHub.",
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
                    message="Versão não encontrada entre tags ou releases do GitHub.",
                    provided_value=component.version,
                )
            )

        if official_license and component.license_name.strip().lower() == str(official_license).strip().lower():
            checks.append(
                make_check(
                    field="license",
                    status="ok",
                    severity="info",
                    message="Licença compatível com o repositório.",
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
                    message="Licença divergente da encontrada no repositório.",
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
                    message="O GitHub não retornou licença clara para esse repositório.",
                    provided_value=component.license_name,
                )
            )

        if last_update and component.last_update == last_update:
            checks.append(
                make_check(
                    field="last_update",
                    status="ok",
                    severity="info",
                    message="Data compatível com a atividade mais recente do repositório.",
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
                    message="A data informada difere da atividade mais recente do repositório.",
                    provided_value=str(component.last_update),
                    official_value=str(last_update),
                )
            )

        return finalize_result(
            self.source_name,
            checks,
            normalized_name=repo_slug,
            official_version=component.version if version_ok else None,
            official_license=str(official_license) if official_license else None,
            official_last_update=last_update,
            official_source_url=official_source_url,
        )

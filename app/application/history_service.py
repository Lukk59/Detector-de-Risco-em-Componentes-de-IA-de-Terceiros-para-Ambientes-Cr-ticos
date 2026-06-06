"""Serviço do histórico."""

from app.infrastructure.repositories import AnalysisRepository


class HistoryService:
    """Entrega dados prontos para a tela de histórico."""

    def __init__(self, repository: AnalysisRepository | None = None) -> None:
        self.repository = repository or AnalysisRepository()

    def list_recent(self):
        # Mantém o controller limpo.
        return self.repository.list_recent()

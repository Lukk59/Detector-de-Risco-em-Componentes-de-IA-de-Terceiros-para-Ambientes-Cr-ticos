"""Repositório de persistência."""

from __future__ import annotations

import json
from datetime import datetime

from app.domain.entities import AnalysisHistoryItem, AnalysisResult, CriterionScore
from app.domain.enums import Recommendation, RiskLevel
from app.infrastructure.database import get_connection


class AnalysisRepository:
    """Camada simples de leitura e escrita."""

    def save(self, result: AnalysisResult) -> int:
        # Salva a análise pronta no banco.
        payload = json.dumps([item.model_dump() for item in result.criteria_scores], ensure_ascii=False)
        with get_connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO analyses (
                    component_name, component_version, component_type, score,
                    risk_level, recommendation, summary_line, justification,
                    criteria_scores_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    result.component_name,
                    result.component_version,
                    result.component_type,
                    result.score,
                    result.risk_level.value,
                    result.recommendation.value,
                    result.summary_line,
                    result.justification,
                    payload,
                    result.created_at.isoformat(),
                ),
            )
            conn.commit()
            return int(cursor.lastrowid)

    def get_by_id(self, analysis_id: int) -> AnalysisResult | None:
        # Busca um resultado completo.
        with get_connection() as conn:
            row = conn.execute("SELECT * FROM analyses WHERE id = ?", (analysis_id,)).fetchone()
        if not row:
            return None
        criteria = [CriterionScore(**item) for item in json.loads(row["criteria_scores_json"])]
        return AnalysisResult(
            id=row["id"],
            component_name=row["component_name"],
            component_version=row["component_version"],
            component_type=row["component_type"],
            score=row["score"],
            risk_level=RiskLevel(row["risk_level"]),
            recommendation=Recommendation(row["recommendation"]),
            summary_line=row["summary_line"],
            justification=row["justification"],
            criteria_scores=criteria,
            created_at=datetime.fromisoformat(row["created_at"]),
        )

    def list_recent(self) -> list[AnalysisHistoryItem]:
        # Lista as análises mais novas primeiro.
        with get_connection() as conn:
            rows = conn.execute(
                "SELECT id, component_name, component_type, score, risk_level, created_at FROM analyses ORDER BY id DESC"
            ).fetchall()
        return [
            AnalysisHistoryItem(
                id=row["id"],
                component_name=row["component_name"],
                component_type=row["component_type"],
                score=row["score"],
                risk_level=RiskLevel(row["risk_level"]),
                created_at=datetime.fromisoformat(row["created_at"]),
            )
            for row in rows
        ]

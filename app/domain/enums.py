"""Enums simples para evitar texto solto no código."""

from enum import Enum


class ComponentType(str, Enum):
    MODEL = "Modelo de IA"
    DATASET = "Dataset"
    API = "API de IA"
    LIBRARY = "Biblioteca / Framework"


class RiskLevel(str, Enum):
    LOW = "Baixo"
    MEDIUM = "Médio"
    HIGH = "Alto"


class Recommendation(str, Enum):
    APPROVE = "Aprovar"
    REVIEW = "Revisar antes de integrar"
    BLOCK = "Bloquear até revisão humana"

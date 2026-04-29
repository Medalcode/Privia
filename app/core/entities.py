from dataclasses import dataclass
from enum import Enum


class Severidad(Enum):
    CRITICA = 30
    ALTA = 20
    MEDIA = 10
    BAJA = 5


@dataclass
class Hallazgo:
    categoria: str
    descripcion: str
    severidad: Severidad
    url_afectada: str | None = None


@dataclass
class InformeAuditoria:
    empresa_id: str
    riesgo_global: int
    hallazgos: list[Hallazgo]

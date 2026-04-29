
from .entities import Hallazgo, InformeAuditoria


class CalcularAuditoriaUseCase:
    def __init__(self):
        self.puntaje_base = 100

    def ejecutar(self, empresa_id: str, hallazgos_crudos: list[Hallazgo]) -> InformeAuditoria:
        total_penalizacion = sum(h.severidad.value for h in hallazgos_crudos)
        puntaje_final = max(0, self.puntaje_base - total_penalizacion)
        return InformeAuditoria(
            empresa_id=empresa_id,
            riesgo_global=puntaje_final,
            hallazgos=hallazgos_crudos,
        )

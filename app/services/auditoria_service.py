from sqlalchemy.orm import Session

from app.adapters.database import Escaneo, HallazgoVulnerabilidad
from app.adapters.scraper import PrivacyScraper
from app.core.entities import Hallazgo
from app.core.use_cases import CalcularAuditoriaUseCase


def ejecutar_auditoria_escaneo(db: Session, escaneo_id: str, url: str) -> dict:
    escaneo = db.query(Escaneo).filter(Escaneo.id == escaneo_id).first()
    if not escaneo:
        raise ValueError("Escaneo no encontrado")

    scraper = PrivacyScraper()
    hallazgos_detectados = scraper.run_sync(url)

    # Evitar duplicados si la tarea se reintenta
    db.query(HallazgoVulnerabilidad).filter(HallazgoVulnerabilidad.escaneo_id == escaneo.id).delete()

    hallazgos_domain: list[Hallazgo] = []
    for hallazgo in hallazgos_detectados:
        db_hallazgo = HallazgoVulnerabilidad(
            escaneo_id=escaneo.id,
            categoria=hallazgo.categoria,
            descripcion=hallazgo.descripcion,
            severidad=hallazgo.severidad.name,
            url_afectada=hallazgo.url_afectada,
        )
        db.add(db_hallazgo)
        hallazgos_domain.append(hallazgo)

    informe = CalcularAuditoriaUseCase().ejecutar(escaneo.empresa_id, hallazgos_domain)
    escaneo.riesgo_global = informe.riesgo_global
    escaneo.estado = "COMPLETADO"
    db.commit()

    return {
        "escaneo_id": escaneo.id,
        "empresa_id": escaneo.empresa_id,
        "riesgo_global": escaneo.riesgo_global,
        "total_hallazgos": len(hallazgos_domain),
    }

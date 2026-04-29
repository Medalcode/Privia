from app.adapters.database import SessionLocal
from app.services.auditoria_service import ejecutar_auditoria_escaneo

from .celery_app import celery_app


@celery_app.task(name="iniciar_auditoria_web")
def iniciar_auditoria_web(escaneo_id: str, url: str):
    db = SessionLocal()
    try:
        return ejecutar_auditoria_escaneo(db, escaneo_id, url)
    finally:
        db.close()

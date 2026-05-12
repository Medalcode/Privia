from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel, AnyHttpUrl, EmailStr
from sqlalchemy.orm import Session
from uuid import uuid4

from app.adapters.database import SessionLocal, init_db, Empresa, Escaneo, HallazgoVulnerabilidad
from app.workers.tasks import iniciar_auditoria_web

# Inicializar DB (crea tablas si no existen)
init_db()

app = FastAPI(title="Privia Auditoría API")


class EmpresaCreate(BaseModel):
    nombre_razon_social: str
    dominio_principal: str
    correo_contacto: EmailStr | None = None


class EscaneoCreate(BaseModel):
    dominio: AnyHttpUrl


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/")
def root():
    return {"status": "Privia Auditoría API activa"}


@app.post("/empresas/")
def registrar_empresa(payload: EmpresaCreate, db: Session = Depends(get_db)):
    existing = db.query(Empresa).filter(Empresa.dominio_principal == payload.dominio_principal).first()
    if existing:
        raise HTTPException(status_code=400, detail="Dominio ya registrado")
    nueva = Empresa(
        id=str(uuid4()),
        nombre_razon_social=payload.nombre_razon_social,
        dominio_principal=payload.dominio_principal,
        correo_contacto=payload.correo_contacto,
    )
    db.add(nueva)
    db.commit()
    db.refresh(nueva)
    return {"message": "Empresa registrada", "id": nueva.id}


@app.post("/escaneos/{empresa_id}")
def iniciar_escaneo(empresa_id: str, payload: EscaneoCreate, db: Session = Depends(get_db)):
    empresa = db.query(Empresa).filter(Empresa.id == empresa_id).first()
    if not empresa:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")

    esc = Escaneo(id=str(uuid4()), empresa_id=empresa_id, estado="EN_COLA")
    db.add(esc)
    db.commit()
    db.refresh(esc)

    iniciar_auditoria_web.delay(esc.id, str(payload.dominio))

    return {"message": "Escaneo encolado", "escaneo_id": esc.id, "estado": esc.estado}


@app.get("/escaneos/{escaneo_id}")
def obtener_escaneo(escaneo_id: str, db: Session = Depends(get_db)):
    esc = db.query(Escaneo).filter(Escaneo.id == escaneo_id).first()
    if not esc:
        raise HTTPException(status_code=404, detail="Escaneo no encontrado")

    resultado = {
        "id": esc.id,
        "empresa_id": esc.empresa_id,
        "fecha_inicio": esc.fecha_inicio,
        "estado": esc.estado,
        "riesgo_global": esc.riesgo_global,
        "hallazgos": [],
    }

    for h in esc.hallazgos:
        resultado["hallazgos"].append({
            "categoria": h.categoria,
            "descripcion": h.descripcion,
            "severidad": h.severidad,
            "url_afectada": h.url_afectada,
        })

    return resultado



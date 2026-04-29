import os
import time
import uuid

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, create_engine
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from sqlalchemy.sql import func

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./audit_database.db")

# For SQLite we need check_same_thread flag
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


class Empresa(Base):
    __tablename__ = "empresas"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    nombre_razon_social = Column(String(255), nullable=False)
    dominio_principal = Column(String(255), unique=True, nullable=False)
    correo_contacto = Column(String(255), nullable=True)
    escaneos = relationship("Escaneo", back_populates="empresa")


class Escaneo(Base):
    __tablename__ = "escaneos"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    empresa_id = Column(String, ForeignKey("empresas.id"), nullable=False)
    fecha_inicio = Column(DateTime(timezone=True), server_default=func.now())
    estado = Column(String(50), default="PENDIENTE")
    riesgo_global = Column(Integer, nullable=True)
    empresa = relationship("Empresa", back_populates="escaneos")
    hallazgos = relationship("HallazgoVulnerabilidad", back_populates="escaneo")


class HallazgoVulnerabilidad(Base):
    __tablename__ = "hallazgo_vulnerabilidad"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    escaneo_id = Column(String, ForeignKey("escaneos.id"), nullable=False)
    categoria = Column(String(100), nullable=False)
    descripcion = Column(Text, nullable=False)
    severidad = Column(String(50), nullable=False)
    url_afectada = Column(String(500), nullable=True)
    escaneo = relationship("Escaneo", back_populates="hallazgos")


def init_db(retries: int = 10, delay_seconds: float = 2.0):
    last_error = None
    for attempt in range(retries):
        try:
            Base.metadata.create_all(bind=engine)
            return
        except Exception as exc:
            last_error = exc
            if attempt == retries - 1:
                break
            time.sleep(delay_seconds)

    raise last_error

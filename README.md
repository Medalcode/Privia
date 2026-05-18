[![CI](https://github.com/Medalcode/Privia/actions/workflows/ci.yml/badge.svg)](https://github.com/Medalcode/Privia/actions/workflows/ci.yml)

# Privia — Auditoría Automatizada de Cumplimiento de Privacidad (MVP)

Privia es un MVP de SaaS B2B para auditoría automatizada de privacidad. La idea es escanear una web, detectar señales técnicas de riesgo y generar una base para reportes de cumplimiento.

## Alcance actual

- API en FastAPI para registrar empresas e iniciar escaneos.
- Dominio separado con entidades y caso de uso de cálculo de riesgo.
- Scraper con Playwright para detectar HTTPS, trackers, cookies y enlaces de privacidad.
- Ejecución asíncrona con Celery + Redis.
- Persistencia con SQLAlchemy + PostgreSQL.
- Despliegue reproducible con Docker y Docker Compose.

## Arquitectura resumida

- `app/main.py`: endpoints REST.
- `app/core/`: entidades y reglas de negocio.
- `app/adapters/`: persistencia y scraper.
- `app/services/`: orquestación del escaneo.
- `app/workers/`: Celery y tareas en segundo plano.

Instalación rápida (entorno Linux):

```bash
python -m pip install -r requirements.txt
playwright install
```

Levantamiento con Docker:

```bash
docker-compose up --build
```

Esto arranca la API, el worker de Celery, Redis y PostgreSQL con los datos de prueba incluidos en `docker-compose.yml`.

Levantar la API en modo desarrollo:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Ejecutar tests:

```bash
pytest -q
```

Flujo mínimo de prueba (curl):

1. Registrar una empresa:

```bash
curl -s -X POST http://localhost:8000/empresas/ \
  -H "Content-Type: application/json" \
  -d '{"nombre_razon_social":"ACME","dominio_principal":"https://example.com","correo_contacto":"hola@acme.com"}'
```

2. Iniciar un escaneo y encolarlo en Celery (reemplazar `<empresa_id>`):

```bash
curl -s -X POST http://localhost:8000/escaneos/<empresa_id> \
  -H "Content-Type: application/json" \
  -d '{"dominio":"https://example.com"}'
```

3. Consultar el estado del escaneo (reemplazar `<escaneo_id>`):

```bash
curl -s http://localhost:8000/escaneos/<escaneo_id>
```

4. Ejecutar el worker de Celery en otra terminal:

```bash
celery -A app.workers.celery_app.celery_app worker --loglevel=info
```

Si usas Docker, ese worker ya queda levantado como servicio aparte.

Notas:
- El worker toma el `escaneo_id`, ejecuta `PrivacyScraper`, guarda los hallazgos y actualiza el riesgo global.
- El estado inicial del escaneo queda como `EN_COLA` y luego pasa a `COMPLETADO` cuando termina el worker.

Ejemplo de payload de registro de empresa:

```bash
curl -s -X POST http://localhost:8000/empresas/ \
  -H "Content-Type: application/json" \
  -d '{"nombre_razon_social":"ACME","dominio_principal":"https://example.com","correo_contacto":"hola@acme.com"}'
```

Notas:
- Este repositorio contiene un esqueleto básico: `app/main.py`, `app/adapters/database.py`, `app/core/entities.py`, `app/core/use_cases.py`.
- También incluye `app/adapters/scraper.py`, `app/services/auditoria_service.py` y el worker en `app/workers/`.

## Próximos pasos sugeridos

- Generación de PDF del reporte final.
- Mejorar reglas del scraper para reducir falsos positivos.
- Añadir pruebas de integración para la API y el worker.
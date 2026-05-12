import asyncio
from typing import List
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
from app.core.entities import Hallazgo, Severidad


class PrivacyScraper:
    """Prototipo de scraper que audita una URL en busca de señales de privacidad.

    Detecta:
    - Uso de HTTPS
    - Presencia de enlace a 'privacidad'/'política' en la página
    - Scripts de trackers conocidos (Google Analytics, Facebook, TikTok, etc.)
    - Cookies detectadas por el contexto

    Este prototipo no sigue enlaces externos y limita la navegación a la URL principal.
    """

    KNOWN_TRACKERS = [
        "googletagmanager",
        "google-analytics",
        "gtag.js",
        "analytics.js",
        "connect.facebook.net",
        "fbevents",
        "facebook.net",
        "pixel",
        "hotjar",
        "tiktok",
        "adsystem",
    ]

    def __init__(self, timeout: int = 15000):
        self.timeout = timeout

    async def auditar_sitio(self, url: str) -> List[Hallazgo]:
        hallazgos: List[Hallazgo] = []

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()

            try:
                # Ir a la página
                await page.goto(url, timeout=self.timeout)

                # HTTPS check
                if not url.lower().startswith("https"):
                    hallazgos.append(Hallazgo(
                        categoria="SEGURIDAD",
                        descripcion="La URL no usa HTTPS",
                        severidad=Severidad.CRITICA,
                        url_afectada=url,
                    ))

                # Buscar enlaces con texto relacionado a privacidad
                body_text = await page.content()
                # búsquedas simples en texto HTML
                if not any(k in body_text.lower() for k in ["privacidad", "política de privacidad", "privacy policy", "aviso de privacidad"]):
                    hallazgos.append(Hallazgo(
                        categoria="LEGAL",
                        descripcion="No se detectó un enlace o texto visible relacionado con Política de Privacidad",
                        severidad=Severidad.MEDIA,
                        url_afectada=url,
                    ))

                # Detectar scripts de trackers por su src o contenido
                scripts = await page.query_selector_all("script")
                found_trackers = set()
                for s in scripts:
                    src = await s.get_attribute("src")
                    inner = await (s.inner_text() or "")
                    hay = (src or "") + " " + inner
                    for t in self.KNOWN_TRACKERS:
                        if t in hay.lower():
                            found_trackers.add(t)

                if found_trackers:
                    for t in sorted(found_trackers):
                        hallazgos.append(Hallazgo(
                            categoria="TRACKER",
                            descripcion=f"Tracker detectado: {t}",
                            severidad=Severidad.ALTA,
                            url_afectada=url,
                        ))

                # Cookies en contexto
                cookies = await context.cookies()
                if cookies and len(cookies) > 0:
                    # diferenciación no implementada en el prototipo
                    hallazgos.append(Hallazgo(
                        categoria="COOKIES",
                        descripcion=f"Se detectaron {len(cookies)} cookies en el contexto",
                        severidad=Severidad.BAJA,
                        url_afectada=url,
                    ))

            except PlaywrightTimeoutError:
                hallazgos.append(Hallazgo(
                    categoria="INFRA",
                    descripcion="Timeout al cargar la página durante el escaneo",
                    severidad=Severidad.MEDIA,
                    url_afectada=url,
                ))
            except Exception as e:
                hallazgos.append(Hallazgo(
                    categoria="ERROR",
                    descripcion=f"Error durante el escaneo: {e}",
                    severidad=Severidad.MEDIA,
                    url_afectada=url,
                ))
            finally:
                await context.close()
                await browser.close()

        return hallazgos

    def run_sync(self, url: str) -> List[Hallazgo]:
        """Helper síncrono para ejecutar desde código no-asíncrono."""
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            # Si ya hay un loop corriendo (ej. en ciertos entornos), creamos uno nuevo
            return asyncio.run(self.auditar_sitio(url))
        else:
            return asyncio.run(self.auditar_sitio(url))


if __name__ == "__main__":
    # Pequeña prueba manual
    import sys

    url = sys.argv[1] if len(sys.argv) > 1 else "https://example.com"
    s = PrivacyScraper()
    resultado = s.run_sync(url)
    for h in resultado:
        print(f"[{h.severidad.name}] {h.categoria}: {h.descripcion}")

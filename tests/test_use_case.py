from app.core.entities import Hallazgo, Severidad
from app.core.use_cases import CalcularAuditoriaUseCase


def test_calculo_riesgo_simple():
    usecase = CalcularAuditoriaUseCase()
    hallazgos = [
        Hallazgo("SEGURIDAD", "Formulario sin HTTPS", Severidad.CRITICA, "https://example.com/contact"),
        Hallazgo("TRACKER", "Meta Pixel cargado sin consentimiento", Severidad.ALTA, "https://example.com"),
    ]
    informe = usecase.ejecutar("empresa-1", hallazgos)
    expected = 100 - (Severidad.CRITICA.value + Severidad.ALTA.value)
    assert informe.riesgo_global == expected


def test_calculo_riesgo_no_negativo():
    usecase = CalcularAuditoriaUseCase()
    # Muchos hallazgos críticos deben dejar el puntaje en 0, no negativo
    hallazgos = [Hallazgo("X", "a", Severidad.CRITICA, None) for _ in range(10)]
    informe = usecase.ejecutar("empresa-2", hallazgos)
    assert informe.riesgo_global == 0

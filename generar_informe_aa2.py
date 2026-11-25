from __future__ import annotations

import json
from pathlib import Path

from reportlab.graphics.shapes import Drawing, Line, Polygon, Rect, String
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    HRFlowable,
    PageBreak,
    Paragraph,
    Preformatted,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

ROOT = Path(__file__).resolve().parent
EVIDENCIAS = ROOT / "artifacts" / "evidencias"
SALIDA = ROOT / "AA2_Pipeline_SistemaRestaurante.pdf"
staging = json.loads((EVIDENCIAS / "staging.json").read_text(encoding="utf-8"))
resumen = json.loads((EVIDENCIAS / "pipeline_resumen.json").read_text(encoding="utf-8"))
assert resumen["resultado"] == "EXITOSO"
assert staging["resultado"] == "APROBADO"

FUENTES = ROOT / "fuentes"
pdfmetrics.registerFont(TTFont("Arial", str(FUENTES / "arial.ttf")))
pdfmetrics.registerFont(TTFont("Arial-Bold", str(FUENTES / "arialbd.ttf")))
pdfmetrics.registerFont(TTFont("Arial-Italic", str(FUENTES / "ariali.ttf")))
pdfmetrics.registerFont(TTFont("Arial-BoldItalic", str(FUENTES / "arialbi.ttf")))
pdfmetrics.registerFontFamily(
    "Arial", normal="Arial", bold="Arial-Bold", italic="Arial-Italic",
    boldItalic="Arial-BoldItalic",
)

NEGRO = colors.black
AZUL = NEGRO
GRIS = NEGRO
CLARO = colors.white
TEXTO = NEGRO

styles = getSampleStyleSheet()
body = ParagraphStyle(
    "Cuerpo", parent=styles["BodyText"], fontName="Arial", fontSize=11,
    leading=22, alignment=TA_LEFT, textColor=TEXTO, spaceAfter=8,
)
small = ParagraphStyle(
    "Pequeno", parent=body, fontSize=9.2, leading=12, spaceAfter=4,
)
caption = ParagraphStyle(
    "Caption", parent=small, fontName="Arial-Italic", alignment=TA_LEFT,
    textColor=GRIS, spaceBefore=4, spaceAfter=7,
)
h1 = ParagraphStyle(
    "Titulo", parent=styles["Heading1"], fontName="Arial-Bold", fontSize=14,
    leading=18, textColor=AZUL, spaceAfter=8, keepWithNext=True,
)
h2 = ParagraphStyle(
    "Subtitulo", parent=styles["Heading2"], fontName="Arial-Bold", fontSize=11,
    leading=15, textColor=AZUL, spaceBefore=5, spaceAfter=5, keepWithNext=True,
)
code_style = ParagraphStyle(
    "Codigo", fontName="Arial", fontSize=7.5, leading=9.4, textColor=TEXTO,
    backColor=CLARO, borderPadding=7, spaceBefore=4, spaceAfter=7,
)
ref_style = ParagraphStyle(
    "Referencia", parent=body, leftIndent=1.27 * cm, firstLineIndent=-1.27 * cm,
    leading=22, spaceAfter=8,
)

story = []


def p(texto: str, estilo=body):
    story.append(Paragraph(texto, estilo))


def titulo(texto: str):
    story.append(Paragraph(texto, h1))


def subtitulo(texto: str):
    story.append(Paragraph(texto, h2))


def salto():
    story.append(PageBreak())


def codigo(texto: str):
    story.append(Preformatted(texto.strip("\n"), code_style))


def tabla(datos, anchos, estilo=small):
    convertido = []
    for fila in datos:
        convertido.append([Paragraph(str(celda), estilo) for celda in fila])
    factor = min(1.0, (15.9 * cm) / sum(anchos))
    anchos = [ancho * factor for ancho in anchos]
    t = Table(convertido, colWidths=anchos, repeatRows=1, hAlign="LEFT")
    t.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, 0), "Arial-Bold"),
        ("LINEABOVE", (0, 0), (-1, 0), 1.2, NEGRO),
        ("LINEBELOW", (0, 0), (-1, 0), 0.7, NEGRO),
        ("LINEBELOW", (0, -1), (-1, -1), 1.2, NEGRO),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(t)
    story.append(Spacer(1, 7))


def diagrama_pipeline():
    d = Drawing(470, 245)
    etiquetas = [
        ("1. Commit / PR", "Git + GitHub"),
        ("2. Build", "compileall"),
        ("3. Calidad", "Ruff"),
        ("4. Pruebas", "Pytest + cobertura"),
        ("5. Seguridad", "Bandit + pip-audit"),
        ("6. Paquete", "Wheel + Docker"),
        ("7. Staging", "Contenedor / API"),
        ("8. Validación", "Smoke + carga"),
    ]
    posiciones = [(5, 165), (123, 165), (241, 165), (359, 165),
                  (359, 55), (241, 55), (123, 55), (5, 55)]
    for i, ((titulo_caja, detalle), (x, y)) in enumerate(zip(etiquetas, posiciones)):
        d.add(Rect(x, y, 105, 52, fillColor=CLARO, strokeColor=AZUL, strokeWidth=1.2))
        d.add(String(x + 52.5, y + 31, titulo_caja, fontName="Arial-Bold",
                     fontSize=8.5, fillColor=AZUL, textAnchor="middle"))
        d.add(String(x + 52.5, y + 15, detalle, fontName="Arial",
                     fontSize=7.5, fillColor=TEXTO, textAnchor="middle"))
        if i < 3:
            nx, ny = posiciones[i + 1]
            d.add(Line(x + 105, y + 26, nx - 5, ny + 26, strokeColor=AZUL))
            d.add(Polygon([nx - 5, ny + 26, nx - 12, ny + 30, nx - 12, ny + 22],
                          fillColor=AZUL, strokeColor=AZUL))
    d.add(Line(464, 165, 464, 112, strokeColor=AZUL))
    d.add(Polygon([464, 107, 460, 115, 468, 115], fillColor=AZUL, strokeColor=AZUL))
    for i in range(4, 7):
        x, y = posiciones[i]
        nx, ny = posiciones[i + 1]
        d.add(Line(x, y + 26, nx + 110, ny + 26, strokeColor=AZUL))
        d.add(Polygon([nx + 110, ny + 26, nx + 117, ny + 30, nx + 117, ny + 22],
                      fillColor=AZUL, strokeColor=AZUL))
    d.add(String(235, 232, "Cada etapa exitosa habilita la siguiente; un fallo detiene el flujo",
                 fontName="Arial-Bold", fontSize=9, fillColor=AZUL, textAnchor="middle"))
    d.add(String(235, 20, "Artefactos y reportes quedan disponibles para trazabilidad",
                 fontName="Arial-Italic", fontSize=8, fillColor=GRIS, textAnchor="middle"))
    d.scale(0.95, 0.95)
    d.width = 446.5
    d.height = 232.75
    return d


# Portada
story.append(Spacer(1, 2.2 * cm))
p("CORPORACIÓN UNIVERSITARIA TECNOLÓGICA DEL ORIENTE", ParagraphStyle(
    "Institucion", parent=body, fontName="Arial-Bold", fontSize=12,
    alignment=TA_CENTER, leading=16, textColor=AZUL))
story.append(Spacer(1, 1.2 * cm))
story.append(HRFlowable(width="70%", thickness=1.5, color=AZUL))
story.append(Spacer(1, 0.8 * cm))
p("AA2 — PROYECTO INTEGRADOR", ParagraphStyle(
    "PortadaTitulo", parent=body, fontName="Arial-Bold", fontSize=22,
    leading=28, alignment=TA_CENTER, textColor=AZUL))
p("Construcción de un Pipeline CI/CD para un Sistema de Gestión de Restaurante", ParagraphStyle(
    "PortadaSubtitulo", parent=body, fontName="Arial-Bold", fontSize=16,
    leading=22, alignment=TA_CENTER, textColor=TEXTO))
story.append(Spacer(1, 1.1 * cm))
story.append(HRFlowable(width="70%", thickness=1.5, color=AZUL))
story.append(Spacer(1, 1.5 * cm))
p("<b>Estudiante:</b> Einer Plaza Prasca", ParagraphStyle(
    "DatosPortada", parent=body, fontSize=12, leading=20, alignment=TA_CENTER))
p("<b>Asignatura:</b> Gestión del Software", ParagraphStyle(
    "DatosPortada2", parent=body, fontSize=12, leading=20, alignment=TA_CENTER))
p("<b>Docente:</b> Carlos Carrascal Avendaño", ParagraphStyle(
    "DatosPortada3", parent=body, fontSize=12, leading=20, alignment=TA_CENTER))
p("<b>Unidad 3:</b> Automatización y entrega continua", ParagraphStyle(
    "DatosPortada4", parent=body, fontSize=12, leading=20, alignment=TA_CENTER))
story.append(Spacer(1, 1.3 * cm))
p("24 de noviembre de 2026", ParagraphStyle(
    "FechaPortada", parent=body, fontSize=12, alignment=TA_CENTER))
salto()

# 1
titulo("1. Introducción")
p("El sistema de gestión de pedidos y reservas de un restaurante requiere cambios frecuentes sin comprometer la disponibilidad ni la exactitud de las operaciones. Una reserva duplicada, un total calculado incorrectamente o una dependencia vulnerable pueden afectar directamente al cliente. Por ello, conforme a los criterios de la actividad (Corporación Universitaria Tecnológica del Oriente, 2026b), el proyecto propone un pipeline de integración y entrega continua (CI/CD) que valide automáticamente cada modificación antes de autorizar su despliegue.")
p("La integración continua consiste en incorporar cambios pequeños a un repositorio compartido y verificarlos mediante construcción, pruebas y validaciones automáticas. La entrega continua extiende esta práctica para mantener el software listo para su liberación. Estas técnicas reducen la detección tardía de errores y fortalecen la colaboración entre desarrollo y operaciones. (Corporación Universitaria Tecnológica del Oriente, 2026a)")
subtitulo("Objetivo general")
p("Diseñar, documentar y ejecutar un pipeline CI/CD para un prototipo realista de restaurante, integrando construcción, pruebas, calidad, seguridad, empaquetado, despliegue a staging y validación no funcional.")
subtitulo("Objetivos específicos")
p("• Automatizar puntos críticos del flujo de desarrollo y establecer puertas de calidad.<br/>• Construir evidencias reales de ejecución exitosa y de bloqueo ante fallos.<br/>• Definir buenas prácticas para escalar el proceso a producción y al trabajo colaborativo.")
subtitulo("Alcance y criterio de éxito")
p("Se implementó una API REST con Python 3.12 y Flask, acompañada por GitHub Actions, Docker y scripts locales. El criterio de éxito exige 28 pruebas aprobadas, cobertura mínima del 85 %, ausencia de hallazgos de seguridad pendientes, generación de artefactos y comprobación funcional del ambiente de pruebas. La entrega combina el informe con el código fuente y los reportes que permiten reproducir los resultados.")
salto()

# 2
titulo("2. Análisis del sistema")
p("El prototipo representa los procesos esenciales de un restaurante. Las reglas de negocio están separadas de la capa HTTP, lo que permite probar cálculos y validaciones sin depender del servidor web. Los datos se almacenan en memoria porque el propósito académico es demostrar el pipeline; una versión productiva deberá incorporar persistencia transaccional.")
p("<b>Tabla 1. Módulos incluidos y validación automatizada</b>", caption)
tabla([
    ["Módulo", "Funcionalidad", "Validación automatizada"],
    ["Reservas", "Registro y confirmación de clientes.", "Formato, fecha, capacidad y duplicados."],
    ["Disponibilidad", "Consulta de mesas por fecha y hora.", "Estado antes y después de reservar."],
    ["Pedidos", "Registro de platos y tipo de entrega.", "Existencia, cantidad y total del pedido."],
    ["Autenticación", "Validación de credenciales.", "Acceso correcto, rechazo y configuración ausente."],
    ["Reportes", "Cantidad de pedidos e ingresos.", "Consistencia del total consolidado."],
    ["Salud", "Estado y versión del servicio.", "Respuesta HTTP 200 en CI y staging."],
], [2.7 * cm, 6.0 * cm, 7.4 * cm])
subtitulo("Flujo funcional representativo")
p("El usuario consulta mesas disponibles y envía una reserva; el sistema valida los datos y confirma únicamente si la mesa está libre y tiene capacidad. Para los pedidos, el cliente selecciona platos y cantidades; el sistema calcula subtotales y total, registra la operación y expone un reporte de ventas. La autenticación usa variables de entorno y comparación segura de credenciales, sin incorporar secretos al código.")
subtitulo("Artefactos del proyecto")
p("El entregable técnico contiene el código en <font face='Arial'>src/</font>, pruebas en <font face='Arial'>tests/</font>, configuración en <font face='Arial'>.github/workflows/ci-cd.yml</font>, contenedor en <font face='Arial'>Dockerfile</font>, automatización local y evidencias. Esta separación facilita mantenimiento, revisión y trazabilidad.")
salto()

# 3
titulo("3. Puntos críticos y arquitectura de automatización")
p("La automatización se concentró en decisiones repetitivas y de alto riesgo. El pipeline no se limita a ejecutar comandos: cada etapa actúa como una puerta que impide promover una versión no conforme. Esta decisión aplica el principio de detección temprana descrito en el material de la unidad. (Corporación Universitaria Tecnológica del Oriente, 2026a)")
p("<b>Tabla 2. Riesgos y respuesta del pipeline</b>", caption)
tabla([
    ["Punto crítico", "Riesgo", "Respuesta automatizada"],
    ["Integración de código", "Errores de sintaxis o estilo.", "Compilación y análisis con Ruff."],
    ["Reglas de negocio", "Totales o reservas incorrectos.", "Pruebas unitarias y de integración."],
    ["Regresiones", "Un cambio daña funciones previas.", "Suite completa en cada push o PR."],
    ["Cobertura insuficiente", "Código sin evidencia de prueba.", "Umbral mínimo del 85 %."],
    ["Seguridad", "Prácticas inseguras o dependencias vulnerables.", "Bandit y pip-audit bloqueantes."],
    ["Despliegue", "Entregar una versión no verificada.", "Staging condicionado a todas las puertas."],
], [3.2 * cm, 5.4 * cm, 7.5 * cm])
subtitulo("Arquitectura lógica")
p("<b>Cliente HTTP → API Flask → reglas de negocio → repositorio en memoria.</b> La capa de presentación devuelve JSON y códigos HTTP; los modelos validan datos y calculan totales; el repositorio controla reservas y pedidos. Waitress sirve la aplicación en staging. El contenedor fija dependencias y configuración para que el artefacto probado sea el mismo que se despliega.")
subtitulo("Trazabilidad")
p("Git conserva el historial, GitHub Actions relaciona la ejecución con el commit y los reportes JUnit, XML, JSON y registros de consola documentan los resultados. Ante un fallo, el equipo puede identificar etapa, causa y versión sin reconstruir manualmente el proceso.")
salto()

# 4
titulo("4. Diseño del pipeline CI/CD")
p("La secuencia comienza con un evento de Git y termina con una versión validada. El orden evita actividades costosas cuando la construcción o las pruebas básicas fallan. La definición como código permite revisar el pipeline con las mismas prácticas del proyecto (Smart, 2011).")
story.append(diagrama_pipeline())
p("Figura 1. Secuencia del pipeline y dependencia entre etapas.", caption)
subtitulo("Política de promoción")
p("Un <i>pull request</i> ejecuta construcción, calidad, pruebas y seguridad. Si el resultado es satisfactorio, se generan el paquete Python y la imagen Docker. Staging solo se despliega cuando el empaquetado depende de una ejecución previa exitosa. La promoción a producción queda limitada a <font face='Arial'>main</font> y a un ambiente protegido con aprobación.")
subtitulo("Herramientas seleccionadas y modularidad")
p("<b>Git y GitHub:</b> versiones y colaboración. <b>GitHub Actions:</b> orquestación. <b>Pytest y Coverage:</b> pruebas y cobertura. <b>Ruff:</b> calidad. <b>Bandit y pip-audit:</b> seguridad. <b>Docker:</b> empaquetado. <b>Waitress:</b> servicio HTTP. Cada etapa tiene un propósito único y puede ejecutarse localmente para diagnosticar fallos.")
salto()

# 5
titulo("5. Etapas, entradas y criterios de salida")
p("<b>Tabla 3. Definición operativa del pipeline</b>", caption)
tabla([
    ["Etapa", "Comando o mecanismo", "Resultado esperado"],
    ["Build", "python -m compileall -q src", "Código importable y compilable."],
    ["Lint", "ruff check src tests scripts", "Cero errores de calidad configurados."],
    ["Test", "coverage run -m pytest -q", "28 pruebas aprobadas y reporte JUnit."],
    ["Cobertura", "coverage report --fail-under=85", "Cobertura igual o superior al 85 %."],
    ["Security", "bandit -r src; pip-audit -r requirements.txt", "Sin hallazgos bloqueantes ni vulnerabilidades conocidas."],
    ["Package", "python -m build; docker build", "Wheel, sdist e imagen identificada por commit."],
    ["Deploy", "docker run; health check", "Servicio disponible en staging."],
    ["Validate", "scripts/validar_staging.py", "Flujo funcional correcto y p95 menor de 500 ms."],
], [2.1 * cm, 7.1 * cm, 6.9 * cm])
subtitulo("Manejo de errores")
p("Los comandos devuelven un código distinto de cero cuando incumplen su criterio. Tanto el ejecutor local como GitHub Actions detienen el flujo; las etapas dependientes no se ejecutan. Los reportes se conservan incluso en una ejecución fallida para facilitar la corrección.")
subtitulo("Configuración y secretos")
p("Las versiones de dependencias están fijadas. Las credenciales se obtienen de variables de entorno y el secreto <font face='Arial'>CLAVE_STAGING</font> se almacena en GitHub, no en el repositorio. El contenedor se ejecuta con un usuario sin privilegios y expone una comprobación de salud.")
subtitulo("Reproducibilidad")
p("La misma versión del código produce artefactos identificables y resultados verificables. El pipeline puede repetirse en una máquina local o en un agente limpio de Ubuntu con Python 3.12.")
salto()

# 6
titulo("6. Configuración real: integración y validaciones")
p("El siguiente fragmento pertenece al archivo <font face='Arial'>.github/workflows/ci-cd.yml</font>. Define los eventos, la versión de Python y la primera puerta de calidad. Se omiten algunas líneas de instalación por espacio; el archivo completo acompaña el informe.")
codigo("""
name: CI/CD Sistema Restaurante
on:
  push:
    branches: [main]
  pull_request:
  workflow_dispatch:
permissions:
  contents: read
env:
  PYTHON_VERSION: "3.12"
  PYTHONPATH: src

jobs:
  calidad-pruebas:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}
          cache: pip
      - run: pip install -r requirements-dev.txt
      - run: python -m compileall -q src
      - run: ruff check src tests scripts
      - run: |
          coverage run -m pytest -q --junitxml=artifacts/evidencias/pytest.xml
          coverage report --fail-under=85
          coverage xml -o artifacts/evidencias/cobertura.xml
      - run: |
          bandit -q -r src -f json -o artifacts/evidencias/bandit.json
          pip-audit -r requirements.txt
""")
subtitulo("Justificación")
p("El desencadenante por <i>push</i> valida la rama principal y el de <i>pull request</i> evita integrar cambios no conformes. Los permisos se limitan a lectura. El caché reduce el tiempo de instalación sin alterar las versiones fijadas. Los reportes JUnit, cobertura y Bandit se almacenan como artefactos de la ejecución.")
salto()

# 7
titulo("7. Configuración real: empaquetado y entrega")
p("Las etapas siguientes se ejecutan mediante dependencias explícitas. <font face='Arial'>needs</font> impide construir o desplegar cuando una puerta anterior ha fallado.")
codigo("""
  empaquetado:
    needs: calidad-pruebas
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: pip install build==1.3.0 && python -m build
      - run: docker build -t sistema-restaurante:${{ github.sha }} .
      - run: docker save sistema-restaurante:${{ github.sha }} -o sistema-restaurante.tar
      - uses: actions/upload-artifact@v4
        with:
          name: paquete-aplicacion
          path: |
            dist/
            sistema-restaurante.tar

  staging:
    needs: empaquetado
    runs-on: ubuntu-latest
    environment: staging
    steps:
      - uses: actions/checkout@v4
      - uses: actions/download-artifact@v4
        with: { name: paquete-aplicacion }
      - run: docker load -i sistema-restaurante.tar
      - run: docker run -d --name restaurante -p 8080:8080
             -e AUTENTICACION_CLAVE=${{ secrets.CLAVE_STAGING }}
             sistema-restaurante:${{ github.sha }}
      - run: python scripts/validar_staging.py

  produccion:
    needs: staging
    if: github.ref == 'refs/heads/main' && github.event_name != 'pull_request'
    environment: production
""")
subtitulo("Entrega continua controlada")
p("La imagen se etiqueta con el hash del commit y se transfiere como artefacto; de este modo, staging utiliza el paquete generado después de las validaciones. Producción no se ejecuta en solicitudes de extracción y requiere las reglas del ambiente protegido. Esta combinación automatiza la preparación y conserva una aprobación explícita para el despliegue de mayor riesgo.")
salto()

# 8
titulo("8. Simulación y ejecución real del pipeline")
p("La ejecución local se realizó el 24 de noviembre de 2026 con Python 3.12 en Windows. El orquestador <font face='Arial'>scripts/pipeline_local.py</font> ejecutó secuencialmente las mismas puertas del flujo remoto y almacenó la salida de cada comando. El proceso completo exitoso duró aproximadamente 58 segundos.")
subtitulo("Comandos principales")
codigo("""
# Configuración aislada
python -m venv .venv
.venv\\Scripts\\python.exe -m pip install -r requirements-dev.txt
.venv\\Scripts\\python.exe -m pip install -e .

# Pipeline completo
.venv\\Scripts\\python.exe scripts\\pipeline_local.py

# Mutación controlada en una copia temporal
.venv\\Scripts\\python.exe scripts\\simular_fallo.py
""")
p("<b>Tabla 4. Secuencia observada en la ejecución exitosa</b>", caption)
tabla([
    ["Orden", "Etapa", "Evidencia generada"],
    ["1", "Construcción", "Compilación sin errores."],
    ["2", "Calidad", "Ruff: todas las comprobaciones aprobadas."],
    ["3–5", "Pruebas y cobertura", "pytest.xml, cobertura.xml y consola."],
    ["6–7", "Seguridad", "bandit.json y auditoría de dependencias."],
    ["8", "Empaquetado", "Wheel y sdist en dist/."],
    ["9", "Staging y validación", "staging.json y registro del servidor."],
], [1.4 * cm, 5.0 * cm, 9.7 * cm])
subtitulo("Resultado global")
p("El archivo <font face='Arial'>pipeline_resumen.json</font> registra el estado <b>EXITOSO</b> y las etapas build, lint, test, coverage, security, package, deploy-staging y smoke-performance. El despliegue local se efectuó como un proceso Waitress controlado; la construcción de la imagen Docker quedó configurada para el agente de GitHub Actions, porque Docker no estaba instalado en el equipo de evidencia.")
salto()

# 9
titulo("9. Evidencia de pruebas y cobertura")
p("La suite combina 18 casos unitarios y 10 de integración, incluidos escenarios parametrizados. Se verificaron validaciones, capacidad de mesas, duplicidad de reservas, cálculo de pedidos, códigos HTTP, autenticación y reporte de ventas.")
codigo("""
$ python -m coverage run -m pytest -q
............................                                             [100%]
28 passed in 1.08s

$ python -m coverage report --fail-under=85
Name                             Stmts   Miss Branch BrPart  Cover
src\\restaurante\\__init__.py          3      0      0      0   100%
src\\restaurante\\app.py              63      0      8      0   100%
src\\restaurante\\modelos.py          53      2     22      0    97%
src\\restaurante\\repositorio.py      28      0      2      0   100%
TOTAL                              147      2     32      0    99%
""")
p("<b>Tabla 5. Interpretación de los resultados</b>", caption)
tabla([
    ["Indicador", "Umbral", "Obtenido", "Decisión"],
    ["Pruebas", "100 % aprobadas", "28 de 28", "Continuar"],
    ["Cobertura", "≥ 85 %", "99 %", "Continuar"],
    ["Ruff", "0 errores", "0 errores", "Continuar"],
], [4.1 * cm, 3.7 * cm, 3.7 * cm, 4.6 * cm])
p("La cobertura no sustituye la calidad de los casos de prueba; por ello se combinaron afirmaciones sobre resultados, estados HTTP y mensajes de error. Las dos líneas no cubiertas corresponden a una excepción defensiva de conversión y no impiden superar el umbral definido.")
salto()

# 10
titulo("10. Validación de seguridad: fallo y corrección")
p("El pipeline incorporó dos técnicas complementarias: Bandit para analizar el código fuente y pip-audit para comparar las dependencias con avisos de seguridad. Ambas son bloqueantes. Durante la primera ejecución, Bandit identificó la escucha en todas las interfaces; se corrigió mediante una variable <font face='Arial'>HOST</font>, usando una dirección local por defecto y la configuración amplia solo dentro del contenedor.")
subtitulo("Bloqueo por dependencia vulnerable")
p("En una ejecución posterior, pip-audit detectó un aviso asociado a Flask 3.1.2 y detuvo el proceso antes del empaquetado. El registro real fue:")
codigo("""
$ python -m pip_audit -r requirements.txt
Name  Version ID              Fix Versions
----- ------- --------------- ------------
flask 3.1.2   PYSEC-2026-2151 3.1.3
Found 1 known vulnerability in 1 package

Pipeline detenido en 07_dependencias; no se autoriza el despliegue.
""")
subtitulo("Corrección y reverificación")
p("Se actualizó Flask a 3.1.3 en <font face='Arial'>requirements.txt</font> y <font face='Arial'>pyproject.toml</font>. Después se repitió el pipeline completo, no solo la etapa corregida, para comprobar que el cambio no introdujera regresiones. El resultado fue <b>“No known vulnerabilities found”</b>, con 28 pruebas aprobadas y Bandit sin hallazgos.")
p("Este caso demuestra que automatizar no significa únicamente acelerar: también impide que una versión con una vulnerabilidad conocida avance por el flujo. La corrección queda trazada en los archivos de dependencias y en las evidencias.")
salto()

# 11
titulo("11. Fallo controlado de pruebas y medida correctiva")
p("Además del fallo real de dependencias, se ejecutó una mutación controlada para demostrar la capacidad de detección de las pruebas. El script copió el proyecto a una carpeta temporal y modificó únicamente la copia, sumando COP 1.000 al total de cada pedido. El código fuente original permaneció intacto.")
codigo("""
Mutación: sumar COP 1.000 al total del pedido.

_________________________ test_calcular_pedido_total _________________________
>       assert pedido["total"] == 63_000
E       assert 64000 == 63000

1 failed, 17 passed in 0.68s
Resultado: pruebas fallidas detectadas (código 1).
Decisión del pipeline: detener y NO desplegar.
""")
p("<b>Tabla 6. Acciones de recuperación</b>", caption)
tabla([
    ["Paso", "Acción", "Propósito"],
    ["1", "Conservar el registro y localizar la afirmación fallida.", "Obtener evidencia del defecto."],
    ["2", "Revertir la mutación en la copia de trabajo.", "Restaurar la regla de negocio."],
    ["3", "Repetir pruebas unitarias y de integración.", "Descartar efectos secundarios."],
    ["4", "Ejecutar nuevamente todas las puertas.", "Validar la versión completa."],
], [1.2 * cm, 8.0 * cm, 6.9 * cm])
p("La corrección no consiste en modificar la prueba para aceptar 64.000, porque el valor esperado deriva de los precios y cantidades definidos. Se debe corregir el código causante y conservar la prueba como protección frente a futuras regresiones.")
salto()

# 12
titulo("12. Empaquetado y despliegue a staging")
p("El empaquetado produce una distribución fuente y un wheel en <font face='Arial'>dist/</font>. Para el flujo remoto, el Dockerfile instala las dependencias fijadas, copia únicamente el código necesario, crea un usuario no administrativo y define una comprobación de salud.")
codigo(r"""
FROM python:3.12-slim
ENV PYTHONPATH=/app/src HOST=0.0.0.0 PORT=8080
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt && \
    useradd --create-home --uid 10001 restaurante
COPY src ./src
USER restaurante
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=3s --retries=3 \
    CMD python -c "import urllib.request; \
    urllib.request.urlopen('http://localhost:8080/api/salud')"
CMD ["python", "-m", "restaurante.app"]
""")
subtitulo("Validación del ambiente de pruebas")
p("La ejecución local inició el servicio en un puerto aislado, esperó una respuesta satisfactoria de <font face='Arial'>/api/salud</font> y creó un pedido de prueba. Después ejecutó 30 solicitudes concurrentes de salud con seis trabajadores y cerró el servidor en un bloque <font face='Arial'>finally</font>, evitando procesos residuales.")
p("<b>Tabla 7. Resultado de staging</b>", caption)
tabla([
    ["Comprobación", "Resultado"],
    ["Pedido funcional", "Creado con el total esperado de COP 42.000."],
    ["Solicitudes / errores", f"{staging['solicitudes']} / {staging['errores']}"],
    ["Disponibilidad", f"{staging['disponibilidad_porcentaje']:.0f} % durante la prueba"],
    ["Latencia p95", f"{staging['latencia_p95_ms']:.2f} ms (umbral: 500 ms)"],
    ["Estado final", staging["resultado"]],
], [6.0 * cm, 10.1 * cm])
salto()

# 13
titulo("13. Validación de requisitos no funcionales")
p("Los requisitos no funcionales se expresan como criterios medibles y vinculados a etapas concretas. Esto evita que calidad, seguridad o rendimiento dependan de revisiones manuales ocasionales.")
p("<b>Tabla 8. Controles no funcionales integrados</b>", caption)
tabla([
    ["Atributo", "Herramienta o técnica", "Criterio y evidencia"],
    ["Rendimiento", "Carga ligera concurrente", "p95 < 500 ms; obtenido: 18,45 ms."],
    ["Disponibilidad", "Health check y 30 solicitudes", "100 % de respuestas correctas; 0 errores."],
    ["Seguridad estática", "Bandit", "Sin hallazgos en la versión final."],
    ["Dependencias", "pip-audit", "Sin vulnerabilidades conocidas tras actualizar Flask."],
    ["Mantenibilidad", "Ruff, arquitectura por capas", "Cero errores; reglas separadas de HTTP."],
    ["Confiabilidad", "Pytest y cobertura de ramas", "28 pruebas aprobadas; 99 % de cobertura."],
    ["Reproducibilidad", "Docker y versiones fijadas", "Imagen por commit y paquete trazable."],
], [3.0 * cm, 5.2 * cm, 7.9 * cm])
subtitulo("Límites de la validación")
p("La prueba de carga es una comprobación inicial, no una certificación de capacidad productiva. Para producción se recomienda ejecutar escenarios prolongados con k6 o Locust, datos representativos y métricas de CPU, memoria y base de datos. La disponibilidad medida corresponde únicamente al intervalo de prueba y no equivale a un acuerdo de nivel de servicio.")
subtitulo("Monitoreo y recuperación")
p("En un ambiente productivo, el despliegue debe conservar la imagen anterior, comparar el estado de salud y activar una reversión si falla la validación. Prometheus y Grafana pueden complementar el pipeline con métricas y alertas, mientras que los registros centralizados facilitan el análisis posterior.")
salto()

# 14
titulo("14. Buenas prácticas, escalamiento y conclusiones")
p("El proyecto combina automatización con revisión humana y responsabilidad compartida, principios esenciales de DevOps (Davis & Daniels, 2016). Las herramientas apoyan la calidad, pero no reemplazan el criterio del equipo.")
p("<b>Tabla 9. Prácticas implementadas</b>", caption)
tabla([
    ["Práctica", "Aplicación en el proyecto"],
    ["Revisión e integración", "Pull requests y validaciones antes de integrar."],
    ["Pipeline como código", "YAML versionado junto con la aplicación."],
    ["Puertas bloqueantes", "Pruebas, cobertura y seguridad condicionan la entrega."],
    ["Gestión de secretos", "Variables de entorno y secretos de GitHub."],
    ["Despliegue controlado", "Staging obligatorio y producción protegida."],
], [5.0 * cm, 10.9 * cm])
subtitulo("Escalamiento")
p("Para el trabajo colaborativo se propone proteger la rama principal, exigir revisiones y almacenar artefactos firmados. Para producción se debe incorporar una base de datos transaccional, migraciones con copia de seguridad, monitoreo y despliegues azul-verde o canary con posibilidad de reversión.")
subtitulo("Conclusiones")
p("El pipeline convirtió los criterios de calidad en verificaciones repetibles: 28 pruebas aprobadas, 99 % de cobertura, controles estáticos y de seguridad satisfactorios, empaquetado y validación de staging. La dependencia vulnerable y la mutación del cálculo demostraron que una falla bloquea la entrega hasta su corrección.")
p("El principal aprendizaje es que CI/CD exige diseño modular, evidencias y mejora continua. La automatización acelera las entregas, pero la promoción a producción debe mantener controles proporcionales al riesgo (Corporación Universitaria Tecnológica del Oriente, 2026a).")
salto()

# 15
titulo("Referencias")
p("Corporación Universitaria Tecnológica del Oriente. (2026a). <i>Automatización y entrega continua</i> [Material de estudio de la Unidad 3, Gestión del Software].", ref_style)
p("Corporación Universitaria Tecnológica del Oriente. (2026b). <i>Guía de aprendizaje: Gestión del Software</i> [Actividad AA2, Unidad 3].", ref_style)
p("Davis, J., & Daniels, K. (2016). <i>Effective DevOps: Building a culture of collaboration, affinity, and tooling at scale</i>. O’Reilly Media.", ref_style)
p("Smart, J. F. (2011). <i>Jenkins: The definitive guide</i>. O’Reilly Media.", ref_style)
subtitulo("Material complementario entregado")
p("El archivo ZIP incluye el código fuente, las pruebas, la configuración de GitHub Actions, el Dockerfile y las evidencias de ejecución en formatos JSON, XML y registros de consola.")


def numero_pagina(canvas, doc):
    canvas.saveState()
    canvas.setFont("Arial", 11)
    canvas.setFillColor(NEGRO)
    canvas.drawRightString(A4[0] - 2.54 * cm, A4[1] - 1.27 * cm, str(doc.page))
    canvas.restoreState()


doc = SimpleDocTemplate(
    str(SALIDA), pagesize=A4, rightMargin=2.54 * cm, leftMargin=2.54 * cm,
    topMargin=2.54 * cm, bottomMargin=2.54 * cm,
    title="AA2 — Construcción de un Pipeline para un Sistema de Restaurante",
    author="Einer Plaza Prasca", subject="Gestión del Software — CI/CD",
)
doc.build(story, onFirstPage=numero_pagina, onLaterPages=numero_pagina)
print(SALIDA)

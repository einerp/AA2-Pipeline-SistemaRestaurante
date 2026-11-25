# AA2 — Pipeline CI/CD para el Sistema de Gestión de Restaurante

**Estudiante:** Einer Plaza Prasca  
**Asignatura:** Gestión del Software  
**Unidad:** 3 — Automatización y entrega continua

## Descripción

Prototipo REST construido con Python y Flask para gestionar reservas, disponibilidad de mesas, pedidos, autenticación y reportes de ventas. El repositorio incluye un pipeline reproducible que integra construcción, análisis estático, pruebas, cobertura, seguridad, empaquetado y despliegue a staging.

## Estructura

- `src/restaurante/`: API y reglas de negocio.
- `tests/unit/`: pruebas de validación y cálculo.
- `tests/integration/`: pruebas de los endpoints REST.
- `.github/workflows/ci-cd.yml`: pipeline de GitHub Actions.
- `scripts/pipeline_local.py`: ejecución local de las puertas de calidad.
- `scripts/simular_fallo.py`: mutación controlada en una copia temporal.
- `scripts/validar_staging.py`: prueba funcional y carga ligera.
- `Dockerfile` y `docker-compose.staging.yml`: empaquetado y despliegue.
- `artifacts/evidencias/`: resultados reales de la ejecución local.

## Requisitos

- Python 3.12.
- Docker opcional para ejecutar el contenedor.
- Node.js solo para el comando opcional `npm run dev`.

## Configuración local

```bash
python -m venv .venv
# Windows: .venv\Scripts\python.exe -m pip install -r requirements-dev.txt
# Linux/macOS: .venv/bin/python -m pip install -r requirements-dev.txt
# Ejecutar desde la raíz del proyecto.
```

En Windows, complete la configuración con:

```bash
.venv\Scripts\python.exe -m pip install -e .
```

## Ejecutar el pipeline local

```bash
.venv\Scripts\python.exe scripts/pipeline_local.py
```

El proceso se detiene ante el primer incumplimiento y no autoriza el despliegue. El umbral mínimo de cobertura es 85 %. La ejecución final obtuvo 28 pruebas aprobadas y 99 % de cobertura.

## Simular un fallo sin modificar el código original

```bash
.venv\Scripts\python.exe scripts/simular_fallo.py
```

El script modifica el total del pedido en una copia temporal. Las pruebas detectan la diferencia de COP 1.000 y devuelven un estado de fallo, lo que impide la entrega.

## Ejecutar la API

```bash
# Vista previa local, puerto 7100
npm run dev -- --host 127.0.0.1 --port 7100

# Alternativa directa en Windows
set PYTHONPATH=src
set PORT=8080
.venv\Scripts\python.exe -m restaurante.app
```

Compruebe `GET /api/salud`. Los módulos disponibles son:

| Método | Ruta | Propósito |
|---|---|---|
| GET | `/api/salud` | Verificar disponibilidad |
| GET | `/api/mesas?fecha=AAAA-MM-DD&hora=HH:MM` | Consultar mesas |
| POST | `/api/reservas` | Confirmar una reserva |
| POST | `/api/pedidos` | Registrar y calcular un pedido |
| GET | `/api/pedidos/<id>` | Consultar un pedido |
| GET | `/api/reportes/ventas` | Consolidar ventas |
| POST | `/api/autenticacion` | Validar credenciales por variables de entorno |

## Docker y GitHub Actions

```bash
docker build -t sistema-restaurante:local .
docker run --rm -p 8080:8080 -e AUTENTICACION_CLAVE=staging-local sistema-restaurante:local
```

En GitHub, agregue el secreto `CLAVE_STAGING` y proteja los ambientes `staging` y `production`. Los `push` a `main`, las solicitudes de extracción y las ejecuciones manuales activan el flujo. Producción requiere aprobación del ambiente protegido.

## Evidencias de la ejecución final

- 28 pruebas unitarias y de integración aprobadas.
- Cobertura total: 99 % (mínimo exigido: 85 %).
- Ruff: todas las comprobaciones aprobadas.
- Bandit: sin hallazgos en la versión corregida.
- pip-audit: sin vulnerabilidades conocidas con Flask 3.1.3.
- Staging: prueba funcional exitosa, 30 solicitudes, 0 errores.
- Disponibilidad durante la prueba: 100 %; latencia p95: 18,45 ms.

> Los resultados corresponden a una ejecución local real. La construcción del contenedor está configurada en GitHub Actions; Docker no estaba instalado en el equipo usado para la evidencia local.

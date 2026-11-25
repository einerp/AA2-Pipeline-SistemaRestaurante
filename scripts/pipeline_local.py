"""Ejecuta localmente las mismas puertas de calidad definidas en GitHub Actions."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
import urllib.request
from datetime import datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
EVIDENCIAS = RAIZ / "artifacts" / "evidencias"
EVIDENCIAS.mkdir(parents=True, exist_ok=True)


def ejecutar(nombre: str, comando: list[str]) -> None:
    print(f"\n=== {nombre} ===", flush=True)
    proceso = subprocess.run(
        comando, cwd=RAIZ, text=True, capture_output=True, encoding="utf-8", errors="replace"
    )
    texto = f"$ {' '.join(comando)}\n{proceso.stdout}{proceso.stderr}"
    (EVIDENCIAS / f"{nombre}.log").write_text(texto, encoding="utf-8")
    print(texto, flush=True)
    if proceso.returncode != 0:
        raise RuntimeError(f"Pipeline detenido en {nombre}; no se autoriza el despliegue.")


def esperar_salud(proceso: subprocess.Popen) -> None:
    for _ in range(30):
        if proceso.poll() is not None:
            raise RuntimeError("El servidor de staging terminó inesperadamente.")
        try:
            with urllib.request.urlopen("http://127.0.0.1:5055/api/salud", timeout=1) as r:
                if r.status == 200:
                    return
        except OSError:
            time.sleep(0.25)
    raise RuntimeError("El servidor de staging no respondió a tiempo.")


def main() -> None:
    os.environ["PYTHONPATH"] = str(RAIZ / "src")
    inicio = datetime.now().astimezone()
    ejecutar("01_construccion", [sys.executable, "-m", "compileall", "-q", "src"])
    ejecutar("02_calidad", [sys.executable, "-m", "ruff", "check", "src", "tests", "scripts"])
    ejecutar(
        "03_pruebas",
        [
            sys.executable,
            "-m",
            "coverage",
            "run",
            "-m",
            "pytest",
            "-q",
            "--junitxml=artifacts/evidencias/pytest.xml",
        ],
    )
    ejecutar("04_cobertura", [sys.executable, "-m", "coverage", "report", "--fail-under=85"])
    ejecutar(
        "05_cobertura_xml",
        [sys.executable, "-m", "coverage", "xml", "-o", "artifacts/evidencias/cobertura.xml"],
    )
    ejecutar(
        "06_seguridad_estatica",
        [
            sys.executable,
            "-m",
            "bandit",
            "-q",
            "-r",
            "src",
            "-f",
            "json",
            "-o",
            "artifacts/evidencias/bandit.json",
        ],
    )
    ejecutar("07_dependencias", [sys.executable, "-m", "pip_audit", "-r", "requirements.txt"])
    ejecutar("08_empaquetado", [sys.executable, "-m", "build"])

    entorno = os.environ.copy()
    entorno.update(
        {
            "PYTHONPATH": str(RAIZ / "src"),
            "PORT": "5055",
            "AUTENTICACION_CLAVE": "staging-local",
            "URL_STAGING": "http://127.0.0.1:5055",
        }
    )
    proceso = subprocess.Popen(
        [sys.executable, "-m", "restaurante.app"],
        cwd=RAIZ,
        env=entorno,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    try:
        esperar_salud(proceso)
        ejecutar("09_staging", [sys.executable, "scripts/validar_staging.py"])
    finally:
        proceso.terminate()
        try:
            salida, _ = proceso.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            proceso.kill()
            salida, _ = proceso.communicate(timeout=5)
        (EVIDENCIAS / "servidor_staging.log").write_text(salida or "", encoding="utf-8")

    resumen = {
        "proyecto": "Sistema de Gestión de Restaurante",
        "inicio": inicio.isoformat(),
        "fin": datetime.now().astimezone().isoformat(),
        "resultado": "EXITOSO",
        "etapas": [
            "build",
            "lint",
            "test",
            "coverage",
            "security",
            "package",
            "deploy-staging",
            "smoke-performance",
        ],
    }
    (EVIDENCIAS / "pipeline_resumen.json").write_text(
        json.dumps(resumen, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print("\nPIPELINE EXITOSO: artefacto validado y despliegue de staging comprobado.")


if __name__ == "__main__":
    main()

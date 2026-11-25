"""Introduce una mutación en una copia temporal y demuestra que las pruebas la detectan."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
SALIDA = RAIZ / "artifacts" / "evidencias" / "fallo_controlado.log"


def main() -> None:
    carpeta_temporal = RAIZ / "artifacts" / "temporal"
    carpeta_temporal.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=carpeta_temporal) as temporal:
        copia = Path(temporal)
        shutil.copytree(RAIZ / "src", copia / "src")
        shutil.copytree(RAIZ / "tests", copia / "tests")
        shutil.copy2(RAIZ / "pyproject.toml", copia / "pyproject.toml")
        modelo = copia / "src" / "restaurante" / "modelos.py"
        contenido = modelo.read_text(encoding="utf-8")
        marca = '"platos": detalle, "total": total}'
        if marca not in contenido:
            raise RuntimeError("No se encontró el punto de mutación controlado.")
        modelo.write_text(
            contenido.replace(marca, '"platos": detalle, "total": total + 1000}'),
            encoding="utf-8",
        )
        entorno = os.environ.copy()
        entorno["PYTHONPATH"] = str(copia / "src")
        proceso = subprocess.run(
            [sys.executable, "-m", "pytest", "tests/unit/test_modelos.py", "-q"],
            cwd=copia,
            env=entorno,
            text=True,
            capture_output=True,
            check=False,
        )
        texto = (
            f"Fecha UTC: {datetime.now(UTC).isoformat()}\n"
            "Mutación: sumar COP 1.000 al total del pedido.\n"
            "Alcance: copia temporal; el código original no fue modificado.\n\n"
            f"{proceso.stdout}\n{proceso.stderr}\n"
            f"Resultado: pruebas fallidas detectadas (código {proceso.returncode}).\n"
            "Decisión del pipeline: detener y NO desplegar. Corrección: revertir la mutación.\n"
        )
        SALIDA.parent.mkdir(parents=True, exist_ok=True)
        SALIDA.write_text(texto, encoding="utf-8")
        print(texto)
        if proceso.returncode == 0:
            raise SystemExit("La mutación no fue detectada; revise las pruebas.")


if __name__ == "__main__":
    main()

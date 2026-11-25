"""Adaptador de arranque para npm run dev y la vista previa local."""

import argparse
import os
import subprocess
import sys
from pathlib import Path

raiz = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument("--host", default="127.0.0.1")
parser.add_argument("--port", default="7100")
argumentos = parser.parse_args()
python_local = raiz / ".venv" / "Scripts" / "python.exe"
python = str(python_local) if python_local.exists() else sys.executable
entorno = os.environ.copy()
entorno["HOST"] = argumentos.host
entorno["PORT"] = str(argumentos.port)
entorno["PYTHONPATH"] = str(raiz / "src")
resultado = subprocess.run([python, "-m", "restaurante.app"], cwd=raiz, env=entorno)
raise SystemExit(resultado.returncode)

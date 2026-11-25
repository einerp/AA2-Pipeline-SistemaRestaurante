"""Punto de entrada serverless de Vercel para la aplicación Flask."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from restaurante.app import app  # noqa: E402

__all__ = ["app"]

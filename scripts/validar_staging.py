"""Pruebas de humo y carga ligera contra el ambiente de staging."""

from __future__ import annotations

import json
import os
import statistics
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

BASE = os.environ.get("URL_STAGING", "http://127.0.0.1:5055")
SALIDA = Path(__file__).resolve().parents[1] / "artifacts" / "evidencias" / "staging.json"


def solicitar(ruta: str, datos: dict | None = None) -> tuple[int, dict]:
    cuerpo = json.dumps(datos).encode() if datos is not None else None
    peticion = urllib.request.Request(
        f"{BASE}{ruta}", data=cuerpo, headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(peticion, timeout=5) as respuesta:
        return respuesta.status, json.load(respuesta)


def medir_salud(_: int) -> float:
    inicio = time.perf_counter()
    estado, cuerpo = solicitar("/api/salud")
    assert estado == 200 and cuerpo["estado"] == "ok"
    return (time.perf_counter() - inicio) * 1000


def main() -> None:
    estado, pedido = solicitar(
        "/api/pedidos",
        {
            "cliente": "Prueba Staging",
            "platos": [{"id": 1, "cantidad": 1}, {"id": 4, "cantidad": 2}],
        },
    )
    assert estado == 201 and pedido["total"] == 42_000
    with ThreadPoolExecutor(max_workers=6) as ejecutor:
        tiempos = list(ejecutor.map(medir_salud, range(30)))
    tiempos.sort()
    resultado = {
        "prueba_funcional": "exitosa",
        "solicitudes": len(tiempos),
        "errores": 0,
        "disponibilidad_porcentaje": 100.0,
        "latencia_promedio_ms": round(statistics.mean(tiempos), 2),
        "latencia_p95_ms": round(tiempos[28], 2),
        "umbral_p95_ms": 500,
        "resultado": "APROBADO" if tiempos[28] < 500 else "FALLIDO",
    }
    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    SALIDA.write_text(json.dumps(resultado, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(resultado, indent=2, ensure_ascii=False))
    if resultado["resultado"] != "APROBADO":
        raise SystemExit(1)


if __name__ == "__main__":
    main()

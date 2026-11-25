"""Persistencia mediante la API REST de Supabase para el despliegue en Vercel."""

from __future__ import annotations

import json
import os
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlsplit
from urllib.request import Request, urlopen


class ErrorPersistencia(RuntimeError):
    """Error seguro para informar una indisponibilidad de Supabase."""


Transporte = Callable[[str, str, dict[str, Any] | None], Any]


class RepositorioSupabase:
    def __init__(
        self,
        url: str | None = None,
        clave: str | None = None,
        transporte: Transporte | None = None,
    ) -> None:
        self.url = (url or os.environ.get("SUPABASE_URL", "")).rstrip("/")
        self.clave = clave or os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
        if not self.url or not self.clave:
            raise ErrorPersistencia("Faltan las credenciales de Supabase.")
        partes = urlsplit(self.url)
        if partes.scheme != "https" or not partes.hostname:
            raise ErrorPersistencia("La URL de Supabase debe usar HTTPS.")
        self._transporte = transporte or self._http

    def _http(self, metodo: str, ruta: str, datos: dict[str, Any] | None) -> Any:
        cuerpo = json.dumps(datos).encode("utf-8") if datos is not None else None
        solicitud = Request(
            f"{self.url}/rest/v1/{ruta}",
            data=cuerpo,
            method=metodo,
            headers={
                "apikey": self.clave,
                "Authorization": f"Bearer {self.clave}",
                "Content-Type": "application/json",
                "Prefer": "return=representation",
            },
        )
        try:
            with urlopen(solicitud, timeout=10) as respuesta:  # nosec B310
                contenido = respuesta.read().decode("utf-8")
        except HTTPError as exc:
            if exc.code == 409:
                raise ValueError("La mesa ya está reservada para esa fecha y hora.") from exc
            raise ErrorPersistencia("Supabase rechazó la operación.") from exc
        except URLError as exc:
            raise ErrorPersistencia("No fue posible conectar con Supabase.") from exc
        return json.loads(contenido) if contenido else None

    def mesa_disponible(self, mesa: int, fecha: str, hora: str) -> bool:
        consulta = urlencode(
            {
                "mesa": f"eq.{mesa}",
                "fecha": f"eq.{fecha}",
                "hora": f"eq.{hora}",
                "select": "id",
                "limit": 1,
            }
        )
        return not self._transporte("GET", f"reservas?{consulta}", None)

    def guardar_reserva(self, reserva: dict[str, Any]) -> dict[str, Any]:
        registro = self._transporte("POST", "reservas", reserva)[0]
        return registro

    def guardar_pedido(self, pedido: dict[str, Any]) -> dict[str, Any]:
        registro = self._transporte("POST", "pedidos", pedido)[0]
        return registro

    def obtener_pedido(self, pedido_id: int) -> dict[str, Any] | None:
        consulta = urlencode({"id": f"eq.{pedido_id}", "select": "*", "limit": 1})
        registros = self._transporte("GET", f"pedidos?{consulta}", None)
        return registros[0] if registros else None

    def reporte_ventas(self) -> dict[str, int]:
        pedidos = self._transporte("GET", "pedidos?select=total", None)
        return {
            "cantidad_pedidos": len(pedidos),
            "ingresos": sum(pedido["total"] for pedido in pedidos),
        }

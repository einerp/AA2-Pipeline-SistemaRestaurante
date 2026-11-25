"""Almacenamiento en memoria para el prototipo y el entorno de pruebas."""

from __future__ import annotations

from threading import RLock
from typing import Any


class RepositorioRestaurante:
    def __init__(self) -> None:
        self.reservas: dict[int, dict[str, Any]] = {}
        self.pedidos: dict[int, dict[str, Any]] = {}
        self._consecutivo = 0
        self._lock = RLock()

    def _siguiente_id(self) -> int:
        with self._lock:
            self._consecutivo += 1
            return self._consecutivo

    def mesa_disponible(self, mesa: int, fecha: str, hora: str) -> bool:
        return not any(
            r["mesa"] == mesa and r["fecha"] == fecha and r["hora"] == hora
            for r in self.reservas.values()
        )

    def guardar_reserva(self, reserva: dict[str, Any]) -> dict[str, Any]:
        with self._lock:
            if not self.mesa_disponible(reserva["mesa"], reserva["fecha"], reserva["hora"]):
                raise ValueError("La mesa ya está reservada para esa fecha y hora.")
            registro = {"id": self._siguiente_id(), **reserva, "estado": "confirmada"}
            self.reservas[registro["id"]] = registro
            return registro

    def guardar_pedido(self, pedido: dict[str, Any]) -> dict[str, Any]:
        registro = {"id": self._siguiente_id(), **pedido, "estado": "recibido"}
        self.pedidos[registro["id"]] = registro
        return registro

    def obtener_pedido(self, pedido_id: int) -> dict[str, Any] | None:
        return self.pedidos.get(pedido_id)

    def reporte_ventas(self) -> dict[str, int]:
        return {
            "cantidad_pedidos": len(self.pedidos),
            "ingresos": sum(p["total"] for p in self.pedidos.values()),
        }

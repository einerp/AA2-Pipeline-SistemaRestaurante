"""Reglas de negocio puras: facilitan las pruebas unitarias."""

from __future__ import annotations

import re
from datetime import date, datetime
from typing import Any

MENU = {
    1: {"nombre": "Bandeja paisa", "precio": 28_000},
    2: {"nombre": "Ajiaco", "precio": 24_000},
    3: {"nombre": "Sancocho", "precio": 22_000},
    4: {"nombre": "Jugo natural", "precio": 7_000},
}

MESAS = {mesa: capacidad for mesa, capacidad in enumerate([2, 2, 4, 4, 4, 6, 6, 8], start=1)}


def validar_reserva(datos: dict[str, Any]) -> dict[str, Any]:
    """Normaliza y valida una reserva; lanza ValueError si es inválida."""
    cliente = str(datos.get("cliente", "")).strip()
    correo = str(datos.get("correo", "")).strip().lower()
    if len(cliente) < 3:
        raise ValueError("El nombre del cliente debe tener al menos 3 caracteres.")
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", correo):
        raise ValueError("El correo electrónico no es válido.")
    try:
        fecha = date.fromisoformat(str(datos.get("fecha", "")))
        hora = datetime.strptime(str(datos.get("hora", "")), "%H:%M").strftime("%H:%M")
        personas = int(datos.get("personas", 0))
        mesa = int(datos.get("mesa", 0))
    except (TypeError, ValueError) as exc:
        raise ValueError("Fecha, hora, personas o mesa tienen un formato inválido.") from exc
    if fecha < date.today():
        raise ValueError("No se permiten reservas en fechas pasadas.")
    if not 1 <= personas <= 8:
        raise ValueError("La reserva debe ser para 1 a 8 personas.")
    if mesa not in MESAS:
        raise ValueError("La mesa solicitada no existe.")
    if personas > MESAS[mesa]:
        raise ValueError("La mesa no tiene capacidad suficiente.")
    return {
        "cliente": cliente,
        "correo": correo,
        "fecha": fecha.isoformat(),
        "hora": hora,
        "personas": personas,
        "mesa": mesa,
    }


def calcular_pedido(datos: dict[str, Any]) -> dict[str, Any]:
    """Valida los platos y calcula el total sin depender del framework web."""
    cliente = str(datos.get("cliente", "")).strip()
    platos = datos.get("platos")
    tipo = str(datos.get("tipo", "recoger"))
    if len(cliente) < 3:
        raise ValueError("El nombre del cliente debe tener al menos 3 caracteres.")
    if not isinstance(platos, list) or not platos:
        raise ValueError("El pedido debe incluir al menos un plato.")
    if tipo not in {"recoger", "domicilio"}:
        raise ValueError("El tipo de pedido debe ser recoger o domicilio.")
    total = 0
    detalle = []
    for item in platos:
        try:
            plato_id = int(item.get("id", 0))
            cantidad = int(item.get("cantidad", 0))
        except (AttributeError, TypeError, ValueError) as exc:
            raise ValueError("Cada plato debe tener id y cantidad válidos.") from exc
        if plato_id not in MENU or cantidad < 1 or cantidad > 20:
            raise ValueError("El plato no existe o la cantidad está fuera de rango.")
        subtotal = MENU[plato_id]["precio"] * cantidad
        total += subtotal
        detalle.append({"id": plato_id, "cantidad": cantidad, "subtotal": subtotal})
    return {"cliente": cliente, "tipo": tipo, "platos": detalle, "total": total}

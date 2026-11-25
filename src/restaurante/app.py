"""API REST del sistema de restaurante."""

from __future__ import annotations

import hmac
import os
from http import HTTPStatus
from typing import Any

from flask import Flask, jsonify, request
from waitress import serve

from .modelos import MESAS, calcular_pedido, validar_reserva
from .repositorio import RepositorioRestaurante
from .supabase_repositorio import ErrorPersistencia, RepositorioSupabase


def create_app(repositorio=None) -> Flask:
    app = Flask(__name__)
    usa_supabase = os.environ.get("SUPABASE_URL") and os.environ.get(
        "SUPABASE_SERVICE_ROLE_KEY"
    )
    repo = repositorio or (RepositorioSupabase() if usa_supabase else RepositorioRestaurante())
    app.config.update(TESTING=False, JSON_SORT_KEYS=False)

    def datos_json() -> dict[str, Any]:
        datos = request.get_json(silent=True)
        if not isinstance(datos, dict):
            raise ValueError("Se requiere un cuerpo JSON válido.")
        return datos

    @app.errorhandler(ValueError)
    def error_validacion(error: ValueError):
        return jsonify({"error": str(error)}), HTTPStatus.BAD_REQUEST

    @app.errorhandler(ErrorPersistencia)
    def error_persistencia(error: ErrorPersistencia):
        return jsonify({"error": str(error)}), HTTPStatus.SERVICE_UNAVAILABLE

    @app.get("/")
    def inicio():
        return jsonify(
            {
                "servicio": "Sistema de Gestión de Restaurante",
                "version": "1.0.0",
                "documentacion": "/api/salud",
            }
        )

    @app.get("/api/salud")
    def salud():
        persistencia = "supabase" if isinstance(repo, RepositorioSupabase) else "memoria"
        return jsonify(
            {
                "estado": "ok",
                "servicio": "restaurante",
                "version": "1.0.0",
                "persistencia": persistencia,
            }
        )

    @app.get("/api/mesas")
    def mesas():
        fecha = request.args.get("fecha", "")
        hora = request.args.get("hora", "")
        return jsonify(
            {
                "mesas": [
                    {
                        "id": mesa,
                        "capacidad": capacidad,
                        "disponible": repo.mesa_disponible(mesa, fecha, hora),
                    }
                    for mesa, capacidad in MESAS.items()
                ]
            }
        )

    @app.post("/api/reservas")
    def crear_reserva():
        reserva = validar_reserva(datos_json())
        return jsonify(repo.guardar_reserva(reserva)), HTTPStatus.CREATED

    @app.post("/api/pedidos")
    def crear_pedido():
        pedido = calcular_pedido(datos_json())
        return jsonify(repo.guardar_pedido(pedido)), HTTPStatus.CREATED

    @app.get("/api/pedidos/<int:pedido_id>")
    def consultar_pedido(pedido_id: int):
        pedido = repo.obtener_pedido(pedido_id)
        if pedido is None:
            return jsonify({"error": "Pedido no encontrado."}), HTTPStatus.NOT_FOUND
        return jsonify(pedido)

    @app.get("/api/reportes/ventas")
    def reporte_ventas():
        return jsonify(repo.reporte_ventas())

    @app.post("/api/autenticacion")
    def autenticacion():
        datos = datos_json()
        usuario_esperado = os.environ.get("AUTENTICACION_USUARIO", "admin")
        clave_esperada = os.environ.get("AUTENTICACION_CLAVE")
        if not clave_esperada:
            return jsonify(
                {"error": "Autenticación no configurada."}
            ), HTTPStatus.SERVICE_UNAVAILABLE
        valido = hmac.compare_digest(str(datos.get("usuario", "")), usuario_esperado)
        valido = hmac.compare_digest(str(datos.get("clave", "")), clave_esperada) and valido
        if not valido:
            return jsonify({"error": "Credenciales incorrectas."}), HTTPStatus.UNAUTHORIZED
        return jsonify({"mensaje": "Autenticación correcta.", "usuario": usuario_esperado})

    return app


app = create_app()

if __name__ == "__main__":  # pragma: no cover
    serve(
        app,
        host=os.environ.get("HOST", "127.0.0.1"),
        port=int(os.environ.get("PORT", "8080")),
        threads=8,
    )

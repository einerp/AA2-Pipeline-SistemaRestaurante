from datetime import date, timedelta
from unittest.mock import patch

import pytest

from restaurante.app import create_app

FECHA = (date.today() + timedelta(days=10)).isoformat()


@pytest.fixture()
def cliente():
    app = create_app()
    app.config.update(TESTING=True)
    return app.test_client()


def reserva(mesa=3):
    return {
        "cliente": "Einer Plaza",
        "correo": "einer@correo.com",
        "fecha": FECHA,
        "hora": "20:00",
        "personas": 4,
        "mesa": mesa,
    }


def test_salud(cliente):
    respuesta = cliente.get("/api/salud")
    assert respuesta.status_code == 200
    assert respuesta.get_json()["estado"] == "ok"


def test_inicio(cliente):
    assert cliente.get("/").status_code == 200


def test_crear_y_consultar_disponibilidad(cliente):
    respuesta = cliente.post("/api/reservas", json=reserva())
    assert respuesta.status_code == 201
    assert respuesta.get_json()["estado"] == "confirmada"
    mesas = cliente.get(f"/api/mesas?fecha={FECHA}&hora=20:00").get_json()["mesas"]
    assert mesas[2]["disponible"] is False
    assert mesas[3]["disponible"] is True


def test_no_duplica_reserva(cliente):
    cliente.post("/api/reservas", json=reserva())
    respuesta = cliente.post("/api/reservas", json=reserva())
    assert respuesta.status_code == 400
    assert "ya está reservada" in respuesta.get_json()["error"]


def test_rechaza_json_ausente(cliente):
    assert cliente.post("/api/reservas").status_code == 400


def test_crear_consultar_pedido_y_reporte(cliente):
    creado = cliente.post(
        "/api/pedidos",
        json={
            "cliente": "Cliente API",
            "platos": [{"id": 2, "cantidad": 2}],
        },
    )
    assert creado.status_code == 201
    pedido_id = creado.get_json()["id"]
    consulta = cliente.get(f"/api/pedidos/{pedido_id}")
    assert consulta.get_json()["total"] == 48_000
    reporte = cliente.get("/api/reportes/ventas").get_json()
    assert reporte == {"cantidad_pedidos": 1, "ingresos": 48_000}


def test_pedido_no_encontrado(cliente):
    assert cliente.get("/api/pedidos/999").status_code == 404


def test_autenticacion_correcta(cliente):
    with patch.dict("os.environ", {"AUTENTICACION_CLAVE": "secreto-pruebas"}):
        respuesta = cliente.post(
            "/api/autenticacion", json={"usuario": "admin", "clave": "secreto-pruebas"}
        )
    assert respuesta.status_code == 200


def test_autenticacion_rechaza_credenciales(cliente):
    with patch.dict("os.environ", {"AUTENTICACION_CLAVE": "secreto-pruebas"}):
        respuesta = cliente.post(
            "/api/autenticacion", json={"usuario": "admin", "clave": "incorrecta"}
        )
    assert respuesta.status_code == 401


def test_autenticacion_requiere_configuracion(cliente):
    with patch.dict("os.environ", {}, clear=True):
        respuesta = cliente.post("/api/autenticacion", json={})
    assert respuesta.status_code == 503

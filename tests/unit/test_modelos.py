from datetime import date, timedelta

import pytest

from restaurante.modelos import calcular_pedido, validar_reserva

FECHA_FUTURA = (date.today() + timedelta(days=7)).isoformat()


def reserva_valida():
    return {
        "cliente": "Einer Plaza",
        "correo": "EINER@CORREO.COM",
        "fecha": FECHA_FUTURA,
        "hora": "19:30",
        "personas": 4,
        "mesa": 3,
    }


def test_validar_reserva_normaliza_datos():
    resultado = validar_reserva(reserva_valida())
    assert resultado["correo"] == "einer@correo.com"
    assert resultado["fecha"] == FECHA_FUTURA


@pytest.mark.parametrize(
    ("campo", "valor"),
    [
        ("cliente", "A"),
        ("correo", "correo-invalido"),
        ("fecha", "2020-01-01"),
        ("fecha", "fecha-invalida"),
        ("hora", "25:00"),
        ("personas", 0),
        ("personas", 9),
        ("mesa", 99),
    ],
)
def test_validar_reserva_rechaza_datos_invalidos(campo, valor):
    datos = reserva_valida()
    datos[campo] = valor
    with pytest.raises(ValueError):
        validar_reserva(datos)


def test_validar_reserva_controla_capacidad():
    datos = reserva_valida()
    datos.update(personas=5, mesa=1)
    with pytest.raises(ValueError, match="capacidad"):
        validar_reserva(datos)


def test_calcular_pedido_total():
    pedido = calcular_pedido(
        {
            "cliente": "Cliente Uno",
            "tipo": "domicilio",
            "platos": [{"id": 1, "cantidad": 2}, {"id": 4, "cantidad": 1}],
        }
    )
    assert pedido["total"] == 63_000
    assert len(pedido["platos"]) == 2


@pytest.mark.parametrize(
    "pedido",
    [
        {},
        {"cliente": "Cliente", "platos": []},
        {"cliente": "Cliente", "platos": [{"id": 99, "cantidad": 1}]},
        {"cliente": "Cliente", "platos": [{"id": 1, "cantidad": 0}]},
        {"cliente": "Cliente", "platos": [{"id": 1, "cantidad": 21}]},
        {"cliente": "Cliente", "platos": [{}]},
        {"cliente": "Cliente", "platos": [{"id": 1}], "tipo": "local"},
    ],
)
def test_calcular_pedido_rechaza_datos_invalidos(pedido):
    with pytest.raises(ValueError):
        calcular_pedido(pedido)

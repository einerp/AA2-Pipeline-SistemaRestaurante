from restaurante.supabase_repositorio import RepositorioSupabase


class TransporteFalso:
    def __init__(self):
        self.reservas = []
        self.pedidos = []

    def __call__(self, metodo, ruta, datos):
        if metodo == "POST" and ruta == "reservas":
            registro = {"id": 1, **datos, "estado": "confirmada"}
            self.reservas.append(registro)
            return [registro]
        if metodo == "POST" and ruta == "pedidos":
            registro = {"id": 1, **datos, "estado": "recibido"}
            self.pedidos.append(registro)
            return [registro]
        if metodo == "GET" and ruta.startswith("reservas?"):
            return self.reservas
        if metodo == "GET" and ruta.startswith("pedidos?id="):
            pedido_id = int(ruta.split("id=eq.")[1].split("&")[0])
            return [pedido for pedido in self.pedidos if pedido["id"] == pedido_id]
        if metodo == "GET" and ruta == "pedidos?select=total":
            return [{"total": pedido["total"]} for pedido in self.pedidos]
        raise AssertionError((metodo, ruta, datos))


def repositorio():
    return RepositorioSupabase(
        "https://proyecto.supabase.co", "clave-pruebas", TransporteFalso()
    )


def test_reserva_y_disponibilidad():
    repo = repositorio()
    reserva = {"cliente": "Einer", "mesa": 3, "fecha": "2026-12-01", "hora": "20:00"}
    assert repo.mesa_disponible(3, "2026-12-01", "20:00") is True
    assert repo.guardar_reserva(reserva)["id"] == 1
    assert repo.mesa_disponible(3, "2026-12-01", "20:00") is False


def test_pedido_consulta_y_reporte():
    repo = repositorio()
    pedido = {"cliente": "Cliente", "tipo": "recoger", "platos": [], "total": 48000}
    assert repo.guardar_pedido(pedido)["estado"] == "recibido"
    assert repo.obtener_pedido(1)["total"] == 48000
    assert repo.reporte_ventas() == {"cantidad_pedidos": 1, "ingresos": 48000}
    assert repo.obtener_pedido(2) is None

export const TASA_IMPUESTO = 0.08;

export function redondear(valor) {
  return Math.round((Number(valor) + Number.EPSILON) * 100) / 100;
}

export function calcularTotales(carrito, tasa = TASA_IMPUESTO) {
  if (!Array.isArray(carrito)) throw new TypeError('El carrito debe ser una lista.');
  if (!Number.isFinite(tasa) || tasa < 0 || tasa > 1) throw new RangeError('La tasa de impuesto no es válida.');
  const subtotal = redondear(carrito.reduce((suma, item) => {
    const cantidad = Number(item.cantidad);
    const precio = Number(item.precio);
    if (!Number.isInteger(cantidad) || cantidad < 1) throw new RangeError('La cantidad debe ser un entero positivo.');
    if (!Number.isFinite(precio) || precio < 0) throw new RangeError('El precio no es válido.');
    return suma + cantidad * precio;
  }, 0));
  const impuesto = redondear(subtotal * tasa);
  return { subtotal, impuesto, total: redondear(subtotal + impuesto) };
}

export function agregarAlCarrito(carrito, producto) {
  if (!producto?.id || !Number.isFinite(Number(producto.precio))) throw new TypeError('Producto no válido.');
  if (!Number.isInteger(producto.stock) || producto.stock < 1) throw new RangeError('No hay unidades disponibles.');
  const existente = carrito.find((item) => item.producto_id === producto.id);
  if (existente) {
    if (existente.cantidad >= producto.stock) throw new RangeError('La cantidad supera el inventario disponible.');
    return carrito.map((item) => item.producto_id === producto.id ? { ...item, cantidad: item.cantidad + 1 } : item);
  }
  return [...carrito, { producto_id: producto.id, nombre: producto.nombre, precio: Number(producto.precio), cantidad: 1, stock: producto.stock }];
}

export function cambiarCantidad(carrito, productoId, delta) {
  return carrito.flatMap((item) => {
    if (item.producto_id !== productoId) return [item];
    const cantidad = item.cantidad + delta;
    if (cantidad > item.stock) throw new RangeError('La cantidad supera el inventario disponible.');
    return cantidad > 0 ? [{ ...item, cantidad }] : [];
  });
}

export function formatoCOP(valor) {
  return new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 }).format(Number(valor) || 0);
}

export function prepararFactura(carrito, cliente) {
  if (!carrito.length) throw new RangeError('Agregue al menos un producto.');
  const nombre = cliente?.nombre?.trim();
  if (!nombre || nombre.length < 2) throw new RangeError('Ingrese el nombre del cliente.');
  return {
    p_cliente_nombre: nombre,
    p_cliente_documento: cliente?.documento?.trim() || '222222222222',
    p_items: carrito.map(({ producto_id, cantidad }) => ({ producto_id, cantidad })),
  };
}

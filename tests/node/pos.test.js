import test from 'node:test';
import assert from 'node:assert/strict';
import { agregarAlCarrito, calcularTotales, cambiarCantidad, formatoCOP, prepararFactura } from '../../src/lib/pos.js';

const producto = { id: 'p1', nombre: 'Sopa del día', precio: 12000, stock: 3 };

test('agrega un producto nuevo al carrito', () => {
  const carrito = agregarAlCarrito([], producto);
  assert.equal(carrito.length, 1);
  assert.equal(carrito[0].cantidad, 1);
});

test('acumula cantidades sin mutar el carrito original', () => {
  const inicial = agregarAlCarrito([], producto);
  const resultado = agregarAlCarrito(inicial, producto);
  assert.equal(resultado[0].cantidad, 2);
  assert.equal(inicial[0].cantidad, 1);
});

test('impide vender más unidades que el inventario', () => {
  let carrito = agregarAlCarrito([], producto);
  carrito = agregarAlCarrito(carrito, producto);
  carrito = agregarAlCarrito(carrito, producto);
  assert.throws(() => agregarAlCarrito(carrito, producto), /inventario/);
});

test('elimina el artículo cuando la cantidad llega a cero', () => {
  const carrito = agregarAlCarrito([], producto);
  assert.deepEqual(cambiarCantidad(carrito, 'p1', -1), []);
});

test('calcula subtotal, impuesto y total con redondeo monetario', () => {
  const totales = calcularTotales([{ cantidad: 2, precio: 12500.25 }]);
  assert.deepEqual(totales, { subtotal: 25000.5, impuesto: 2000.04, total: 27000.54 });
});

test('el carrito vacío tiene totales en cero', () => {
  assert.deepEqual(calcularTotales([]), { subtotal: 0, impuesto: 0, total: 0 });
});

test('rechaza cantidades y precios inválidos', () => {
  assert.throws(() => calcularTotales([{ cantidad: 0, precio: 1000 }]), /cantidad/);
  assert.throws(() => calcularTotales([{ cantidad: 1, precio: -5 }]), /precio/);
});

test('prepara el payload de factura para la función transaccional', () => {
  const carrito = agregarAlCarrito([], producto);
  const payload = prepararFactura(carrito, { nombre: 'Cliente de prueba', documento: '123' });
  assert.equal(payload.p_cliente_nombre, 'Cliente de prueba');
  assert.equal(payload.p_items[0].producto_id, 'p1');
});

test('exige productos y nombre del cliente para facturar', () => {
  assert.throws(() => prepararFactura([], { nombre: 'Cliente' }), /producto/);
  assert.throws(() => prepararFactura([{}], { nombre: '' }), /nombre/);
});

test('presenta valores en pesos colombianos', () => {
  assert.match(formatoCOP(12000), /12\.000/);
});

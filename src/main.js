import '@fontsource-variable/manrope';
import '@fontsource-variable/fraunces';
import 'bootstrap/dist/css/bootstrap.min.css';
import 'bootstrap-icons/font/bootstrap-icons.css';
import './styles.css';
import { Collapse, Modal, Toast } from 'bootstrap';
import { agregarAlCarrito, calcularTotales, cambiarCantidad, formatoCOP, prepararFactura } from './lib/pos.js';
import { cargarDatos, supabase, supabaseConfigurado } from './lib/supabase.js';

const app = document.querySelector('#app');
const modalRoot = document.querySelector('#modal-root');
const estado = {
  usuario: null,
  vista: 'resumen',
  categorias: [],
  productos: [],
  facturas: [],
  carrito: [],
  categoriaPos: 'todas',
  busqueda: '',
  modoAuth: 'login',
};

const vistas = [
  ['resumen', 'grid-1x2-gap', 'Resumen'],
  ['categorias', 'tags', 'Categorías'],
  ['productos', 'box-seam', 'Productos'],
  ['pos', 'cart3', 'Punto de venta'],
  ['facturas', 'receipt', 'Facturas'],
];

const escapar = (valor = '') => String(valor).replace(/[&<>'"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' })[c]);
const fecha = (valor) => new Intl.DateTimeFormat('es-CO', { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(valor));

function notificar(mensaje, tipo = 'success') {
  const nodo = document.createElement('div');
  nodo.className = `toast align-items-center border-0 text-bg-${tipo}`;
  nodo.setAttribute('role', 'status');
  nodo.innerHTML = `<div class="d-flex"><div class="toast-body">${escapar(mensaje)}</div><button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Cerrar"></button></div>`;
  document.querySelector('#toast-root').append(nodo);
  const toast = new Toast(nodo, { delay: 4200 });
  nodo.addEventListener('hidden.bs.toast', () => nodo.remove());
  toast.show();
}

function errorLegible(error) {
  const mensaje = error?.message || 'No fue posible completar la operación.';
  if (mensaje.includes('row-level security')) return 'Supabase bloqueó la operación. Verifique las políticas RLS.';
  if (mensaje.includes('Invalid login')) return 'El correo o la contraseña no son correctos.';
  if (mensaje.includes('already registered')) return 'Este correo ya está registrado. Inicie sesión.';
  return mensaje;
}

function renderConfiguracion() {
  app.innerHTML = `<main class="config-page container py-5">
    <div class="config-card mx-auto p-4 p-lg-5">
      <div class="brand-mark mb-4"><i class="bi bi-egg-fried"></i></div>
      <p class="section-label">Configuración pendiente</p>
      <h1>Conecte Mesa Lista con Supabase</h1>
      <p class="lead">Copie <code>.env.example</code> como <code>.env</code>, agregue la URL y la clave anónima del proyecto, ejecute <code>supabase/schema.sql</code> y reinicie el servidor.</p>
      <div class="alert alert-warning mb-0"><i class="bi bi-shield-lock me-2"></i>No use la clave <strong>service_role</strong> en el navegador.</div>
    </div>
  </main>`;
}

function renderAuth() {
  const registro = estado.modoAuth === 'registro';
  app.innerHTML = `<main class="auth-layout">
    <section class="auth-brand d-none d-lg-flex">
      <div class="auth-brand-content">
        <div class="brand-logo brand-logo-light mb-4"><i class="bi bi-egg-fried"></i><span>Mesa Lista</span></div>
        <p class="auth-overline">Su restaurante, bajo control</p>
        <h1>Del primer pedido<br>a la última cuenta.</h1>
        <p>Catálogo, inventario, ventas y facturación en un espacio de trabajo simple y seguro.</p>
        <div class="auth-feature"><i class="bi bi-check2-circle"></i><span>Datos protegidos por usuario con Supabase</span></div>
        <div class="auth-feature"><i class="bi bi-check2-circle"></i><span>Facturación POS con actualización de inventario</span></div>
      </div>
      <small>Proyecto académico · Gestión del Software</small>
    </section>
    <section class="auth-form-wrap">
      <div class="auth-form-card">
        <div class="brand-logo d-lg-none mb-4"><i class="bi bi-egg-fried"></i><span>Mesa Lista</span></div>
        <p class="section-label">${registro ? 'Cree su espacio de trabajo' : 'Bienvenido de nuevo'}</p>
        <h2>${registro ? 'Registrar usuario' : 'Iniciar sesión'}</h2>
        <p class="text-secondary mb-4">${registro ? 'Use un correo válido y una contraseña segura.' : 'Ingrese sus credenciales para administrar el restaurante.'}</p>
        <form data-form="auth" novalidate>
          <div class="mb-3"><label for="email" class="form-label">Correo electrónico</label><div class="input-with-icon"><i class="bi bi-envelope"></i><input class="form-control" id="email" name="email" type="email" autocomplete="email" required placeholder="nombre@correo.com"></div></div>
          <div class="mb-3"><label for="password" class="form-label">Contraseña</label><div class="input-with-icon"><i class="bi bi-lock"></i><input class="form-control" id="password" name="password" type="password" autocomplete="${registro ? 'new-password' : 'current-password'}" minlength="8" required placeholder="Mínimo 8 caracteres"><button class="password-toggle" type="button" data-action="ver-clave" aria-label="Mostrar contraseña"><i class="bi bi-eye"></i></button></div></div>
          <button class="btn btn-primary-brand w-100" type="submit">${registro ? 'Crear cuenta' : 'Ingresar'}<i class="bi bi-arrow-right ms-2"></i></button>
        </form>
        <p class="auth-switch">${registro ? '¿Ya tiene una cuenta?' : '¿Aún no tiene cuenta?'} <button type="button" data-action="cambiar-auth">${registro ? 'Iniciar sesión' : 'Crear cuenta'}</button></p>
        <div class="auth-security"><i class="bi bi-shield-check"></i><span>Autenticación administrada por Supabase Auth</span></div>
      </div>
    </section>
  </main>`;
}

function renderCarga() {
  app.innerHTML = `<main class="min-vh-100 d-flex flex-column align-items-center justify-content-center gap-3"><div class="brand-mark"><i class="bi bi-egg-fried"></i></div><div class="spinner-border text-success" role="status"><span class="visually-hidden">Cargando datos</span></div><p class="text-secondary">Preparando su restaurante…</p></main>`;
}

function navegacion(movil = false) {
  return vistas.map(([id, icono, nombre]) => `<button type="button" class="nav-link-app ${estado.vista === id ? 'active' : ''}" data-view="${id}"><i class="bi bi-${icono}"></i><span>${nombre}</span>${id === 'pos' && estado.carrito.length ? `<b class="cart-badge">${estado.carrito.length}</b>` : ''}</button>`).join('');
}

function renderShell() {
  const nombre = estado.usuario?.email?.split('@')[0] || 'Usuario';
  app.innerHTML = `<div class="app-shell">
    <aside class="sidebar d-none d-lg-flex">
      <div class="brand-logo brand-logo-light"><i class="bi bi-egg-fried"></i><span>Mesa Lista</span></div>
      <p class="sidebar-label">GESTIÓN DEL RESTAURANTE</p>
      <nav class="sidebar-nav" aria-label="Navegación principal">${navegacion()}</nav>
      <div class="sidebar-footer"><div class="avatar">${escapar(nombre.charAt(0).toUpperCase())}</div><div class="user-data"><strong>${escapar(nombre)}</strong><small>${escapar(estado.usuario.email)}</small></div><button type="button" class="btn-icon-dark" data-action="logout" aria-label="Cerrar sesión" title="Cerrar sesión"><i class="bi bi-box-arrow-right"></i></button></div>
    </aside>
    <div class="workspace">
      <header class="topbar">
        <div class="d-flex align-items-center gap-3">
          <button class="btn btn-outline-secondary d-lg-none" type="button" data-bs-toggle="collapse" data-bs-target="#menu-movil" aria-controls="menu-movil" aria-expanded="false" aria-label="Abrir menú"><i class="bi bi-list"></i></button>
          <div><p class="topbar-kicker">MESA LISTA</p><h1>${vistas.find(([id]) => id === estado.vista)?.[2]}</h1></div>
        </div>
        <div class="topbar-actions"><span class="status-pill"><i></i>Supabase conectado</span><button type="button" class="btn btn-primary-brand d-none d-sm-inline-flex" data-view="pos"><i class="bi bi-plus-lg"></i>Nueva venta</button><button type="button" class="btn btn-outline-secondary d-lg-none" data-action="logout" aria-label="Cerrar sesión"><i class="bi bi-box-arrow-right"></i></button></div>
      </header>
      <nav id="menu-movil" class="collapse mobile-nav d-lg-none" aria-label="Navegación móvil">${navegacion(true)}</nav>
      <main id="contenido" class="content-area"></main>
    </div>
  </div>`;
  renderVista();
}

function encabezadoVista(descripcion, accion = '') {
  return `<div class="page-heading"><div><h2>${descripcion.titulo}</h2><p>${descripcion.texto}</p></div>${accion}</div>`;
}

function renderVista() {
  const contenedor = document.querySelector('#contenido');
  if (!contenedor) return;
  if (estado.vista === 'resumen') contenedor.innerHTML = vistaResumen();
  if (estado.vista === 'categorias') contenedor.innerHTML = vistaCategorias();
  if (estado.vista === 'productos') contenedor.innerHTML = vistaProductos();
  if (estado.vista === 'pos') contenedor.innerHTML = vistaPOS();
  if (estado.vista === 'facturas') contenedor.innerHTML = vistaFacturas();
}

function vistaResumen() {
  const ventas = estado.facturas.reduce((suma, f) => suma + Number(f.total), 0);
  const unidades = estado.productos.reduce((suma, p) => suma + p.stock, 0);
  const recientes = estado.facturas.slice(0, 5);
  return `${encabezadoVista({ titulo: `Hola, ${escapar(estado.usuario.email.split('@')[0])}`, texto: 'Este es el pulso de su restaurante hoy.' }, '<button class="btn btn-primary-brand" data-view="pos"><i class="bi bi-cart-plus"></i>Registrar venta</button>')}
    <section class="metrics-grid" aria-label="Indicadores principales">
      <article class="metric-card metric-featured"><div class="metric-icon"><i class="bi bi-cash-stack"></i></div><span>Ventas registradas</span><strong>${formatoCOP(ventas)}</strong><small>${estado.facturas.length} facturas emitidas</small></article>
      <article class="metric-card"><div class="metric-icon soft-green"><i class="bi bi-box-seam"></i></div><span>Productos activos</span><strong>${estado.productos.filter((p) => p.activo).length}</strong><small>${unidades} unidades disponibles</small></article>
      <article class="metric-card"><div class="metric-icon soft-blue"><i class="bi bi-tags"></i></div><span>Categorías</span><strong>${estado.categorias.length}</strong><small>Organización del catálogo</small></article>
    </section>
    <section class="dashboard-grid">
      <div class="panel"><div class="panel-heading"><div><h3>Actividad reciente</h3><p>Últimas ventas facturadas</p></div><button class="btn btn-text" data-view="facturas">Ver todas<i class="bi bi-arrow-right"></i></button></div>
      ${recientes.length ? `<div class="table-responsive"><table class="table table-app align-middle"><thead><tr><th>Factura</th><th>Cliente</th><th>Fecha</th><th class="text-end">Total</th></tr></thead><tbody>${recientes.map((f) => `<tr><td><strong>#${f.numero}</strong></td><td>${escapar(f.cliente_nombre)}</td><td>${fecha(f.creado_en)}</td><td class="text-end amount">${formatoCOP(f.total)}</td></tr>`).join('')}</tbody></table></div>` : estadoVacio('receipt', 'Aún no hay ventas', 'Registre la primera venta desde el punto de venta.', 'pos', 'Abrir POS')}
      </div>
      <div class="panel quick-panel"><div class="panel-heading"><div><h3>Accesos rápidos</h3><p>Continue su operación</p></div></div><button class="quick-action" data-action="nuevo-producto"><span class="quick-icon"><i class="bi bi-box-seam"></i></span><span><strong>Agregar producto</strong><small>Cree un plato y defina su precio</small></span><i class="bi bi-chevron-right"></i></button><button class="quick-action" data-action="nueva-categoria"><span class="quick-icon"><i class="bi bi-tag"></i></span><span><strong>Crear categoría</strong><small>Organice su oferta gastronómica</small></span><i class="bi bi-chevron-right"></i></button><button class="quick-action" data-view="pos"><span class="quick-icon"><i class="bi bi-receipt"></i></span><span><strong>Facturar una venta</strong><small>Calcule totales y descargue inventario</small></span><i class="bi bi-chevron-right"></i></button></div>
    </section>`;
}

function estadoVacio(icono, titulo, texto, vista, boton) {
  return `<div class="empty-state"><i class="bi bi-${icono}"></i><h4>${titulo}</h4><p>${texto}</p>${vista ? `<button class="btn btn-outline-brand" data-view="${vista}">${boton}</button>` : ''}</div>`;
}

function vistaCategorias() {
  return `${encabezadoVista({ titulo: 'Categorías del menú', texto: 'Agrupe los productos para encontrarlos más rápido en el POS.' }, '<button class="btn btn-primary-brand" data-action="nueva-categoria"><i class="bi bi-plus-lg"></i>Nueva categoría</button>')}
    <section class="panel">${estado.categorias.length ? `<div class="table-responsive"><table class="table table-app align-middle"><thead><tr><th>Categoría</th><th>Descripción</th><th>Productos</th><th class="text-end">Acciones</th></tr></thead><tbody>${estado.categorias.map((c) => `<tr><td><div class="category-name"><span><i class="bi bi-tag"></i></span><strong>${escapar(c.nombre)}</strong></div></td><td>${escapar(c.descripcion || 'Sin descripción')}</td><td><span class="count-pill">${estado.productos.filter((p) => p.categoria_id === c.id).length}</span></td><td><div class="table-actions"><button class="btn btn-sm btn-light" data-action="editar-categoria" data-id="${c.id}" aria-label="Editar ${escapar(c.nombre)}"><i class="bi bi-pencil"></i></button><button class="btn btn-sm btn-light text-danger" data-action="eliminar-categoria" data-id="${c.id}" aria-label="Eliminar ${escapar(c.nombre)}"><i class="bi bi-trash3"></i></button></div></td></tr>`).join('')}</tbody></table></div>` : estadoVacio('tags', 'Cree su primera categoría', 'Por ejemplo: entradas, platos fuertes o bebidas.', null, '')}</section>`;
}

function vistaProductos() {
  return `${encabezadoVista({ titulo: 'Productos e inventario', texto: 'Administre precios, disponibilidad y existencias.' }, '<button class="btn btn-primary-brand" data-action="nuevo-producto"><i class="bi bi-plus-lg"></i>Nuevo producto</button>')}
    <section class="panel">${estado.productos.length ? `<div class="table-responsive"><table class="table table-app align-middle"><thead><tr><th>Producto</th><th>Categoría</th><th>Precio</th><th>Inventario</th><th>Estado</th><th class="text-end">Acciones</th></tr></thead><tbody>${estado.productos.map((p) => `<tr><td><strong>${escapar(p.nombre)}</strong><small class="d-block text-secondary">SKU ${escapar(p.sku)}</small></td><td>${escapar(p.categorias?.nombre || 'Sin categoría')}</td><td class="amount">${formatoCOP(p.precio)}</td><td><span class="stock-pill ${p.stock < 5 ? 'low' : ''}">${p.stock} und.</span></td><td><span class="state-pill ${p.activo ? '' : 'inactive'}">${p.activo ? 'Activo' : 'Inactivo'}</span></td><td><div class="table-actions"><button class="btn btn-sm btn-light" data-action="editar-producto" data-id="${p.id}" aria-label="Editar ${escapar(p.nombre)}"><i class="bi bi-pencil"></i></button><button class="btn btn-sm btn-light text-danger" data-action="eliminar-producto" data-id="${p.id}" aria-label="Eliminar ${escapar(p.nombre)}"><i class="bi bi-trash3"></i></button></div></td></tr>`).join('')}</tbody></table></div>` : estadoVacio('box-seam', 'El catálogo está vacío', 'Agregue un producto para comenzar a vender.', null, '')}</section>`;
}

function vistaPOS() {
  const productos = estado.productos.filter((p) => p.activo && (estado.categoriaPos === 'todas' || p.categoria_id === estado.categoriaPos) && p.nombre.toLowerCase().includes(estado.busqueda.toLowerCase()));
  const totales = calcularTotales(estado.carrito);
  return `${encabezadoVista({ titulo: 'Nueva venta', texto: 'Seleccione productos, confirme el cliente y emita la factura.' })}
    <div class="pos-layout"><section class="pos-catalog"><div class="pos-tools"><div class="search-box"><i class="bi bi-search"></i><input type="search" class="form-control" id="buscar-producto" value="${escapar(estado.busqueda)}" placeholder="Buscar producto…" aria-label="Buscar producto"></div></div>
      <div class="category-filters" aria-label="Filtrar por categoría"><button class="filter-chip ${estado.categoriaPos === 'todas' ? 'active' : ''}" data-action="filtrar-categoria" data-id="todas">Todos</button>${estado.categorias.map((c) => `<button class="filter-chip ${estado.categoriaPos === c.id ? 'active' : ''}" data-action="filtrar-categoria" data-id="${c.id}">${escapar(c.nombre)}</button>`).join('')}</div>
      ${productos.length ? `<div class="product-grid">${productos.map((p) => `<button class="product-card" data-action="agregar-producto" data-id="${p.id}" ${p.stock < 1 ? 'disabled' : ''}><span class="product-letter">${escapar(p.nombre.charAt(0).toUpperCase())}</span><span class="product-info"><small>${escapar(p.categorias?.nombre || 'General')}</small><strong>${escapar(p.nombre)}</strong><b>${formatoCOP(p.precio)}</b><em class="${p.stock < 5 ? 'text-danger' : ''}">${p.stock ? `${p.stock} disponibles` : 'Agotado'}</em></span><span class="add-circle"><i class="bi bi-plus-lg"></i></span></button>`).join('')}</div>` : estadoVacio('search', 'No encontramos productos', 'Cambie el filtro o agregue productos activos al catálogo.', 'productos', 'Ir a productos')}
    </section><aside class="cart-panel"><div class="cart-heading"><div><h3>Pedido actual</h3><p>${estado.carrito.reduce((n, i) => n + i.cantidad, 0)} artículos</p></div><i class="bi bi-receipt"></i></div>
      <div class="cart-items">${estado.carrito.length ? estado.carrito.map((item) => `<div class="cart-item"><div class="cart-item-top"><strong>${escapar(item.nombre)}</strong><button data-action="quitar-item" data-id="${item.producto_id}" aria-label="Quitar ${escapar(item.nombre)}"><i class="bi bi-x-lg"></i></button></div><small>${formatoCOP(item.precio)} c/u</small><div class="cart-item-bottom"><div class="quantity-control"><button data-action="cantidad" data-id="${item.producto_id}" data-delta="-1" aria-label="Disminuir cantidad"><i class="bi bi-dash"></i></button><span>${item.cantidad}</span><button data-action="cantidad" data-id="${item.producto_id}" data-delta="1" aria-label="Aumentar cantidad"><i class="bi bi-plus"></i></button></div><strong>${formatoCOP(item.precio * item.cantidad)}</strong></div></div>`).join('') : '<div class="cart-empty"><i class="bi bi-basket2"></i><p>Su pedido está vacío</p><small>Toque un producto para agregarlo.</small></div>'}</div>
      <div class="cart-totals"><div><span>Subtotal</span><strong>${formatoCOP(totales.subtotal)}</strong></div><div><span>IVA académico (8 %)</span><strong>${formatoCOP(totales.impuesto)}</strong></div><div class="total-row"><span>Total</span><strong>${formatoCOP(totales.total)}</strong></div></div>
      <form data-form="factura" class="checkout-form" novalidate><div class="mb-2"><label for="cliente-nombre" class="form-label">Cliente</label><input class="form-control" id="cliente-nombre" name="nombre" value="Consumidor final" minlength="2" required></div><div class="mb-3"><label for="cliente-documento" class="form-label">Documento</label><input class="form-control" id="cliente-documento" name="documento" value="222222222222" required></div><button class="btn btn-primary-brand w-100" type="submit" ${estado.carrito.length ? '' : 'disabled'}><i class="bi bi-check2-circle"></i>Facturar ${formatoCOP(totales.total)}</button></form>
    </aside></div>`;
}

function vistaFacturas() {
  return `${encabezadoVista({ titulo: 'Historial de facturas', texto: 'Consulte el detalle y vuelva a imprimir los comprobantes.' }, '<button class="btn btn-primary-brand" data-view="pos"><i class="bi bi-plus-lg"></i>Nueva factura</button>')}
    <section class="panel">${estado.facturas.length ? `<div class="table-responsive"><table class="table table-app align-middle"><thead><tr><th>Número</th><th>Cliente</th><th>Fecha</th><th>Artículos</th><th>Total</th><th class="text-end">Detalle</th></tr></thead><tbody>${estado.facturas.map((f) => `<tr><td><strong class="invoice-number">#${f.numero}</strong></td><td>${escapar(f.cliente_nombre)}<small class="d-block text-secondary">${escapar(f.cliente_documento)}</small></td><td>${fecha(f.creado_en)}</td><td>${f.detalle_factura.reduce((n, i) => n + i.cantidad, 0)}</td><td class="amount">${formatoCOP(f.total)}</td><td class="text-end"><button class="btn btn-sm btn-outline-brand" data-action="ver-factura" data-id="${f.id}"><i class="bi bi-eye"></i>Ver factura</button></td></tr>`).join('')}</tbody></table></div>` : estadoVacio('receipt', 'Todavía no hay facturas', 'Las ventas finalizadas aparecerán aquí.', 'pos', 'Crear primera factura')}</section>`;
}

function abrirModal(titulo, contenido, grande = false) {
  modalRoot.innerHTML = `<div class="modal fade" id="modal-app" tabindex="-1" aria-labelledby="modal-title" aria-hidden="true"><div class="modal-dialog modal-dialog-centered ${grande ? 'modal-lg' : ''}"><div class="modal-content"><div class="modal-header"><h2 class="modal-title fs-4" id="modal-title">${titulo}</h2><button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Cerrar"></button></div><div class="modal-body">${contenido}</div></div></div></div>`;
  const elemento = document.querySelector('#modal-app');
  const modal = new Modal(elemento);
  elemento.addEventListener('hidden.bs.modal', () => { modal.dispose(); modalRoot.innerHTML = ''; });
  modal.show();
}

function modalCategoria(categoria = {}) {
  abrirModal(categoria.id ? 'Editar categoría' : 'Nueva categoría', `<form data-form="categoria" data-id="${categoria.id || ''}" novalidate><div class="mb-3"><label for="categoria-nombre" class="form-label">Nombre</label><input class="form-control" id="categoria-nombre" name="nombre" value="${escapar(categoria.nombre)}" maxlength="60" required autofocus placeholder="Ej. Platos fuertes"></div><div class="mb-4"><label for="categoria-descripcion" class="form-label">Descripción</label><textarea class="form-control" id="categoria-descripcion" name="descripcion" rows="3" maxlength="180" placeholder="Descripción breve">${escapar(categoria.descripcion)}</textarea></div><div class="d-flex justify-content-end gap-2"><button type="button" class="btn btn-light" data-bs-dismiss="modal">Cancelar</button><button class="btn btn-primary-brand" type="submit"><i class="bi bi-check2"></i>Guardar categoría</button></div></form>`);
}

function modalProducto(producto = {}) {
  if (!estado.categorias.length) { notificar('Cree una categoría antes de agregar productos.', 'warning'); return; }
  abrirModal(producto.id ? 'Editar producto' : 'Nuevo producto', `<form data-form="producto" data-id="${producto.id || ''}" novalidate><div class="row g-3"><div class="col-12"><label for="producto-nombre" class="form-label">Nombre del producto</label><input class="form-control" id="producto-nombre" name="nombre" value="${escapar(producto.nombre)}" maxlength="90" required placeholder="Ej. Bandeja paisa"></div><div class="col-md-6"><label for="producto-sku" class="form-label">SKU</label><input class="form-control" id="producto-sku" name="sku" value="${escapar(producto.sku)}" maxlength="30" required placeholder="PF-001"></div><div class="col-md-6"><label for="producto-categoria" class="form-label">Categoría</label><select class="form-select" id="producto-categoria" name="categoria_id" required>${estado.categorias.map((c) => `<option value="${c.id}" ${producto.categoria_id === c.id ? 'selected' : ''}>${escapar(c.nombre)}</option>`).join('')}</select></div><div class="col-md-6"><label for="producto-precio" class="form-label">Precio COP</label><input class="form-control" id="producto-precio" name="precio" type="number" min="0" step="0.01" value="${producto.precio ?? ''}" required></div><div class="col-md-6"><label for="producto-stock" class="form-label">Inventario</label><input class="form-control" id="producto-stock" name="stock" type="number" min="0" step="1" value="${producto.stock ?? 0}" required></div><div class="col-12"><div class="form-check form-switch"><input class="form-check-input" id="producto-activo" name="activo" type="checkbox" ${producto.activo === false ? '' : 'checked'}><label class="form-check-label" for="producto-activo">Disponible para la venta</label></div></div></div><div class="d-flex justify-content-end gap-2 mt-4"><button type="button" class="btn btn-light" data-bs-dismiss="modal">Cancelar</button><button class="btn btn-primary-brand" type="submit"><i class="bi bi-check2"></i>Guardar producto</button></div></form>`);
}

function modalFactura(factura) {
  abrirModal(`Factura #${factura.numero}`, `<div id="factura-imprimible" class="receipt"><div class="receipt-brand"><i class="bi bi-egg-fried"></i><h3>Mesa Lista</h3><p>Comprobante académico de venta</p></div><div class="receipt-meta"><span>Factura <strong>#${factura.numero}</strong></span><span>${fecha(factura.creado_en)}</span></div><p><strong>Cliente:</strong> ${escapar(factura.cliente_nombre)}<br><strong>Documento:</strong> ${escapar(factura.cliente_documento)}</p><table class="table"><thead><tr><th>Producto</th><th>Cant.</th><th class="text-end">Valor</th></tr></thead><tbody>${factura.detalle_factura.map((i) => `<tr><td>${escapar(i.producto_nombre)}</td><td>${i.cantidad}</td><td class="text-end">${formatoCOP(i.subtotal)}</td></tr>`).join('')}</tbody></table><div class="receipt-total"><span>Subtotal: ${formatoCOP(factura.subtotal)}</span><span>IVA académico: ${formatoCOP(factura.impuesto)}</span><strong>Total: ${formatoCOP(factura.total)}</strong></div><p class="text-center text-secondary mt-4 mb-0">Gracias por su compra</p></div><div class="d-flex justify-content-end gap-2 mt-4 no-print"><button type="button" class="btn btn-light" data-bs-dismiss="modal">Cerrar</button><button type="button" class="btn btn-primary-brand" data-action="imprimir"><i class="bi bi-printer"></i>Imprimir</button></div>`, true);
}

async function refrescar(vista = estado.vista) {
  const datos = await cargarDatos();
  Object.assign(estado, datos, { vista });
  renderShell();
}

async function ejecutar(operacion, mensaje, vista) {
  try {
    const { error } = await operacion();
    if (error) throw error;
    Modal.getInstance(document.querySelector('#modal-app'))?.hide();
    await refrescar(vista);
    notificar(mensaje);
  } catch (error) { notificar(errorLegible(error), 'danger'); }
}

document.addEventListener('click', async (event) => {
  const botonVista = event.target.closest('[data-view]');
  if (botonVista) {
    estado.vista = botonVista.dataset.view;
    renderShell();
    Collapse.getInstance(document.querySelector('#menu-movil'))?.hide();
    return;
  }
  const boton = event.target.closest('[data-action]');
  if (!boton) return;
  const { action, id } = boton.dataset;
  try {
    if (action === 'cambiar-auth') { estado.modoAuth = estado.modoAuth === 'login' ? 'registro' : 'login'; renderAuth(); }
    if (action === 'ver-clave') { const input = document.querySelector('#password'); input.type = input.type === 'password' ? 'text' : 'password'; boton.innerHTML = `<i class="bi bi-${input.type === 'password' ? 'eye' : 'eye-slash'}"></i>`; }
    if (action === 'logout') { await supabase.auth.signOut(); Object.assign(estado, { usuario: null, carrito: [] }); renderAuth(); }
    if (action === 'nueva-categoria') modalCategoria();
    if (action === 'editar-categoria') modalCategoria(estado.categorias.find((c) => c.id === id));
    if (action === 'nuevo-producto') modalProducto();
    if (action === 'editar-producto') modalProducto(estado.productos.find((p) => p.id === id));
    if (action === 'filtrar-categoria') { estado.categoriaPos = id; renderVista(); }
    if (action === 'agregar-producto') { estado.carrito = agregarAlCarrito(estado.carrito, estado.productos.find((p) => p.id === id)); renderShell(); }
    if (action === 'cantidad') { estado.carrito = cambiarCantidad(estado.carrito, id, Number(boton.dataset.delta)); renderShell(); }
    if (action === 'quitar-item') { estado.carrito = estado.carrito.filter((i) => i.producto_id !== id); renderShell(); }
    if (action === 'ver-factura') modalFactura(estado.facturas.find((f) => f.id === id));
    if (action === 'imprimir') window.print();
    if (action === 'eliminar-categoria') {
      const categoria = estado.categorias.find((c) => c.id === id);
      if (confirm(`¿Eliminar la categoría “${categoria.nombre}”?`)) await ejecutar(() => supabase.from('categorias').delete().eq('id', id), 'Categoría eliminada.', 'categorias');
    }
    if (action === 'eliminar-producto') {
      const producto = estado.productos.find((p) => p.id === id);
      if (confirm(`¿Eliminar el producto “${producto.nombre}”?`)) await ejecutar(() => supabase.from('productos').delete().eq('id', id), 'Producto eliminado.', 'productos');
    }
  } catch (error) { notificar(errorLegible(error), 'danger'); }
});

document.addEventListener('input', (event) => {
  if (event.target.id === 'buscar-producto') {
    estado.busqueda = event.target.value;
    const posicion = event.target.selectionStart;
    renderVista();
    const input = document.querySelector('#buscar-producto');
    input.focus();
    input.setSelectionRange(posicion, posicion);
  }
});

document.addEventListener('submit', async (event) => {
  const form = event.target.closest('form[data-form]');
  if (!form) return;
  event.preventDefault();
  if (!form.checkValidity()) { form.classList.add('was-validated'); return; }
  const datos = Object.fromEntries(new FormData(form));
  const boton = form.querySelector('[type="submit"]');
  boton.disabled = true;
  boton.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Procesando…';
  try {
    if (form.dataset.form === 'auth') {
      const operacion = estado.modoAuth === 'registro' ? supabase.auth.signUp({ email: datos.email, password: datos.password }) : supabase.auth.signInWithPassword({ email: datos.email, password: datos.password });
      const { data, error } = await operacion;
      if (error) throw error;
      if (!data.session) { estado.modoAuth = 'login'; renderAuth(); notificar('Cuenta creada. Confirme el correo antes de ingresar.', 'info'); return; }
      estado.usuario = data.user;
      renderCarga();
      await refrescar('resumen');
      notificar(estado.modoAuth === 'registro' ? 'Cuenta creada correctamente.' : 'Sesión iniciada correctamente.');
    }
    if (form.dataset.form === 'categoria') {
      const valores = { nombre: datos.nombre.trim(), descripcion: datos.descripcion.trim() || null };
      await ejecutar(() => form.dataset.id ? supabase.from('categorias').update(valores).eq('id', form.dataset.id) : supabase.from('categorias').insert(valores), 'Categoría guardada.', 'categorias');
    }
    if (form.dataset.form === 'producto') {
      const valores = { nombre: datos.nombre.trim(), sku: datos.sku.trim().toUpperCase(), categoria_id: datos.categoria_id, precio: Number(datos.precio), stock: Number(datos.stock), activo: datos.activo === 'on' };
      await ejecutar(() => form.dataset.id ? supabase.from('productos').update(valores).eq('id', form.dataset.id) : supabase.from('productos').insert(valores), 'Producto guardado.', 'productos');
    }
    if (form.dataset.form === 'factura') {
      const payload = prepararFactura(estado.carrito, datos);
      const { data, error } = await supabase.rpc('crear_factura', payload);
      if (error) throw error;
      estado.carrito = [];
      await refrescar('facturas');
      notificar(`Factura #${data.numero} creada e inventario actualizado.`);
      const factura = estado.facturas.find((f) => f.id === data.id);
      if (factura) modalFactura(factura);
    }
  } catch (error) {
    notificar(errorLegible(error), 'danger');
    boton.disabled = false;
    boton.textContent = 'Reintentar';
  }
});

async function iniciar() {
  if (!supabaseConfigurado) { renderConfiguracion(); return; }
  renderCarga();
  try {
    const { data, error } = await supabase.auth.getSession();
    if (error) throw error;
    estado.usuario = data.session?.user || null;
    if (!estado.usuario) { renderAuth(); return; }
    await refrescar();
  } catch (error) {
    renderAuth();
    notificar(errorLegible(error), 'danger');
  }
}

iniciar();

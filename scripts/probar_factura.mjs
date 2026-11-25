import { createClient } from '@supabase/supabase-js';
const { SUPABASE_URL, SUPABASE_ANON_KEY, PRUEBA_EMAIL, PRUEBA_PASSWORD } = process.env;
if (![SUPABASE_URL, SUPABASE_ANON_KEY, PRUEBA_EMAIL, PRUEBA_PASSWORD].every(Boolean)) throw new Error('Faltan variables de entorno.');
const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY);
const { error: authError } = await supabase.auth.signInWithPassword({ email: PRUEBA_EMAIL, password: PRUEBA_PASSWORD });
if (authError) throw authError;
const { data: productos, error: productosError } = await supabase.from('productos').select('id,nombre,stock').in('sku', ['PF-001', 'BEB-001', 'BEB-002']);
if (productosError) throw productosError;
if (productos.length !== 3) throw new Error('Ejecute primero scripts/cargar_demo.mjs.');
const antes = Object.fromEntries(productos.map((p) => [p.nombre, p.stock]));
const { data: factura, error: facturaError } = await supabase.rpc('crear_factura', {
  p_cliente_nombre: 'Cliente académico AA2',
  p_cliente_documento: '1030000000',
  p_items: productos.map((p) => ({ producto_id: p.id, cantidad: 1 })),
});
if (facturaError) throw facturaError;
const { data: detalle, error: detalleError } = await supabase.from('detalle_factura').select('*').eq('factura_id', factura.id);
if (detalleError) throw detalleError;
const { data: despuesData, error: despuesError } = await supabase.from('productos').select('id,nombre,stock').in('sku', ['PF-001', 'BEB-001', 'BEB-002']);
if (despuesError) throw despuesError;
const despues = Object.fromEntries(despuesData.map((p) => [p.nombre, p.stock]));
console.log(JSON.stringify({ factura: factura.numero, subtotal: factura.subtotal, impuesto: factura.impuesto, total: factura.total, detalles: detalle.length, inventario_antes: antes, inventario_despues: despues }));
await supabase.auth.signOut();

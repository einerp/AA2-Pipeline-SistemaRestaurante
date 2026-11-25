import { createClient } from '@supabase/supabase-js';

const { SUPABASE_URL, SUPABASE_ANON_KEY, PRUEBA_EMAIL, PRUEBA_PASSWORD } = process.env;
if (![SUPABASE_URL, SUPABASE_ANON_KEY, PRUEBA_EMAIL, PRUEBA_PASSWORD].every(Boolean)) throw new Error('Faltan variables de entorno para cargar datos demo.');
const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY);
const { data: auth, error: errorAuth } = await supabase.auth.signInWithPassword({ email: PRUEBA_EMAIL, password: PRUEBA_PASSWORD });
if (errorAuth) throw errorAuth;
const usuario_id = auth.user.id;
const categorias = [
  { nombre: 'Platos fuertes', descripcion: 'Preparaciones principales del menú.' },
  { nombre: 'Bebidas', descripcion: 'Bebidas frías y calientes.' },
  { nombre: 'Postres', descripcion: 'Opciones dulces para finalizar.' },
];
const { error: errorCategorias } = await supabase.from('categorias').upsert(categorias.map((c) => ({ ...c, usuario_id })), { onConflict: 'usuario_id,nombre' });
if (errorCategorias) throw errorCategorias;
const { data: guardadas, error: errorConsulta } = await supabase.from('categorias').select('id,nombre');
if (errorConsulta) throw errorConsulta;
const id = (nombre) => guardadas.find((c) => c.nombre === nombre).id;
const productos = [
  { nombre: 'Bandeja paisa', sku: 'PF-001', categoria_id: id('Platos fuertes'), precio: 28000, stock: 15 },
  { nombre: 'Arroz con pollo', sku: 'PF-002', categoria_id: id('Platos fuertes'), precio: 22000, stock: 20 },
  { nombre: 'Limonada natural', sku: 'BEB-001', categoria_id: id('Bebidas'), precio: 8000, stock: 30 },
  { nombre: 'Café americano', sku: 'BEB-002', categoria_id: id('Bebidas'), precio: 5000, stock: 25 },
  { nombre: 'Tres leches', sku: 'POS-001', categoria_id: id('Postres'), precio: 10000, stock: 12 },
];
const { error: errorProductos } = await supabase.from('productos').upsert(productos.map((p) => ({ ...p, usuario_id, activo: true })), { onConflict: 'usuario_id,sku' });
if (errorProductos) throw errorProductos;
console.log(JSON.stringify({ categorias: guardadas.length, productos: productos.length, usuario: auth.user.email }));
await supabase.auth.signOut();

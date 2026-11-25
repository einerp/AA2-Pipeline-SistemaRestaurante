import { createClient } from '@supabase/supabase-js';

const url = import.meta.env.VITE_SUPABASE_URL;
const anonKey = import.meta.env.VITE_SUPABASE_ANON_KEY;

export const supabaseConfigurado = Boolean(url && anonKey);
export const supabase = supabaseConfigurado
  ? createClient(url, anonKey, { auth: { persistSession: true, autoRefreshToken: true } })
  : null;

export async function cargarDatos() {
  const [categorias, productos, facturas] = await Promise.all([
    supabase.from('categorias').select('*').order('nombre'),
    supabase.from('productos').select('*, categorias(nombre)').order('nombre'),
    supabase.from('facturas').select('*, detalle_factura(*)').order('creado_en', { ascending: false }).limit(100),
  ]);
  const error = categorias.error || productos.error || facturas.error;
  if (error) throw error;
  return { categorias: categorias.data, productos: productos.data, facturas: facturas.data };
}

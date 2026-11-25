import { createClient } from '@supabase/supabase-js';

const { SUPABASE_URL, SUPABASE_ANON_KEY, PRUEBA_EMAIL, PRUEBA_PASSWORD } = process.env;
if (![SUPABASE_URL, SUPABASE_ANON_KEY, PRUEBA_EMAIL, PRUEBA_PASSWORD].every(Boolean)) {
  throw new Error('Defina SUPABASE_URL, SUPABASE_ANON_KEY, PRUEBA_EMAIL y PRUEBA_PASSWORD.');
}
const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY);
const conLimite = (promesa, nombre) => Promise.race([
  promesa,
  new Promise((_, reject) => setTimeout(() => reject(new Error(`Tiempo agotado: ${nombre}`)), 15000)),
]);
const { data: sesion, error: errorAuth } = await conLimite(supabase.auth.signInWithPassword({ email: PRUEBA_EMAIL, password: PRUEBA_PASSWORD }), 'autenticación');
if (errorAuth) throw errorAuth;
const resultados = await conLimite(Promise.all([
  supabase.from('categorias').select('*'),
  supabase.from('productos').select('*'),
  supabase.from('facturas').select('*'),
]), 'consulta de datos');
const errores = resultados.map((r) => r.error).filter(Boolean);
if (errores.length) throw errores[0];
console.log(JSON.stringify({ autenticacion: Boolean(sesion.session), categorias: resultados[0].data.length, productos: resultados[1].data.length, facturas: resultados[2].data.length }));
await supabase.auth.signOut();
process.exit(0);

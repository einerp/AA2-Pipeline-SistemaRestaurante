# Mesa Lista — Sistema de restaurante y pipeline CI/CD

**AA2 Proyecto Integrador: Construcción de un pipeline para un proyecto de software**
**Estudiante:** Einer Plaza Prasca
**Asignatura:** Gestión del Software
**Repositorio:** https://github.com/einerp/AA2-Pipeline-SistemaRestaurante

## Descripción

Mesa Lista es una aplicación web académica construida con **Node.js 22, JavaScript, Vite, Bootstrap y Supabase**. Permite administrar categorías y productos, autenticar usuarios con correo y contraseña, registrar ventas mediante un punto de venta (POS), descontar inventario y generar comprobantes imprimibles.

El repositorio incorpora un pipeline de GitHub Actions que ejecuta pruebas, cobertura, auditoría de dependencias, construcción, validación de staging y despliegue de producción en Vercel.

## Funcionalidades

- Registro e inicio de sesión con Supabase Auth.
- Cierre de sesión y protección de datos por usuario.
- Creación, edición y eliminación de categorías.
- Creación, edición y eliminación de productos con precio, IVA e inventario.
- Carrito POS con cantidades, subtotal, impuestos y total.
- Facturación transaccional y descuento automático de existencias.
- Historial de facturas y comprobante imprimible.
- Diseño adaptable a equipos de escritorio y dispositivos móviles.

## Arquitectura

| Capa | Tecnología | Responsabilidad |
|---|---|---|
| Presentación | JavaScript, Bootstrap y CSS | Interfaz, formularios, catálogo y POS |
| Reglas de negocio | Módulo `src/lib/pos.js` | Totales, carrito e inventario |
| Autenticación | Supabase Auth | Registro, inicio y cierre de sesión |
| Persistencia | PostgreSQL de Supabase | Categorías, productos, facturas y detalles |
| Seguridad de datos | Row Level Security | Aislamiento de registros por `usuario_id` |
| Transacción | Función RPC `crear_factura` | Factura, detalles e inventario atómicos |
| Automatización | GitHub Actions | Calidad, staging y producción |
| Alojamiento | Vercel | Distribución del paquete Vite |

## Estructura principal

```text
src/
  lib/pos.js              Reglas de negocio del POS
  lib/supabase.js         Cliente y acceso a Supabase
  main.js                 Interfaz y flujos de la aplicación
  styles.css              Presentación adaptable
supabase/schema.sql       Tablas, RLS, permisos y RPC transaccional
tests/node/pos.test.js    Pruebas unitarias de las reglas POS
scripts/                  Comprobaciones y carga de datos demostrativos
docs/evidencias/          Evidencias técnicas del proyecto
.github/workflows/        Pipeline CI/CD
```

## Requisitos

- Node.js 22.12 o superior.
- Una cuenta y un proyecto de Supabase.
- Una cuenta de Vercel para producción.

## Configuración local

1. Instale las dependencias:

   ```bash
   npm ci
   ```

2. Copie `.env.example` como `.env` y complete:

   ```dotenv
   VITE_SUPABASE_URL=https://SU_PROYECTO.supabase.co
   VITE_SUPABASE_ANON_KEY=SU_CLAVE_PUBLICA
   ```

   La clave anónima o publicable es adecuada para el navegador. **Nunca use ni publique la clave `service_role`.** El archivo `.env` está excluido de Git.

3. Ejecute `supabase/schema.sql` en el SQL Editor de Supabase.

4. Inicie el servidor de desarrollo:

   ```bash
   npm run dev
   ```

5. Abra la dirección informada por Vite. Registre un usuario nuevo o inicie sesión con un usuario ya confirmado.

## Datos de demostración

El script opcional carga tres categorías y cinco productos para un usuario existente. Requiere las variables `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `PRUEBA_EMAIL` y `PRUEBA_PASSWORD`, definidas únicamente en el entorno local:

```bash
node scripts/cargar_demo.mjs
```

Las credenciales personales o de demostración no se incluyen en este repositorio.

## Pruebas y calidad

```bash
npm test
npm run test:coverage
npm audit --audit-level=high
npm run build
```

Resultados comprobados localmente para esta versión:

- **10 pruebas aprobadas**.
- **100 % de líneas y funciones** en `src/lib/pos.js`.
- **68,75 % de ramas** en ese módulo.
- Umbral obligatorio: **80 % de líneas**.
- **0 vulnerabilidades** informadas por `npm audit`.
- Construcción correcta de **111 módulos** con Vite.

La cobertura se concentra deliberadamente en las reglas del POS: cálculo de totales, redondeo, cantidades, validación de existencias y preparación del comprobante.

## Comprobación del flujo de facturación

Con las variables públicas de Supabase configuradas, los scripts permiten comprobar conexión y facturación real:

```bash
node scripts/probar_supabase.mjs
node scripts/probar_factura.mjs
```

La evidencia local registró una factura de tres artículos con subtotal de **COP 41.000**, IVA de **COP 3.280** y total de **COP 44.280**. Las existencias de los tres productos disminuyeron en una unidad, lo que confirma la ejecución de la transacción. El detalle está en `docs/evidencias/prueba-factura.json`.

> Estos scripts utilizan variables de autenticación locales que no se distribuyen con el proyecto.

## Pipeline CI/CD

Archivo: `.github/workflows/ci-cd.yml`.

1. **Calidad, pruebas, cobertura y seguridad**
   - Instalación reproducible con `npm ci`.
   - Pruebas unitarias y cobertura mínima.
   - Auditoría de dependencias.
   - Construcción del paquete Vite.
   - Publicación de artefactos y evidencias.

2. **Staging**
   - Descarga del mismo paquete aprobado.
   - Publicación temporal con Vite Preview.
   - Comprobación de HTTP 200 y presencia de Mesa Lista.
   - Si esta puerta falla, producción no se ejecuta.

3. **Producción con integración GitHub–Vercel**
   - El proyecto Vercel se conecta directamente al repositorio de GitHub.
   - Cada cambio publicado en `main` activa la construcción y el despliegue de Vercel.
   - El estado del despliegue queda asociado al commit y puede comprobarse en GitHub y Vercel.
   - Las ramas y solicitudes de extracción generan vistas previas, no producción.

Esta separación evita almacenar tokens de despliegue en GitHub: Actions constituye la puerta de calidad y Vercel realiza la entrega continua mediante su integración nativa.

## Configuración de Vercel

1. En Vercel, seleccione **Add New → Project** e importe `einerp/AA2-Pipeline-SistemaRestaurante`.
2. Conserve **Vite** como framework, `npm run build` como comando y `dist` como directorio de salida.
3. Configure en Production y Preview:
   - `VITE_SUPABASE_URL`.
   - `VITE_SUPABASE_ANON_KEY`.
4. Ejecute **Deploy** y compruebe la URL pública devuelta por Vercel.

Después de cambiar variables, vuelva a desplegar para incorporarlas al paquete. La integración nativa vuelve a construir y publicar automáticamente cada `push` a `main`.

## Base de datos y seguridad

El esquema crea las tablas `categorias`, `productos`, `facturas` y `detalle_factura`. Las políticas RLS exigen que `auth.uid()` coincida con `usuario_id`. La función `crear_factura` valida el usuario autenticado, comprueba productos y existencias, calcula los importes, inserta cabecera y detalles, y descuenta inventario dentro de una única transacción.

Los permisos del rol `authenticated` permiten únicamente las operaciones necesarias sobre el esquema y las tablas; RLS sigue limitando las filas visibles para cada cuenta.

## Evidencias

La carpeta `docs/evidencias/` conserva resultados técnicos y capturas sin contraseñas ni tokens. Las pruebas locales no sustituyen la validación del pipeline: la ejecución de GitHub Actions y la respuesta HTTP de Vercel deben comprobarse por separado antes de considerar completado el despliegue.

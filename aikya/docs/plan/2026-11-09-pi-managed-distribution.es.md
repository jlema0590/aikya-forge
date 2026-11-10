# D — Distribución administrada de la terminal Pi

**Estado:** D1 implementado; D2–D4 en aceptación; D5 y regresión completa pendientes.
C tiene aceptación local registrada. No se cambia aún la instalación estable 7.2.2, no se
publican artefactos y no se configura el equipo personal durante estas pruebas.

## Objetivo y base real

Después de instalar el canal elegido, `aikya` abre la terminal del proyecto sin
clonar el repositorio ni proporcionar `--runtime-dir`. Se mantienen ayuda y comandos
de soporte. La inferencia continúa desactivada hasta elegir proveedor/modelo y
presupuesto; instalar el producto no inicia un loop ni concede acceso a credenciales.

La entrada de desarrollo inicial exigía un directorio y Node externo. D1 ya ofrece
resolución administrada y conserva esa entrada explícita. El instalador
actual ya tiene raíz con propietario, bloqueo, archivos de releases con hashes,
entornos versionados, launchers, receipts, conservación de personalizados y gestión
opcional de Mods. La migración v8 existente cubre perfiles; no distribuye el runtime.
D ampliará estas piezas, sin crear otro instalador o mover la memoria fuera del proyecto.

## D1. Resolver la terminal y conservar las entradas

- [x] Red: resolución administrada sin depender de cwd/PATH, runtime ausente,
  receipt alterado, archivos adicionales/cambiados, plataforma incorrecta y ayuda.
- [x] Un lector pequeño del receipt/manifest elige Python, Node y launcher de la
  misma versión final, bajo la raíz administrada. Rechaza escapes/enlaces y no
  descubre instalaciones personales. Verifica identidad/integridad antes de ejecutar.
- [x] `aikya` sin subcomando abre la terminal administrada; `aikya terminal` conserva
  target/resume/modelo y `--runtime-dir` queda explícitamente para desarrollo.
  No duplicar ejecutables en PATH ni recurrir silenciosamente al checkout.
- [x] Mantener el comportamiento de soporte/ayuda y la estable 7.x en su canal.
  Procesos aislados, errores útiles sin secretos, TTY obligatoria y cancelación observada.

## D2. Construir un producto autocontenido verificable

- [ ] Builder por plataforma/arquitectura con Python, Node, paquete Aikya, runtime
  Pi y recursos/dependencias fijados. No copiar binarios Homebrew ni entornos Python
  con rutas absolutas del desarrollador como si fueran redistribuibles.
- [ ] Resolver assets oficiales/públicos fijados y checksums; registrar origen,
  versión, destino, arquitectura, tamaño, hashes, licencias y requisitos del sistema.
  Preservar el lock de npm; instalar dependencias en staging sin scripts por defecto.
- [ ] Emitir manifest acotado y archivo de distribución. Materializar únicamente
  archivos/directorios permitidos y detectar truncamiento, colisiones y escapes antes
  de activar. No descubrir ni importar configuración npm/Claude/Codex personal.
- [ ] Construir versiones privadas desde staging con identidad coherente; conservar
  `VERSION` estable hasta H. Hashes de transporte verifican integridad, no sustituyen
  la confianza en el publicador ni acreditan funcionamiento nativo.
- [ ] Probar en una carpeta final distinta con espacios/Unicode y sin herramientas
  del checkout. Registrar por separado build, import, terminal y ejecución de SDK.

[Sonda macOS real](../research/2026-11-09-pi-portable-runtime-probe.md): Python/Node
movidos a una ruta con espacios/Unicode, import aislado y ocho pruebas Pi de skills
con ambos ejecutables temporales. Es evidencia parcial de D2, no cierre del builder
ni de instalación administrada.

## D3. Extender install/update/rollback/uninstall

- [ ] Reutilizar la raíz, propietario, bloqueo y launchers existentes. Separar
  payloads administrados de estado de usuario; la biblioteca global de skills de C
  debe sobrevivir al uninstall ordinario. No borrar memoria, proyectos o clientes.
- [ ] Resolver canal estable/prerelease explícito. `latest` estable nunca adopta una
  alpha; fijar versión/asset/hash antes de escribir. Mantener la activa mientras se
  descarga, inspecciona y prueba la nueva versión final.
- [ ] Promoción atómica mediante receipt vigente, anterior retenida y rollback
  revisable. Reservar efectos y conservar operaciones parciales sin reejecución
  automática ni borrado de datos desconocidos.
- [ ] Windows: manejar archivos bloqueados sin reemplazar binarios de una sesión
  abierta. Versionar payloads y cambiar el puntero/launcher solo tras prueba; nunca
  suponer que se puede borrar la versión en uso.
- [ ] Reutilizar el comando corto existente para stable y añadir selección explícita
  de preview. El bootstrap debe poder obtener/verificar el intérprete cuando falta;
  no exigir Git, npm global o un clon al usuario final.
- [ ] Un único comando `aikya` efectivo; conservar/restaurar wrappers gestionados
  conocidos y preservar cualquier launcher o configuración modificados por el usuario.

## D4. Migrar instalaciones y sesiones 7.x

- [ ] Preview de instalación/proyecto con identidad actual, versión/cliente y
  cambios concretos. Distinguir migración de instalación, perfil y sesión.
- [ ] Copia exacta de metadatos administrados antes de promoción. Reutilizar
  `migration_v8.py`; no copiar historiales Claude a Pi como sesiones equivalentes.
- [ ] Conservar memoria/notas, documentación, skills elegidas, configuración local y
  contratos del proyecto; no activar skills/proveedores/loops durante la migración.
- [ ] Rollback de bytes conocidos y referencias administradas. Los cambios posteriores
  del usuario bloquean restauración automática y permanecen para revisión.

## D5. Aceptación y siguientes dependencias

- [ ] macOS real: instalación limpia → `aikya` → sesión local → actualización →
  rollback → uninstall, sin herramientas del checkout y con datos conservados.
- [ ] Matriz Windows/Linux por arquitectura disponible: mismo recorrido; distinguir
  jobs configurados de resultados remotos ejecutados. Mantener los gates G abiertos
  donde no exista entorno nativo. No simular sistemas operativos y llamarlos aceptados.
- [ ] Artefactos corruptos/incompletos, permisos, proxy, carpetas largas, Unicode,
  binarios bloqueados, ausencia de red/TTY, cancelación y claves/estado ajenos.
- [ ] Después de D, E valida memoria/HTML/themes sobre el producto resultante; F se
  ejecuta en el entorno de proveedor indicado por el usuario. H conserva las puertas
  alpha → beta → RC → estable. Una prueba local no autoriza publicar v8.

## Progreso observado

Se han implementado el builder, manifest/archivos deterministas, scripts fijados sin
Python previo, el ciclo administrado y respaldos v7. Las pruebas dirigidas pasan;
la primera instalación real detectó la ruta temporal `/var` de macOS y se añadió
su regresión/corrección. Falta repetir la aceptación instalada con artefactos nuevos
y cerrar la batería completa antes de marcar D2–D5. Windows/Linux siguen sin
aceptación nativa; no se publican v8 ni scripts en Pages.

[Guía privada](../deployment/pi-managed-terminal.md) y
[evidencias](../validation/2026-11-09-pi-managed-distribution.md).

## Fuentes primarias y límites por resolver con artefactos reales

[Node 22.19.0](https://nodejs.org/download/release/v22.19.0/) ofrece archivos y
checksums por plataforma; es el mínimo de compatibilidad actual, no una recomendación
de versión de seguridad para el producto final. La versión distribuida se fijará tras
comprobar dependencias y seguridad; se conservará la prueba del mínimo admitido.

[python-build-standalone](https://gregoryszorc.com/docs/python-build-standalone/main/distributions.html)
documenta distribuciones autocontenidas y metadatos de plataforma/intérprete. Es una
fuente candidata de empaquetado, pendiente de seleccionar release/hash/licencias y
probar relocación real. [npm ci](https://docs.npmjs.com/cli/v11/commands/npm-ci/)
proporciona instalación basada en lock y control de scripts; eso no prueba que todas
las dependencias nativas funcionen sin sus pasos de construcción.

La tabla de plataformas saldrá de assets realmente disponibles y pruebas nativas.
No se afirmará soporte universal de Linux: glibc/musl, arquitectura y mínimos del
sistema deben constar explícitamente. Cada fallback se revisará sin instalar paquetes
sistema ni introducir otra distribución de runtime silenciosamente.

## Primera regresión completa y correcciones posteriores

La instantánea congelada de 1.470 entradas ejecutó 1.213 tests Python: seis fallos
por imports relativos al ejecutar directamente la entrada antigua y dos omisiones
esperadas. Se han corregido los imports y los casos dirigidos pasan. La instalación
real detectó después Git obligatorio incluso sin repositorio; su regresión ahora
permite carpetas sin Git, manteniendo comprobación real en repositorios.
El ciclo con Git disponible terminó instalación/sesiones/update/rollback/uninstall
y conservó skills, notas, fuente y theme. Falta repetir sin Git y la batería final.
Instalar de nuevo la misma versión exacta es inocuo; una nueva actualiza la anterior,
y se rechazan reemplazos de versión/downgrades implícitos.

GENERATED BY AIKYA HARNESS

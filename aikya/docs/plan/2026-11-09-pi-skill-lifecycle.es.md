# Skills nativas: fuentes fijadas, ámbito global y actualización

**Estado:** C implementado y verificado localmente. La autorización secuencial del
plan maestro continúa con D; no se modifica ninguna instalación personal ni se
publica una versión estable. La aceptación real/nativa permanece en F/G.

**Objetivo:** completar el ciclo nativo de skills elegidas por el usuario, manteniendo
un catálogo efectivo por proyecto, activación explícita y memoria exclusivamente local.

**Base:** `services/selected_skills.py`, `skill_source.py`, Pi `selected-skills.ts`,
`catalogs/external.py` y la raíz de instalación de `installation/bootstrap/options.py`.
Se conservan los tres comandos actuales; no se registra otro instalador ni se
reintroducen recomendaciones externas por defecto en Aikya/README.

## Contrato y límites

- Mantener la entrada actual `{ "source": "/ruta/local" }` como instalación de
  proyecto compatible. Los nuevos campos/acciones se validan explícitamente.
- Añadir `scope:project|global`. Global significa biblioteca de paquetes inertes,
  no activación ni memoria global. Usar la raíz administrada de instalación; las
  pruebas escriben únicamente en una raíz temporal elegida para ellas.
- Un proyecto elige explícitamente nombre/origen/versión. Copiar el paquete elegido
  a su caché inmutable actual permite conservar las rutas relativas verificadas de
  Pi y evita depender de permisos o cambios posteriores de la biblioteca global.
- Mantener un nombre efectivo por proyecto. Ante una colisión global/local, exigir
  la elección concreta; no sobrescribir ni activar otra copia automáticamente.
- Conservar la fuente original exacta y el manifiesto preparado. Las instrucciones
  importadas son datos: no ejecutar scripts, hooks, plugins ni dependencias.
  Instalación y compatibilidad de datos no acreditan ejecución funcional.
- Mantener los límites actuales de paquetes, archivos, recursos y contexto por
  proyecto. Acotar también páginas/versiones retenidas del almacén global; alcanzar
  un límite exige archivado revisado, nunca borrado automático de personalizaciones.
- Actualización/rollback no reactivan instrucciones en una sesión abierta. Invalidar
  expansiones activas que ya no coincidan con la selección vigente antes del próximo
  proveedor y exigir reinicio/invocación explícita según el contrato actual.

## C1. Separar paquete y selección sin duplicar instaladores

**Archivos:** factorizar auxiliares de manifiesto/archivo/reserva desde
`selected_skills.py`; añadir módulos pequeños de almacén y selección únicamente
cuando compartan responsabilidades reales con proyecto/global.

- [x] Red: inspección sin efectos, paquete local existente intacto, archivo original
  exacto, archivos extra/enlaces/reemplazos, colisión de nombre y falta de aprobación.
- [x] Un solo compositor de paquete/manifiesto; estado firmado e identidad de raíz,
  fuente y destino. Reutilizar política de paths/propiedad y archivo original.
- [x] Biblioteca global sin descubrimiento de skills/contexto de clientes ni
  creación de memoria global. Selección de proyecto fijada a un contenido concreto.
- [x] Confirmación separada de instalar globalmente y seleccionar para el proyecto.
  Informe de selección local dentro de `aikya/docs/operations/`; comparación solo de selección
  efectiva y footer/índice con propiedad conservadora.

## C2. GitHub fijado y descarga revisable

**Archivos:** reutilizar/factorizar las comprobaciones de origen de
`catalogs/external.py`; no crear un segundo downloader que eluda controles existentes.
Verificar el protocolo con documentación primaria antes de implementar.

- [x] Aceptar repositorio/subruta y revisión de commit completa. Separar resolución
  o descarga confirmada de inspección/contenido e instalación confirmada.
- [x] Capturar identidad observada y hashes. Rechazar ref cambiado, redirección/origen
  ajeno, archivo truncado, árbol excesivo y subruta fuera de la selección.
- [x] Desactivar configuración/credenciales/helpers/hooks personales en el proceso
  de descarga. Leer objetos/datos sin ejecutar checkout filters ni código importado;
  si un caso necesita autenticación no disponible, indicarlo sin copiar credenciales.
- [x] La inspección muestra procedencia, campos ignorados y requisitos externos no
  validados. Recursos incompatibles requieren revisión; no prometer herramientas que
  el runtime de autor/revisor no posee.
- [x] Tests con transporte/locales acotados y una fuente pública fijada, si la red
  lo permite; cualquier prueba real se registra aparte, sin importar skills del usuario.

## C3. Actualización, rollback y efectos inciertos

- [x] Preview compara selección actual, contenido, origen, archivos conservados y
  cambios propuestos. Proyecto/global mantienen versiones explícitas independientes.
- [x] Reservar antes de efectos y promover solo tras lectura posterior/integridad.
  La instalación activa anterior sobrevive a descarga/copia/promoción fallida.
- [x] Conservar versiones originales y metadatos firmados para rollback revisado;
  restaurar únicamente propiedad/bytes conocidos. Una copia modificada requiere
  revisión y se preserva. No renovar permisos ni activar después de restaurar.
- [x] Recuperar solo resultados completos observados, sin repetir efectos ni
  convertir paquetes parciales en selección válida. Mantener pendiente/origen
  incierto como bloqueo explícito de la operación correspondiente.
- [x] Un update global no cambia la copia/versión elegida por otro proyecto.
  Un update del proyecto revoca la versión activa anterior antes de más inferencia.

## C4. Interfaz y verificación integrada

**Modificar:** `services/runtime_state.py`, Pi `host.ts`, `selected-skills.ts` y
validación de instrucciones antes del proveedor. Conservar una sola entrada de
cada comando canónico y separar administración de herramientas del modelo.

- [x] Menús/action JSON de plan/install/select/update/rollback/status con rutas,
  ámbito y versión concretos, sin opciones que concedan consentimiento al modelo.
- [x] No inferencia ni filtrado de administración al contexto. El revisor conserva
  su aislamiento sin skills de autor. Invocación/resolución de recursos continúa
  limitada a la selección efectiva y al manifiesto actual.
- [x] Probar dos proyectos, global/local, caché/instrucciones caducadas, caída entre
  efectos/registro, origen cambiado, datos personalizados y recursos externos.
- [x] Regresión Python completa, Pi/TypeScript, wheel instalado/Node mínimo y
  terminal real. Informar SDK simulado, paquete, terminal y plataforma nativa por
  separado; actualizar README, changelog, matriz, evidencia e índice.

[Informe final](../validation/2026-11-09-pi-skill-lifecycle.md): **1.134 pruebas Python**
en **1263.117 s**, sin fallos/dos omisiones; **87 Pi en Node 22/26**, **77 contratos
instalados**, TypeScript y calidad. Los **1.416 hashes** de código, documentación y
recursos permanecieron iguales durante la regresión final. La terminal macOS
comprueba rechazo/confirmación, ámbitos independientes, update/rollback/recuperación
y descarga pública fijada con instalación separada, con cero llamadas a modelos.

## Entrega y dependencias

Cierra C cuando fuentes/ámbitos/update/rollback estén implementados y verificados,
sin modificar la memoria por proyecto ni duplicar comandos. D reutiliza la misma
raíz/propiedad para distribución administrada. No se promociona la versión estable.

Se mantiene el rango preliminar de C: 12–24 horas antes de reserva, no horas ya
trabajadas ni precio fijado. El comando `/aikya-uninstall-skills` conserva su plan
separado y no se introduce por este subplan; tampoco se elimina ninguna skill actual.

## Contraste de procedencia y propuesta de transporte

La implementación genérica actual de `catalogs/external.py` clona sin checkout,
materializa `HEAD` y comprueba el commit después. Se preserva el comportamiento
estable mediante un adaptador, pero C debe compartir validación/procedencia y
captura de datos con la vía nativa, sin introducir otro instalador de paquetes.

La documentación primaria de [Git trees](https://docs.github.com/en/rest/git/trees)
expone modos distintos para archivos, directorios, symlinks y submódulos, además del
indicador de truncamiento. [Get a blob](https://docs.github.com/en/rest/git/blobs)
permite leer contenido; [repository contents](https://docs.github.com/en/rest/repos/contents)
puede devolver el contenido del destino de un symlink. Por eso una descarga de
contenido sin validar antes el tipo del árbol no basta para aplicar nuestra política.

Propuesta para la vía nativa: identificar commit/subárbol por HTTPS público, comprobar
modo/identidad/límites de la selección antes de capturar archivos regulares y
contrastar bytes con sus identidades de objeto y el manifiesto SHA-256 revisado.
Evaluar contenido raw fijado al commit para no usar una llamada de API por recurso;
rechazar redirecciones inesperadas, truncamiento y discrepancias. No ejecutar Git ni
checkout permite evitar filtros/configuración/credenciales de clientes y una nueva
dependencia binaria del instalador. Rate limits y falta de red permanecen estados
explícitos; el fallback local elegido por el usuario sigue disponible.

Si las pruebas obligan a usar objetos Git locales, [ls-tree](https://git-scm.com/docs/git-ls-tree)
y [cat-file](https://git-scm.com/docs/git-cat-file) son las interfaces inspeccionadas;
no activar `--filters`/`--textconv` ni materializar un checkout. La elección definitiva
se fijará con las primeras pruebas Red del capturador compartido, antes del código.

GENERATED BY AIKYA HARNESS

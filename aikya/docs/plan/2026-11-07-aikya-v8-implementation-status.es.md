# Implementación Aikya v8.0.0: estado de la ruta B

Rama: `feat/aikya-v8-pi`. Base: `origin/develop`,
`e7415238cbafa24f285d2fb3a006333d37be7ee6`, consultada el 7 de noviembre de 2026.
Se conserva la investigación y los planes mediante un commit aplicado sobre esa
base, sin crear worktrees ni modificar la configuración personal.

El usuario autoriza implementar la ruta B completa del
[plan principal](2026-11-07-aikya-multi-host.es.md) y su
[ampliación de terminal/TDD/RDD](2026-11-07-aikya-v8-terminal-tdd-rdd.es.md).
Esta autorización permite continuar las fases, pero no acredita que estén terminadas.

## Trabajo implementado inicialmente

- [x] Crear rama desde develop actualizado y conservar los documentos pendientes.
- [x] Fijar Pi 1.5.0 en un paquete TypeScript privado con lockfile.
- [x] Implementar servicio Python de lectura con operaciones permitidas, protocolo
      limitado, identidad de proyecto y errores sin filtrado de datos privados.
- [x] Conectar el servicio a un comando y una herramienta de una sesión real Pi.
- [x] Probar sesiones por proyecto y reanudación sin copiar configuración global.
- [x] Evitar descubrimiento automático de extensiones/contexto del repositorio.
- [x] Preparar CI de contratos para macOS, Windows y Linux; ejecución remota pendiente.

Se observaron pruebas Red antes de implementar el servicio, transporte, sesiones
y conexión SDK. Las comprobaciones posteriores añaden JSON ambiguo, perfiles
anidados, archivos FIFO, cancelación, symlinks y extensiones de proyecto hostiles.

Validación inicial: 11 pruebas del puente Python y cinco del SDK Pi pasan;
TypeScript y construcción del wheel pasan. La regresión completa y sus repeticiones
por restricciones del entorno se detallan en el
[informe de validación](../validation/2026-11-07-aikya-v8-first-slice.md).

## Segundo bloque: contexto y contratos RDD (verificado el 8 de noviembre)

- [x] Consultar contexto acotado desde Pi sin actualizar el índice; probar las
      29 extensiones registradas y la omisión de fuente desactualizada.
- [x] Aislar Python del proyecto y de PYTHONPATH; reproducir y corregir una
      interceptación del servicio mediante un archivo local aikya.py.
- [x] Añadir contratos iniciales R1: snapshots completos dentro de límites,
      historial, sucesores, recibos de procesos y protección frente a conflictos.
- [x] Añadir evaluación descriptiva inicial R2 y CLI de preview/almacenamiento/estado.
      Esta evaluación no ejecuta checks ni concede cierre o entrega.

Pruebas dirigidas actuales: 16 del puente Python, 26 de contratos/CLI RDD y nueve
Pi pasan. Véase la [validación del segundo bloque](../validation/2026-11-07-aikya-v8-rdd-context.md).
En ese bloque los recibos conservaban entradas del host. El bloque siguiente
conecta checks a procesos reales; sigue pendiente el revisor.

## Tercer bloque: ejecutor y terminal de lectura (8 de noviembre)

- [x] Ejecutar checks aprobados con definición, ejecutable y entorno congelados;
      conservar metadatos y recibos sin copiar salida privada al diario.
- [x] Validar resultados JUnit, TAP 13, TRX y Go JSON; rechazar ausencia de informe,
      cero pruebas, omisiones, límites excedidos y cambios de fuente/definición.
- [x] Bloquear la repetición de una ejecución y los nuevos intentos cuando exista
      una ejecución incierta pendiente de conciliación.
- [x] Añadir `aikya terminal` como arranque explícito de desarrollo con la interfaz
      real de Pi, estado local excluido de Git y solo consultas de lectura.
- [x] Bloquear inferencia, comandos nativos de mutación, atajos de ejecución y
      descubrimiento automático; validar estado/contexto/cierre en una PTY de macOS.
- [x] Regresión completa: 772 pruebas Python, sin fallos, dos omitidas; 19 pruebas
      Pi y TypeScript pasan. Node y Go ejecutan pruebas reales.

La terminal exige seleccionar el paquete privado con `--runtime-dir`; no es un
instalador final. Los formatos XML cuentan con fixtures y procesos controlados,
sin aceptación nativa de todos los frameworks. No se ha invocado ningún modelo ni
probado Windows/Linux en esta entrega. Véase la
[validación del tercer bloque](../validation/2026-11-08-aikya-v8-executor-terminal.md).

## Cuarto bloque: runtime controlado y adaptación de Gentle — 8 de noviembre

- [x] Escrituras con preview desplazable, concesión HMAC de un uso y verificación
      de contenido, proyecto, sesión, caducidad y vigencia de la fuente.
- [x] Vinculación SDD firmada a una tarea aprobada, sesión y archivos explícitos;
      los cambios de estado o de alcance impiden reutilizar la autorización.
- [x] Presupuesto local duradero en la ruta real de inferencia Pi; atribución por
      rol/fase/proveedor/modelo, sin restablecimiento al reanudar o cambiar límites.
- [x] Bloqueo ante uso incierto, credenciales sin configurar, peticiones excesivas
      o herramientas duplicadas. Compactación explícita, sin resumidor adicional.
- [x] Notas locales revisadas y vigentes, búsqueda acotada, actualización del índice
      y HTML tras escrituras autorizadas, conservando políticas y HTML personalizado.
- [x] Preview claro/oscuro, validación y preferencia local persistente; panel de
      tokens separado de cuotas observadas, con ausencia/antigüedad explícitas.
- [x] Onboarding independiente de Claude con elección ODD/SDD y plantillas canónicas
      para proyectos nuevos/existentes de desarrollo, infraestructura y DevOps.
- [x] Transiciones SDD nativas, aprobación explícita por etapa y estado por ID.
- [x] Revisor independiente con sesión/llamada medidas y vinculadas al candidato,
      admisión firmada, historial e informe; cierre técnico separado de la entrega.
- [x] Recuperación de ejecución conocida sin relanzar procesos; políticas TDD
      opcionales que requieren Red ejecutado y las mismas pruebas en Green.
- [x] Regresión Python del snapshot: **817 pruebas en 1002.121 s**, sin fallos,
      dos omitidas. Prueba PTY real de tema/presupuesto persistentes, cancelación
      y onboarding SDD con HTML local y sin archivos de Claude ni llamadas a modelos.

Estas marcas acreditan contratos y el alcance indicado, no el cierre completo de
las fases de producto. Las pruebas Pi utilizan el SDK real y transportes de proveedor
controlados, sin inferencia real. El entorno nativo observado sigue siendo macOS.
Véanse la [arquitectura actual](../architecture/2026-11-08-pi-controlled-runtime.md),
[guía del prototipo](../deployment/pi-controlled-preview.md) y
[matriz de comandos](../validation/2026-11-08-pi-command-coverage.md).

## Quinto bloque: continuidad local y migración — 8 de noviembre

- [x] Conectar sesiones Pi interactivas y SDK al observador existente; actualizar
      HTML por cambios externos sin inferencia, renovar la sesión inactiva localmente
      y cerrar solo su lease, esperando cualquier renovación en curso.
- [x] Migración explícita de perfiles legacy administrados, manteniendo ODD/SDD,
      código/documentos/memoria, con originales respaldados y registros firmados.
      Reversión exacta, rechazo de personalizaciones e informe MD localizado/indexado.
- [x] Probar perfiles reales del instalador para desarrollo/infraestructura/DevOps
      en ODD/SDD y ambos idiomas, así como interrupciones y respaldos alterados.
- [x] Recuperar onboarding interrumpido mediante un nuevo preview aprobado y admitir
      análisis posterior de proyectos inicializados sin ocultar código bajo `aikya`.
- [x] Catálogo local de modelos paginado, sin refresco de proveedores ni secretos;
      excluir resultados administrativos del contexto y mostrar un footer local claro.
- [x] Regresión completa actual: **829 pruebas en 1095.316 s**, sin fallos y dos
      omitidas; **46 pruebas Pi** y TypeScript pasan. La migración/reversión se
      ejercitó también desde la PTY de macOS.

Los cambios no sustituyen la instalación integrada ni acreditan aceptación remota o
con proveedores reales. El [informe de continuidad y migración](../validation/2026-11-08-pi-memory-migration.md)
separa esas limitaciones de los contratos locales ya verificados.

## Sexto bloque: checks/revisión nativos y continuidad por rol — 8 de noviembre

- [x] `/aikya-tests`: snapshot, renovación, ejecución y estado de checks congelados;
      objetivo/aceptación explícitos, política ordenada y pruebas TDD sin cambios.
- [x] `/aikya-verify`: estado, revisor independiente con presupuesto y recuperación
      de observaciones conocidas sin relanzar procesos ni autorizar la entrega.
- [x] Herramienta de autor `aikya_check` limitada a identificadores, con confirmación
      nativa obligatoria; sin ejecución en consumidores sin interfaz.
- [x] Cancelación cooperativa y espera de resultado observado; testigos privados
      firmados para admisión/recuperación, sin tomar JSON público como prueba suficiente.
- [x] Alcance de sucesores, conservación del check TDD y ausencia de contadores;
      informes en el idioma del proyecto con identidad estable.
- [x] Roles privados de autor/revisor que impiden reanudar una revisión como autor;
      conservación y rechazo de transcripciones anteriores sin rol comprobado.
- [x] PTY macOS: fallo Red real, Green real que sigue requiriendo revisión,
      rechazo de revisión sin modelo y cancelación sin permiso de cierre.

El [informe del bloque](../validation/2026-11-08-pi-native-checks.md) separa la regresión
completa, SDK real con transporte fixture, wheel instalado y pruebas de interfaz.
No acredita proveedores reales ni cierre de las fases de producto.

## Séptimo bloque: ODD nativo y alcance de tareas — 8 de noviembre

- [x] Reutilizar el motor/plantillas ODD con preparación confirmada, estado paginado,
      selección de tarea, finalización con evidencia y reconciliación explícita.
- [x] Ligar escrituras/checks a sesión, tarea vigente y archivos; revocar permisos
      anteriores al seleccionar otra vez y liberar solo mediante confirmación.
- [x] Exigir intención/criterios/checks/alcance coincidentes y revisión admitida;
      reservar antes del efecto y verificar fuente, Git y reporte tras registrarlo.
- [x] Preservar incertidumbre sin replay y proteger documentos personalizados;
      mantener el flujo SDD separado y la entrega sin autorización automática.
- [x] Contratos adversarios y PTY macOS Node 22: cancelar sin expediente, generar
      documentos españoles/indexados, ver fases inglesas, denegar cierre no observado
      y liberar selección conservando la documentación.

- [x] Regresión completa: **855 pruebas en 1147.281 s**, sin fallos y dos omitidas;
      **52 pruebas Pi** con Node 22/26, wheel instalado y TypeScript correctos.

El [informe ODD](../validation/2026-11-08-pi-odd-workflow.md) registra la batería y
sus límites; este bloque no cierra toda la paridad ni la aceptación de producto.

## Octavo bloque: skills locales elegidas y contexto verificado — 8 de noviembre

- [x] Status/planning sin efectos; instalación local confirmada con originales exactos,
      registro firmado, comparación/informe localizados y footer/índice.
- [x] Preservar datos anteriores/personalizados y efectos inciertos; no ejecutar
      scripts/hooks/dependencias ni recomendar fuentes externas automáticamente.
- [x] Cargar solo entradas aprobadas mediante APIs públicas de Pi, sin descubrimiento
      ni listado automático; referencias acotadas solo tras invocación del autor.
- [x] Comprobar la expansión real antes del envío/admisión del modelo: los errores
      de hooks por sí solos no siempre detienen el SDK. Revisor separado.
- [x] 17 contratos host, 57 pruebas Pi con Node 22/26 y PTY de instalación/cancelación;
      **872 pruebas Python en 1137.467 s**, sin fallos/dos omitidas, y wheel instalado
      con 57 Pi/17 contratos host fuera del checkout.

El [informe de skills](../validation/2026-11-08-pi-selected-skills.md) declara los
límites. Los ámbitos/fuentes/lifecycle restantes y aceptación real siguen abiertos.

## Noveno bloque: diagnóstico y calidad locales — 8 de noviembre

- [x] `/aikya-doctor`: perfil, versiones del runtime, presencia de herramientas y
      proveedor/auth configurados; sin ejecutar SDKs, leer secretos ni afirmar
      compatibilidad/conectividad o preparación del entorno.
- [x] `/aikya-quality`: instantánea acotada de archivos explícitos, motor existente,
      excepciones ligadas al hash, resultados limitados y cobertura estática honesta
      de todas las extensiones del índice, incluidos Dart, módulos JS y stubs Python.
- [x] Mantener las herramientas del modelo y excluir informes administrativos del
      contexto posterior; cero llamadas de inferencia/presupuesto por estas consultas.
- [x] Regresión completa: **883 pruebas Python en 1141.019 s**, sin fallos/dos omitidas.
- [x] 11 contratos host, 59 pruebas SDK, TypeScript y wheel instalado fuera del
      checkout; terminal macOS Node 22 con error/corrección Python, límite Dart,
      rechazo de rutas privadas y salida normal, sin documentación nueva.

El [informe del bloque](../validation/2026-11-08-pi-local-diagnostics.md) registra
los resultados y los límites de aceptación. La paridad queda en 19/28 adaptaciones,
algunas limitadas; no son aceptación completa de producto.

## Décimo bloque: perfiles y documentación nativos — 8 de noviembre

- [x] `/aikya-answers`: perfil explícito new/existing y ODD/SDD, archivo local
      acotado ligado a sus bytes, idioma establecido y preservación de proyectos.
- [x] `/aikya-docs`: catálogo verificado, composición/merge canónicos, revisión
      before/after y propiedad firmada de páginas; expedientes dedicados protegidos.
- [x] `/aikya-docs-sync`: baseline firmado de rutas seleccionadas, sin REQ cuando
      no hay cambios; registro localizado de hashes y documentos realmente escritos.
- [x] Reservas previas a efectos, revalidación final de idioma/contenido/propiedad,
      conservación de páginas personalizadas e incertidumbre sin replay automático.
- [x] Footer único corregido en nuevos overview de onboarding; índice y memoria/HTML
      actuales, sin inferencia administrativa ni aprobación técnica implícita.
- [x] 26 contratos host, cuatro escenarios SDK, 63 pruebas Pi y matriz instalada
      de 24 previews; terminal macOS con paquete instalado y footer/índice verificados.
- [x] Regresión completa: **909 pruebas en 1134.853 s**, sin fallos/dos omitidas.

[Informe del bloque](../validation/2026-11-08-pi-profile-documentation.md).
La matriz queda en 22/28 adaptaciones con límites explícitos; siguen pendientes
project/infra/scaffold/bugfix/arc-review/mobile-feature y la aceptación de producto.

## Fases aún abiertas

El [plan de pendientes](2026-11-08-aikya-v8-pendientes.es.md) sigue autorizado. La
adaptación de memoria, themes y uso de Gentle ya tiene los contratos anteriores;
no se instaló Gentle ni se introdujo Engram o un segundo almacén.

- [ ] B0: aceptación con proveedor/modelo y presupuesto en el entorno de pruebas
      reales indicado por el usuario; fixtures no acreditan suscripción ni ahorro.
- [ ] B1: escrituras grandes/patches, operaciones adicionales y aceptación de
      permisos/recuperación; no hay aislamiento del sistema operativo.
- [ ] R1–R3: aceptación completa de checks/revisor y recuperación,
      clasificación TDD transversal y matriz de runners/lenguajes nativos.
- [ ] B2/T1: entrada única `aikya`, instalación integrada del runtime, selección
      de modelo y compactación larga/proveedores con aceptación real.
- [ ] B3: paridad de los 28 comandos, orquestación ODD completa y ciclo de skills; veintiocho comandos
      canónicos tienen adaptación Pi, con limitaciones documentadas.
- [x] B4, contratos locales: observador externo con renovación/cierre de leases,
      migración reversible de perfiles administrados y recuperación por preview
      nuevo de onboarding interrumpido.
- [ ] B4, aceptación de producto: migración de la instalación/runtime, convivencia
      de clientes, restauración en sistemas nativos y casos personalizados no admitidos.
- [ ] B5: instalación/actualización/desinstalación nativas, CI remota, prerelease
      verificable y publicación v8.0.0 tras superar los criterios de aceptación.

La versión estable continúa en 7.2.2. El paquete privado mantiene 8.0.0-alpha.0.
No se ha publicado una versión ni cambiado la selección de actualizaciones estables.

## Undécimo bloque: project/infra/scaffold — 9 de noviembre

- [x] Planes explícitos y registro localizado; artefactos nombrados conservan existentes.
- [x] Lotes ligados a fuente/perfil/idioma/tarea, creación exclusiva y reserva durable.
- [x] Resolución exacta/archivo SHA-512, preparación en staging y copia confirmadas
      por separado; inspección acotada, cancelación observada y sin helpers del proyecto.
- [x] Catálogo de validadores compartido, estados de proceso y recibos sin tests inventados.
- [x] Rutas nativas Pi sin inferencia, sin herramientas nuevas del modelo y excluidas
      del contexto posterior; catálogo 25/28 con límites explícitos.
- [x] Regresión final: **950 pruebas Python en 1178.797 s**, sin fallos/dos omitidas;
      64 Pi en Node 22/26, 41 contratos del wheel y terminal macOS en español.
- [x] Terraform real, generación/build .NET y generación Vite fijada; memoria/HTML
      incremental y alcance seleccionado ODD/SDD comprobados. Nombre de workspace
      por defecto de SDK documentado para corregir en B.
- [ ] Aceptación oficial de generadores/SDK y sistemas nativos: continúa en G.

[Informe de A1](../validation/2026-11-09-pi-bootstrap-generation.md).
Las cifras de los bloques anteriores corresponden a sus snapshots, no a esta entrega.
El resto del plan maestro sigue autorizado; este bloque no completa v8.

## Duodécimo bloque: bugfix, arquitectura y móvil — 9 de noviembre

- [x] Hallazgos de arquitectura ligados a fragmentos/líneas/hashes actuales y
      documentación canónica confirmada; interpretación distinta de ejecución.
- [x] Bugs: evidencia nativa Red/Green, cero tests no acreditan reproducción,
      revisión independiente y fuente vigente antes de `fixed`; registro append-safe.
- [x] Contexto móvil tipado en ODD y selección firmada SDD; reelección invalida
      grants anteriores. Presencia SDK no acredita build, tests ni simulador.
- [x] Tres comandos únicos en Pi, confirmación headless, revisor separado y sin
      inferencia ni contexto administrativo posterior. Catálogo 28/28 con límites.
- [x] **971 pruebas Python en 1221.651 s**, sin fallos/dos omitidas; 65 Pi con
      Node 22/26, TypeScript, 21 contratos del wheel instalado y 112 perfiles móviles.
- [x] Terminal macOS en español: fragmentos actuales, cancelación/registro, bugs
      preservados, contexto móvil tipado y selección, footer único y salida normal.
- [ ] Aceptación real de plataformas/proveedores y recorridos completos sigue abierta.

La versión estable y el runtime privado conservan sus versiones; este bloque no
cierra B–H ni convierte adaptadores limitados en aceptación de producto.

[Informe de A2](../validation/2026-11-09-pi-engineering-workflows.md).

## Decimotercer bloque: operaciones y ciclo acotado — 9 de noviembre

- [x] B1/B2: clasificación de procesos/tests, baseline de refactorización,
      continuidad y recuperación de documentación confirmada sin transferir aceptación.
- [x] B3: lotes fuente con parches exactos, reserva/lectura posterior y recuperación
      de efectos completos sin reescritura ni permisos renovados.
- [x] B4: tarea ODD/SDD seleccionada, límites duraderos, fases inglesas y guard previo
      a cada proveedor, incluidos resumen/revisión; una única corrección con evidencia.
- [x] Historial grande/custom conservado, rol de autor/revisor separado, deadline
      exacto por JSON y checkpoint de tarea conservado tras compactación medida.
- [x] Terminal real ODD/SDD con documentación confirmada, checks y revisor de fixture.
      Cancelar y reanudar el registro conserva tres llamadas y no repite efectos/checks.
- [x] Snapshot final: **1.078 pruebas Python en 1226.288 s**, sin fallos/dos omitidas;
      **84 Pi en Node 22/26**, 38 contratos instalados de tarea/SDD/índice y
      prueba de un solo owner ante dos inicios concurrentes.
- [ ] C–H: skills globales/GitHub/update, distribución, memoria/themes instalados,
      proveedores reales, matriz nativa y preparación/publicación de producto.

[Validación B4](../validation/2026-11-09-pi-bounded-task-cycle.md) y
[subplan C](2026-11-09-pi-skill-lifecycle.es.md). Los snapshots anteriores conservan
sus propias cifras; esta aceptación local no publica v8 ni sustituye F/G.

## Decimocuarto bloque: ciclo de skills — 9 de noviembre

- [x] Fuentes locales/capturadas y biblioteca global inerte, con selección fijada
      por proyecto, escritor común, originales exactos y metadatos firmados.
- [x] Resolución/captura pública fijada sin checkout ni código importado; modos,
      identidades, truncamiento, límites y rutas portables verificados.
- [x] Update/rollback independientes, reserva antes de efectos y recuperación de
      promociones completas selladas sin repetir descarga/copia.
- [x] Revocar expansiones antiguas antes del proveedor, capacidad del registro
      antes de copiar y propiedad de informes antes de reemplazar documentos.
- [x] 75 contratos de skills con wheel instalado; 87 Pi con Node 22/26, TypeScript
      y terminal macOS real con cero inferencia, actualización/rollback/recuperación.
- [x] Regresión final: **1.134 Python en 1263.117 s**, sin fallos/dos omisiones;
      **87 Pi en Node 22/26**, **77 contratos instalados** y **1.416 hashes de inputs
      sin cambios**, tras corregir el fixture y congelar también los recursos.
- [x] Terminal pública: captura fijada rechazada/confirmada, originales comprobados
      e instalación separada confirmada; cero llamadas a modelos.
- [ ] D–H: distribución administrada, aceptación instalada de memoria/themes,
      proveedor real en el entorno elegido, matriz nativa y puertas de publicación.

[Informe C](../validation/2026-11-09-pi-skill-lifecycle.md) y
[subplan D](2026-11-09-pi-managed-distribution.es.md). No se publica una versión
ni se modifican instalaciones/skills personales durante estas pruebas.

## Distribución administrada D — ejecución del 9 de noviembre

La entrada sin subcomando ya resuelve el runtime administrado con integridad; se
conservan ayuda, soporte y desarrollo explícito. El builder nativo incluye intérpretes
oficiales fijados, núcleo privado y dependencias Pi verificables. Se han implementado
promoción, rollback, preservación de datos, recuperación sin replay y respaldo v7.
Las pruebas dirigidas pasan; la aceptación instalada y regresión completa siguen en
curso tras corregir el alias temporal de macOS observado en la primera ejecución.
Consulta el [informe D](../validation/2026-11-09-pi-managed-distribution.md). E–H y
los gates nativos/proveedores permanecen abiertos; la estable sigue en 7.2.2.

GENERATED BY AIKYA HARNESS

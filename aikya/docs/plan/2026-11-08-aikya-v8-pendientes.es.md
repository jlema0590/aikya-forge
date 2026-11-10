# Plan vigente del trabajo pendiente para Aikya v8.0.0

Fecha de revisión: 9 de noviembre de 2026. Rama: `feat/aikya-v8-pi`.
Base contrastada: `76b6d41` y snapshot B4 verificado. Estado: implementación secuencial en curso.

**Objetivo:** completar Aikya como producto de terminal sobre Pi, instalable en
macOS, Windows y Linux, con ODD/SDD, TDD, Receipt Driven Development (RDD), memoria
local por proyecto y documentación auditable.

**Arquitectura:** conservar los servicios Python y los motores canónicos; adaptar
la interfaz y ejecución de Pi mediante contratos del host acotados. Mantener un
responsable de permisos, presupuesto y revisión por sesión. Evitar otro planificador,
una segunda memoria autoritativa o el funcionamiento simultáneo de dos orquestadores.

**Tecnología verificada:** Python, TypeScript, Pi 1.5.0 fijado y Node mínimo 22.19.0.
Estable 7.2.2; runtime privado 8.0.0-alpha.0. Ejecución prevista: secuencial en la
rama actual, con pruebas por entrega y commits revisables.

**Especificaciones:** [ruta B](2026-11-07-aikya-multi-host.es.md),
[TDD/RDD/terminal](2026-11-07-aikya-v8-terminal-tdd-rdd.es.md),
[estado de implementación](2026-11-07-aikya-v8-implementation-status.es.md) y
[matriz de comandos](../validation/2026-11-08-pi-command-coverage.md).
Esta revisión sustituye la lista inicial de pendientes. Los resultados anteriores
se conservan en el estado de implementación, los informes enlazados y Git.

## Base existente y evidencia

- 28 de 28 comandos canónicos tienen adaptación Pi; varios mantienen límites
  explícitos. La cantidad de adaptadores no mide la aceptación del producto.
- Existen onboarding/perfiles ODD/SDD, etapas SDD, selección de tareas ODD,
  escrituras confirmadas, checks congelados y admisión de revisión independiente.
- Existen presupuestos locales duraderos, observación de uso/cuota disponible,
  contexto acotado, memoria/HTML incrementales y preferencias claro/oscuro.
- Existen skills locales elegidas explícitamente, migración reversible de perfiles
  administrados y composición/sincronización documental con propiedad firmada.
- Última batería registrada: 1.078 pruebas Python en 1226.288 segundos, sin fallos,
  dos omitidas; 84 pruebas Pi en Node 22/26, paquete instalado y terminal macOS
  verificados. Los recorridos ODD/SDD incluyen documentación antes de revisión.
- Las dos omisiones corresponden a fallback de dependencias opcionales con extras
  instalados y una prueba que necesita PowerShell. Las pruebas Pi usan transportes
  de proveedor de prueba; la aceptación con proveedores reales sigue pendiente.

[Evidencia de la última entrega](../validation/2026-11-09-pi-bounded-task-cycle.md).

## Restricciones comunes

- Conservar fases visibles en inglés: `explore`, `plan`, `implement`, `validate`,
  `security`, `review`. Una fase mostrada no acredita su finalización.
- Conservar ODD/SDD como elecciones explícitas. TDD/RDD son controles transversales;
  documentar la no aplicabilidad cuando corresponda, con ejecución observable.
- Escribir planes, bugs, features e informes en `aikya/docs/`; respetar en/es,
  footer único e índice real. JSON conserva su formato sin footer.
- Mantener memoria, sesiones y evidencia por proyecto. No instalar skills externas
  recomendadas por defecto ni copiar credenciales personales.
- Un único propietario del ejecutable `aikya`; preservar instalaciones y datos
  personalizados. Crear worktrees solo por petición explícita del usuario.
- Reutilizar módulos del paquete y contratos existentes. No introducir archivos
  nuevos de más de 1.000 líneas ni duplicar orquestadores/almacenes.
- Consulta administrativa, indexación y render local sin inferencia. Uso ausente
  permanece desconocido; compactación que llame a un modelo se contabiliza.
- Mantener consentimiento del host, fuente vigente, recuperación y revisión
  independientes de las afirmaciones del modelo. Conservar efectos inciertos.
- CI configurada, presencia de SDK, extensión inventariada y prueba simulada son
  evidencias distintas de un build, ejecución nativa o aceptación con proveedor real.

## Orden y dependencias

| Entrega | Pendiente concreto | Dependencia | Estimación orientativa |
| --- | --- | --- | ---: |
| A1 | Project, infra y scaffold: planificación y efectos aprobados | Base actual | 24–40 h |
| A2 | Bugfix, arquitectura y mobile-feature | A1 para generación; controles actuales para diagnóstico | 24–40 h |
| B | Completar operaciones, continuidad y ciclo ODD/SDD/TDD/RDD | A1/A2 | 20–36 h |
| C | Skills nativas globales, GitHub y actualización | Base actual; selección instalada compartida con D | 12–24 h |
| D | Entrada única, bundle, instalación, actualización y migración del runtime | A1/A2/B/C para aceptación integrada | 32–56 h |
| E | Aceptación de memoria, HTML y themes sobre instalación administrada | D | 12–20 h |
| F | Proveedores reales, tokens y compactación larga | B/D; entorno real acordado | 12–24 h |
| G | Matriz completa por sistema/lenguaje y pruebas adversarias | A–F; CI desde cada entrega | 20–32 h |
| H | Documentación final, artefactos y release | A–G aceptadas | 8–12 h |
| | Total antes de reserva | | **164–284 h** |
| | Total con reserva del 25 % | | **205–355 h** |

Nueva estimación preliminar del trabajo restante, no horas registradas ni resta
aritmética del presupuesto anterior. Aproximadamente 5–9 semanas a 40 h/semana,
sin contar esperas de entornos/CI. Las 225–370 h de la revisión inicial no se suman
a esta estimación. Tras la aceptación local de A1/A2/B/C, D–H suman preliminarmente **84–144 horas**
antes de reserva (**105–180 horas** con el 25 %). Es un rango restante por alcance,
no horas registradas; la aceptación con proveedores/sistemas reales sigue abierta.

Coste de desarrollo: horas × tarifa acordada, todavía sin importe monetario fijado.
Consumo de modelos: presupuesto aparte, medido en F, incluyendo revisión y
compactación. No se presupone ahorro. E valida funciones ya implementadas; G cubre
la aceptación transversal, sin volver a presupuestar su implementación.

## A1. Project, infra y scaffold: adaptación limitada verificada

| Comando pendiente | Comportamiento requerido | Cierre de la entrega |
| --- | --- | --- |
| `/aikya-project` | Planificar proyecto/módulos desde decisiones confirmadas, con archivos, límites, criterios y checks; registrar documentos solo tras confirmar. | Plan sin efectos, fuentes vigentes y documentación localizada; implementación SDD ligada a su tarea aprobada. |
| `/aikya-infra` | Planificar, generar archivos nombrados sin sobrescribir y ejecutar validadores locales aprobados. | Distinguir generado, validado, bloqueado y no configurado; conservar existentes y separar operaciones cloud/despliegue. |
| `/aikya-scaffold` | Previsualizar y ejecutar generadores identificados para proyectos nuevos. | Versiones/argumentos/destinos revisados, cancelación y efectos parciales observados; proyecto existente preservado; pasos manuales no equivalen a ejecución. |

**Reutilizar:** `src/aikya/tools/scaffold.py`, `tools/infrastructure.py`,
`installation/profile.py`, `installation/requirements.py`, `services/authorization.py`,
`services/task_binding.py`, documentación y recibos existentes.
**Modificar:** `services/runtime_state.py` y Pi `host.ts`, `extension.ts`, `editor.ts`.
**Archivos propuestos nuevos:** `services/project_bootstrap.py`,
`services/generation.py`, Pi `project-bootstrap.ts`,
`tests/test_pi_project_bootstrap.py`, `tests/test_pi_generation.py` y
`packages/aikya-pi/tests/project-bootstrap.test.ts`. Implementados en el snapshot A1;
se añaden auxiliares de recetas/registros y validación local por responsabilidad.

**Interfaces propuestas:**
`project_bootstrap.preview(root, command, input_data, session_id)` devuelve plan y
revisión concreta; `project_bootstrap.apply(root, plan, approved=False)` valida
consentimiento y vigencia. `generation.preview(root, files, session_id, category, details)` y
`generation.apply(root, plan, files, approved=False)` envuelven lotes nombrados;
`scaffold_generation.preview/apply` encapsulan solo recetas conocidas,
con ejecutable/versión/argumentos/entorno/destinos e identidad de fuente. El modelo
no recibe una herramienta de shell general. La forma JSON exacta de cada acción se
fijará en el subplan A1 antes de implementar; estas son fronteras de responsabilidad.

**Adaptaciones verificadas que deben resolverse:**

- `scaffold.command_plans()` contiene referencias `@latest`. Resolver y fijar la
  versión/origen antes de confirmar su ejecución; la resolución/descarga también
  requiere el flujo aprobado correspondiente. Una versión no resuelta bloquea apply.
- `scaffold.apply()` busca e importa un detector copiado dentro del proyecto.
  El adaptador Pi debe usar los módulos instalados del paquete y la política del
  host; no depender de assets Claude ni ejecutar un helper local por su nombre.
- Los backends actuales usan contratos distintos: strings, códigos de salida,
  mensajes y funciones de ejecución. Convertirlos en resultados estructurados;
  una guía manual o salida cero sin generador ejecutado no es un build observado.
- Revisar efectos reales de validadores según su configuración. Aprobar un
  formatter o render local no autoriza descargas, plugins, credenciales ni cambios
  remotos. Los controles sin tests no deben inventar contadores de pruebas.

- [x] Red: `test_project_plan_has_no_effects`, `test_stale_generation_is_refused`,
  `test_existing_project_cannot_scaffold`, `test_existing_infra_is_preserved`,
  `test_unresolved_generator_version_cannot_execute`,
  `test_project_helper_is_not_imported`, `test_cancelled_generator_is_not_success`.
- [x] Observar los fallos antes de añadir adaptadores; implementar por comando,
  con confirmación concreta, reserva previa y lectura posterior de resultados.
- [x] Green: comprobar esos comportamientos con procesos/archivos reales locales;
  generar informes con estados distintos de tests, build y pasos manuales.
- [x] Ejecutar SDK, TypeScript, paquete instalado y terminal; actualizar la matriz
  solo para capacidades verificadas. 41 contratos host instalados, 64 SDK con
  Node 22/26 y PTY macOS; Terraform y .NET reales en proyectos temporales.
- [x] Cerrar la regresión Python completa del snapshot inmutable y el informe;
  commit separado antes de A2. SDKs oficiales restantes/plataformas siguen en G.

Subplanes de ejecución: [A1](2026-11-09-pi-bootstrap-generation.es.md) y
[A2](2026-11-09-pi-engineering-workflows.es.md). La evidencia parcial de A1 no
cierra la aceptación global ni implica ejecutar proveedores en este equipo.

## A2. Los otros tres comandos: adaptación limitada verificada

- `/aikya-bugfix`: reproducción, hipótesis contrastada, regresión Red/Green, fix
  acotado y registro append-safe en `aikya/docs/bugs/bugs.md` con el escritor existente.
- `/aikya-arc-review`: observaciones de arquitectura sobre fuentes seleccionadas,
  hallazgos/riesgos con procedencia y documentación confirmada. Reutilizar la
  infraestructura de revisión; no confundir una API de revisor con este flujo completo.
- `/aikya-mobile-feature`: alcance Android/iOS/Flutter/React Native según perfil,
  ODD/SDD y validación de SDK, build/tests/simulador realmente disponibles.

**Reutilizar:** motores `workflows/odd.py`, `workflows/sdd/`, selección de tareas,
checks/revisión, `documentation/templates.py`, `documentation/composition.py` y
memoria/contexto existentes. Añadir adaptadores por responsabilidad, sin otro motor.

- [x] Red: no reproducido distinto de corregido; dato de arquitectura sin fuente;
  plataforma fuera del perfil; SDK/simulador ausente; test cero o informe inválido;
  tarea SDD no aprobada; documento personalizado preservado.
- [x] Implementar y verificar cada comando separadamente. Cada efecto conserva
  su consentimiento, alcance y resultado observable.
- [x] Completar catálogo 28/28 y matriz de límites; la aceptación funcional de las
  adaptaciones limitadas continúa en B/G. Actualizar pruebas, informes y commits.

## B. Completar operaciones, sesiones y ciclo del agente

La revisión de A2 identifica continuidad documental pendiente: una página canónica
escrita entre Red y la revisión final cambia la identidad completa y puede bloquear
el refresh fuera del alcance firmado. Crear pruebas de transición documental
observada por el host, sin transferir aceptación ni excluir controles de metodología
por omisión; conservar el lineage de tests inmutables y exigir revisión del candidato
final. Los registros de bugs son snapshots, no renovaciones de aprobación.

Hallazgo de A1 en el SDK .NET real: el nombre predeterminado toma `workspace`,
que es el directorio privado del generador. Añadir prueba de nombre explícito del
perfil y conservarlo en el staging sin cambiar los destinos revisados; comprobar
.NET y generadores npm. No copiar `obj`/caches por omisión al seleccionar artefactos.

**Modificar:** `services/authorization.py`, `task_binding.py`, `odd_workflow.py`,
`checks.py`, `documentation.py`, `review/` y los adaptadores Pi correspondientes.

- [x] Incorporar parches y operaciones multifichero con previsualización exacta,
  alcance aprobado y preservación de cambios concurrentes; ampliar límites solo
  con contratos, pruebas y motivos, sin eludirlos silenciosamente.
- [x] Conectar el ciclo acotado de tarea y sus fases inglesas a ejecución/checks,
  revisión independiente y recuperación existentes. Mantener límites de turnos,
  tiempo y uso; una corrección máxima antes de escalado según el MVP actual.
- [x] Completar reanudación/compactación/cambio de sesión sin reutilizar grants
  vencidos, reiniciar presupuesto ni cargar un transcript de revisor como autor.
- [x] Añadir recuperación explícita de operaciones documentales y otros efectos
  pendientes, con evidencia de qué ocurrió y sin repetir un efecto incierto.
- [x] Revisar clasificación TDD de código, infraestructura y acciones documentales.
  Conservar causas verificables de no aplicabilidad; proceso exitoso y tests
  superados tienen contratos distintos.
- [x] Pruebas: caída entre efecto/recibo, fuente cambiada durante ejecución,
  dos sesiones concurrentes, falta de uso, cancelación y evidencia alterada.

Cierre: un recorrido ODD y otro SDD completos, incluida documentación final antes
del candidato final de checks/revisión. Cambiar páginas después puede invalidar
aceptación anterior; mantener la vigencia de la evidencia y separar entrega.

B1/B2 verificadas: clasificación de checks/baseline de refactorización, límites previos
a efectos y continuidad/recuperación documental confirmada. El revisor recibe las
páginas finales y no se transfiere aceptación. Se ha comprobado el nombre del perfil
con .NET y Vite oficiales. Esos efectos y recorridos continuaron en B3/B4. [Informe](../validation/2026-11-09-pi-checks-document-continuity.md).

B3 verificada: parches con anclas exactas y lotes confirmados dentro del candidato
nativo, recuperación de efectos completos sin reescritura y pruebas instaladas de
un archivo de 36 KB. Se mantiene la revisión completa de 6.000 bytes y el escalado
explícito. B4 verificada: ciclo Pi acotado, fases inglesas, guard async en cada inferencia,
una corrección con evidencia y reanudación/compactación sin reset. Terminal ODD/SDD
con documentación confirmada, checks y revisión independiente de fixture; reanudar
registro aceptado conserva tres llamadas totales y no repite efectos/checks. El run
conserva su deadline y bloquea incertidumbre. 1.078 Python, 84 Pi en Node 22/26,
contratos instalados y dos inicios concurrentes verificados. [Subplan B4](2026-11-09-pi-bounded-task-cycle.es.md).
La aceptación de modelos/sistemas reales permanece en F/G; no se cierra el producto.

## C. Skills: completar fuentes, ámbitos y actualización

Verificado localmente: [subplan C](2026-11-09-pi-skill-lifecycle.es.md).
[La evidencia C](../validation/2026-11-09-pi-skill-lifecycle.md) registra 1.134 Python,
87 Pi en Node 22/26, 77 contratos instalados y terminal macOS real, incluida la
captura pública y su instalación separada. No sustituye F/G ni publica v8.

**Modificar:** `services/selected_skills.py`, `skill_source.py` y Pi
`selected-skills.ts`; reutilizar procedencia/descargas compatibles de
`catalogs/external.py` en lugar de añadir otro instalador independiente.

- [x] Añadir fuente GitHub identificada por revisión e integridad verificables;
  revisar descarga/contenido antes de instalación, sin ejecutar hooks/dependencias.
- [x] Diseñar instalación global con selección/activación por proyecto, precedencia
  explícita y un solo comando visible. La memoria permanece local por proyecto.
- [x] Actualizar con comparación de contenido, rollback e integridad de paquetes;
  conservar personalizados y originales. No reactivar automáticamente una skill.
- [x] Probar origen cambiado, archivos extra, enlaces, actualización interrumpida,
  colisión global/local, referencias caducadas y límites de contexto.
- [x] Acreditar qué skills son datos compatibles y cuáles requieren herramientas
  externas; la instalación no certifica ejecución ni concede permisos adicionales.

`/aikya-uninstall-skills` conserva su [plan específico](2026-10-29-uninstall-skills.es.md)
pendiente. Su diseño parte de Claude/7.x y requiere adaptación a Pi. Se mantiene
separado de las horas anteriores: añadirlo eleva el catálogo a 29. Estimación
preliminar adicional de adaptación/retirada/restauración: 12–24 h antes de reserva.
No se autoriza eliminar ninguna skill actual al redactar este plan.

## D. Entrada única, instalación y migración del runtime

**Modificar:** `cli/main.py`, `cli/terminal.py`, `installation/bootstrap/`,
`installation/migration_v8.py`, Pi `launcher.ts`, `session.ts`, empaquetado y CI.

- [x] Hacer que `aikya` abra el runtime administrado y conserve ayuda/subcomandos;
  reservar `--runtime-dir` para desarrollo. Evitar ejecutables duplicados en PATH.
- [ ] Empaquetar Python/Node/recursos necesarios con versiones e integridad
  verificables; instalación por comando corto sin clonar el repositorio.
- [ ] Completar instalación, update, rollback y uninstall para macOS/Linux/Windows;
  preservar código, memoria, configuración y datos personales.
- [ ] Separar stable y prerelease; resolver actualizaciones deterministas y conservar
  la instalación activa ante descarga corrupta, interrupción o fallo de activación.
- [ ] Migrar instalación/runtime 7.x por proyecto, con preview, respaldo e identidad
  de sesiones; completar lo que la migración de perfiles ya existente no cubre.
- [ ] Probar espacios/Unicode, permisos, proxy, ruta larga, runtime ausente,
  falta de terminal interactiva y binarios bloqueados durante actualización Windows.

Cierre: instalación limpia → `aikya` → sesión → update → rollback → uninstall,
con datos conservados, en los sistemas de destino. CI se amplía en cada entrega;
configurar un job no acredita que haya pasado.

[Subplan de distribución D](2026-11-09-pi-managed-distribution.es.md), preparado
durante C y en ejecución: D1 implementado; builder/ciclo/migración en aceptación.
El primer ensayo real detectó y corrigió la ruta temporal de macOS; batería completa
y recorridos nativos siguen pendientes. No se publican artefactos estables.

## E. Aceptación integrada de memoria, HTML y themes

**Reutilizar:** `code_index/`, `context/`, `memory/viewer/`,
`services/maintenance.py` y Pi `memory-lifecycle.ts`, `theme.ts`.

- [ ] Sobre el producto instalado: crear, editar, renombrar y borrar clases/archivos,
  incluidos cambios externos; comprobar índice, consultas y HTML vigentes.
- [ ] Conservar notas/evidencia y aislamiento entre proyectos al reiniciar,
  compactar, actualizar, migrar y restaurar. Comprobar caché obsoleta y corrupción.
- [ ] Derivar cobertura del catálogo real de parsers/extensiones y señalar
  inventario/fallback; cobertura del índice no implica un generador/build disponible.
- [ ] Validar temas claro/oscuro, preview/cancelación, persistencia, configuración
  inválida y legibilidad. La preferencia de terminal y HTML es explícita por vista.
- [ ] Comprobar cero inferencia en mantenimiento/render/consulta administrativa y
  conservar cambios personalizados del usuario.

Cierre: memoria y preferencias siguen siendo coherentes tras el recorrido D; no
se introduce Engram global ni un segundo almacén para estas funciones.

## F. Proveedores reales, tokens y sesiones largas

**Modificar según evidencia:** Pi `runtime.ts`, `budgeted-inference.ts`, `usage.ts`,
`usage-view.ts`, `session.ts` y servicios de contabilidad existentes.

- [ ] En el entorno real indicado por el usuario: fijar proveedor/modelo, esfuerzo,
  presupuesto y condiciones de caché; probar autenticación sin importar credenciales
  de otros clientes. Incluir el consumo de revisión y compactación.
- [ ] Medir entrada/salida/caché, llamadas y fase/rol/modelo; comprobar una sola
  contabilización, agotamiento, cancelación, uso desconocido y continuidad larga.
- [ ] Validar selección de modelo desde la experiencia instalada, compactación
  acotada y reanudación sin restaurar permisos o presupuesto anteriores.
- [ ] Mostrar ventanas 5 horas/semanal, reinicio, fuente y antigüedad solo cuando
  el proveedor las aporte; conservar último dato marcado como antiguo ante fallo.
- [ ] Comparar tres repeticiones de tareas equivalentes con 7.2.2 y, en proyectos
  separados, Gentle Shell 4.7.0 fijado en la investigación. Registrar modelo,
  esfuerzo, caché, permisos y métricas ausentes; informar ahorro solo si se mide.

Una llamada iniciada puede superar el saldo antes de informar su uso: el control
local no se presenta como límite duro del proveedor. La aceptación real sucede
en el otro entorno acordado; el resto del trabajo local puede avanzar mientras tanto.

## G. Matriz nativa y pruebas adversarias finales

Verificar especialmente .NET/TRX con `bin`/`obj`: por lectura de código, esos nombres
no figuran en las exclusiones compartidas del índice/candidato y una ejecución puede
cambiar el inventario. Reproducir con runner real antes de corregir. Conservar código
fuente relevante/tracked aunque viva en directorios con nombres habituales de build;
no introducir una exclusión ciega que permita esconder cambios de comportamiento.

**Ampliar:** pruebas Pi/host, `tests/test_review_*.py`, fixtures de lenguajes y
`.github/workflows/pi-runtime.yml`, además de pruebas de distribución.

- [ ] Derivar comandos de `cli/commands.py`, extensiones del catálogo del índice
  y runners del perfil; evitar una segunda lista manual de capacidades.
- [ ] Cruzar nuevo/existente, ODD/SDD, desarrollo/infraestructura/DevOps, en/es,
  instalación global/local y macOS/Windows/Linux para los casos aplicables.
- [ ] Ejecutar builds/tests/validadores pertinentes por ecosistema admitido;
  registrar ejecutado, fallido, no disponible o no aplicable con motivo.
- [ ] Atacar límites, informes vacíos/truncados, cero tests, cancelación,
  descendientes, permisos, fuentes cambiadas, duplicados y pérdida de conexión.
- [ ] Repetir memoria/themes/uso en la instalación administrada de cada sistema.
  Los fixtures de otro sistema no sustituyen su aceptación nativa.

Cierre: informes trazables por requisito/comando/entorno; sin fallos críticos
pendientes ni capacidades declaradas a partir de mera presencia de una herramienta.

## H. Preparación y publicación v8.0.0

- [ ] Consolidar README inglés/español, changelog, guía de instalación, migración,
  recuperación y limitaciones; actualizar matriz y documentación real.
- [ ] Preparar artefactos/manifest/hash y comprobar actualización entre versiones,
  canal de distribución y restauración de datos.
- [ ] Alpha → beta → RC → v8.0.0 según resultados de A–G; conservar el canal estable
  existente hasta completar la aceptación y preparación de la nueva versión.
- [ ] Hacer el recorrido de usuario final sin checkout de desarrollo ni clientes
  Claude Code/Codex obligatorios; registrar evidencia antes de declarar el producto listo.

## Revisión transversal de cinco condiciones

| Condición | Prueba y entrega responsable |
| --- | --- |
| Versión cambiante o helper modificado dentro del proyecto | A1: fijar identidad de generador y usar módulos del paquete; no ejecutar el helper local por nombre. |
| Interrupción, efecto parcial o edición concurrente | A1/B/C/D: reserva previa, lectura posterior, estado incierto conservado y recuperación explícita. |
| Cambio de sesión/modelo/compactación | B/F: no compartir permisos ni reiniciar presupuesto; mantener autor/revisor y uso observado separados. |
| Instalación/actualización sobre personalizaciones | C/D/E: comparar propietarios/hashes, preservar datos, duplicados visibles y rollback comprobable. |
| Falta de SDK, parser, cuota o proceso de pruebas válido | A2/E/F/G: estado desconocido/no disponible explícito; no inventar éxito, símbolos, porcentajes o contadores. |

## Método de ejecución y límites de alcance

Cada entrega se divide en tareas independientes: prueba Red observada → cambio
mínimo → Green → integración pertinente → informe y commit. Para Python ejecutar
la batería del proyecto en un entorno temporal limpio; para Pi ejecutar `npm test`
y `npm run typecheck`. Registrar omisiones/fallos y distinguir pruebas locales,
paquete instalado, terminal, CI remota y proveedor real. Los documentos y el índice
se validan con `python -m aikya.documentation.guard base` y el guard del diff.

Este plan mantiene la ejecución secuencial ya utilizada. El subplan A1 debe concretar
los esquemas JSON, recetas y tests antes de tocar código. Una entrada en el menú o
un prompt genérico no cierra un comando. Cada capacidad se marca al observarla y
sus límites permanecen en la matriz hasta completar la aceptación correspondiente.

Las adaptaciones Gentle conservan los comportamientos acordados de memoria,
previsualización/persistencia de temas y panel/presupuestos de uso. La trazabilidad
Gentle → requisito Aikya → prueba → resultado se completa en E/F/G. La referencia
fijada sigue en [la investigación](2026-11-07-aikya-multi-host.es.md).

Adaptadores nativos de clientes Claude Code/Codex u otros hosts, MCP optativo,
RDD de cuatro lentes, voz/música y una TUI propia quedan fuera de estas horas.
Usar modelos de sus proveedores dentro de Pi mantiene un alcance distinto de
integrar los clientes CLI/apps. Este documento actualiza planificación; no ejecuta
instalaciones, no cambia versiones ni publica una release.

GENERATED BY AIKYA HARNESS

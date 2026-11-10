# Plan Aikya v8.0.0: base Aikya y reconstrucción sobre Pi

Fecha: 7 de noviembre de 2026. Estado: propuesta; no implementada.

**Objetivo:** definir Aikya v8.0.0 tomando Aikya como base funcional y evaluando
Pi como runtime principal, incluida una reescritura completa si resulta necesaria.
Entregar un producto instalable y utilizable desde terminal en macOS, Windows y
Linux, con una experiencia similar a Gentle Shell. Mantener ODD/SDD, añadir TDD y
RDD (Receipt Driven Development), memoria local y documentación auditable.
**Arquitectura recomendada:** reconstrucción controlada del runtime sobre Pi,
reutilizando servicios Aikya mediante contratos acotados cuando superen las pruebas.
Los adaptadores de clientes y el backend que ejecuta modelos son alcances distintos.
**Tecnología candidata:** TypeScript/Pi para el runtime; Python, SQLite y Markdown
actuales donde aporten valor. Fijar versiones y resolver el diseño mediante prototipo.
**Base:** `origin/develop` en `e7415238cbafa24f285d2fb3a006333d37be7ee6`,
árbol equivalente a la release 7.2.2.
**Especificación de referencia:** [investigación comparativa](../research/2026-11-07-gentle-shell-4.7.0-vs-aikya.es.md).
**Ampliación de alcance:** [terminal multiplataforma, TDD y RDD](2026-11-07-aikya-v8-terminal-tdd-rdd.es.md).

## Restricciones globales

- Todos los planes, bugs, features y evidencias permanecen en `aikya/docs/`.
- Memoria e índice por proyecto; ningún almacén global compartido por defecto.
- Mantener `odd` y `sdd`; conservar aprobaciones y migraciones existentes.
- Aplicar TDD a nuevos comportamientos y correcciones; integrar RDD como control
  de candidato, recibos y revisión. RDD significa Receipt Driven Development.
- No crear worktrees por una petición de cambio o de rama.
- No instalar skills externas, activar otros modelos, copiar credenciales o cambiar
  permisos del usuario como consecuencia de instalar un adaptador.
- La política común no sustituye controles nativos ausentes: informar capacidad
  limitada, nunca inventar que un hook se ejecutó.
- Ningún módulo nuevo supera 1.000 líneas. Los estimados no son autorización de
  implementación, despliegue o gasto de inferencia.
- Cada cambio de comportamiento comienza con una prueba que falle por la causa
  prevista; sigue Green y Refactor, y termina con evidencia aplicable al candidato.
  Consultas y cambios solo documentales usan comprobaciones proporcionales.

## Casos que deben fijar el diseño

1. Instalar global y después proyecto no duplica comandos; una personalización no
   se borra para conseguir ese resultado.
2. Dos clientes en el mismo proyecto no mezclan sesiones, permisos, presupuestos
   ni evidencia de una revisión anterior.
3. Un cliente sin hooks o una versión desconocida no aparece como integración completa.
4. Cambiar modelo, reiniciar o compactar no renueva una autorización ni borra el uso.
5. Un fallo de memoria, parser o MCP no dispara una lectura completa o una llamada
   a un modelo sin límites; los datos no disponibles siguen siendo desconocidos.

## Decisión de alcance: Aikya v8.0.0

La versión objetivo de esta evolución será **v8.0.0**. El producto toma Aikya como
base funcional: metodología, comandos, memoria local, seguridad, documentación y
migraciones. El código puede cambiar sustancialmente si la prueba de viabilidad
lo justifica. Esta ampliación del plan no es una implementación ni una release;
`VERSION` permanece en 7.2.2 hasta comenzar la entrega de software de la nueva rama.

El objetivo principal es abrir `aikya` en una terminal y trabajar con sesiones,
modelos, herramientas y flujos propios en los tres sistemas. Los adaptadores para
Claude Code o Codex quedan como compatibilidad adicional; no son la experiencia
principal que define esta entrega. Se incorpora **Pi como candidato a runtime
principal**, con una reconstrucción controlada recomendada.
Empezar desde cero queda como alternativa explícita, no
como supuesto de que el código actual sea inutilizable. No se recomienda bifurcar
Pi ni copiar la implementación completa de Gentle Shell para la primera versión.

### Alternativas comparables

Las cifras cubren alcances diferentes. La ruta A prioriza adaptadores para clientes
existentes; B prioriza un runtime Pi nativo; C reemplaza además servicios actuales.
No sumarlas ni interpretar B como si incluyera todos los adaptadores nativos de A.
La ruta A por sí sola no satisface el nuevo objetivo de terminal autónoma.
Las cifras siguientes incluyen el núcleo RDD; B y C incluyen también el launcher
de producto. TDD ya formaba parte de las pruebas previstas y no se suma dos veces.

| Ruta | Qué se construye | Qué se conserva | Estimación antes de reserva | Riesgo |
|---|---|---|---:|---|
| A. Evolución del núcleo Python | Adaptadores Claude/Codex y RDD sobre la arquitectura actual; alternativa transitoria. | Casi todo el núcleo y sus flujos. | 140–228 h | Menor cambio; sigue dependiendo de clientes externos y no entrega la terminal autónoma. |
| B. Reconstrucción controlada sobre Pi — recomendada si pasa el prototipo | Terminal Aikya sobre Pi, contrato acotado con servicios actuales, RDD y migración versionada. | Políticas, ODD/SDD, catálogo, documentación, parsers, memoria y pruebas reutilizables tras verificarlos. | 224–360 h | Medio/alto: dos lenguajes, empaquetado y nueva superficie de ejecución. |
| C. Reescritura completa sobre Pi | Terminal, runtime, RDD y servicios de dominio nuevos; migración mediante contratos y aceptación. | Requisitos de Aikya, formatos que se decida mantener y fixtures de compatibilidad. | 360–584 h | Alto: mayor posibilidad de regresiones y pérdida de comportamiento implícito. |

Para B, una reserva del 25 % da **280–450 horas**, aproximadamente **7–12 semanas**
de una persona a 40 horas semanales. Para C, 450–730 horas con reserva,
aproximadamente 12–19 semanas redondeando a semanas completas. Son estimaciones
nuevas de alcance, no resultados de implementación ni precios contratados.
Desglose B: B0–B5 = 160–256 h; controlador RDD R1–R3 = 48–80 h;
launcher T1 = 16–24 h. Las tareas de la ampliación se integran en B1–B5 y sus horas
se suman una vez. Revisar la estimación al terminar el prototipo.

La reescritura completa se elige solo después de identificar qué contratos no
puede cumplir la reutilización y comparar el coste de adaptarlos con reemplazarlos.
No se borra la rama 7.x, no se elimina código primero para justificar reconstruirlo
y no se usa el número de archivos como criterio para decidir.

### Arquitectura objetivo de la ruta B

**Pi se ocupa de:** ciclo de agente, interfaz terminal existente, sesiones y
comunicación con sus proveedores de modelos. Aikya controla el flujo del producto,
los permisos anunciados, su evidencia y sus datos locales. Cada responsabilidad
se prueba en su límite; adoptar Pi no activa por sí solo las políticas de Aikya.

**Aikya conserva como servicios candidatos a reutilización:**

- ODD y SDD, selección inicial y aprobaciones por etapa.
- Índice de código, recuperación acotada, políticas y notas por proyecto.
- Generación determinista del HTML Memory y actualización local sin inferencia.
- Documentación dentro de `aikya/docs/`, índice y footer de documentos generados.
- Catálogo de skills/especialistas, validadores y checks de ingeniería.
- Protección de archivos del usuario, manifiestos de propiedad y migraciones.

La reutilización no implica copiar todos los imports del paquete a la extensión.
Primero se identifican dependencias de Claude/SDK y se extraen contratos pequeños.
El worker actual de Claude Agent SDK no se convierte automáticamente en worker Pi.

**Estructura propuesta, todavía inexistente:**

```text
packages/aikya-pi/
  package.json                 # paquete y versión Pi fijados
  src/
    extension.ts               # registro de la extensión
    session.ts                 # identidad, eventos y reanudación
    workflow.ts                # puente de recetas ODD/SDD
    review.ts                  # adaptación al controlador RDD propuesto
    tools.ts                   # herramientas con entradas/salidas acotadas
    permissions.ts             # autorización antes de efectos
    usage.ts                   # uso observado y presupuestos
    bridge.ts                  # proceso Python, sin shell genérico
src/aikya/
  services/bridge.py           # frontera de operaciones locales permitidas
  workflows/                  # ODD/SDD candidatos a reutilizar
  review/                     # candidatos, recibos y decisiones RDD propuestos
  code_index/                 # índice local existente
  context/                    # contexto acotado existente
  memory/                     # notas y HTML existentes
  documentation/              # generación y validación existentes
  hosts/                      # compatibilidad con clientes, si se aprueba
  installation/               # instalación/migración del producto
```

El puente propuesto usa mensajes JSON versionados, con ID de petición, identidad
canónica de proyecto, operación permitida y límites de salida/tiempo. No acepta
un nombre arbitrario de módulo ni un comando de shell enviado por el modelo.
La extensión llama procesos con argumentos separados y valida sus respuestas.
Los servicios vuelven a validar alcance y propiedad: la validación de TypeScript
no es autorización suficiente para escribir desde Python.

La memoria y estado de proyecto quedan ligados al proyecto; las sesiones de Pi
se configuran mediante su API soportada y se comprueba la ubicación real. No se
presupone que su configuración predeterminada satisfaga este requisito. Engram,
un servidor global y un vector store no son dependencias obligatorias de v8.

### Pi, modelos y compatibilidad con los clientes actuales

La primera ruta B produce **Aikya ejecutándose sobre Pi**. Podrá usar proveedores
y modelos que admita la versión fijada y la cuenta configurada por el usuario.
El plan no promete acceso a una suscripción ni una reducción de cuota.

Usar un modelo OpenAI dentro de Pi no equivale a abrir Codex CLI o la app Codex;
usar Anthropic dentro de Pi tampoco ejecuta Claude Code. Los adaptadores para esos
clientes son otro alcance: las fases de la ruta A se conservan más abajo para
planificarlos, pero no se incluyen completos en las 224–360 horas de B ampliada.

Para usuarios 7.x se mantiene una ruta de continuidad explícita durante la
transición. La elección de runtime se registra por proyecto y no se cargan los
dos orquestadores simultáneamente. La conversión de los 28 comandos se valida por
ID/semántica en Pi; la sintaxis y disponibilidad de cada invocación se confirman
en el prototipo antes de prometer equivalencia al menú de Claude.

### B0. Prototipo y decisión de arquitectura — 16–24 h

**Entregables:** contrato en `aikya/docs/architecture/`, prototipo temporal de
`packages/aikya-pi` y fixtures de aceptación. Pi 1.4.0, inspeccionado en la
investigación, es la referencia inicial; no una promesa de compatibilidad con
todas las versiones. Fijar la versión que realmente pase las pruebas, lockfile,
Node soportado y procedencia de las dependencias.

- [ ] Registrar un comando y una herramienta Pi que consulte estado Aikya local
      mediante el puente sin un modelo; capturar errores y límites de respuesta.
- [ ] Verificar sesión por proyecto, cancelación, reanudación y procedencia de eventos.
- [ ] Verificar que el control de herramientas bloquea un efecto no autorizado,
      también ante error del handler, y que no hay una ruta alternativa sin guardas.
- [ ] Probar una tarea con cada proveedor elegido, con credenciales del usuario
      gestionadas por el runtime y presupuesto de inferencia definido previamente.
      Sin esa evidencia solo se declara viabilidad técnica parcial.
- [ ] Resolver si la interfaz terminal de Pi y su extensión bastan o hace falta
      un launcher con el SDK; no construir una TUI propia en este prototipo.
- [ ] Validar el recorrido de terminal T1 y el contrato de candidato/recibos RDD
      de la ampliación; conservar un único propietario del ejecutable `aikya`.
- [ ] Emitir una decisión documentada: continuar B, volver a A o justificar C con
      los contratos que no se pudieron conservar y su coste de reemplazo.

**Criterio de salida:** evidencia de capacidades, lista de brechas y arquitectura
seleccionada. Las pruebas de Gentle Shell de la investigación no son pruebas de
una implementación Aikya-Pi que aún no existe.

### B1. Frontera del núcleo y contratos de datos — 24–40 h

**Archivos propuestos:** `src/aikya/services/bridge.py`,
`packages/aikya-pi/src/bridge.ts`, `tests/test_service_bridge.py` y
`packages/aikya-pi/tests/bridge.test.ts`.

- [ ] Fijar el esquema de peticiones/respuestas y las operaciones permitidas;
      probar versión desconocida, proyecto equivocado, escape de ruta, mensajes
      grandes, timeout y proceso hijo que termina sin respuesta completa.
- [ ] Exponer primero lectura de estado/contexto. Las operaciones de escritura
      requieren autorización ligada al proyecto, operación y revisión de fuente.
- [ ] Separar imports del SDK Claude; no introducir un requisito Anthropic en
      indexación, documentación, memoria o consultas locales.
- [ ] Reutilizar o reemplazar cada servicio mediante pruebas de contrato antes
      de conectarlo al runtime nuevo.
- [ ] Incorporar los contratos RDD de R1 al puente; los prompts y la salida del
      modelo no pueden asignarse por sí solos una decisión de aceptación.

### B2. Runtime Pi y permisos de Aikya — 40–64 h

**Archivos:** módulos TypeScript propuestos `extension`, `session`, `tools`,
`permissions`, `usage`; pruebas de extensiones y de ciclo de sesión.

- [ ] Incorporar comandos/skills Aikya con carga mínima y sin registrar copias
      repetidas por paquete, scope o reanudación.
- [ ] Mapear permisos, cancelación, errores, reintentos y eventos a la política
      común. Las extensiones Pi comparten privilegios del proceso: un hook no
      constituye por sí solo un sandbox del sistema operativo.
- [ ] Restringir herramientas iniciales; exigir petición explícita de worktree,
      conservar archivos del usuario y evitar escapes por procesos/herramientas anidadas.
- [ ] Registrar uso por llamada/rol/modelo/proyecto cuando esté disponible;
      desconocido no es cero. No reiniciar presupuesto al compactar o reanudar.
- [ ] Mantener permisos deterministas por defecto; no activar un clasificador
      por modelo ni revisiones múltiples por instalar Pi.
- [ ] Conectar T1 y R2: terminal, cancelación, recibos de ejecución y bloqueo de
      cierre ante evidencia ausente, obsoleta o de otra sesión/candidato.

### B3. Paridad de workflows y catálogo — 24–40 h

**Archivos:** `packages/aikya-pi/src/workflow.ts`, catálogo común y fixtures de
los 28 comandos. Reutilizar los motores ODD/SDD Python que superen B1.

- [ ] Probar nuevos/existentes y desarrollo/infraestructura/DevOps, ambos idiomas
      y ambos modos; conservar rutas, aprobaciones y documentos con datos reales.
- [ ] Cubrir todos los comandos: ejecutado, rechazado con causa o pendiente visible;
      no declarar completa una función solo porque aparece en un menú.
- [ ] Separar orientación para el modelo y transición determinista. Las pruebas
      de texto no sustituyen pruebas de ejecución de los flujos.
- [ ] Mantener seguimiento y revisión proporcionales; skills externas elegidas
      por el usuario y especialistas seleccionados por necesidad.
- [ ] Aplicar la matriz TDD/RDD de la ampliación a los 28 comandos, ambos modos y
      todos los lenguajes inventariados; distinguir parser de runner ejecutable.

### B4. Memoria, HTML y migración 7.x → 8 — 24–40 h

**Archivos:** servicios locales actuales de índice/memoria, adaptador de eventos Pi,
fixtures de migración y manual bajo `aikya/docs/`.

- [ ] Probar creación/edición/renombrado/borrado de clases y archivos: índice y HTML
      se actualizan sin consulta a modelos y sin releer el repositorio completo.
- [ ] Probar que proyectos y sesiones no comparten notas, datos o autorizaciones.
- [ ] Inventariar rutas/formatos 7.x y diseñar preview, respaldo y migración con
      versión de esquema; preservar personalizaciones y evidencia existente.
- [ ] No abrir datos migrados con el binario 7.x si perdió compatibilidad. El
      rollback selecciona el runtime previo y restaura una copia compatible,
      sin borrar cambios posteriores ni degradar el almacén en sitio.
- [ ] Resolver comandos locales antiguos mediante conciliación del proyecto
      seleccionado. No repetir el supuesto de que una actualización global
      elimina copias ya existentes en todos los proyectos.

### B5. Instalación, pruebas y publicación v8.0.0 — 32–48 h

- [ ] Crear una instalación corta con versiones e integridad verificables de
      Aikya, Pi, Node y Python cuando sean necesarios; sin clonar el repositorio,
      modificar runtimes del usuario o copiar credenciales entre perfiles.
- [ ] Probar instalación, actualización, desinstalación y recuperación en Windows,
      macOS y Linux. Publicar límites de plataforma y versión observados.
- [ ] Ejecutar regresiones de servicios reutilizados, runtime Pi, migración,
      ODD/SDD, idiomas, parsers, permisos y fallo/cancelación de herramientas.
- [ ] Ejecutar tareas reales comparables con 7.2.2 y medir aceptación, llamadas,
      tokens disponibles, cache y tiempo. Definir presupuesto y repeticiones;
      Pi no garantiza ahorro automáticamente.
- [ ] Ampliar primero los contratos de versión/build/update para prereleases: el
      recorrido estable no debe seleccionar alpha/beta/RC ni abrir su estado por
      accidente. Cubrir selección, integridad y rollback con fixtures.
- [ ] Preparar `8.0.0-alpha`, beta/RC y finalmente v8.0.0. Actualizar `VERSION`,
      manifiestos, changelog, README y artefactos al entregar esa implementación,
      no al guardar esta propuesta.
- [ ] Publicar matriz de funciones conservadas, cambiadas y pendientes, guía de
      migración y compatibilidad 7.x. No sustituir la versión estable antes de
      superar las pruebas de salida.
- [ ] Superar R3 y T1 en sistemas nativos: instalación limpia → `aikya` → tarea
      con TDD → revisión RDD → reanudación → actualización/desinstalación.

### Condiciones para recomendar una reescritura completa (ruta C)

B0 debe demostrar una razón concreta: acoplamiento no separable, imposibilidad de
mantener un contrato crítico o coste de adaptación superior al reemplazo probado.
Si se selecciona C, se prepara un mapa de reemplazo por servicio y se conserva
un recorrido vertical verificable desde el principio. El diseño no hereda todos
los detalles internos, pero sí las obligaciones de producto y migración de Aikya.

La base de 296–480 horas incluye reconstruir servicios, reproducir comportamientos
y recuperar compatibilidad. Con RDD y launcher pasa a 360–584 horas; no es
«sumar unas semanas» a B sin revisar el alcance.
Si B0 no justifica sustituir el índice, HTML o documentación, esos servicios se
reutilizan. La decisión y el coste restante se revisan antes de seguir.

### Fuentes y límites de viabilidad Pi

La documentación oficial describe el SDK y las extensiones:
[SDK](https://github.com/earendil-works/pi/blob/main/packages/coding-agent/docs/sdk.md),
[extensiones](https://github.com/earendil-works/pi/blob/main/packages/coding-agent/docs/extensions.md).
La investigación inspeccionó además el paquete Pi 1.4.0 instalado. `main` puede
cambiar: la implementación deberá fijar y verificar sus APIs reales. Esta revisión
establece que existe una vía de integración; no valida todavía Aikya 8, su
seguridad, sus migraciones ni su consumo de modelos.

## Ruta A conservada como alternativa: adaptación del núcleo actual

Las fases siguientes son el plan previo de adaptadores Claude/Codex. Se conservan
para la decisión de B0 o una compatibilidad adicional aprobada. Su estimación
base de 92–148 h excluye el controlador RDD y no es la del runtime Pi v8.0.0.
Con RDD pasa a 140–228 h; no se suma automáticamente a la ruta B.


### A0 — Contratos y matriz de capacidades (12–20 horas)

**Archivos propuestos:** crear `src/aikya/hosts/contracts.py`, `registry.py`,
`tests/test_host_capabilities.py` y un contrato en `aikya/docs/architecture/`.

**Interfaz propuesta, todavía inexistente:**
`HostCapabilities` identifica `host_id`, versión observada, soporte de skills,
instrucciones, eventos, herramientas, MCP, uso y compactación. `inspect_host(host_id)`
solo hace sondeos locales acotados; no autentica ni inicia sesiones con modelos.
La versión observada no prueba acceso a un modelo ni a una suscripción.

- [ ] Fijar en pruebas capacidades conocidas, cliente ausente, versión no
      interpretable y sondeo con timeout; desconocido no equivale a soportado.
- [ ] Documentar Claude/Codex por separado y distinguir host, proveedor del modelo
      y backend opcional del loop.
- [ ] Establecer el contrato de eventos: proyecto, host, sesión, tarea, fase,
      procedencia y disponibilidad de uso. Un evento observado no acredita una acción.
- [ ] Probar identidad de proyecto/sesión entre dos hosts y rechazo de datos de otro origen.
- [ ] Revisar la matriz y confirmar los mínimos de versión con documentación oficial
      y pruebas del cliente instalado, sin introducir mínimos inventados.

**Salida aceptable:** matriz reproducible y límites explícitos; ningún cambio del
comportamiento Claude ni modificación de configuración personal.

### A1 — Catálogo único e instalación por host (24–40 horas)

**Archivos:** crear `src/aikya/hosts/catalog.py`, `rendering.py` y
`tests/test_host_installation.py`; modificar
`src/aikya/installation/registration.py`, `command_scopes.py` y los recursos
estrictamente necesarios. No convertir esas dos piezas existentes en otro monolito.

**Interfaz propuesta:** `render_skill(skill_id, host_id, capabilities) -> bytes`
y `plan_host_install(root, scope, host_id) -> list[ManagedOperation]`.
El plan es de solo lectura y conserva huellas de origen/propiedad, conflictos,
respaldo y retirada. Reutilizar la infraestructura existente de manifiestos.

- [ ] Probar un mismo ID en scopes global/proyecto, actualización de un archivo
      administrado y conservación de ediciones, archivos extra, enlaces y respaldos
      conflictivos. No crear otra copia si se puede reutilizar una válida.
- [ ] Clasificar los 28 comandos, 29 skills técnicas y ocho workflows base sin
      presentarlos como 65 capacidades independientes ni duplicar instrucciones.
- [ ] Renderizar solo frontmatter admitido por el host; no portar `allowed-tools`,
      contextos o hooks de Claude como si concedieran permisos en Codex.
- [ ] Generar instrucciones Claude/AGENTS mediante bloques administrados y fusiones
      conservadoras; preservar contenido del usuario y precedencia nativa.
- [ ] Proponer un selector explícito de host en el instalador. Cualquier opción
      como `--host codex` es futura; aún no existe en Aikya 7.2.2.
- [ ] Probar preview sin escrituras, rollback de archivos administrados y desinstalación
      por propietario. Mantener aparte el plan previo de uninstall-skills.

**Salida:** instalar/actualizar/restaurar archivos de los dos hosts sin duplicación
ni cambios de modelos, credenciales o políticas privadas.

### A2 — Adaptador Codex y paridad Claude (32–48 horas)

**Archivos:** crear `src/aikya/hosts/codex.py`, `claude.py`,
`tests/test_codex_host.py`, `tests/test_host_event_identity.py` y recursos nativos
por host. Reutilizar `middleware/commands.py`, `core/state.py`, políticas y CLI
existentes; no duplicar el motor ODD/SDD.

**Interfaces propuestas:** `plan_host_install` produce los archivos; cada adaptador
normaliza eventos disponibles al contrato de la fase 0. La configuración de skills,
MCP y hooks usa el formato/documentación de la versión efectivamente soportada.

- [ ] Probar descubrimiento de instrucciones y skills del host real en un hogar
      temporal; no considerar `--version` o parsear TOML prueba suficiente.
- [ ] Completar las recetas de consulta, onboarding ODD/SDD, feature, pruebas,
      revisión y memoria con la invocación nativa que realmente admita Codex.
      No prometer el mismo slash-command que Claude.
- [ ] Probar checkpoints, reanudación, compaction si el host la ofrece y dos sesiones
      concurrentes sobre el mismo proyecto, sin reutilizar aprobaciones ajenas.
- [ ] Probar edición ordinaria/creación de rama y creación explícita de worktree.
      Un host que no expone el evento necesario informa el límite y mantiene su
      control nativo; no se intenta eludirlo por otro proceso.
- [ ] Ejecutar una pequeña tarea real con cada host tras asignar modelo y presupuesto,
      comparar diff, evidencia y documentos. Los fixtures sin modelo no sustituyen
      esta aceptación. Si falta acceso, dejar la integración experimental.
- [ ] Ejecutar la regresión completa de Aikya y la matriz de instalación nativa.

**Salida:** Claude conserva su comportamiento; Codex tiene un nivel de soporte
publicado y verificable. Esta fase no crea un loop universal que lance cualquier
asistente desde Python: ese backend sería otro proyecto.

### A3 — Memoria portable mediante MCP, optativa (24–40 horas)

**Archivos:** crear `src/aikya/mcp/server.py`, `contracts.py`,
`tests/test_memory_mcp.py`, `tests/test_memory_host_isolation.py` y documentación
bajo `aikya/docs/architecture/`. Evaluar primero si las herramientas MCP del host
son la opción adecuada; no añadir un segundo gestor MCP propio.

**Interfaz propuesta:** operaciones iniciales de estado, búsqueda y contexto
acotado que consuman `code_index/`, `context/` y `memory/` existentes. La primera
versión es de lectura; no permite aprobar notas o ejecutar comandos remotos.

- [ ] Probar proyecto errado, escapes/enlaces, fuente modificada tras indexación,
      límite de salida, cancelación y servidor ausente.
- [ ] Probar que la misma consulta autorizada desde dos hosts accede al mismo
      proyecto y que otro proyecto queda fuera del alcance.
- [ ] Mantener notas/HTML en sus rutas actuales. Ni indexar ni actualizar el HTML
      requiere llamadas a modelos.
- [ ] Mantener fallback explícito y acotado cuando no hay parser o índice.
- [ ] Documentar que un puente Engram futuro sería optativo y no migra el almacén
      del usuario ni convierte memoria global en comportamiento por defecto.

**Salida:** memoria Aikya accesible con un protocolo estándar, sin almacenamiento
remoto ni dos índices autoritativos del mismo código.

### A4 — Medición, revisión proporcional y entrega del MVP (24–40 horas)

**Archivos:** extender `src/aikya/routing/policy.py`,
`src/aikya/middleware/metrics.py`, `middleware/usage.py` y
`quality/efficiency.py`; crear `tests/test_host_usage_accounting.py` y fixtures de
aceptación multihost. Reutilizar sus almacenes y contratos actuales; no crear otro recibo de uso
autoritativo para cada host.

- [ ] Probar uso desconocido, cache, eventos repetidos, interrupción y cambio de
      modelo; un replay no suma dos veces ni restaura el presupuesto consumido.
- [ ] Resolver perfiles por rol/fase con procedencia y elección del usuario. No
      decidir acceso efectivo por el nombre comercial del modelo.
- [ ] Aplicar checks/revisión según riesgo sin delegar por cantidad de líneas.
      No convertir cada tarea ODD en una revisión con cuatro modelos.
- [ ] Preparar benchmark de cambio pequeño, feature y corrección de seguridad;
      mismo modelo/versión/esfuerzo, tres repeticiones y estado de cache registrado.
      Medir llamadas, tokens disponibles, herramientas, tiempo y aceptación.
- [ ] Fijar antes el presupuesto total de inferencia. No hay ahorro porcentual
      ni coste monetario demostrado por los tests offline de esta investigación.
- [ ] Publicar matriz de capacidades, limitaciones, changelog/versionado de la
      implementación y manual de rollback; pasar instalación, update y migración
      desde proyectos previos con duplicados y personalizaciones.

**Salida:** MVP Claude + Codex con evidencia verificable y medición honesta.

### A5 — Ampliaciones posteriores

| Ampliación | Estimación | Condición para aprobarla |
|---|---:|---|
| Gemini CLI + OpenCode | 32–56 h | Contratos de las fases 0–2 estables y pruebas por host, sin declarar paridad uniforme. |
| RDD avanzado: cuatro lentes y escalado de revisión | 32–56 h | El núcleo RDD ya forma parte del alcance v8. Esta ampliación requiere un caso y presupuesto; no incluye interoperabilidad con la autoridad nativa de Gentle. |
| Ejecutor Pi acotado desde la ruta A | 24–48 h | Estimación previa de un complemento; no incluye la reconstrucción principal ni migración v8 de la ruta B. |
| TUI propia similar a Shell | 80–160 h | Proyecto de producto independiente; no es requisito para reducir tokens ni portar skills. |
| Mejoras al HTML/CLI existente | 16–32 h | Estados, perfiles y límites útiles al desarrollador; evitar replicar controles en tres interfaces. |

No son compromisos ni se suman automáticamente al MVP. Música, voz y persona de
Gentle no resuelven las prioridades actuales de compatibilidad y consumo.

## Tiempo y coste de la ruta A

Solo para la ruta A, base sin MCP: fases A0, A1, A2 y A4 = **92–148 horas**.
Con RDD R1–R3: **140–228 horas**. Con un 25 % de reserva: **175–285 horas**,
unas 5–8 semanas laborables a 40 horas semanales redondeando hacia arriba.
Esta alternativa mantiene clientes externos; no entrega la terminal autónoma.
La fase MCP añade 24–40 horas antes de reserva. Son estimaciones de ingeniería,
no un tiempo medido de implementación ni una oferta contractual.

Coste de desarrollo = horas acordadas × tarifa del equipo. No se presupone una
tarifa ni un coste de suscripción. Dependencias locales no son una tarifa de
memoria; usar un modelo sí puede consumir cuota o API según el proveedor.

Orden: contratos → catálogo/instalación → Codex + regresión Claude → medición y
aceptación → MCP si aporta valor → otros hosts. Una primera entrega puede conservar
la CLI de memoria actual en ambos hosts; no necesita esperar un servidor nuevo.

## Riesgos y criterios de parada

| Riesgo | Nivel | Respuesta |
|---|---|---|
| Dos orquestadores escriben documentos/controlan permisos | Alto | Un responsable por sesión; no activar Gentle y Aikya completos sobre la configuración personal como prueba. |
| Pérdida de skills o instrucciones del usuario | Alto | Preflight sin escrituras, hashes de propietario, respaldos, conflictos conservados y migración por proyecto. |
| Falsa equivalencia de seguridad entre hosts | Alto | Matriz de eventos/capacidades y pruebas de denegación; publicar degradación explícita. |
| Coste de revisión/Auto/delegación mayor que el ahorro | Medio/alto | Medición por llamada y rol; permisos deterministas y delegación proporcional por defecto. |
| Cambio de formato de cliente o SDK | Medio | Versiones observadas, fixtures nativos y CI; no depender del mismo frontmatter en todos. |
| Perder SDD o la memoria local | Alto | Contratos de conservación y pruebas de rutas; no migración implícita a ODD/Engram. |

Se detiene la activación de un adaptador si no puede conservar configuración,
identidad de proyecto o controles anunciados. La investigación ha producido el
plan; las futuras implementaciones requieren su revisión y autorización de alcance.

GENERATED BY AIKYA HARNESS

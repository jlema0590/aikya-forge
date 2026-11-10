# Gentle Shell 4.7.0 frente a Aikya Harness 7.2.2

Fecha de corte: 7 de noviembre de 2026. Investigación de código, documentación,
instalaciones temporales y pruebas locales en macOS arm64. Las valoraciones de
conveniencia son recomendaciones; las funciones existentes se identifican por
fuentes fijadas a versiones. El [informe de validación](../validation/2026-11-07-gentle-shell-comparison.es.md)
y su recibo JSON separan lo ejecutado de lo pendiente.

## 1. Conclusión

Gentle Shell es un entorno de trabajo interactivo sobre **Pi**. Su componente
**Gentle AI** aporta instalación y adaptación a otros asistentes. Aikya es un
harness de ingeniería orientado actualmente a **Claude Code**, con herramientas
Python locales, onboarding de proyectos, ODD/SDD, controles y documentación.
No son sustitutos equivalentes en todas las capas.

La ventaja principal de Gentle es el entorno interactivo, la orquestación,
la configuración por asistente y los perfiles de modelos. La ventaja práctica de
Aikya para este proyecto es mantener metodología elegible, documentación dentro
de `aikya/docs/`, catálogo técnico por stack y memoria/indexación por proyecto.

La recomendación inicial de esta comparación fue una evolución por adaptadores.
Después, el usuario amplió el objetivo a **Aikya v8.0.0**, admitiendo reconstruir
sobre Pi y reescribir servicios si es necesario. El
[plan actualizado](../plan/2026-11-07-aikya-multi-host.es.md) compara ambas rutas
con una reescritura completa y recomienda una reconstrucción controlada sobre Pi,
sujeta a un prototipo. Se conservan SDD, memoria local y contratos Aikya; Engram y
una TUI propia no son requisitos implícitos. Los resultados de esta investigación
siguen correspondiendo a 7.2.2 y Gentle Shell 4.7.0, no a una implementación v8.

## 2. Versiones y procedencia

| Elemento | Versión/identidad verificada | Observación |
|---|---|---|
| Gentle Shell, paquete npm `gentle-pi` | 4.7.0; commit `8e11f0e2fb19af2a28233d1774848f7a3a33bbf1` | Última release publicada consultada; no confundir nombre del producto y paquete. |
| Gentle AI incluido | 4.4.0; commit `55240afb100ad6d2ef5fbe16f7be33a7693f77ad` | Binario Go fijado por el instalador de Shell. |
| Pi del lockfile | 1.4.0 | El peer admite un rango más amplio; las pruebas usaron el lockfile, no ese rango abierto. |
| Engram fijado por Shell | 3.5.2 | Se descargó el artefacto macOS arm64 y se verificaron tamaño y SHA-256. |
| Aikya publicado | 7.2.2; tag/commit `0e411e5df559f0d57b67c5eabf8cd2fb1906c7aa` | Release publicada el 5 de noviembre. |
| Aikya `develop` | `e7415238cbafa24f285d2fb3a006333d37be7ee6` | Su árbol coincide con el de la release: `4c6d6ba04558bd8be441333b79c5e0759df773b1`. |
| Gentle Shell `main` consultado | `d17c6f98cc69ea9a7a5a359c79934ee9292f1fcf` | Tres commits posteriores a 4.7.0; no forman parte de la instalación probada. |

Fuentes: [release Shell](https://github.com/Gentleman-Programming/gentle-shell/releases/tag/v4.7.0),
[manifest Shell](https://github.com/Gentleman-Programming/gentle-shell/blob/v4.7.0/package.json),
[pin Gentle AI](https://github.com/Gentleman-Programming/gentle-shell/blob/v4.7.0/scripts/gentle-ai-installer.mjs),
[pins de distribución](https://github.com/Gentleman-Programming/gentle-shell/blob/v4.7.0/scripts/installer-downloads.mjs),
[release Aikya](https://github.com/jlema0590/aikya-harness/releases/tag/v7.2.2).

## 3. Comparación funcional

| Área | Gentle Shell 4.7.0 y componente Gentle AI 4.4.0 | Aikya 7.2.2 |
|---|---|---|
| Interfaz de trabajo | TUI Pi: cambios Git, agentes, tareas, comandos, perfiles y personalización. | Comandos en Claude Code, herramientas Python y visor HTML Memory; sin TUI propia equivalente. |
| Onboarding | Configura el ecosistema del asistente y sus componentes. | Entrevista y analiza proyectos nuevos/existentes de desarrollo, infraestructura y DevOps; elige idioma, stack y ODD/SDD. |
| Metodología cotidiana | ODD proporcional; trabajo pequeño entendido en línea y trabajo recuperable mediante documento cuando procede. | ODD con estado y tareas verificables; consultas/cambios pequeños no requieren un dossier de feature. |
| SDD | Gentle AI 4.x retiró el componente y las skills SDD. | Flujo explícito de especificación, aclaración, plan, tareas, implementación y estado con aprobaciones. |
| Revisión | RDD: receipt-driven development; revisión de candidato congelado, linaje, evidencia y corrección bajo autoridad Go. Lentes Risk, Readability, Reliability y Resilience; Judgment Day opcional. | Revisión, checks y evidencias; loop con fases, checkpoints y alcance de archivos. No se identificó un controlador general equivalente al protocolo nativo de linajes de Gentle. |
| Autorización de entrega | Los recibos de revisión no conceden por sí solos permiso para commit/push/PR/publicación. | Aprobaciones y controles independientes; ni metadatos ni evidencia sintética autorizan despliegues o entregas. |
| Agentes | Escritores/exploradores/verificadores y mensajería entre sesiones; admisión y superficies de edición para concurrencia dentro del runtime soportado. | Catálogo de especialistas, selección por stack y loop acotado. El loop ejecuta sus fases; no equivale a una interfaz de coordinación entre distintos asistentes. |
| Modelos | Perfiles por rol, proveedor, modelo y esfuerzo; rutas de reviewer y fallback. Autenticación mediante el registro del host. | Política y asesoramiento de modelos para su recorrido Claude; worker opcional mediante Claude Agent SDK. |
| Memoria | Engram: memoria de observaciones/decisiones con búsqueda y MCP; Shell dispone de políticas para reutilizar un servidor local compartido. | Notas revisadas, índice de código y recuperación acotada ligados al proyecto. HTML regenerable y observador local. |
| Ubicación de memoria | En el recorrido documentado, almacén compartido `~/.engram` con organización por proyecto; admite sincronización/exportación al repositorio. | Índice en `.harness/state/code-index/index.sqlite`; políticas en `.aikya`; notas y reportes en `aikya/docs/memory/`. |
| Grafo de código | Herramienta CodeGraph opcional, integrada mediante un CLI externo; fallback explícito si falta. | Índice propio: AST Python y parsers opcionales para Java, JS/TS, C#, Go y Dart; otros formatos pueden quedar como inventario. |
| Skills | Skills de flujo, diseño, colaboración y revisión; registro que descubre raíces de varios asistentes. | Skills técnicas de arquitectura, backend, frontend, mobile, seguridad y DevOps; instalación de skills elegidas por el usuario. |
| Tokens y uso | TPS, estadísticas, costes/uso disponibles y perfiles; el modo Auto de permisos puede añadir inferencia. | Recibos de uso, contexto acotado, continuidad de compactación y presupuestos opcionales del loop; Mods Flow/Usage son componentes distintos. |
| Compaction | Se apoya en las capacidades de Pi y continuidad de tareas; no asumir semántica idéntica a Claude. | Integración con eventos de compactación del host y recuperación de referencias; no ejecuta un resumidor adicional por defecto. |
| Permisos | Normal, Auto, YOLO y variantes; controles destructivos y rutas protegidas. Auto consulta al modelo. | Permisos del host, hooks locales, guardas y controles estrictos del worker; política explícita de worktrees. |
| Instalación | Instalador bundle, launcher aislado, adquisición verificada de runtimes/binarios, upgrade/rollback y desinstalación con propiedad. | Instalador Windows/macOS/Linux, runtime gestionado, verificación de artefactos, alcance global/proyecto y conservación de datos. |
| Personalización | Temas, layouts, animación, modo Vim, notificaciones, música, diseño HTML y voz local opcional. | Memory HTML, documentación por idioma y observabilidad; no se verificó un equivalente a música/voz/TUI completa. |
| Auditoría | Documentos ODD en `odd/tasks/`, estado de revisión y memoria, según componente/host. | Documentación de ingeniería centralizada en `aikya/docs/`; estado operativo local separado. |

Fuentes de implementación: [Shell técnico](https://github.com/Gentleman-Programming/gentle-shell/blob/v4.7.0/docs/readme-reference.md),
[permisos](https://github.com/Gentleman-Programming/gentle-shell/blob/v4.7.0/docs/permission-modes.md),
[revisión](https://github.com/Gentleman-Programming/gentle-shell/blob/v4.7.0/docs/review-integration.md),
[CodeGraph](https://github.com/Gentleman-Programming/gentle-shell/blob/v4.7.0/extensions/codegraph-tools.ts),
[componentes Gentle AI](https://github.com/Gentleman-Programming/gentle-ai/blob/v4.4.0/docs/components.md),
[loop Aikya](https://github.com/jlema0590/aikya-harness/blob/v7.2.2/src/aikya/core/runtime.py),
[metodología Aikya](https://github.com/jlema0590/aikya-harness/blob/v7.2.2/src/aikya/workflows/methodology.py),
[almacén Aikya](https://github.com/jlema0590/aikya-harness/blob/v7.2.2/src/aikya/code_index/store.py).

## 4. Claude, Codex y los demás asistentes

Hay que distinguir cuatro cosas: modelo de un proveedor, cliente asistente,
configuración que un instalador escribe y sesión real que ejecuta el trabajo.
Un provider llamado `openai-codex` en Pi no convierte Pi en el CLI o la aplicación
Codex. Un registro que lee `.claude/skills` tampoco ejecuta Claude Code.

| Cliente/capa | Gentle: verificación y límites | Aikya actual |
|---|---|---|
| Pi | Host nativo Shell. Launcher instalado: Shell 4.7.0, Pi 1.4.0. | No existe un adaptador de instalación Pi en el recorrido auditado. |
| Claude Code | Gentle AI escribe `CLAUDE.md`, skills, agentes y hooks según selección. Se generaron archivos en un hogar temporal. | Integración de producto existente: `.claude/skills`, agentes, settings/hooks, contrato CLAUDE y worker opcional. |
| Codex | Gentle AI dispone de adaptador; se generaron `AGENTS.md`, skills, `hooks.json` y configuración respetando el modelo del usuario. `codex features list` aceptó la configuración. | Se puede invocar Python desde un shell, pero no hay un adaptador de producto equivalente que instale skills, políticas y observación para Codex. |
| Gemini CLI | Adaptador y archivos específicos, con capacidades nativas experimentales documentadas. Archivos generados; cliente no ejecutado. | Sin adaptador nativo identificado. |
| OpenCode | Configuración, agentes, skills/plugins y MCP según componentes. Se generaron archivos; no se inició una sesión OpenCode. | Sin adaptador nativo identificado. |
| Otros | Catálogo Gentle AI: 18 entradas; incluye Kilo, Cursor, Copilot, Antigravity, Windsurf, Kimi, Qwen, Kiro, OpenClaw, Trae y Hermes. Conductor es detección/herencia de Claude, no escritura propia. | No extrapolar soporte a partir de archivos Markdown o de la palabra «adapter». |
| Modelos en Pi | Las dependencias fijadas incluyen providers Anthropic/OpenAI y otros; NaN añade su propia configuración. No se autenticó ni probó un modelo remoto. | El worker actual depende de Claude Agent SDK; no es un ejecutor universal de modelos. |

El catálogo completo y sus límites están en [agents.md](https://github.com/Gentleman-Programming/gentle-ai/blob/v4.4.0/docs/agents.md)
y [catalog/agents.go](https://github.com/Gentleman-Programming/gentle-ai/blob/v4.4.0/internal/catalog/agents.go).
El [adaptador de revisión Codex](https://github.com/Gentleman-Programming/gentle-ai/blob/v4.4.0/internal/reviewerprovider/codex_adapter.go)
es una ruta concreta del componente Go, diferente del proveedor de modelos Pi.

Los adaptadores actuales de Aikya en
[installation/compatibility.py](https://github.com/jlema0590/aikya-harness/blob/v7.2.2/src/aikya/installation/compatibility.py)
son launchers Python de compatibilidad. No acreditan integración de un nuevo
asistente. El `AGENTS.md` de contribuidores de este repositorio tampoco es un
instalador Codex para los proyectos del usuario.

Codex reconoce instrucciones jerárquicas `AGENTS.md`, skills y configuración MCP;
las políticas, precedencia y superficies de ejecución deben adaptarse a ese host,
no copiarse de Claude. Referencias oficiales: [instrucciones](https://developers.openai.com/codex/guides/agents-md),
[skills](https://developers.openai.com/codex/skills), [MCP](https://developers.openai.com/codex/mcp).
Para Claude: [skills](https://code.claude.com/docs/en/skills) y
[hooks](https://code.claude.com/docs/en/hooks). Disponibilidad de hooks o agentes
no implica que todas sus opciones sean portables entre clientes o versiones.

## 5. Skills: inventario y comparación

Conteo de archivos fuente del tag, no de capacidades independientes ni de todo lo
que termina instalado en un proyecto:

| Catálogo | Archivos |
|---|---:|
| Gentle Shell `skills/*/SKILL.md` | 15 |
| Aikya catálogo técnico `engineering/skills` | 29 |
| Aikya workflows base del template | 8 |
| Aikya comandos públicos empaquetados como skills | 28 |

Aikya contiene además 30 entradas de agentes del catálogo y ocho templates base
de agentes. No todos se instalan a la vez ni deben sumarse como especialistas
únicos sin estudiar la selección y los solapamientos. Gentle AI incorpora otras
skills propias: por ejemplo `go-testing`; son una capa distinta de las 15 de Shell.
Las skills técnicas comunitarias de Gentleman-Skills no se cuentan como incluidas.

Las 15 de Shell son: `branch-pr`, `chained-pr`, `cognitive-doc-design`,
`comment-writer`, `design`, `gentle-ai`, `gentle-ui-design`, `issue-creation`,
`judgment-day`, `rdd-defect-workflow`, `skill-creator`, `skill-improver`,
`skill-registry`, `tui-design` y `work-unit-commits`.

Aikya agrupa sus 29 técnicas en frontend (Angular, Astro, Next, React, Vue),
backend/mobile (Java, .NET, Node, Python, Kotlin y Flutter), arquitectura
(clean, cloud, eventos, capas, microservicios y monolito modular), DevOps/cloud
(Ansible, CI/CD, Docker, Helm, Kubernetes, Kustomize, Terraform, FinOps),
seguridad y revisión/pruebas. El inventario con rutas y hashes se conserva en
[JSON](2026-11-07-gentle-shell-inventory.json).

La brecha de Aikya está más en descubrimiento, metadatos portables y adaptación
que en añadir muchas skills. Conviene un catálogo fuente único con renderizadores
por host, identificación de propietario y resolución global/proyecto. No copiar
las mismas instrucciones a varias raíces y asumir que dejarán de duplicarse.

## 6. ODD, SDD, TDD y RDD

**Alcance futuro acordado para v8:** el usuario incorpora TDD y RDD entendido como
**Receipt Driven Development**, y fija una terminal Aikya sobre Pi para macOS,
Windows y Linux como experiencia principal. La
[ampliación del plan](../plan/2026-11-07-aikya-v8-terminal-tdd-rdd.es.md)
define el controlador y su aceptación. Esto no cambia los resultados observados
de 7.2.2 ni acredita una implementación futura.

**Gentle:** ODD opera sobre la petición cotidiana; explora proporcionalmente,
resuelve incertidumbre y decide seguimiento por recuperabilidad. La documentación
usa `odd/tasks/<feature>.md` para trabajo grande, con espejo Engram cuando existe.
La evidencia de ejecución no debe confundirse con cumplimiento del modelo. TDD
se resuelve mediante configuración/elección; RDD es una capa opcional de revisión,
activada por defecto en el componente actual, no otro nombre para SDD.

Las unidades de commit de unas 400 líneas son una orientación de revisión,
no un límite de seguridad ni una razón automática para delegar. RDD mantiene
linaje/candidato/evidencia y correcciones acotadas. Sus recibos no conceden
aprobación de entrega. No trasladar esa autoridad completa a prompts de Aikya
ni inventar recibos compatibles.

**Aikya:** permite elegir ODD o SDD en onboarding. ODD mantiene feature, tareas,
dependencias y evidencia; SDD conserva sus etapas y aprobaciones en
`aikya/docs/specs/<project_type>/SPEC-NNN/`. Las fases observables existentes son
`explore`, `plan`, `implement`, `validate`, `security`, `review`; no son nombres
de modelos ni prueba de que el trabajo se haya ejecutado.

La política aconsejada es mantener ambos modos y añadir revisión proporcional
por riesgo sobre ellos. Una consulta no debe generar un expediente grande ni
una revisión con múltiples modelos. Un cambio de alto riesgo sí necesita evidencia
independiente apropiada, aunque sea corto.

## 7. Memoria, contexto, privacidad y tokens

Aikya ya tiene almacenamiento local, índice verificable de declaraciones y HTML.
«Tener memoria» no exige un servicio remoto ni un vector store. Engram aporta otra
función útil: observaciones y decisiones consultables desde varios asistentes por
MCP. No reemplaza por sí solo la indexación semántica de clases, funciones o imports.
CodeGraph es otro componente, no una propiedad automática de Engram.

La prueba aislada de Engram 3.5.2 pasó guardado/búsqueda/contexto, escrituras
concurrentes y una prueba breve de búsqueda. No se probó extracción automática de
conocimiento por un modelo ni sincronización real de un equipo. Su almacén de
usuario compartido tampoco coincide con el requisito de Aikya de datos locales
por proyecto. Cualquier puente debe mantener namespaces y política explícita.

No hay una medición comparable de tokens entre productos en esta investigación.
Los límites en bytes de prompts no equivalen a tokens facturados. El modo Auto de
Gentle usa inferencia adicional; la revisión con varios roles también puede añadir
llamadas. Las estadísticas dependen de lo que declare cada proveedor y no convierten
datos desconocidos en cero. La telemetría de uso de Gentle es opcional y puede
transmitir agregados: no asumir que toda observabilidad permanece en disco.

Para Aikya recomiendo medición por tarea y rol, separación de entrada/salida/cache,
causas de fallback, revisiones/delegación y coste de permisos. La indexación, el
watcher y el HTML deben seguir funcionando sin llamadas a modelos. Una prueba de
ahorro necesita tareas equivalentes, mismo modelo/versión/esfuerzo y reglas de
cache comparables, al menos tres repeticiones y un presupuesto explícito.

Fuentes: [presupuesto de prompts](https://github.com/Gentleman-Programming/gentle-shell/blob/v4.7.0/docs/prompt-budget.md),
[Auto](https://github.com/Gentleman-Programming/gentle-shell/blob/v4.7.0/docs/permission-modes.md),
[telemetría](https://github.com/Gentleman-Programming/gentle-shell/blob/v4.7.0/docs/telemetry.md).

## 8. Conviven los archivos; la metodología requiere un responsable

Se instaló Aikya globalmente en el mismo hogar **temporal** usado por los cuatro
adaptadores de Gentle AI. Conservó la persona, las skills y hooks Gentle, el valor
Codex del usuario y los settings sintéticos. Registró 28 comandos Aikya y el
registro posterior de proyecto no creó copias locales duplicadas.

Esto prueba conservación de archivos, no una conversación compatible. Dos
orquestadores pueden discrepar sobre rutas (`odd/tasks` frente a `aikya/docs`),
reglas de parada, revisión, memoria y quién autoriza cada transición. Recomiendo
un harness principal por sesión/proyecto y puentes limitados. No instalar ambos
con todas sus políticas activas sobre la configuración personal como experimento.

Aikya sigue teniendo un límite de migración importante: actualizar lo global no
recorre todos los proyectos existentes. Las copias locales antiguas requieren
reconciliación del proyecto. Se verificó en esta investigación el caso nuevo y la
conservación, no una migración universal al iniciar cualquier host.

## 9. Qué aporta el main posterior a 4.7.0

La [comparación fijada](https://github.com/Gentleman-Programming/gentle-shell/compare/v4.7.0...d17c6f98cc69ea9a7a5a359c79934ee9292f1fcf)
contiene tres commits. Afecta instrucciones de delegación/seguimiento, skill
`branch-pr`, exposición de herramientas y pruebas relacionadas. La
[nota de fricción ODD/RDD](https://github.com/Gentleman-Programming/gentle-shell/blob/d17c6f98cc69ea9a7a5a359c79934ee9292f1fcf/docs/rdd-odd-friction-triage-2026-11-07.md)
describe correcciones y trabajo pendiente.

No instalé ese main ni reproduje todas las incidencias del documento. Algunas
referencias de la nota son históricas y citan otro pin Gentle AI; el pin ejecutado
aquí es 4.4.0. Un issue abierto o una mejora en main no bastan para declarar que
un defecto persiste o está resuelto en una release. El resultado verde de la
suite 4.7.0 tampoco demuestra ausencia de defectos de comportamiento del modelo.

## 10. Decisiones recomendadas

1. **Adoptar:** adaptadores por host, matriz de capacidades, catálogo portable,
   perfiles con procedencia, seguimiento proporcional y evidencias ligadas al cambio.
2. **Conservar:** ODD/SDD, `aikya/docs`, memoria local por proyecto, verificaciones
   deterministas, permisos y protección de personalizaciones.
3. **Revisar según la ruta elegida:** la recomendación inicial de posponer Pi se
   refería a evolución incremental. Para v8.0.0, evaluar Pi como runtime principal
   con prototipo y migración; mantener TUI propia, música y voz fuera del MVP.
4. **No activar por defecto:** autorización por modelo, multi-review constante,
   memoria global compartida o instalación de skills externas. Son elecciones del usuario.
5. **No prometer:** equivalencia de hooks entre hosts, ahorro porcentual de tokens,
   soporte uniforme de 18 clientes o funcionamiento real de modelos no autenticados.

Las licencias inspeccionadas son MIT. Reutilizar código requiere conservar los
avisos correspondientes; MIT no concede derechos de marca. Es preferible adaptar
contratos pequeños y patrones, evitando importar extensiones monolíticas: en el tag
hay una extensión de 13.306 líneas. El inventario Python de Aikya examinado tiene
168 archivos, ninguno de más de 1.000 líneas; el diseño propuesto conserva módulos
pequeños. Estos conteos describen estructura, no certifican calidad ni seguridad.

GENERATED BY AIKYA HARNESS

# Plan de implementación: /aikya-uninstall-skills

**Estado:** propuesta para revisión; no autoriza eliminar ninguna skill actual.
**Objetivo:** retirar skills globales o de proyecto mediante selección explícita,
previsualización, respaldo recuperable y registro del resultado real.
**Arquitectura:** un motor local del paquete compartido por el CLI y el comando
slash. Reutilizar inventarios, manifiestos, hashes y escritura atómica existentes;
añadir únicamente la política de exclusión y el diario necesarios para esta operación.
**Tecnologías:** Python 3.10–3.13, biblioteca estándar, JSON y unittest; Claude Code
para invocación. Sin dependencias nuevas ni agente auxiliar.
**Base verificada:** develop `f11ffb5`, versión 7.2.0; la fuente local coincide con
esa base. Rama propuesta al ejecutar: `feat/skills-uninstall`, desde develop actualizado.
**Especificación:** petición del usuario de añadir `/aikya-uninstall-skills` para
eliminar skills globales o locales. Este documento concreta su comportamiento.
**Ejecución propuesta:** secuencial, con pruebas por entrega y commits separados.

## Hallazgos del código actual

- `catalogs/skills.py` inventaría principalmente `.claude/skills` del proyecto;
  las skills globales no se atribuyen automáticamente a ese proyecto.
- `catalogs/external.py` instala una skill seleccionada, registra procedencia en
  `.harness/external-skills-lock.json` y preserva destinos existentes. El registro
  externo antiguo no contiene un manifiesto completo de hashes por archivo.
- `catalogs/engineering.py` selecciona skills/agentes por stack y conserva hashes
  en `.harness/engineering-catalog.json`. Puede instalar de nuevo una skill que
  continúe en la selección aunque alguien borre su carpeta manualmente.
- `installation/registration.py` registra los comandos en el scope global o
  proyecto y conserva personalizaciones. Su manifiesto de runtime no equivale a
  propiedad de todos los archivos adicionales de una carpeta activa de skill.
- `installation/bootstrap/cli.py` desinstala el harness completo mediante recibos;
  no debe reutilizarse como si fuera un desinstalador selectivo de skills.
- Hay 28 comandos públicos actuales; el nuevo comando eleva el catálogo a 29.
  Los informes históricos con 28 comandos permanecen como evidencia histórica.

## Comportamiento propuesto

| Invocación | Resultado |
|---|---|
| `/aikya-uninstall-skills` | Mostrar inventario resumido y elegir scope/skills; sin eliminación |
| `/aikya-uninstall-skills --scope project` | Mostrar las skills del proyecto y sus dependencias |
| `/aikya-uninstall-skills --scope local` | Alias de `project`, normalizado en el recibo |
| `/aikya-uninstall-skills --scope global` | Mostrar skills personales de la configuración Claude seleccionada |
| `… --scope project --name flutter-architecture` | Previsualizar retirada de una skill concreta |
| `… --scope project --name example --name another-example` | Previsualizar selección múltiple |
| `… --scope global --all` | Previsualizar todas las skills elegibles del scope, con exclusiones visibles |
| `… --scope project --restore <operation-id>` | Previsualizar restauración desde un respaldo verificado |

El slash presenta el plan y, tras la autorización de esa selección concreta,
ejecuta el backend con `--approved --plan-token <sha256-del-plan>`. Sin ambos,
el backend solo informa: no escribe un plan, no crea respaldos ni modifica el índice.
Un cambio de archivos desde el preview invalida el token y exige otro preview.

El CLI compartido propuesto es `aikya skills list|uninstall|restore`; no son
tres comandos slash nuevos. El parser de skills es independiente del `--scope`
de discovery, que actualmente significa un subdirectorio del repositorio.
Una operación de retirada afecta a un único scope; eliminar ambas copias requiere
dos operaciones seleccionadas. El listado puede mostrar ambas para explicar cuál
seguirá disponible, sin recorrer todos los proyectos del usuario.

## Alcance y protecciones

### Tipos de skill

1. **Técnicas de Aikya:** eliminables con evidencia de propiedad y análisis de
   los agentes que las precargan. Eliminar una skill no implica ejecutar su código.
2. **Externas registradas:** eliminables con respaldo de la carpeta completa y
   procedencia. Un recibo antiguo sin hashes no acredita por sí solo integridad.
3. **Personalizadas/no registradas o modificadas:** visibles, pero preservadas en
   `--all`. Su retirada requiere nombres explícitos, `--include-custom` y revisión
   del contenido/rutas/hashes del plan; nunca una excepción global silenciosa.
4. **Comandos `/aikya-*`:** protegidos por defecto. Su retirada necesita selección
   explícita y `--include-commands`; advertir qué funciones dejarán de estar
   disponibles. `--all` conserva siempre `/aikya-uninstall-skills`.
5. **Plugins/Mods, skills sincronizadas, empresariales y directorios añadidos o
   anidados:** identificar como origen aparte y no borrar sus cachés ni directorios
   administrados. Informar del mecanismo propietario para retirarlos. La primera
   entrega administra únicamente skills independientes de los scopes seleccionados.

No borrar runtime, hooks, permisos, agentes no seleccionados, CLAUDE.md, memoria,
HTML, planes, código de aplicación, SDKs ni binarios externos. Eliminar la skill de
Graphify, por ejemplo, no desinstala su CLI ni elimina los índices que creó.
El nuevo comando no llama al desinstalador general de Aikya ni al de un marketplace.

### Dependencias

Inspeccionar referencias `skills:` de los agentes y registrar los afectados antes
de aplicar. Por defecto, una dependencia activa bloquea esa retirada concreta.
Ofrecer `--include-dependents` para retirar también agentes dependientes que sean
gestionados, intactos y estén enumerados en el preview; no cambiar sus instrucciones
a medias ni modificar agentes personalizados. Respaldar sus archivos y registrar
su exclusión para que no reaparezcan automáticamente. Un agente personalizado que
dependa de la skill exige resolver esa dependencia explícitamente fuera del comando.

En scope global, revisar agentes globales y los del proyecto indicado, si lo hay.
Las dependencias de otros repositorios no examinados quedan expresamente como
no verificadas; no recorrer el disco ni prometer ausencia de impacto universal.

No tratar una mención textual arbitraria como dependencia ejecutable. Las referencias
documentadas que no puedan resolverse se muestran como incertidumbre; no se fabrica
un grafo semántico. Restaurar una operación incluye sus dependencias exactas y su
política anterior, conservando cualquier cambio posterior para revisión.

### Scopes, recuperación y auditoría

- Proyecto: `<target>/.claude/skills/`. Global: `<claude-config>/skills/`, normalmente
  `~/.claude/skills/`; respetar la configuración efectiva y `CLAUDE_CONFIG_DIR`.
  No ampliar permisos del host para acceder a un scope inaccesible.
- Política de exclusión de proyecto: `.aikya/skills-policy.json`. Global:
  `<claude-config>/aikya/skills-policy.json`. Solo afecta al scope correspondiente.
- Respaldos/diario del proyecto: `.harness/state/skill-operations/<id>/`.
  Globales: `<claude-config>/aikya/state/skill-operations/<id>/`.
  Fuera de carpetas que Claude descubre como skills; sin caducidad/borrado automático
  en esta entrega. Permisos privados según las capacidades del sistema.
- Auditoría Markdown de proyecto: `aikya/docs/changes/skills-<id>.md`; global:
  `<claude-config>/aikya/docs/changes/skills-<id>.md`. Sin perfil de proyecto,
  una operación global sigue funcionando y no crea documentación en el cwd.
- Registrar scope, identidad, selección, hashes, resultado por elemento y respaldo;
  no copiar prompts, credenciales ni cuerpos de skills al informe Markdown.
- Actualizar solo inventarios/documentos administrados. Si un documento del usuario
  requiere edición, mostrar la discrepancia; el resultado operativo se conserva en
  el diario y no se presenta como fallo total si la retirada ya se completó.

Reutilizar atomicidad y bloqueos locales existentes. Comprobar rutas, propietarios,
hashes y dependencias nuevamente dentro del bloqueo compartido con los escritores
de skills. Rechazar symlinks, junctions/redirecciones Windows, traversal, archivos
especiales y escapes del scope, incluidos los de las rutas de respaldo.

Un directorio con archivos adicionales desconocidos se considera personalizado;
no borrarlo recursivamente basándose solo en el hash de SKILL.md. Respaldar y
verificar todos los archivos seleccionados antes de retirar nada. Si no se puede
crear/verificar el respaldo, no retirar la skill. Ante corte o fallo de permisos,
mantener diario recuperable y resultados reales, sin prometer atomicidad entre
volúmenes. Otra aplicación puede restaurar una skill externa: Aikya informa de
ello, pero no puede controlar instaladores ajenos.

## Exclusiones y actualizaciones

La retirada aprobada registra skills y agentes retirados como excluidos del scope.
`setup`, `init`, `analyze`, actualización administrada y activación del catálogo
respetan esta política. No alcanza con filtrar el catálogo técnico: también hay
que filtrar la copia de plantillas y el registro de comandos.

La restauración o reinstalación **explícita** de nombres concretos puede levantar
su exclusión después del preview. Una actualización pasiva no la levanta. Un recibo
de instalación nuevo y uno antiguo siguen siendo legibles; no eliminar evidencia
de procedencia para hacer desaparecer una fila del inventario.

## Archivos e interfaces propuestos

| Archivo | Responsabilidad |
|---|---|
| Crear `src/aikya/catalogs/skill_inventory.py` | Inventario por scope, propiedad, duplicidades y dependencias |
| Crear `src/aikya/catalogs/skill_policy.py` | Exclusiones y selección efectiva; ninguna eliminación |
| Crear `src/aikya/catalogs/skill_removal.py` | Preview, token, respaldo, retirada, recuperación y restauración |
| Crear `src/aikya/cli/skills.py` | Parsear las acciones del CLI y sus códigos de salida |
| Modificar `src/aikya/cli/main.py` | Despachar `skills` antes del parser de discovery |
| Modificar `catalogs/skills.py`, `external.py`, `engineering.py` | Reutilizar inventario, registrar hashes nuevos y respetar exclusiones |
| Modificar `installation/project_assets.py`, `registration.py` | Respetar política al copiar skills/plantillas/comandos |
| Modificar `installation/bootstrap/cli.py`, `state.py` si procede | Conservar recibos/bloqueos compatibles, sin restaurar skills excluidas |
| Modificar `cli/commands.py` y crear `resources/commands/aikya-uninstall-skills/SKILL.md` | Registrar el comando público 29, manual y acotado |
| Modificar `middleware/commands.py`, `observer.py` | Listado/preview de solo lectura; escritura solo tras aprobación |
| Modificar `module_map.json` y `installation/assets.py` solo si hace falta adaptador | Mantener una implementación para wheel, runtime global y runtime de proyecto |
| Modificar `scripts/ci/command_acceptance.py`, README en/es, CHANGELOG y docs de skills | Aceptación del comando nuevo, ejemplos y documentación del resultado |

Interfaces públicas internas:

```python
inventory(scope: str, *, target: Path | None, claude_config: Path) -> dict
effective_selection(names: list[str], policy: dict, kind: str) -> list[str]
plan_removal(context: dict, selection: dict) -> dict
apply_removal(plan: dict, *, approved: bool, plan_token: str) -> dict
plan_restore(context: dict, operation_id: str) -> dict
apply_restore(plan: dict, *, approved: bool, plan_token: str) -> dict
```

`context` fija scope, raíz canónica e identidad. `selection` contiene nombres o
`all`, además de las opciones explícitas de comandos/personalizaciones/dependientes.
El preview devuelve `schema`, `scope`, `root_identity`, `items`, `blocked`,
`dependencies`, `remaining_copies`, `plan_token` y `writes: false`. El token vincula
todos los archivos/rutas y cambios de política previstos, no solo sus nombres.
El resultado de aplicación devuelve `operation_id`, `removed`, `preserved`,
`failed`, `backup`, `audit`, `documentation_status` y estado real.
Código CLI 0: preview/operación completa/no-op; 2: entrada o aprobación inválida;
4: conflicto, dependencia o resultado parcial/recuperación pendiente. No convertir
un fallo parcial en éxito silencioso. `--all` y `--name` son excluyentes.

## Tareas de implementación

### 1. Inventario global/proyecto y dependencias · 3–4 h

**Pruebas:** crear `tests/test_skill_inventory.py`.

- [ ] Añadir casos de dos copias con el mismo nombre, config global alternativo,
  inventario sin perfil, symlink/junction, skill sin procedencia y agente dependiente.
- [ ] Ejecutar `python -m unittest discover -s tests -p test_skill_inventory.py -v`
  y observar el fallo del contrato nuevo.
- [ ] Implementar `inventory()` y normalizar `local` a `project`; listar un scope
  no implica registrar el otro en el proyecto ni escanear todos los repositorios.
- [ ] Verificar los casos, el lector anterior y compatibilidad en/es. Indicar ambas
  copias sin asumir que borrar una desactiva la otra; resolver prioridad según host.
- [ ] Cerrar un commit del inventario compartido.

### 2. Retirada recuperable y restauración · 6–8 h

**Pruebas:** crear `tests/test_skill_removal.py`.

- [ ] Añadir preview sin escrituras, rechazo sin aprobación/token, cambio tras
  preview, fallo de respaldo, archivo adicional inesperado, corte entre pasos,
  restauración con conflicto y doble ejecución idempotente. Probar escapes de rutas,
  retirada global sin tocar proyectos y retirada de proyecto sin tocar el global.
- [ ] Ejecutar `python -m unittest discover -s tests -p test_skill_removal.py -v`
  y comprobar el fallo antes de implementar.
- [ ] Implementar las cuatro funciones de plan/aplicación en `skill_removal.py`,
  reutilizando almacenamiento/bloqueo y preservando la recuperación del diario.
- [ ] Verificar personalizadas con selección explícita, comandos protegidos,
  `--include-dependents`, agente modificado que bloquea y fallo de permisos Windows.
- [ ] Cerrar el commit de retirada/restauración, sin desinstalar nada del equipo real.

### 3. Persistencia y compatibilidad con instalación/update · 4–6 h

**Pruebas:** crear `tests/test_skill_policy.py`; ampliar
`tests/test_engineering_catalog.py`, `test_v52.py` y contratos del instalador.

- [ ] Añadir un ciclo real en fixture: instalar → retirar → repetir init/analyze o
  update → comprobar ausencia → restaurar explícitamente → comprobar presencia.
  Probar scope global/proyecto, registro directo sin instalador limpio, manifiesto
  antiguo sin hashes y conservación del resto de selecciones/recibos.
- [ ] Ejecutar los casos y observar la reinstalación no deseada del comportamiento actual.
- [ ] Implementar política y filtrado en todos los escritores indicados. Las nuevas
  instalaciones externas registran el mapa completo de hashes; no atribuirlo a las antiguas.
- [ ] Actualizar estados del inventario a retirada/excluida/presente según evidencia;
  conservar procedencia y documentos personalizados. Actualizar hashes de respaldos.
- [ ] Verificar contratos de instalación y cerrar commit de persistencia.

### 4. CLI, comando slash y fases · 2–3 h

**Pruebas:** crear `tests/test_uninstall_skills_command.py`; ampliar aceptación.

- [ ] Añadir invocación sin argumentos/preview, scope inválido, selección múltiple,
  alias local, operación global sin perfil, restauración y comando registrado una vez.
- [ ] Ejecutar los casos nuevos y observar que el comando todavía no existe.
- [ ] Implementar `cli/skills.py`, despacho y SKILL.md con
  `disable-model-invocation: true`; reutilizar el observador, sin agente auxiliar.
- [ ] Preview: Explore/Plan/Validate locales, sin Implement ni expediente vacío.
  Aplicación: registrar solo operaciones y comprobaciones realmente ejecutadas;
  mantener aprobación y controles de seguridad. No repetir herramientas por ritual.
- [ ] Verificar ayuda y runtime instalado fuera del checkout; cerrar commit del comando.

### 5. Aceptación, documentación y versión · 5–7 h

- [ ] Extender la batería a 29 comandos desde el catálogo, con casos positivos y
  denegaciones de retirada/restauración en proyectos y HOME temporales.
- [ ] Ejecutar regresión aislada, wheel instalado, global/project, ODD/SDD y en/es;
  CI nativa Linux/macOS/Windows con Python 3.10–3.13. Sin borrar skills personales
  ni llamar a modelos para comprobar operaciones deterministas.
- [ ] Revisar que `/aikya-install-skill`, inventario, Memory y desinstalación completa
  siguen funcionando. Una copia del otro scope o un plugin no se declara retirado.
- [ ] Actualizar README en/es, CHANGELOG, docs operativas, ejemplos de auditoría e
  índice. Proponer v7.3.0, sujeta al contrato de versión vigente al implementar.
- [ ] Guardar resultados/omisiones reales bajo `aikya/docs/validation/`. Preparar
  commits y descripción de PR; publicación solo cuando se solicite.

## Riesgos, tokens y aceptación

Riesgo principal: borrar archivos del usuario o dejar referencias activas rotas.
Se reduce con alcance explícito, hashes, respaldo completo, dependencias y exclusiones.
Cambiar configuración global afecta a todos los proyectos que usen esas skills;
el preview lo debe explicar. El paquete de recuperación no se purga automáticamente.

Retirar una skill evita invocaciones futuras desde esa copia, pero no vacía el
contenido ya cargado en la conversación ni reinicia la cuota de cinco horas/semanal.
El CLI local no requiere llamadas LLM; el slash y su conversación conservan el
consumo normal del asistente. No prometer ahorro proporcional al número de skills.

La entrega se acepta cuando una selección se puede previsualizar, retirar y
restaurar sin tocar otros scopes; las actualizaciones respetan su exclusión;
dependencias/personalizaciones/conflictos se muestran con resultados veraces;
la auditoría y la recuperación permiten explicar exactamente qué ocurrió.

**Estimación:** 20–28 horas de ingeniería, unas 3–4 jornadas, más esperas de CI/revisión.
No incluye un gestor general de plugins ni medir ahorro real de modelos. No hay
presupuesto monetario o consumo de IA deducible de esta estimación.

## Referencias verificadas

- [Skills: ubicaciones, retirada y ciclo de vida](https://code.claude.com/docs/en/skills).
- [Plugins: componentes y propiedad de sus skills](https://code.claude.com/docs/en/plugins-reference).
- Código citado de Aikya bajo `src/aikya/catalogs/`, `installation/`, `cli/` y
  `middleware/`; este plan no ejecutó retiradas ni instalaciones.

GENERATED BY AIKYA HARNESS

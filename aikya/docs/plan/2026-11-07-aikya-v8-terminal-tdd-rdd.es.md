# Aikya v8.0.0: terminal multiplataforma, TDD y Receipt Driven Development

Fecha: 7 de noviembre de 2026. Estado: ampliación propuesta; no implementada.
Plan principal: [Aikya v8.0.0 sobre Pi](2026-11-07-aikya-multi-host.es.md).

## Objetivo y decisiones

Convertir Aikya en un asistente instalable y utilizable directamente desde la
terminal de macOS, Windows y Linux, con una experiencia similar a Gentle Shell.
Pi es la base propuesta para la interfaz y la ejecución. Aikya aporta metodología,
memoria local, controles, documentación y experiencia de producto.

**RDD significa Receipt Driven Development.** La propuesta anterior de
Requirements Driven Development queda sustituida por esta decisión del usuario.
Los requisitos y criterios existentes siguen formando parte de ODD/SDD.

| Capa | Responsabilidad en Aikya v8 |
|---|---|
| ODD o SDD | Organizar el trabajo y sus aprobaciones; el desarrollador elige el modo. |
| TDD | Desarrollar cambios de comportamiento mediante Red → Green → Refactor. |
| RDD | Revisar candidatos identificados, registrar recibos y comprobar que la evidencia corresponde al código revisado. |
| Pi | Interfaz de terminal, sesiones y ejecución mediante proveedores soportados. |

TDD y RDD atraviesan ambos modos; no añaden otras dos opciones al selector ODD/SDD.
Las fases visibles permanecen en inglés: `explore`, `plan`, `implement`, `validate`,
`security`, `review`. Red/Green/Refactor son pasos de implementación y validación,
no nuevos estados del ciclo completo.

## Experiencia de terminal y aceptación

Recorrido objetivo: instalar → abrir `aikya` dentro del proyecto → configurar
proveedor/modelo explícitamente → elegir ODD/SDD cuando corresponda → trabajar →
ver pruebas y revisión → salir y reanudar con el estado conservado.

- Una instrucción de instalación por familia de shell: shell POSIX para macOS/Linux
  y PowerShell para Windows. Usar la publicación GitHub existente; no inventar un dominio.
- Sin clonar el repositorio ni instalar Claude Code o Codex para usar el runtime Pi.
  Resolver dependencias en una instalación administrada por Aikya y verificarlas.
- Reutilizar la TUI de Pi, adaptando identidad, ayuda, comandos, estado y errores.
  Una TUI totalmente nueva queda fuera de esta estimación.
- Mantener una única entrada `aikya`: sin argumentos abre la terminal interactiva;
  conservar subcomandos de soporte y salidas para automatización. Esa apertura
  interactiva es nueva: el comando actual es una CLI de soporte.
- Configuración y autenticación mediante mecanismos soportados por el proveedor;
  no inferir acceso por una suscripción ni copiar credenciales silenciosamente.
- Ver proyecto, sesión, modo, fase, modelo y uso disponible. Uso desconocido se
  muestra como desconocido; estado y ayuda locales no llaman a modelos.
- Actualizar, diagnosticar y desinstalar desde la terminal; conservar datos del
  proyecto por defecto. Prever errores de PATH, espacios, Unicode, proxy,
  interrupciones, falta de TTY y archivos bloqueados durante updates de Windows.

La aceptación requiere ejecutar el recorrido en cada sistema nativo. Los tests
con rutas Windows simuladas en macOS no acreditan funcionamiento en Windows.
Publicar arquitecturas y shells realmente verificados; no prometer soporte
universal por el nombre del instalador.

## TDD aplicado con evidencia

Para comportamiento nuevo o un bug reproducible:

1. Delimitar el comportamiento y el criterio de aceptación en el expediente actual.
2. **Red:** ejecutar una prueba pequeña que falle por el comportamiento esperado;
   un entorno roto o una dependencia ausente no demuestra ese fallo.
3. **Green:** implementar lo mínimo y ejecutar la misma prueba con resultado válido.
4. **Refactor:** mejorar la estructura y repetir las pruebas afectadas.
5. Ejecutar comprobaciones de integración, seguridad y regresión según el alcance.
6. Vincular las ejecuciones observadas al candidato que se presenta a RDD.

Red corresponde a la versión anterior y Green a otra posterior: no exigir el
mismo hash para ambas. Conservar qué versión y prueba produjo cada resultado.
Las pruebas ya existentes pueden reutilizarse; no atribuirles retrospectivamente
un ciclo TDD que no fue observado. Cero pruebas, skipped o un runner ausente no
equivalen a verificación satisfactoria.

Consultas, documentación y configuración sin comportamiento ejecutable usan
comprobaciones pertinentes, sin fabricar una prueba fallida. Registrar la causa
de no aplicabilidad. Un cambio de infraestructura ejecutable requiere pruebas o
validación propia de esa plataforma, no se excluye por no ser código Python.

## Contrato mínimo RDD de Aikya

Se toma como referencia el control de candidatos y evidencia de Gentle Shell
4.7.0. No se promete compatibilidad con sus recibos, autoridad Go o protocolos.
El MVP implementa un controlador Aikya acotado y determinista; cuatro lentes,
refutadores y Judgment Day requieren un alcance y presupuesto posteriores.

**Candidato:** identidad canónica de proyecto, cambio, sesión, base, política,
alcance y manifiesto de archivos con hashes, incluidos tests, configuración y
archivos nuevos pertinentes. Registrar cambios previos ajenos y exclusiones;
no eliminarlos ni incorporarlos silenciosamente. El prototipo debe resolver
también el caso de un proyecto nuevo sin Git, sin crear un repositorio o worktree
por defecto. Un hash detecta cambios; no convierte el directorio en inmutable.

**Recibo:** ID único, versión de esquema, candidato/linaje, acción, actor/origen,
resultado, inicio/fin, referencias y hashes de evidencia. Para ejecución: comando
como lista de argumentos, directorio, código de salida y resumen/log acotado.
Para revisión: alcance, hallazgos, pruebas concretas y decisión admitida por el
controlador. Registrar modelo y uso observado solo cuando existan.

**Reglas de aceptación:**

- Congelar un candidato antes de revisar. Rechazar recibos de otro proyecto,
  candidato, política o sesión sin una reanudación explícita y compatible.
- Un prompt, un Markdown o un JSON escrito por el modelo no acredita que una
  herramienta se ejecutó ni puede autoconceder una revisión satisfactoria.
- Admitir resultados mediante el controlador después de validar identidad,
  esquema, evidencia y transición. Recepción duplicada es idempotente; datos
  contradictorios o reintentos obsoletos se rechazan.
- Si cambia un archivo cubierto, el veredicto anterior queda asociado a su
  candidato histórico. Crear un sucesor con linaje y verificar el nuevo estado;
  nunca transferir automáticamente la aprobación. Una corrección autorizada
  conserva hallazgos y alcance, y exige validación dirigida y comprobación final.
- Una revisión puede aceptar, pedir corrección o escalar. Ausencia de herramientas,
  cancelación y evidencia obsoleta impiden declarar el trabajo verificado.
- Compactar o reanudar conserva linaje y presupuesto, pero no amplía permisos.
  Reinicio y reanudación revalidan la autorización; no restaurar un consentimiento
  de sesión como una autorización permanente.
- Aplicar revisión proporcional: checks locales para documentación demostrada,
  revisión acotada para cambios ordinarios y revisión especializada para riesgo
  alto. La cantidad de líneas no es el único criterio; no lanzar cuatro modelos
  por defecto. El MVP permite una corrección; superar su alcance o presupuesto
  escala al desarrollador, sin ciclos automáticos ilimitados.
- La conclusión RDD describe el candidato revisado. No autoriza commit, push,
  publicación o despliegue, ni añade un bloqueo oculto de esos comandos Bash.
  Los permisos y controles de seguridad siguen siendo independientes.

Persistir datos por proyecto bajo
`aikya/docs/validation/<change-id>/`: `candidate.json`, `receipts.jsonl` y
`review.md` cuando existan datos. Referenciar evidencia de ODD/SDD existente sin
copiar logs completos ni crear otro expediente autoritativo. El Markdown termina
con el footer acordado y aparece en el índice; no insertar ese footer en JSON.
No registrar secretos, prompts completos o credenciales en los recibos.

El controlador local y su ejecutor son parte de la base de confianza. Las salidas
del modelo y los archivos del repositorio son entradas sin autoridad. Las
extensiones Pi comparten privilegios del proceso: estos controles no son
atestación externa ni protección frente al propietario del equipo que modifica
el controlador. Cualquier aislamiento adicional debe probarse por separado.

## Tareas implementables añadidas

### R1. Candidatos y contrato de recibos — 16–24 h

**Crear:** `src/aikya/review/contracts.py`, `candidates.py`, `receipts.py`,
`tests/test_review_candidates.py` y `tests/test_review_receipts.py`.
**Interfaces propuestas:** `freeze_candidate(root, change_id, scope)` produce un
`CandidateSnapshot`; `record_receipt(candidate, execution)` produce un `Receipt`.
Fijar sus esquemas versionados antes de conectar el runtime.

- [ ] Escribir y ejecutar pruebas que fallen para archivos nuevos omitidos,
      escapes de ruta, candidato cambiado, proyecto incorrecto y recibo duplicado.
- [ ] Implementar captura y persistencia atómica acotadas; comprobar concurrencia,
      reinicio tras interrupción y conservación de archivos previos del usuario.
- [ ] Verificar Green, refactorizar y registrar evidencia del propio controlador.

### R2. Controlador, TDD y adaptación Pi — 16–32 h

**Crear:** `src/aikya/review/controller.py`,
`packages/aikya-pi/src/review.ts`, `tests/test_review_controller.py` y
`packages/aikya-pi/tests/review.test.ts`.
**Modificar:** adaptadores ODD/SDD y puente propuestos, sin duplicar sus motores.
**Interfaz propuesta:** `assess_candidate(candidate, receipts, policy)` produce
una decisión estructurada con estado, razones, hallazgos y siguiente acción legal.

- [ ] Empezar por pruebas de falsa aprobación: prosa del modelo, evidencia antigua,
      cero tests, salida malformada, replay, cancelación y cambio durante revisión.
- [ ] Conectar eventos de ejecución reales y revisión al controlador; limitar
      tiempo, tamaño de logs, correcciones y presupuesto. Persistir antes de
      informar un cierre; errores del almacenamiento impiden declararlo cerrado.
- [ ] Probar Red/Green sobre versiones diferentes, corrección con candidato
      sucesor, bloqueo por evidencia obsoleta y cierre sin permisos de entrega.

### R3. Cobertura de comandos, lenguajes y límites — 16–24 h

**Crear:** `tests/test_review_workflow_matrix.py`,
`tests/test_review_language_matrix.py` y fixtures propios del paquete Pi.
**Reutilizar:** catálogos de comandos/lenguajes y fixtures existentes.

- [ ] Clasificar los 28 comandos como consulta, generación documental o cambio
      ejecutable; definir y verificar TDD/RDD aplicable, sin fingir una ejecución
      por comprobar únicamente que existe la definición de la skill.
- [ ] Probar ODD/SDD, proyectos nuevos/existentes, desarrollo/infraestructura/DevOps,
      idiomas y todos los lenguajes actualmente inventariados. Detectar runners
      por configuración; parser disponible no implica framework de tests instalado.
- [ ] Probar un runner representativo real por ecosistema admitido y declarar los
      ausentes; ejecutar fixtures adversarios sin modelos y una aceptación real
      con modelo y presupuesto acordados. Medir también coste de revisión.

### T1. Producto de terminal y launcher único — 16–24 h

**Modificar:** `src/aikya/cli/main.py`,
`src/aikya/installation/bootstrap/launchers.py` y `coordinator.py`.
**Crear:** `packages/aikya-pi/src/launcher.ts`,
`tests/test_terminal_entrypoint.py` y `packages/aikya-pi/tests/terminal.test.ts`.

- [ ] Fijar en pruebas apertura sin argumentos, ayuda sin modelo, subcomandos
      existentes y selección del proyecto. Mantener un solo propietario del
      ejecutable `aikya`; el paquete Pi no instala otro binario que lo oculte.
- [ ] Abrir Pi mediante argumentos separados, usando el runtime administrado.
      Integrar onboarding, autenticación soportada y resumen TDD/RDD en la TUI.
- [ ] Unificar acceso a mantenimiento desde la CLI preservando compatibilidad con
      `aikya-manage`; probar salida limpia, señales y restauración de la terminal.
- [ ] Verificar el recorrido en macOS, Windows y Linux dentro de la aceptación
      B5: instalación limpia, primera tarea, reanudación, update y desinstalación.
      La matriz completa de instaladores sigue contabilizada en B5.

## Secuencia, coste y límites

Orden de la ruta B: B0 → B1 + R1 → B2 + T1 → B3 + R2 → B4 → B5 + R3.
TDD se usa para construir estas piezas y para el flujo posterior del usuario.
RDD es un componente nuevo; no está validado por la suite actual de Aikya 7.2.2.

| Alcance | Base previa | Incremento | Total antes de reserva |
|---|---:|---:|---:|
| A: adaptadores existentes con RDD, sin terminal autónoma | 92–148 h | 48–80 h | 140–228 h |
| B: terminal Pi reutilizando servicios Aikya | 160–256 h | RDD 48–80 h + launcher 16–24 h | 224–360 h |
| C: reescritura completa sobre Pi | 296–480 h | RDD 48–80 h + launcher 16–24 h | 360–584 h |

Para B, 25 % de reserva = **280–450 h**, unas **7–12 semanas** a 40 h/semana
redondeando hacia arriba. Coste = horas acordadas × tarifa; no se supone una
tarifa. Los tests y la instalación ya previstos no se factorizan dos veces.
Reestimar tras B0, especialmente si Pi requiere otra interfaz o faltan runners.

No se promete ahorro automático de tokens. Recibos, hashes, estado y actualización
local de memoria/HTML no necesitan inferencia; una revisión con modelos sí consume
cuota. Reutilizar evidencia vigente y acotar lecturas; una revisión completa de
varios modelos o una TUI propia quedan fuera del MVP.

## Referencias y validación del plan

TDD sigue el ciclo descrito por
[Martin Fowler](https://martinfowler.com/bliki/TestDrivenDevelopment.html).
Para RDD se inspeccionaron los archivos oficiales de Gentle Shell en el commit
`8e11f0e2fb19af2a28233d1774848f7a3a33bbf1` (4.7.0):
[contrato de revisión](https://github.com/Gentleman-Programming/gentle-shell/blob/8e11f0e2fb19af2a28233d1774848f7a3a33bbf1/skills/_shared/review-ledger-contract.md)
y [coordinador](https://github.com/Gentleman-Programming/gentle-shell/blob/8e11f0e2fb19af2a28233d1774848f7a3a33bbf1/docs/review-coordinator.md).
Se adaptan conceptos; las tareas anteriores no son funciones ya disponibles.

Esta revisión cambia documentación: comprobar enlaces locales, footer único,
sumas, índice y diff. La validación del producto y los tres sistemas se ejecutará
durante la implementación; no presentar pruebas previas como aceptación de v8.

GENERATED BY AIKYA HARNESS

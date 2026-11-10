# Ciclo acotado y continuidad de sesión: ejecución B4

**Objetivo:** ejecutar una tarea ODD/SDD seleccionada mediante el loop de Pi, con
fases observables, límites persistentes y revisión independiente antes de registrar
su finalización. Continuar la ejecución secuencial autorizada del plan vigente.

**Arquitectura:** Pi conserva su loop de herramientas; Python valida selección,
presupuesto, evidencia y checkpoints. Un único run activo por proyecto. Las órdenes
del modelo no conceden permisos ni aprueban checks/revisiones/completaciones.

**Tecnología:** Python, Pi 1.5.0 y Node mínimo 22.19.0.
**Especificación:** [pendientes B](2026-11-08-aikya-v8-pendientes.es.md).

## Restricciones

- Fases exactas: `explore`, `plan`, `implement`, `validate`, `security`, `review`.
  Estado mostrado distinto de fase ejecutada o aprobada.
- Tarea y change_id del mismo autor, intención/aceptación y scope coincidentes;
  selección ODD vigente o las tres etapas SDD aprobadas.
- Una corrección máxima; hasta 6 llamadas del run y 300 segundos por defecto,
  confirmados antes de comenzar. Límites máximos de 20 llamadas y 600 segundos.
  El presupuesto global del proyecto puede detenerlo antes y nunca se reinicia.
- Contabilizar autor, revisor y compactación. Uso desconocido detiene inferencia;
  los tokens del proveedor son observados, no estimaciones de cuota/facturación.
- Cada escritura/check/revisión/completación conserva su confirmación nativa.
  Escape, rechazo, error, evidencia caducada o efecto incierto detienen el avance.
- No llamadas a proveedores reales en este equipo: esa aceptación permanece en F,
  en el entorno externo que el usuario ha reservado para ella.

## 1. Checkpoint y prueba de finalización

Precondición reproducida al cerrar B3: un índice personalizado que conserva el footer
puede sobrescribirse y dejar obsoleto el candidato recién guardado. Unificar el
reconocimiento de la proyección canónica entre layout y RDD, bloquear el primer
efecto ante prosa personalizada y verificar índices válidos en inglés y español.

**Archivos:** crear `services/task_runs.py`, `task_run_inputs.py`,
`task_run_records.py`, auxiliares de lifecycle/revisión/completación y `sdd_completion.py`; ampliar `task_binding.py` y
`runtime_state.py` sin introducir motores ODD/SDD paralelos; reutilizar sus transiciones canónicas.

**Interfaces:** `task_runs.preview(root,change_id,session_id,provider,model,limits,security)` devuelve
selección, modelo elegido por el host, scope, intención y límites exactos;
`start(root,plan,approved=False)` reserva el run. `status(root,session_id)` y
`guard(root,run_id,session_id)` comprueban autor, selección, deadline original,
presupuesto e incertidumbre. Las transiciones locales conservan historial firmado
en `.aikya/pi/task-runs/`; el informe se proyecta en el dossier del change_id.

- [x] Red: sin selección/aprobación/budget; autor o intención distintos; otro run
  activo; deadline/calls agotados; reinicio que intenta borrar gasto; firma alterada.
- [x] Implementar límites sobre el ledger actual, sin otro contador de tokens.
  Conservar el inicio/deadline al reanudar y una única corrección consumible.
- [x] Derivar intención SDD de descripción y aceptación de requisitos referenciados;
  si excede el paquete vigente, exigir dividir la tarea, sin truncar criterios.
- [x] `sdd_completion.preview/apply` exige candidato actual, checks positivos y
  aceptación independiente de esa tarea, reserva antes de `engine.progress`,
  verifica efectos/fingerprints y registra aceptación en esa transición. No aprueba
  automáticamente toda la especificación ni transfiere evidencia tras cambios.
- [x] Green y pruebas de ODD/SDD sobre servicios instalados.

## 2. Conexión al loop y fases

**Archivos:** crear Pi `task-run.ts` y `task-run-policy.ts`; ampliar `runtime.ts`,
`budgeted-inference.ts`, `odd-workflow.ts`, `workflow.ts`, `native-checks.ts`,
`permissions.ts` y registro de fases de comandos.

**Interfaces nativas:** acciones `run`, `run-status`, `resume-run` y `stop-run`
en `/aikya-feature` y `/aikya-implement`, sin registrar un segundo comando canónico.
El run inicia exclusivamente una tarea ya seleccionada y un change_id congelado.
Los comandos administrativos y los nuevos menús describen también `edit` y
`recover-batch`; no requieren inferencia.

- [x] Red: guard async antes del proveedor, límites durante tool loops, modelo que
  insiste tras needs_host_action, cancelación/timeout y máximo de una corrección.
- [x] Usar los hooks públicos de Pi y su cola de follow-up; no iniciar un segundo
  loop Python ni parchear el dispatcher. El orden real de agent_end/settlement se comprobó:
  usar `agent_before_settle` y sus entradas/continue para revisión/corrección; detenerse en confirmación pendiente/rechazada.
- [x] Explorar/planificar contexto acotado, observar Red cuando proceda, implementar
  por herramientas confirmadas y validar checks congelados. Los checks de security
  se eligen explícitamente entre esas definiciones; si no aplican, exigir una razón
  confirmada y visible para el revisor, sin inventar un escaneo satisfactorio.
- [x] Revisar con una sesión independiente, modelo/presupuesto confirmados y paquete
  vigente. Solo changes_requested verificadas pueden alimentar la única corrección.
  Una aceptación permite proponer el registro de tarea; no autoriza entrega.
- [x] Propagar abort a procesos de escritura/check y revisión; conservar reservas
  si hubo efectos o uso desconocidos. Mantener fases visibles en inglés también en
  inicialización, generación y validación local, sin fingir ejecución de modelos.
- [x] Green con transportes de proveedor deterministas y SDK real; costes de fixture
  separados de uso real y pruebas de no inferencia administrativa.

Al cancelar el registro final, conservar un checkpoint firmado de la revisión vigente,
candidato y aplicabilidad security de este run. Reanudar solo ese registro local si
los efectos/evidencias permanecen idénticos; no repetir checks ni llamadas del modelo.
La prueba real de terminal detectó el fallo previo y las regresiones lo reproducen.

## 3. Reanudación, compactación y aceptación integrada

**Archivos:** `session.ts`, `session-roles.ts`, `project.ts`, controlador B4,
pruebas de sesiones y la guía del runtime privado.

- [x] Red: un transcript viejo grande/corrupto no debe impedir crear una sesión
  nueva; un revisor más reciente no se adopta como autor. Reanudar solo la identidad
  autorizada, conservando selección, gasto y deadline; no reutilizar grants.
- [x] Compactación explícita, medida y sujeta al presupuesto; conservar task/run,
  intención, rutas y evidencia en checkpoint local sin enviar toda la memoria.
  Cambiar de sesión no adopta automáticamente autoría ni evidencia ajena.
- [x] Recorrido completo de una tarea ODD y otra SDD, con documentación confirmada
  antes de checks/revisión finales, seguimiento de phases y registro de tarea.
- [x] Mantener el límite de revisión completa de 6.000 bytes hasta implementar y
  verificar un contrato ampliado explícito; un parche grande no acredita una revisión
  completa de un archivo grande. Probar escalado y no ocultar esa limitación.
- [x] Regresión Python completa, SDK/TypeScript, paquete instalado y terminal;
  informe y commit revisable antes de C. Proveedores/sistemas nativos pendientes
  no se marcan completados por la ejecución de fixtures o configuración de CI.

GENERATED BY AIKYA HARNESS

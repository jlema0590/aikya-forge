# Plan de aceptación interactiva y publicación de Forge 0.2.0

Fecha: 19 de noviembre de 2026. Base: 7d8fbc4. Rama existente:
feat/forge-0.2.0-completion. Ejecución secuencial autorizada al pedir empezar los
seis pendientes; no crear worktrees ni migrar instalaciones v7.

**Objetivo:** cerrar defectos de arranque, reproducibilidad, validación interactiva
y preparación de entrega, manteniendo pendientes las pruebas externas no realizadas.
**Arquitectura:** reutilizar verificación del payload, Pi 1.5.0, recibos y gate de
publicación. Incorporar herramientas inmutables al payload, sin descargas al arrancar.
**Tecnologías:** Python 3.10–3.13, Node >=22.19.0, TypeScript, binarios oficiales
fd 10.5.2/ripgrep 15.2.0, CI nativa de siete objetivos.
**Especificación:** petición del usuario de empezar los seis puntos enumerados en
la conversación; procedimiento de proveedor y dossier pendientes en validation/.

## Restricciones

- Documentos nuevos dentro de aikya/docs/, índice de Markdown y footer único.
- Modelos reales solo en el otro entorno acordado; no leer claves ni usar cuentas
  locales como prueba de procedencia. No inventar ahorro ni completar el dossier.
- La publicación solicitada depende de evidencias actuales y de los gates existentes;
  no eliminar restricciones de main, hashes, procedencia o revisión para publicarla.
- Nuevos binarios: origen oficial/versionado, SHA-256, archivo/arquitectura/licencias,
  verificación antes de efectos y prueba nativa. No ejecutar binarios de proyecto.
- Conservar archivos personalizados y operaciones inciertas; no repetir efectos.

## Riesgos que deben quedar cubiertos

1. Caché bin/ del proyecto puede prevalecer sobre PATH en Pi: rechazar cachés no
   revisadas antes de importar/montar la UI; conservar sus bytes sin ejecutarlos.
2. Herramienta ausente/corrupta o de otra arquitectura: fallo previo a activación,
   nunca fallback a descarga ni a otra arquitectura; --help permanece sin efectos.
3. Operación de host detenida o rechazada: diagnóstico acotado sin mensajes,
   rutas, prompts, stdout ni secretos; nunca reintento automático de escritura.
4. TTY lenta/cancelación/resize: resultados delimitados, restaurar terminal y cerrar
   solo procesos propios; distinguir simulación, PTY y aceptación visual humana.
5. Evidencia externa anterior a un cambio: rechazar fingerprint/versiones obsoletos;
   un paquete de pruebas preparado no es aceptación ni publicación.

## 1. Arranque offline e identidad

Archivos: crear installation/managed_tools.py, resources/terminal-tools.json y
pruebas test_managed_tool_inputs.py; integrar managed_bundle.py y cli/terminal.py.
Añadir validación de caché en el launcher TypeScript; usar runtimeVersion para
ayuda/título y probar las salidas mediante launcher/SDK reales.

Interfaces: load(target, source=None) valida el catálogo; prepare(target, assets,
fetch=False) verifica bytes; install(recipe, raws, downloads, payload) conserva
licencias/binarios; environment(runtime, base) antepone solo directorios verificados.

- [ ] Añadir pruebas que fallen: ausencia/corrupción/origen/arquitectura, caché
  de proyecto y versión/título heredados; verificar que no hay efectos ni ejecución.
- [ ] Integrar fd/rg oficiales para siete objetivos; Linux usa variantes musl
  revisadas, sin depender de la glibc del equipo de construcción.
- [ ] Probar versiones reales y búsqueda/autocompletado con PATH limpio, sin red.
- [ ] Actualizar procedencia/licencias/operación y guardar commit revisable.

## 2. Diagnóstico y reproducción de Windows

Archivos: servicios/runtime_state.py y nuevo helper de diagnóstico acotado, host.ts,
task-run.ts, tests/test_service_host_failures.py y prueba SDK de reanudación.

Interfaz: respuesta negativa mantiene error público y añade solo categoría/stage
estáticos acotados. HostOperationError conserva operación/categoría segura; el
resultado needs_host_action muestra esos metadatos sin repetir efectos.

- [ ] Probar fallos reales de proceso/respuesta y privacidad antes de implementar.
- [ ] Instrumentar fallo de reanudación con estado y transporte de fixtures sintéticos.
- [ ] Reproducir en Windows; corregir únicamente la causa observada y añadir su
  regresión. Si no se reproduce, registrar causa desconocida y evidencia disponible.
- [ ] No ampliar plazos, omitir validaciones ni aceptar el reintento como corrección.

## 3. Aceptación interactiva

Archivos: crear scripts/ci/terminal_pty_acceptance.py y pruebas de su recolector;
integrar comprobaciones de herramientas en native_terminal_acceptance.py.

Interfaz: recolector acotado del PTY del binario instalado registra inicio,
comandos, presupuesto, confirmación de tema y resize sin invocar modelos.

- [ ] Probar recolector, límite de bytes/tiempo y cierre de sus procesos propios.
- [ ] Ejecutar PTY real en macOS/Linux; en Windows comprobar contratos nativos y
  ejecutar ConPTY con colas acotadas y cierre de los procesos propios; mantener
  revisión visual y éxito de ConPTY pendientes hasta contar con evidencia real.
- [ ] Conservar capturas sin ocultar avisos; no convertir headless en revisión visual.
- [ ] Revisar teclado, tema, cancelación y estado retenido donde el host lo permita.

## 4. Ensayos externos

Archivos: procedimiento y dossier existentes; crear preparador del paquete de
aceptación externo y prueba de procedencia/salida nueva.

- [ ] Preparar paquete sin claves, con versión/fingerprint actuales, nueve casos,
  tres observaciones comparativas y comandos verificables para el otro entorno.
- [ ] Rechazar salida existente y evidencia obsoleta; no generar observaciones falsas.
- [ ] Incorporar resultados reales solo cuando estén disponibles y revisados.

## 5. Revisión y CI de la PR

- [ ] Ejecutar regresión completa apropiada, SDK en Node 22/26, wheel instalado,
  contratos/índice/footers/calidad y nuevos casos negativos.
- [ ] Empujar un conjunto coherente de cambios para una nueva matriz nativa,
  reduciendo reinicios; revisar fallos y resultados reales de todos los trabajos.
- [ ] Revisar el diff y actualizar PR/evidencias; distinguir código validado de
  documentación posterior, y mantener los pendientes externos explícitos.

## 6. Entrega pública condicionada

- [ ] Descargar siete artefactos actuales del mismo commit, comprobar huella única,
  ensamblar y verificar checksums/entradas universales sin publicar.
- [ ] Revisar el estado actual del proveedor/visual y la rama requerida por release.
- [ ] Publicar release, URL corta y Pages únicamente cuando esos gates estén
  satisfechos; si falta evidencia, dejar paquete concreto y motivo de bloqueo.

## Avance contrastado del 19 de noviembre

- Implementados los componentes offline, identidad actual y rechazo de cachés.
  La revisión independiente añadió búsqueda segura en Windows y rechazo de rutas
  ambiguas antes de activación. La matriz nativa debe repetirse con esa corrección.
- Diagnósticos acotados implementados y probados, incluido doble fallo al detener.
  La ejecución 97daaf8 pasó las seis combinaciones OS/Node; la causa intermitente
  anterior sigue desconocida y no se declara corregida por una repetición verde.
- PTY macOS real verifica autocompletado recursivo, teclado, tema y resize. Se añade
  el lanzador instalado con PATH vacío a los siete ciclos nativos. ConPTY requiere
  confirmar la corrección de handles mediante ejecución real en Windows.
- Regresión congelada de 24fb92b: 1.306 pruebas Python, sin fallos/errores; fallback
  opcional probado aparte y 11 casos de wheel instalado correctos. La revisión
  posterior requiere resultados nuevos; no se reutiliza ese total como prueba final.
- Paquete externo preparado sin ejecutar ensayos. Cada repetición requiere copia
  prístina/ledger propio. Regenerar el paquete tras fijar la nueva huella de código.
- Entrega pública pendiente de matriz actual, revisión visual y resultados reales
  del otro entorno. No se ha publicado release, etiqueta estable ni Pages.

GENERATED BY AIKYA HARNESS

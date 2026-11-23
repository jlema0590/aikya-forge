# Plan de configuración y panel lateral de Forge

**Objetivo:** añadir configuración interactiva de proveedores, apariencia y un
panel derecho con flujo y consumo observado, dentro de la terminal de Forge.
**Arquitectura:** componer la TUI pública de Pi, reutilizar su autenticación y el
ledger de Aikya. Las preferencias locales contienen únicamente opciones no secretas.
**Tecnologías:** TypeScript, Pi 1.5.0, Node >=22.19.0 y el host Python existente.
**Especificación:** petición del usuario del 22 de noviembre: proveedores, temas,
colores, letras, flujo lateral y consumo de Claude/Codex.

## Restricciones

- Trabajar desde develop en feat/forge-settings-sidebar, sin worktrees.
- Credenciales mediante login nativo, sin incluirlas en mensajes ni preferencias.
- Ninguna llamada de inferencia al configurar, renderizar o refrescar el panel.
- Conservar los permisos, presupuestos y binding del modelo de cada sesión.
- Diferenciar presupuesto del proyecto, contexto estimado y cuota del proveedor.
- Mostrar unavailable/stale cuando falte fuente; no convertir tokens a cuota.
- Familia y tamaño de letra pertenecen al emulador; Forge configura estilo ANSI.
- Mantener fuentes, instrucciones y documentación técnica en inglés.

## Riesgos y comprobaciones

1. Terminal estrecha: colapsar el lateral sin tapar texto, foco o autocompletado.
2. Datos incompletos: no mostrar porcentajes de atribución como totales completos.
3. Login cancelado o fallido: ninguna clave en transcript ni mensajes de error.
4. Preferencias corruptas/enlazadas: conservar bytes y rechazar sobrescritura.
5. Modelo distinto: guardar selección para el siguiente arranque, sin cambiar el
   binding de una sesión o activar inferencia sin presupuesto disponible.

## Tarea 1: preferencias y paleta

Archivos: src/console-preferences.ts, src/console-appearance.ts y
tests/console-preferences.test.ts dentro de packages/aikya-pi/.
Interfaz: ConsolePreferences.load/save, configuración validada con theme,
accent/text/muted, textStyle, sidebar y provider/model opcionales.

- [x] Escribir y ejecutar casos rojos de persistencia, colores inválidos,
  secretos/campos desconocidos, archivo corrupto y symlink.
- [x] Implementar escritura atómica local y construcción de Theme desde la paleta
  instalada, conservando el resto de tokens de Pi.
- [x] Verificar reinicio y aplicación del estilo sin modificar el emulador.

## Tarea 2: consumo y composición lateral

Archivos: src/console-sidebar.ts, src/console-layout.ts, src/local-commands.ts,
src/usage.ts y tests/console-sidebar.test.ts.
Interfaces: renderSidebar(snapshot,width,now), ForgeWorkbench.render(width),
local.viewUsage() devuelve budget y vistas del QuotaCache existente.

- [x] Escribir y ejecutar casos rojos para cifras conocidas/desconocidas,
  grupos parciales, cuotas antiguas y anchos con ANSI/Unicode.
- [x] Mostrar fase, estado, modelo, contexto estimado, presupuesto local,
  desglose author/reviewer y Claude/Codex, cuotas con origen y antigüedad.
- [x] Componer contenido y lateral en columnas reales; colapsar en terminales
  estrechas, conservar cursor y reenviar coordenadas del ratón.
- [x] Refrescar por eventos; el reloj visual solo repinta datos en memoria.

## Tarea 3: panel de configuración y proveedores

Archivos: src/console-settings.ts, src/provider-settings.ts, src/secret-input.ts,
src/extension.ts, src/editor.ts, src/runtime.ts y src/launcher.ts;
tests/console-settings.test.ts.
Interfaz: /aikya-settings abre Providers, Appearance, Sidebar y Flow; login usa
ModelRuntime.login y entrada secreta enmascarada; selección guardada para reinicio.

- [x] Escribir y ejecutar casos rojos con SDK real: comando sin inferencia,
  selección local, cancelación y preservación de los límites de ejecución.
- [x] Implementar selección de proveedores/modelos del catálogo fijado, login
  explícito, eliminación de autenticación confirmada y selección persistida.
- [x] Añadir temas, colores HEX, normal/bold/italic y lateral on/off.
- [x] Reutilizar estado y stop-run del flujo existente; sin ejecutar tareas nuevas
  desde render ni relajar confirmaciones de reanudación.

## Tarea 4: integración y evidencia

- [x] Ejecutar typecheck y npm test completos; registrar fallos por nombre.
- [x] Verificar Node mínimo, contratos Python relacionados y documentación.
- [x] Ejecutar terminal PTY real con configuración, tema, lateral, resize y salida;
  conservar captura que identifique que no se invocó ningún modelo real.
- [x] Actualizar guía, changelog e índice. Las evidencias externas previas no
  acreditan el nuevo runtime; proveedores reales siguen en el entorno acordado.

## Resultado y límites

Implementación local terminada. Dos suites completas de 115 casos (114 correctos,
una omisión exclusiva de Windows por suite), typecheck, 16 regresiones Python y
PTY real de macOS correctos. Las capturas son replay de salida PTY, no fotografías
ni aceptación humana de dispositivos. Ver el
[informe](../validation/2026-11-22-forge-console-settings.md).

La rama nueva requiere CI nativa de Windows/Linux y ensayos reales de proveedor en
el entorno acordado. El antiguo fallo de limpieza del observador en Windows sigue
separado; esta funcionalidad no se presenta como su corrección. No se publica release.

GENERATED BY AIKYA HARNESS

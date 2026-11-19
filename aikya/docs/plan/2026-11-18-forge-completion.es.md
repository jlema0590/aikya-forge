# Plan de cierre de Aikya Forge 0.2.0

Fecha: 18 de noviembre de 2026. Base: Forge 0.1.0, commit 43a71ea.
Rama: `feat/forge-0.2.0-completion`. Ejecución secuencial autorizada por el usuario.

**Objetivo:** completar el producto nuevo sobre Pi: instalación, memoria, skills,
control de consumo, aceptación y preparación de publicación. La migración real
desde Harness v7 queda expresamente fuera del alcance por decisión del usuario.
**Arquitectura:** reutilizar el núcleo Python, Pi, contratos firmados y almacenes
actuales. No añadir un segundo orquestador, memoria global de proyectos ni shell
libre. Separar código implementado, aceptación local y aceptación externa.
**Tecnologías:** Python 3.10–3.13, TypeScript, Pi 1.5.0, Node >=22.19.0,
.NET SDK >=8 para el aislamiento de artefactos de sus validadores.
**Especificación:** petición de implementar los pendientes del resumen de Forge,
excepto migración real desde v7; planes v8 importados como contexto histórico.

## Restricciones comunes

- Planes, bugs, features y evidencias nuevos en `aikya/docs/`; índice y footer único.
- Memoria local por proyecto y mantenimiento sin inferencia; modelos y presupuestos
  explícitos. Las pruebas reales de proveedor permanecen en el otro entorno acordado.
- No ocultar código en `bin/obj`: dirigir salidas aprobadas a directorios privados
  de cada ejecución y mantener íntegra la instantánea de todas las fuentes.
- Un propietario por ejecutable; conservar personalizaciones, respaldos y efectos
  inciertos. No crear worktrees ni migrar instalaciones v7 del usuario.
- Publicación solo de artefactos verificados con versión/canal explícitos. No prometer
  una URL corta activa ni compatibilidad nativa por tener un workflow configurado.

## Revisión transversal

1. Código relevante/tracked en directorios de build: nunca excluirlo por su nombre.
2. Cambios simultáneos o interrupciones: negar operación obsoleta y conservar diario.
3. Skills globales compartidas: una retirada global no borra copias de proyectos.
4. Parser/SDK/proveedor ausente: informar fallback/no disponible, nunca éxito inventado.
5. Actualización y recuperación: no reinstalar skills retiradas ni reutilizar permisos.

## Entregas

### 1. Corrección .NET y artefactos de validación

Archivos: `review/definitions.py`, `review/executor.py`; crear `review/artifacts.py`
y `tests/test_review_artifacts.py`. Mantener candidato, recibo y firma existentes.
Interfaces: validar y expandir `{artifacts}` a un destino privado único de la ejecución;
.NET build/test/restore/publish requiere `--artifacts-path {artifacts}` revisado.

- [x] Red: resultado generado no debe cambiar candidato; código real en bin/obj
  continúa inventariado; definición .NET sin aislamiento se rechaza antes de ejecutar.
- [x] Green: expansión privada ligada a run_id, límites y enlaces rechazados.
- [x] Ejecutar build .NET real offline y contratos de checks, recuperación y revisión.
- [x] Documentar evidencia y cerrar commit de la corrección.

### 2. Retirada y restauración de skills nativas

Archivos: servicios de skills actuales, nuevo módulo de retirada, CLI y adaptador Pi;
registro canónico y plantilla `/aikya-uninstall-skills`. Reutilizar paquetes inmutables,
locks, registros, auditoría y consentimiento existentes. Adaptar la propuesta antigua
al producto Forge antes de añadir soporte a assets de clientes heredados.

- [x] Red: preview sin efectos, ámbitos aislados, nombres protegidos, conflicto de
  hashes, interrupción, restauración y rechazo sin confirmación.
- [x] Green: deselección recuperable de paquetes propios, sin ejecutar código importado;
  mantener archivos personalizados y versiones exactas; registrar resultado veraz.
- [x] Integrar comando/CLI, pruebas instaladas y documentación. No afirmar retirada de
  plugins ni de copias externas que Forge no controla.

### 3. Distribución nueva de Forge

Archivos: `installation/managed_*`, scripts CI y workflows de Forge; builder de parsers.

- [x] Resolver faltantes de lanzamiento/update/rollback por evidencia; excluir pruebas
  de migración real v7 del criterio de aceptación del producto nuevo.
- [x] Incluir parsers binarios compatibles fijados con hashes; fallback explícito si
  un objetivo carece de rueda compatible, sin compilar fuentes ni cambiar ABIs.
- [x] Construcción y ciclo nativos en CI macOS/Linux/Windows; contrastar resultados
  remotos disponibles, incluyendo permisos, rutas Unicode y datos conservados.
- [x] Preparar publicación revisada, checksum/manifest y Pages del nuevo repositorio;
  mantener entrega/publicación condicionada a sus comprobaciones reales.

### 4. Memoria, HTML y themes instalados

Archivos: motores existentes y pruebas de integración/navegador; informe nuevo.

- [x] Crear/editar/renombrar/borrar fuentes externas; comprobar índice y HTML sin IA.
- [x] Notas, aislamiento, corrupción, reinicio/update/rollback y preferencias persistentes.
- [x] Cobertura derivada del catálogo y capacidades realmente instaladas; no confundir
  extensión inventariada con símbolos analizados o build ejecutado.
- [x] Registrar recorridos nativos en los siete objetivos, sin extrapolar aceptación visual.

### 5. Uso y aceptación de proveedor en entorno externo

Archivos: servicios/terminal de uso y sesiones existentes; nuevo dossier de aceptación.

- [x] Preparar casos reproducibles para presupuesto, cancelación, compactación,
  reanudación y procedencia de métricas, con datos anonimizados y sin claves.
- [x] Ejecutar las partes deterministas locales. Las pruebas de proveedor real y la
  comparación de consumo se ejecutan en el otro entorno, con modelo/caché fijados.
- [ ] Registrar evidencia externa cuando exista; ausencia de cuota permanece desconocida.

### 6. Matriz final, documentación y versión

- [x] Derivar comandos/extensiones/runners de los catálogos y verificar denegaciones,
  ODD/SDD, en/es y perfiles nuevos/existentes en entornos temporales.
- [x] Ejecutar regresión local Python/Pi, wheel instalado, navegador y calidad del diff;
  conservar por separado los resultados nativos y los ajustes de fixtures Windows.
- [x] Actualizar README en/es, changelog, versión propia 0.2.0 e índice; sustituir
  el plan activo v8 por este plan, preservando historia y pendientes externos.
- [x] Registrar fuentes congeladas, resultados/omisiones y commits revisables.

## Resultado verificado

[El informe](../validation/2026-11-18-forge-completion.md) registra 1.288 pruebas
Python sin fallos (una omisión comprobada aparte), 94/94 contratos SDK en las seis
combinaciones de sistema/Node, 110 comprobaciones de navegador y wheel instalado.
Las matrices de Python, instalación limpia y los siete ciclos nativos pasaron en
40d7d8e. Cada ciclo comprobó 29 comandos y 24 perfiles sin llamadas a proveedores.

Los siete artefactos descargados comparten commit de construcción y huella. El
ensamblado local pasó y sus 16 checksums se verificaron. La diferencia CRLF de
Windows del pase anterior está corregida; ese conjunto antiguo sigue rechazado.
Un intento local restringido falló por permisos de puertos; la repetición completa
con ese permiso pasó sin cambios. El informe conserva ambos resultados.

## Pendientes de aceptación y salida pública

- [ ] Ejecutar los ensayos reales de proveedor y comparación de consumo en el otro
  entorno, manteniendo modelo/caché y evidencia de procedencia. No inventar ahorros.
- [ ] Completar revisión visual, teclado, redimensionado, temas y sesiones reales en
  macOS/Windows/Linux. Las capturas locales actuales son salida PTY de macOS ARM,
  en modo sin modelo; no equivalen a esa aceptación completa.
- [ ] Resolver el aviso de fd ausente en modo offline y comprobar fd/rg en equipos
  limpios: autocompletado y fallback, con entradas revisadas y hashes si se empaquetan.
  Conservar el bloqueo de descargas no revisadas al arrancar.
- [ ] Sustituir el título heredado Aikya v8 por la identidad/versionado actual de Forge.
- [ ] Identificar la causa intermitente de la reanudación final de Windows Node 26:
  falló una vez y pasó al repetir sin cambios; no se declara corregida por ello.
- [ ] Revisar/aprobar la PR y publicar release/instalador corto/Pages solo cuando
  corresponda, superadas las validaciones. La preparación actual no publica nada.

El dossier externo sigue pending y bloquea publicación. La migración real desde v7
permanece fuera del alcance. El producto es nuevo y usa versionado propio 0.2.0.

GENERATED BY AIKYA HARNESS

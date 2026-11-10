# Revisión de marca e instalación de Aikya Forge

Fecha: 2026-11-10. Alcance: inventario textual de todos los archivos versionados y
revisión dirigida de metadatos, CLI, generación documental, compatibilidad,
constructores, instaladores y CI. No equivale a una auditoría completa de seguridad
ni a una ejecución de todos los flujos del producto.

## Hallazgos

El repositorio tiene 1.475 archivos versionados. La búsqueda sin distinguir
mayúsculas encuentra 10.539 apariciones de `harness` en 909 archivos. El recuento
corresponde al estado anterior a incorporar esta revisión y su plan.

| Área | Archivos con coincidencias |
|---|---:|
| `src/aikya/` | 303 |
| `examples/` | 285 |
| `aikya/` | 177 |
| `tests/` | 97 |
| `docs/` | 11 |
| `scripts/` | 9 |
| `.github/` | 8 |
| `packages/aikya-pi/` | 8 |
| Contratos, metadatos y otros archivos de raíz | 11 |

La portada, las direcciones operativas de actualización y la versión `0.1.0` ya
identifican Forge. `pyproject.toml` todavía publica `aikya-harness`; los consumidores
de metadatos y descarga esperan `aikya_harness-*.whl`. Cambiar únicamente el nombre
del paquete dejaría inconsistentes la instalación y las comprobaciones nativas.

`src/aikya/documentation/layout.py` genera la firma antigua. Servicios de edición,
composición y memoria también la usan para validar propiedad y proteger contenido
personalizado. La firma nueva necesita reconocimiento explícito de documentos
heredados y pruebas de actualización; sustituirla indiscriminadamente invalidaría
contenido existente. `AGENTS.md` exige actualmente la firma antigua: el plan
propone cambiar ese contrato junto con sus consumidores.

`.harness/`, `harness.json` y `aikya/scripts/harness/` son interfaces funcionales
utilizadas por perfiles, memoria, comprobaciones, recursos y migraciones. Se
conservarán como rutas de compatibilidad en esta entrega, según el contrato del
repositorio. El cambio de marca no debe mover automáticamente datos de proyectos.
Los documentos históricos, catálogos de migración y fixtures con hashes fijados
requieren conservar sus identidades originales. Las atribuciones y nombres de
proyectos de terceros tampoco son marca propia de Forge.

## Instaladores existentes

Hay dos familias distintas:

- `scripts/ci/build_installers.py` crea el instalador Python heredado. Requiere
  Python previamente instalado y no entrega por sí solo la terminal Pi completa.
- `scripts/ci/build_terminal_bundle.py` y `src/aikya/installation/managed_bundle.py`
  reúnen Python, Node y Pi en un paquete nativo. Los scripts generados comprueban
  plataforma y SHA-256 antes de instalar. El usuario final no necesita preparar
  Python, Node ni npm.

El constructor nativo solo ejecuta y valida la plataforma del equipo anfitrión.
`managed_entries.build(version, assets, destination)` ya puede generar entradas
que incluyen únicamente las plataformas presentes en un conjunto de archivos
verificados. No es necesario crear un segundo motor de instalación.

Las recetas declaran macOS ARM64/x64, Windows ARM64/x64, Linux GNU ARM64/x64 y
Linux musl x64. Una receta disponible no demuestra una instalación nativa válida.
La primera matriz propuesta cubre macOS ARM64/x64, Windows x64 y Linux GNU x64;
las demás variantes requieren su propia ejecución antes de anunciarlas.

Los workflows heredados de publicación y Pages siguen restringidos al repositorio
anterior. Sustituir ese identificador por Forge activaría comportamientos ajenos
a generar instaladores locales. La propuesta agrega construcción y pruebas con
artefactos descargables, manteniendo separada la publicación de releases/Pages.
No se ha consultado el estado remoto de releases: no se afirma que exista o falte
una descarga pública actual.

## Comprobaciones observadas

```sh
PYTHONPATH=src:tests python3.13 -B -m unittest test_managed_bootstrap_entries test_managed_distribution_output test_managed_bundle_builder test_managed_runtime_inputs -v
```

Resultado: 14 pruebas aprobadas en macOS. Incluyen vista previa sin Python/Node,
rechazo de archivos corruptos, conservación de salidas existentes, ensamblado de
manifiestos y selección explícita de plataformas. Una prueba inspecciona el script
Windows; no lo ejecuta en Windows. No se han ejecutado instalaciones reales nuevas,
la suite completa, compilaciones nativas ni las pruebas TypeScript.

El entorno dispone de Python 3.13.18 y Node 26.12.1. No hay paquete Aikya instalado,
frontend `build`, backend `setuptools`, dependencias npm locales ni PowerShell
detectado. El Python predeterminado es 3.15.1; para las comprobaciones se eligió
explícitamente Python 3.13. Los builds necesitan preparar las dependencias de
desarrollo y descargar o proporcionar componentes fijados.

El único cambio previo del usuario es `.gitignore`, con las entradas `.claude/` y
`.git/` añadidas. No se ha modificado durante esta revisión.

## Propuesta revisable

El [plan de implementación](../plan/2026-11-10-forge-brand-installers.es.md)
define el cambio de marca, sus excepciones de compatibilidad y los instaladores
sencillos que reutilizan el motor nativo existente.

GENERATED BY AIKYA FORGE

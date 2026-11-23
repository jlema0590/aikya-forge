# Aikya Forge

[English](README.md) | [Español](README.es.md)

**Flujos de ingeniería, memoria local por proyecto y ejecución controlada de IA desde la terminal.**

Aikya Forge combina un núcleo Python y una terminal interactiva basada en Pi.
Incorpora los comandos, las plantillas y los controles de Aikya en un repositorio
con versionado independiente. Su versión de desarrollo actual es **0.2.0**.

La aceptación de la instalación y la terminal se registra por plataforma en el
[informe de validación](aikya/docs/validation/2026-11-19-interactive-acceptance.md). Las pruebas
con proveedores reales constituyen una condición separada de publicación. El código
disponible no implica una release ni un instalador corto publicado.

## Inicio rápido desde el código

Requisitos: Python 3.10–3.13 con pip/venv, Node.js 22.19.0+ con npm y Git.
Se recomienda Python 3.13 para el entorno de pruebas de desarrollo.

```sh
git clone --branch develop https://github.com/jlema0590/aikya-forge.git
cd aikya-forge
python3 -m venv .venv
. .venv/bin/activate
python -m pip install 'setuptools>=77' wheel build
python -m pip install --no-build-isolation -e ".[terminal]"
npm --prefix packages/aikya-pi ci --ignore-scripts --no-audit --no-fund
```

En Windows PowerShell, crea y activa el entorno con estos comandos y ejecuta
después los mismos comandos `python -m pip` y `npm` del bloque anterior:

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Elige un directorio de proyecto existente y abre la terminal de desarrollo:

```sh
aikya terminal --runtime-dir ./packages/aikya-pi --target /ruta/absoluta/al/proyecto
```

La opción explícita del runtime de código es necesaria hasta instalar un paquete
nativo administrado. Ejecutar `aikya` sin opciones utiliza la terminal administrada
que ya esté instalada. La inferencia requiere configuración, credenciales y un
presupuesto local positivo; abrir la terminal no implica llamar a un modelo.

## Configuración y control del flujo

Abre `/aikya-settings` o pulsa **F2** para conectar un proveedor del catálogo local,
elegir el modelo del siguiente arranque, configurar temas claro/oscuro y colores
HEX, elegir texto normal/negrita/cursiva y mostrar u ocultar el lateral derecho.
La familia y el tamaño de letra se configuran en la aplicación de terminal.

El tema **Aikya Forge** (`aikya`) utiliza el azul marino, cian y turquesa del logo
original. Es el tema inicial para proyectos nuevos; conserva las selecciones ya
existentes. El arranque dibuja **Aikya** con `pyfiglet` 1.0.4 y fuentes ASCII slant/small,
según el ancho disponible. La instalación nativa incluye librería, fuentes y
licencia para funcionar sin conexión; desde código se instala el extra `terminal`.
El núcleo Python sin dependencias mantiene una alternativa de texto simple.
El rótulo se guarda en caché local y no llama a modelos. El arranque conserva
el nombre Aikya Forge legible. Se elige con `/aikya-theme aikya` o Appearance.

El bloque Project & Git del panel derecho muestra el proyecto, la rama y el usuario de
`git config user.name`. No muestra el correo ni remotos. La rama se actualiza desde
la caché del SDK; no ejecuta Git al repintar. El usuario se consulta al iniciar
la sesión. Sin Git o sin configuración se indican valores no disponibles.
En terminales estrechas, los datos se conservan en el resumen inferior.

El lateral reserva sus propias columnas para la fase, controles del flujo, tokens
y llamadas locales, porcentajes de presupuesto y contexto estimado, y atribución
de Claude/Codex y los roles author/reviewer. La cuota de cuenta solo aparece si
se observa en las cabeceras del proveedor, con antigüedad y estado obsoleto;
si no existe esa fuente, se indica como no disponible. Configurar o repintar el
panel no invoca modelos. La selección guardada requiere presupuesto disponible y
no cambia el modelo de una sesión activa. Consulta la
[guía del panel](aikya/docs/features/forge-console-settings.md).

## Componentes

| Componente | Función |
|---|---|
| Núcleo Python (`src/aikya/`) | Inicialización, metodología, pruebas, memoria, instalación y evidencias persistentes. |
| Terminal Pi (`packages/aikya-pi/`) | Comandos interactivos, confirmaciones, temas, selección de modelos y sesiones acotadas. |
| Adaptadores de comandos | 29 flujos canónicos con su cobertura nativa y sus límites documentados. |
| Memoria local | Inventario incremental, símbolos en lenguajes compatibles, notas revisadas, observación y visualización HTML. |
| Plantillas | Documentos incluidos que se seleccionan según el flujo y el tipo de proyecto. |
| Skills | Paquetes inertes elegidos expresamente, fijados por versión y administrados por proyecto o globalmente. |

ODD y SDD organizan el trabajo. TDD controla los cambios de comportamiento; RDD
significa **Receipt Driven Development**, con recibos de ejecución y evidencias
de revisión. Pruebas, revisión independiente y aprobación de entrega son decisiones separadas.

## Comandos y datos locales

Utiliza `/aikya-init` para un proyecto nuevo o `/aikya-analyze` para uno existente;
elige ODD o SDD durante la inicialización. `/aikya-memory` ofrece las funciones de
memoria local. El [informe de cobertura](aikya/docs/validation/2026-11-08-pi-command-coverage.md)
detalla todos los comandos canónicos y sus límites nativos actuales.

Cada proyecto conserva su memoria y sus sesiones. Los documentos generados se guardan
en `aikya/docs/` y el estado privado del runtime en `.aikya/`. Actualizar el índice o
el HTML utiliza procesamiento local, sin llamadas a modelos. El control local de
consumo no inventa porcentajes de la cuota de suscripción del proveedor.

## Distribución nativa administrada

El constructor para desarrolladores reúne Python, Node y Pi fijados y verificados.
Incluye fd/ripgrep revisados para autocompletado y búsqueda offline; al arrancar
no descarga herramientas ni ejecuta binarios de la caché del proyecto.
Genera instaladores shell/PowerShell vinculados a sumas de comprobación y permite
instalación/actualización explícitas, rollback conservado y desinstalación conservadora.

```sh
python scripts/ci/build_terminal_bundle.py --version 0.2.0 --output ../forge-native-0.2.0 --fetch-components
```

El directorio de salida debe ser nuevo. La construcción descarga componentes públicos
y paquetes npm fijados, y solo construye para la plataforma nativa compatible actual.
No publica una release. Consulta la
[guía de distribución nativa](aikya/docs/deployment/pi-managed-terminal.md) y el
[registro de traslado a Forge](aikya/docs/changes/REQ-20261110-f0900100.md).
La URL corta de instalación de Forge se documentará cuando esté desplegada y validada.

## Desarrollo y validación

```sh
python -m unittest discover -s tests -p 'test_*.py' -v
npm --prefix packages/aikya-pi run typecheck
npm --prefix packages/aikya-pi test
python scripts/ci/release_contract.py check
python -m build --no-isolation
```

Los analizadores opcionales se instalan con `python -m pip install '.[code-index]'`.
Los lenguajes sin analizador semántico disponible conservan un inventario de archivos;
el informe no atribuye símbolos que no haya podido verificar.

```text
src/aikya/             Paquete Python y recursos incluidos
packages/aikya-pi/     Terminal Pi y pruebas TypeScript
tests/                Contratos Python y de navegador
scripts/ci/           Validación y construcción de distribuciones
aikya/docs/           Planes, arquitectura, bugs, cambios y evidencias
examples/             Perfiles y documentación de ejemplo
```

## Versionado y compatibilidad

`VERSION` y el paquete Pi están en **0.2.0**, tras la importación inicial 0.1.0. Las siguientes versiones de Forge
seguirán versionado semántico independiente. El [changelog](CHANGELOG.md) registra
los cambios de Forge; el [histórico heredado](aikya/docs/history/harness-CHANGELOG.md)
conserva los cambios del Harness.

En esta primera importación se mantienen los comandos, los módulos Python (`aikya`)
y el nombre de distribución Python (`aikya-harness`) por compatibilidad. Las direcciones
operativas de actualización apuntan al nuevo repositorio. Se conservan las identidades
v8 para compatibilidad explícita, sin alterar la numeración propia de Forge.

Los workflows heredados de publicación siguen limitados al Harness. Forge incluye
una matriz de construcción/aceptación de siete destinos y preparación manual de releases.
La publicación está desactivada por defecto y exige main, pruebas nativas y evidencia
revisada de proveedor real. Este cambio no publica una release estable ni la URL de Pages. El
[índice documental](aikya/docs/indice.md) conserva planes y evidencias anteriores;
las referencias a v7/v8 de los registros históricos describen aquellas versiones.

## Licencia

MIT. Consulta [LICENSE](LICENSE) y los [avisos de terceros](THIRD_PARTY_LICENSES.md).

## Administración y aceptación de Forge

`/aikya-uninstall-skills` permite revisar y confirmar la retirada de selecciones de
skills propias de Forge. Conserva los paquetes exactos para restaurarlos; no borra
plugins externos ni copias de otros proyectos. `aikya skills --help` muestra los ámbitos
project/local/global, la vista previa, la restauración y la recuperación de operaciones
interrumpidas. Reinicia la sesión de autor tras cambiar la selección.

```sh
aikya skills uninstall --target /ruta/proyecto --scope project --name example-skill
# Añade --yes solo después de revisar la vista previa.
aikya skills restore --target /ruta/proyecto --scope project --all --operation OPERATION_ID
```

La instalación nativa utiliza una raíz propia: AikyaForge en macOS/Windows y aikya-forge
en Linux. Conserva las instalaciones anteriores del Harness y no incluye migración v7.
En Windows se desinstala con el instalador PowerShell externo verificado y
`-Action uninstall`; el gestor no intenta borrar su propio ejecutable en uso.

Los paquetes nativos incluyen analizadores binarios compatibles y verificados por hash.
Windows ARM64 no dispone de una rueda Dart revisada y mantiene el inventario de esos
archivos. `--code-index none` permite construir expresamente un paquete reducido.
La instalación de desarrollo desde el código requiere el extra code-index para parsers.

Los checks .NET 8+ build/test/restore/publish/pack necesitan
`--artifacts-path {artifacts}`: cada ejecución tiene sus salidas privadas y se sigue
inventariando el código real en bin/obj. Cada check debe construir sus entradas; un
`--no-build` posterior no puede asumir las salidas privadas de otro check.

Consulta la [guía Forge](aikya/docs/deployment/forge-0.2.0.md) y el
[procedimiento de aceptación externa](aikya/docs/validation/forge-provider-procedure.md).
La memoria, el HTML y la administración de skills no llaman a modelos. Los tokens
medidos no prueban porcentajes de cuota de suscripción ni ahorros de consumo.

GENERATED BY AIKYA HARNESS

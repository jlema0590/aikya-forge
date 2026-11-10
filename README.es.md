# Aikya Forge

[English](README.md) | [Español](README.es.md)

**Flujos de ingeniería, memoria local por proyecto y ejecución controlada de IA desde la terminal.**

Aikya Forge combina un núcleo Python y una terminal interactiva basada en Pi.
Incorpora los comandos, las plantillas y los controles de Aikya en un repositorio
con versionado independiente. Su primera base de desarrollo es **0.1.0**.

Es una base de desarrollo. Existen pruebas nativas en macOS de la implementación
heredada; quedan abiertas las pruebas nativas en Windows/Linux y con proveedores
reales. El código disponible no implica una release ni un instalador corto publicado.

## Inicio rápido desde el código

Requisitos: Python 3.10–3.13 con pip/venv, Node.js 22.19.0+ con npm y Git.
Se recomienda Python 3.13 para el entorno de pruebas de desarrollo.

```sh
git clone --branch develop https://github.com/jlema0590/aikya-forge.git
cd aikya-forge
python3 -m venv .venv
. .venv/bin/activate
python -m pip install 'setuptools>=77' wheel build
python -m pip install --no-build-isolation -e .
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

## Componentes

| Componente | Función |
|---|---|
| Núcleo Python (`src/aikya/`) | Inicialización, metodología, pruebas, memoria, instalación y evidencias persistentes. |
| Terminal Pi (`packages/aikya-pi/`) | Comandos interactivos, confirmaciones, temas, selección de modelos y sesiones acotadas. |
| Adaptadores de comandos | 28 flujos canónicos con su cobertura nativa y sus límites documentados. |
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
Genera instaladores shell/PowerShell vinculados a sumas de comprobación y permite
instalación/actualización explícitas, rollback conservado y desinstalación conservadora.

```sh
python scripts/ci/build_terminal_bundle.py --version 0.1.0 --output ../forge-native-0.1.0 --fetch-components
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

`VERSION` y el paquete Pi comienzan en **0.1.0**. Las siguientes versiones de Forge
seguirán versionado semántico independiente. El [changelog](CHANGELOG.md) registra
los cambios de Forge; el [histórico heredado](aikya/docs/history/harness-CHANGELOG.md)
conserva los cambios del Harness.

En esta primera importación se mantienen los comandos, los módulos Python (`aikya`)
y el nombre de distribución Python (`aikya-harness`) por compatibilidad. Las direcciones
operativas de actualización apuntan al nuevo repositorio. Se conservan las identidades
v8 para compatibilidad explícita, sin alterar la numeración propia de Forge.

Los workflows heredados de publicación de releases y Pages siguen limitados al
repositorio original del Harness. Las pruebas se ejecutan aquí; publicar requiere
una configuración de releases de Forge revisada por separado. El
[índice documental](aikya/docs/indice.md) conserva planes y evidencias anteriores;
las referencias a v7/v8 de los registros históricos describen aquellas versiones.

## Licencia

MIT. Consulta [LICENSE](LICENSE) y los [avisos de terceros](THIRD_PARTY_LICENSES.md).

GENERATED BY AIKYA HARNESS

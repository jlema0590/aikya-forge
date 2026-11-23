# Validación local de la comparación Gentle Shell–Aikya

Fecha: 7 de noviembre de 2026. Rama:
`research/gentle-shell-4.7.0-comparison`, creada desde `origin/develop`.
El [recibo JSON](2026-11-07-gentle-shell-comparison.json) conserva versiones,
hashes de logs, resultados y límites. La [investigación](../research/2026-11-07-gentle-shell-4.7.0-vs-aikya.es.md)
contiene la interpretación; el [plan](../plan/2026-11-07-aikya-multi-host.es.md)
no está implementado.

## Entorno y separación

macOS arm64; Python 3.13.18, Node 26.12.1, pnpm 11.1.1 y TypeScript 5.9.3.
Se observó Claude Code 2.1.311 y Codex CLI 0.163.0 mediante sus versiones.
Node satisface el mínimo del paquete; no es el Node 24.21.0 del bundle comercial.
Las pruebas no acreditan equivalencia entre esos dos entornos.

Las copias fuente y las instalaciones se crearon en temporales. Un launcher de
pruebas construyó un entorno reducido con hogares/configuración/cache separados;
no se copiaron las sesiones o claves del usuario. Los comandos con capacidades de
red se limitaron a descargar dependencias/artefactos públicos. Se desactivó la
telemetría en las comprobaciones nativas posteriores. No se ejecutó una petición
a un modelo ni un benchmark de cuota.

La configuración personal y los proyectos Jourpass no se modificaron. El plan
previo de uninstall-skills y su entrada local del índice se conservan aparte.
No se creó ningún worktree ni se publicó esta rama.

## Instalaciones verificadas

1. Se descargó el tag Shell 4.7.0, se revisaron scripts y se instalaron dependencias
   del lockfile con pnpm 11.1.1, `--frozen-lockfile --ignore-scripts`.
2. Se ejecutó explícitamente el instalador auditado del binario Gentle AI fijado.
   Instaló/verificó 4.4.0 dentro de `.gentle-ai/v4.4.0/` de la copia temporal;
   no modificó los settings Pi del usuario.
3. El launcher devolvió `gentle-shell 4.7.0`, `pi 1.4.0` y un hogar aislado.
   `setup --dry-run` produjo el plan Pi/persona/Engram. No se aplicó el setup
   completo del bundle ni se instaló el companion Pi de Engram.
4. Gentle AI instaló realmente persona/skills para Claude, Codex, Gemini CLI y
   OpenCode en el hogar temporal. Esos componentes pueden añadir sus propios
   agentes/hooks auxiliares: la selección no significa «solo dos archivos».
   Un primer intento rechazó correctamente un `CODEX_HOME` explícito inexistente;
   se creó ese directorio y se repitió la instalación con éxito.
5. Se descargó Engram 3.5.2 a temporales y se verificó tamaño y SHA-256 contra el
   pin de Shell. Se ejecutaron sus autopruebas aisladas, no un servicio compartido
   sobre los datos del usuario.
6. Aikya 7.2.2 se instaló en un venv sin el SDK opcional, se generaron wheel/sdist
   y se ejecutó aceptación del wheel instalado en otros entornos desechables.

## Resultados observados

| Comprobación | Resultado |
|---|---|
| Suite oficial Shell `pnpm test` | 9.335 tests: 9.252 aprobados, cero fallos, 83 omitidos; 134.097,086542 ms en su etapa de unit tests. |
| Etapas del runner Shell | `unit-tests`, `provider-contract` y `runtime-harness`: las tres terminaron con PASS. |
| Espejo de contrato | 1.4.0, diez entradas y dos baselines verificados. |
| TypeScript | Cero diagnósticos registrados, sin regresiones. |
| Módulos runtime generados | 16 coinciden con sus fuentes TypeScript. |
| Engram `test --quick --json` | Tres escenarios aprobados: guardado/búsqueda/contexto, escrituras concurrentes y búsqueda. |
| Aikya build | Wheel y sdist 7.2.2 generados correctamente. |
| Aikya wheel | Once casos aprobados: scopes, reutilización global/proyecto, bridge mobile y onboarding ODD/SDD, sin imports del checkout ni SDK opcional. |
| Aikya regresión completa | 706 tests: 700 aprobados, cero fallos y seis omitidos; 1.050,264 segundos. Seis omisiones por parsers opcionales/entorno; no cuentan como funcionalidad probada. |
| Parsers opcionales Aikya, comprobación posterior | Tras instalar los binarios fijados, 14 casos: 13 aprobados y uno omitido por exigir un entorno sin dependencias. Se ejecutaron las pruebas de declaraciones omitidas en la suite mínima. No se repitió la suite completa con extras ni se suman casos solapados. |
| Instalación multihost Gentle AI | Archivos generados para cuatro clientes; conservó los valores sintéticos del usuario en Claude y Codex. |
| Parser de configuración Codex | `codex features list` terminó correctamente con la configuración temporal. No prueba ejecución de skills o modelos. |
| CLI Claude sin sesión | `claude agents --json` devolvió una lista de sesiones de background vacía; no enumera definiciones de agentes y no acredita su ejecución. |
| Coexistencia de archivos | Aikya conservó persona/skills/hooks Gentle, settings del usuario y configuración Codex; 28 comandos globales Aikya y cero copias locales en el registro del proyecto posterior. |

El conteo de tests no es una comparación de cobertura equivalente. Node ejecuta
la suite de otro producto con otra estructura; Python verifica otras funciones.
No usar las duraciones como benchmark de latencia de asistentes o de tokens.
Las omisiones no cuentan como funcionalidades demostradas.

## Reproducción

Los logs completos están en el directorio `evidence` del entregable local
`deliverables/gentle-shell-comparison-2026-11-07/`. El recibo contiene su ruta
absoluta y las huellas SHA-256. Se conservan el launcher de entorno y el pin del
artefacto Engram; los repositorios se identifican por sus commits publicados.

Comandos principales, ejecutados con el entorno temporal:

```sh
# En el checkout Gentle Shell v4.7.0
pnpm install --frozen-lockfile --ignore-scripts
node scripts/install-gentle-ai.mjs
pnpm test
pnpm typecheck
node scripts/build-runtime-modules.mjs --check
node bin/gentle-shell.mjs --version
node bin/gentle-shell.mjs setup --dry-run

# Con el binario Gentle AI fijado, sobre un hogar de pruebas
# Preparar CODEX_HOME antes si se especifica explícitamente.
gentle-ai install --agents claude-code,codex,gemini-cli,opencode --components persona,skills --scope global

# Engram de prueba, verificado contra el pin de Shell
engram test --quick --json

# Desde el checkout Aikya, en el venv temporal
python -m build --no-isolation --outdir <artefactos>
python scripts/ci/package_smoke.py --wheel <wheel-7.2.2> --output <recibo.json>
python scripts/ci/run_isolated_tests.py
```

No ejecutar el ejemplo de instalación global sobre el hogar personal para
reproducir este estudio. El aislamiento es parte de la prueba, no un parámetro
que pueda omitirse sin cambiar su efecto.

## Lo que no está validado

- Sesiones reales de implementación/revisión con Claude, Codex, Pi u otro modelo.
- Autenticación, permisos de cuenta, límites de suscripción, ahorro real de tokens
  o calidad del código generado. Las versiones del CLI no acreditan esos puntos.
- TUI interactiva completa, voz, música o procesos de background reales con un modelo.
- Instaladores nativos completos de Windows/Linux en esta máquina ni todos los
  recorridos de los 18 clientes del catálogo Gentle AI.
- CodeGraph externo instalado/indexando un proyecto; solo se inspeccionó su integración
  y se ejecutaron las pruebas de Shell que forman parte de la suite.
- Estado de conexión MCP en una versión Pi sin la API nativa requerida. La propia
  documentación de Shell avisa de esa condición; no se infiere salud de un contador.
- Semántica de dos orquestadores activos sobre una conversación. Conservar archivos
  y respetar valores no demuestra ausencia de conflictos de política.
- Los tres commits de main posteriores al tag, ni todas las incidencias mencionadas
  en su triage. Ese documento contiene referencias históricas y no es una reproducción.

GENERATED BY AIKYA HARNESS

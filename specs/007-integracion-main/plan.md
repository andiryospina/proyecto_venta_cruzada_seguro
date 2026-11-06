# Plan: Integrar `main` sobre el modelo final de la rama (`007-integracion-main`)

**Fecha:** 2026-11-06 · **Spec:** `specs/007-integracion-main/spec.md` · **Estado:** borrador, pendiente de aprobación del grupo
**Rama de trabajo:** `007-integracion-main`, creada desde `006-registro-modelo` · **Destino:** *pull request* a `main`

## Resumen

Se fusiona `origin/main` en una rama nueva salida de `006-registro-modelo`, **sin guardar** (`--no-commit`), y se decide archivo por
archivo con una tabla fija (abajo): **R** = queda la versión de la rama, **M** = queda la de `main`, **A** = se adapta o se rehace
sobre el modelo de la rama, **Q** = se quita (y se anota por qué). Git no basta: en `src/`, `tests/`, notebooks 01–06,
`train.parquet` e informes 04–06 **no marca conflicto** y se quedaría con `main` (ver `research.md`, R1).

Lo único que se programa es `src/proyecto/inference/serving.py` (traducir lo que escribe una persona a las columnas limpias del modelo
de la rama) con sus pruebas, y el notebook 09 que exporta `models/model.joblib` y `models/input_schema.json`. El resto es elegir
versiones y corregir textos. **No se reentrena ni se abre la prueba.**

## Contexto técnico

- **Lenguaje:** Python 3.12 · **Dependencias:** las de `requirements.txt` (se adopta `pyarrow==25.0.1` que agregó `main`).
- **Pruebas:** `pytest` (se adopta `pytest.ini` de `main`: solo recoge `tests/`). Punto de partida: **113 pruebas en verde** en la rama.
- **Modelo:** `models/final_pipeline.joblib` (pasos `features` → `prep` → `model`), 304.238 clientes de entrenamiento. Entradas: `Gender`,
  `Age`, `Driving_License`, `Region_Code`, `Previously_Insured`, `Vehicle_Age`, `Vehicle_Damage`, `Annual_Premium`, `Vintage`,
  `is_min_premium` (y `id`, que el `Pipeline` descarta). Categorías ya codificadas como números (`CATEGORY_MAPS` de `config.py`).
- **App:** la de `main` (Streamlit, formulario construido desde `models/input_schema.json`); no consulta Databricks.
- **Sin pendientes de investigación:** todo lo dudoso se resolvió en `research.md`.

## Revisión de la constitución (antes y después del diseño)

| Principio | ¿Cumple? | Cómo |
|---|---|---|
| I. Datos originales intactos | Sí | No se toca `data/raw/`. `data/processed/train.parquet` vuelve a la versión de la rama (la que usó el modelo). |
| II. Partir por la unidad | Sí | Un cliente = una fila, `id` único (prueba existente en `test_split.py`). No cambia la partición. |
| III. La prueba se abre una sola vez | **Con salvedad** | Esta integración **no** la abre. Pero en el grupo ya se abrió **dos veces** (19:09 y 20:43 del 2026-11-05). Ver "Excepciones justificadas". |
| IV. Decisión escrita con su motivo | Sí | `reports/integracion_main.md` (tabla de archivos) y `reports/decisiones_del_grupo.md` (D12, D14, etapa 4, P12). |
| V. Nada sensible sale | Sí | Se quitan los correos de 3 archivos de `main`; búsqueda automática al final. |
| VI. El código es nuestro | Sí | `serving.py` es pequeño y se revisa con `revisor-de-codigo-ia`; el notebook 09 solo orquesta. |
| VII. No se inventan datos | Sí | Toda cifra de prueba sale de `reports/07_metricas_test.json`; se verifica con una búsqueda de cifras. |

### Excepciones justificadas

| Qué | Por qué hace falta | Alternativa más simple descartada |
|---|---|---|
| La prueba quedó abierta dos veces en el grupo (dos modelos distintos) | Ya ocurrió y no se puede deshacer. El modelo final se eligió por un criterio de alcance fijado sin mirar cifras de prueba ("debe incluir las 5 variables nuevas"); la diferencia de costo entre ambos (0,3312 frente a 0,3317) no se usa para nada | Ocultarlo: viola los principios III y VII. Partir de nuevo la prueba: no hay datos nuevos y la prueba ya se vio |

## Estructura del trabajo

```text
specs/007-integracion-main/   plan.md  research.md  data-model.md  quickstart.md  contracts/  (tasks.md lo crea /speckit-tasks)

src/proyecto/inference/serving.py     # A: se reescribe para las columnas de la rama (contracts/serving.md)
tests/test_serving.py                 # A: pruebas de serving.py con un Pipeline de juguete
notebooks/09_inferencia.ipynb         # A: exporta model.joblib + input_schema.json; ejemplo con clientes de ENTRENAMIENTO
models/model.joblib                   # A: ServingModel(final_pipeline) — se regenera
models/input_schema.json              # A: se regenera (contracts/input_schema.md)
reports/integracion_main.md           # NUEVO: tabla de archivos (R/M/A/Q) con motivo
```

## Tabla de decisión por archivo

Detalle y motivo de cada fila en `data-model.md`. Resumen:

| Grupo | Archivos | Decisión |
|---|---|---|
| Código del modelo | `src/proyecto/config.py`, `data/cleaning.py`, `data/split.py`, `features/__init__.py`, `features/engineering.py`, `features/preprocessing.py`*, `features/transformers.py`*, `models/train.py`, `models/tuning.py` | **R** (*`main` los borró: se restauran) |
| Pruebas del modelo | `tests/test_cleaning.py`, `test_features.py`, `test_models.py`, `test_split.py`, `test_tuning.py`, `test_preprocessing.py`* | **R** |
| Datos de la etapa 3 | `data/processed/train.parquet` | **R** (304.238 filas; el modelo se entrenó con este) |
| Notebooks | `01` a `08` | **R** (los de `main` importan funciones que ya no existen) |
| Informes 04–07 y especificación 03 | `reports/04_features.md`, `04_features_tabla.csv`, `05_torneo.md`, `06_optimizacion.md`, `06_best_params.json`, `07_*`, `especificaciones/03-preprocesamiento.md`, `specs/002-variables/spec.md`, `reports/08_registro.md` | **R** |
| Solo de `main`, atados a su código | `src/proyecto/data/loading.py`, `models/metrics.py`, `models/baselines.py`, `tests/test_tournament.py`, `reports/04_features_tabla_nuevas.csv`, `05_torneo_tabla.csv` | **Q** |
| Constancia del modelo de `main` | `reports/08_registro.json` (tiene un correo; describe el modelo viejo) | **Q** (la regenera T009 de `006-registro-modelo`) |
| Configuración | `pytest.ini`, `requirements.txt`, `.gitignore`, `specs/README.md`, `src/proyecto/inference/predict.py`, `schema.py`, `tests/test_inference.py`, `app/streamlit_app.py`, `reports/06_mlflow_runs.csv` | **M** |
| Caso y EDA | `reports/00_caso.md`, `reports/01_eda.md`, `especificaciones/02-eda.md` | **M**, revisando que no citen cifras o secciones que solo existen en los notebooks de `main` |
| Se rehacen | `serving.py`, `test_serving.py`, notebook `09`, `model.joblib`, `input_schema.json`, `ficha_modelo.md`, `09_despliegue.md`, `informe_tecnico.md`, `presentacion/ejecutiva.md`, `decisiones_del_grupo.md`, `README.md` | **A** |
| Se combinan | `especificacion-proyecto.md`, `reports/prueba_abierta.txt`, `reports/07_validacion.md` | **A** (base de la rama + lo de `main` que siga siendo cierto, incluida la apertura de las 19:09) |

## Orden de trabajo

1. **Rama y fusión sin guardar:** `git switch -c 007-integracion-main` → `git merge --no-commit --no-ff origin/main`.
2. **R:** `git checkout HEAD -- <archivos R>` (incluye los 8 con conflicto y los que `main` borró).
3. **Q:** `git rm <archivos Q>`.
4. **Comprobación intermedia:** `pytest` debe dar las 113 pruebas de la rama en verde (más las de `main` que se conservan:
   `test_inference.py`). Si no, se para aquí.
5. **Primer commit** (la fusión ya resuelta, sin los archivos A todavía): así queda un punto al que volver.
6. **A — código:** `serving.py` y `test_serving.py` (prueba primero) → notebook 09 → `model.joblib` + `input_schema.json`.
7. **A — textos:** registro de decisiones → `07_validacion.md` y `prueba_abierta.txt` → ficha, despliegue, informe técnico,
   presentación, README, `especificacion-proyecto.md` → `reports/integracion_main.md`. El nombre del modelo en el notebook 08 pasa a
   `venta_cruzada_seguros` (supuesto de la spec).
8. **Verificación final:** `quickstart.md` completo (pruebas, ida y vuelta, cifras, correos, app).
9. **Revisión:** subagentes `auditor-de-fuga` y `revisor-de-codigo-ia`; luego *push* y *pull request* a `main`.

## Riesgos

- **Fuga / prueba:** el notebook 09 de `main` calculaba costos con `per_client_cost`; el nuevo **no lee `test.parquet`**: el ejemplo y
  la ida y vuelta usan clientes de entrenamiento.
- **Métrica engañosa:** si el informe técnico mezcla cifras de los dos modelos, el error no lo detecta `pytest`; por eso el
  `quickstart.md` incluye una búsqueda de las cifras del modelo de `main` (0,3317, 0,8519, 0,3533…) que debe salir vacía fuera del
  registro de decisiones y del reporte de integración.
- **Databricks:** el alias `champion` sigue apuntando al modelo de `main` hasta que se ejecute T009 de `006-registro-modelo`. La app no
  depende de eso (carga `model.joblib`), pero el informe debe decirlo mientras esté pendiente.
- **Trabajo del grupo:** se quitan o reemplazan archivos hechos por compañeros. Quedan en la historia de Git y listados en
  `reports/integracion_main.md`; el *pull request* lo revisa el grupo antes de entrar a `main`.

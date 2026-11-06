# Modelo de datos: integración de `main` (`007-integracion-main`)

## 1. Decisión por archivo (lo que irá a `reports/integracion_main.md`)

Estados: **R** = versión de la rama · **M** = versión de `main` · **A** = se adapta o rehace · **Q** = se quita.
"Cambio de `main`" = qué hizo `main` desde la base común `e94c0cb` (M modificado, A agregado, D borrado).

| Archivo | Cambio de `main` | Decisión | Motivo |
|---|---|---|---|
| `src/proyecto/config.py` | M | R | Constantes de las 5 variables nuevas y de la validación |
| `src/proyecto/data/cleaning.py`, `data/split.py` | M | R | Limpieza y partición con las que se entrenó el modelo (304.238 clientes) |
| `src/proyecto/features/__init__.py`, `engineering.py` | M | R | Calculan las 5 variables nuevas |
| `src/proyecto/features/preprocessing.py`, `transformers.py` | D | R | El `Pipeline` guardado usa sus clases; sin ellas no carga |
| `src/proyecto/models/train.py`, `tuning.py` | M | R | Funciones que usan los notebooks 07 y 08 |
| `src/proyecto/data/loading.py` | A | Q | Llama a funciones de la limpieza de `main` que no existen en la rama |
| `src/proyecto/models/metrics.py`, `baselines.py` | A | Q | Solo los usan los notebooks 04–06 y 09 de `main`; la rama tiene sus equivalentes en `train.py` |
| `src/proyecto/inference/serving.py` | A | A | Se reescribe para las columnas de la rama (`contracts/serving.md`) |
| `src/proyecto/inference/predict.py`, `schema.py` | sin cambio | M | Genéricos |
| `tests/test_cleaning.py`, `test_features.py`, `test_models.py`, `test_split.py`, `test_tuning.py` | M | R | Prueban el código R |
| `tests/test_preprocessing.py` | D | R | Prueba `preprocessing.py` |
| `tests/test_tournament.py` | A | Q | Prueba funciones de `main` que se quitan |
| `tests/test_serving.py` | A | A | Se reescribe junto con `serving.py` |
| `pytest.ini`, `requirements.txt`, `.gitignore` | A/M/M | M | Solo recoge `tests/`; agrega `pyarrow`; comentario sobre la prueba cerrada |
| `data/processed/train.parquet` | M | R | Ver `research.md` R2 |
| `notebooks/01` a `06` | M | R | Ver `research.md` R3 |
| `notebooks/07`, `08` | M (conflicto) | R | Modelo final; en el 08 se cambia el nombre del modelo a `venta_cruzada_seguros` |
| `notebooks/09_inferencia.ipynb` | M | A | Se rehace sobre `serving.py` nuevo |
| `reports/00_caso.md`, `01_eda.md`, `especificaciones/02-eda.md` | M | **R** + notas de `main` *(cambiado en T015)* | La revisión mostró que la versión de `main` no corregía la de la rama: la reemplazaba por un borrador de sus notebooks 01–02 (que ya no están), con la métrica principal como PR-AUC (el modelo final usa costo esperado) y las hipótesis del EDA en blanco. Se conservan de `main` la nota sobre la eliminación del canal (D13, P11) y el enlace al registro de decisiones |
| `especificaciones/03-preprocesamiento.md`, `specs/002-variables/spec.md` | M | R | Describen la limpieza y las variables de la rama |
| `reports/04_features.md`, `04_features_tabla.csv`, `05_torneo.md`, `06_optimizacion.md`, `06_best_params.json` | M | R | Resultados del código de la rama |
| `reports/04_features_tabla_nuevas.csv`, `05_torneo_tabla.csv` | A | Q | Resultados del código de `main` |
| `reports/06_mlflow_runs.csv` | A | M | Exporta los 44 ensayos de Optuna de la rama (sin datos personales) |
| `reports/07_*` (json, csv, png, md) | A/M (conflicto) | R | Validación del modelo final; `07_validacion.md` se completa (A) con la doble apertura |
| `reports/prueba_abierta.txt` | A (conflicto) | A | Combina: primera apertura 19:09 (modelo de `main`) y la de 20:43 (modelo final) |
| `reports/08_registro.json` | A | Q | Modelo de `main` y un correo; lo regenera T009 de `006-registro-modelo` |
| `reports/08_registro.md` | M | R | Plantilla de la rama (la llena T010 de `006`) |
| `reports/09_despliegue.md`, `informe_tecnico.md`, `models/ficha_modelo.md`, `presentacion/ejecutiva.md`, `README.md` | M | A | Estructura de `main`, cifras y variables del modelo final |
| `reports/decisiones_del_grupo.md` | A | A | Ver sección 2 |
| `especificacion-proyecto.md` | M (conflicto) | A | Une la sección 7 de ambos |
| `models/model.joblib`, `models/input_schema.json` | A | A | Se regeneran con el notebook 09 |
| `specs/README.md` | A | M | Índice de especificaciones; se agrega `007` |

## 2. Cambios en el registro de decisiones del grupo

Se agrega el estado **[REEMPLAZADO]**: la decisión no se borra, se tacha su vigencia y se enlaza la nueva.

| Entrada | Antes | Después |
|---|---|---|
| D12 | Retirar `Vintage` y `Driving_License`; conservar `Gender` | [REEMPLAZADO 2026-11-06] por D15: el modelo final conserva `Vintage` y `Driving_License` (venían en el modelo de la rama); `Gender` sigue (auditoría por género en `reports/07_segmentos.csv`) |
| D14 | Mantener parámetros de partida | [REEMPLAZADO 2026-11-06] por D15: parámetros de Optuna, ensayo #13 |
| Etapa 4 de `main` | Descartar las 5 ideas de variables nuevas | [REEMPLAZADO 2026-11-06] por D15: el modelo final incluye las 5 variables nuevas de la rama (otras 5 ideas distintas a las de `main`) |
| D15 (nueva) | — | [DECIDIDO por el grupo 2026-11-06] Modelo final = el de la rama: 5 variables nuevas, sin `Policy_Sales_Channel`, con `Gender`, Optuna #13. Motivo: el grupo exige incluir las variables nuevas. No se eligió comparando cifras de prueba |
| P12 | Pendiente | [CERRADO 2026-11-06] Las 649 filas son repetidas al quitar el canal; la limpieza de la rama las quita |
| D13 | Quitar `Policy_Sales_Channel` | Sin cambio |

## 3. Columnas de entrada (persona → modelo)

| Lo que escribe la persona | Valores | Columna limpia que recibe el modelo |
|---|---|---|
| Edad | 18–100 | `Age` (número) |
| Género | `Female`, `Male` | `Gender` (0, 1) |
| ¿Tiene licencia? | `Yes`, `No` | `Driving_License` (1, 0) |
| Región | código entero | `Region_Code` |
| ¿Ya tiene seguro? | `Yes`, `No` | `Previously_Insured` (1, 0) |
| Antigüedad del vehículo | `< 1 Year`, `1-2 Year`, `> 2 Years` | `Vehicle_Age` (0, 1, 2) |
| ¿El vehículo tuvo daño? | `Yes`, `No` | `Vehicle_Damage` (1, 0) |
| Prima anual | > 0 | `Annual_Premium`; además `is_min_premium = (prima == 2.630)` |
| Días como cliente | ≥ 0 | `Vintage` |

Las codificaciones salen de `CATEGORY_MAPS` y `MIN_PREMIUM` de `config.py` (no se escriben otra vez).

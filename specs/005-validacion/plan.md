# Plan: Validación final con el conjunto de prueba (`005-validacion`)

**Fecha:** 2026-11-05 · **Spec:** `specs/005-validacion/spec.md` · **Estado:** aprobado por el grupo (2026-11-05)

## Diseño

```text
src/proyecto/config.py                    # + AGE_BANDS, MIN_REGION_SIZE = 1000, SENSITIVITY_RATIOS = (3, 5, 10), TEST_MARKER
src/proyecto/models/validation.py         # NUEVO: funciones de la etapa 07 (tabla de abajo)
tests/test_validation.py                  # NUEVO: una prueba por función
notebooks/07_validacion_interpretacion.ipynb   # se llena el esqueleto existente; solo orquesta
reports/07_validacion.md                  # se llena la plantilla existente
reports/07_metricas_test.json · reports/07_segmentos.csv · reports/07_calibracion.png · reports/07_shap.png
reports/prueba_abierta.txt                # lo crea el notebook al abrir la prueba
models/final_pipeline.joblib              # el modelo final entero; .gitignore (no se sube)
```

Se reutiliza lo que ya existe y está probado: `build_pipeline`, `split_xy`, `metrics_from_proba`, `decide`, `expected_cost`,
`BusinessRuleClassifier` (de `models/train.py`), `make_lgbm` y `bootstrap_cost_difference` (de `models/tuning.py`), y
`configure_mlflow` / `set_experiment` / `log_run` (de `tracking/mlflow_utils.py`). No se reescribe nada de eso.

## Funciones nuevas de `validation.py`

| Función | Qué hace |
|---|---|
| `bootstrap_log_loss_difference(y, proba_a, proba_b)` | Diferencia de log loss (A − B) con intervalo del 95 %, remuestreando clientes |
| `should_calibrate(raw, calibrated, log_loss_diff)` | `True` solo si todo el intervalo de la diferencia de log loss está bajo cero (mejora mínima) **y** el costo no sube (regla de la spec) |
| `fit_final_model(train, params, calibrate)` | Pipeline de LightGBM con los parámetros de `06_best_params.json`, ajustado con todo el entrenamiento; envuelto en `CalibratedClassifierCV` (isotónica, 3 pliegues) solo si `calibrate=True` |
| `open_test_once(marker_path, test_path, decisions, commit)` | Si la marca existe o alguna decisión congelada está vacía, **lanza un error** y no lee nada; si no, escribe fecha, hora, usuario del sistema y commit, y devuelve la prueba |
| `bootstrap_mean(values, n_boot=1000, seed=42)` | Promedio con intervalo del 95 %, remuestreando clientes (para el costo del modelo y el de la línea base por separado) |
| `age_band(age)` | Tramo de edad: `18–29`, `30–44`, `45–59`, `60+` |
| `segment_table(segments, y, decision, min_size=None)` | Por segmento: clientes, costo, % contactado, % real de interesados, recall; agrupa como "otras" los segmentos con menos de `min_size` |
| `cost_sensitivity(y, decision, ratios)` | Costo por cliente con matrices `[[0,1],[r,0]]` para cada `r` (3, 5, 10) con la **misma** decisión |

La diferencia modelo − línea base usa `bootstrap_cost_difference` (ya probada en la etapa 06): la línea base entra como
probabilidad de `BusinessRuleClassifier` ajustada con todo el entrenamiento; con el umbral 1/6 llama exactamente a quienes cumplen
la regla (su tasa de interés ≈ 25 % > 1/6; la del resto ≈ 1 % < 1/6). Una prueba lo verifica.

## Orden del notebook 07

1. Cargar `train.parquet`. Escribir las **decisiones congeladas** con fecha y hora (celda y `reports/07_validacion.md`).
2. **Calibración** con la reserva de la etapa 06 (25 %, semilla 7): sin calibrar vs. calibrado → `should_calibrate` → curva en
   `reports/07_calibracion.png`.
3. Modelo final con todo el entrenamiento → `models/final_pipeline.joblib`.
4. `open_test_once` → métricas del modelo y de la línea base, intervalos y diferencia → `reports/07_metricas_test.json`.
5. Segmentos (`Gender`, `age_band(Age)`, `Region_Code` con mínimo 1.000) → `reports/07_segmentos.csv`; sensibilidad 3 / 5 / 10.
6. SHAP en una muestra de 5.000 clientes de la prueba → `reports/07_shap.png`.
7. Una ejecución de MLflow (`venta-cruzada-validacion`, `etapa=07_validacion`) con todas las métricas.

## Revisión contra la constitución

- **II:** 1 fila = 1 cliente (`id` único); reserva y prueba son por fila estratificada, válido. Prueba: la reserva no comparte `id` con el 75 %.
- **III:** la prueba se lee una sola vez, a través de `open_test_once`, **después** de congelar decisiones y guardar el modelo final.
  La calibración se decide con la reserva. El umbral 1/6 no cambia. La sensibilidad y los segmentos solo se reportan.
- **IV / VII:** todas las cifras salen del notebook a `reports/`; nada se escribe a mano en el JSON.
- **V:** los reportes por segmento son agregados (mínimo 1.000 clientes por región); no se imprimen filas de clientes.
- **Regla 7 de `CLAUDE.md`:** MLflow en Databricks vía `configure_mlflow()`; si cae a local, se dice en el reporte.
- **Regla 9:** cada función nueva de `validation.py` tiene prueba en `tests/test_validation.py`.

## Decisiones técnicas (sin investigación pendiente)

- **Calibración isotónica**, no sigmoide: hay ≈ 228.000 clientes en el 75 %, suficientes para la isotónica (la guía usa la misma).
- **SHAP con `TreeExplainer`** sobre el LightGBM ya ajustado (rápido, exacto para árboles). Si se calibra, SHAP explica el LightGBM
  de dentro, y se dice en el reporte. Si falla, importancia por permutación con `sklearn`.
- No se generan `research.md`, `data-model.md`, `contracts/` ni `quickstart.md`: igual que en las specs 001 a 004, la etapa no expone
  interfaces nuevas y no hay dudas técnicas abiertas. La comprobación está en "Cómo verificar".

## Cómo verificar

```bash
pytest tests/test_validation.py -q     # funciones nuevas
pytest tests -q                        # todo el proyecto en verde
```
Después de ejecutar el notebook: existe `reports/prueba_abierta.txt`; volver a ejecutar la celda de la prueba **da error**;
`reports/07_metricas_test.json` tiene `modelo`, `linea_base` y `diferencia` con sus intervalos.

## Riesgos

- **Se abre la prueba por error antes de tiempo** (por ejemplo, ejecutando todo el notebook con decisiones vacías). Mitigación:
  `open_test_once` exige que las decisiones congeladas estén completas antes de leer el archivo.
- **La marca se borra a mano para "volver a abrir".** El código no puede impedirlo; la marca queda en Git y cualquier reapertura se
  declara en el reporte.
- **Mejora pequeña frente a la línea base o diferencia que cruza el cero:** es un resultado válido y se reporta tal cual.
- **Atributos sensibles** (`Gender`, `Age`, `Region_Code`) en el modelo: se declaran; no se quitan en esta etapa (sería cambiar el
  modelo después de ver la prueba).
- **Tiempo:** calibración (3 ajustes) + modelo final + SHAP en 5.000 filas: estimado 3–8 minutos.

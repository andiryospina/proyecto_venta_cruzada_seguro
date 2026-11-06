# Plan: Optimización de hiperparámetros (`004-optimizacion`)

**Fecha:** 2026-11-05 · **Spec:** `specs/004-optimizacion/spec.md` · **Estado:** aprobado por el grupo (2026-11-05)

## Diseño

```text
src/proyecto/config.py            # + TUNE_HOLDOUT = 0.25, TUNE_SEED = 7, TUNE_FOLDS = 3, TUNE_TRIALS = 40
src/proyecto/models/tuning.py     # NUEVO (adaptado del tuning.py del ejemplo del curso)
tests/test_tuning.py              # NUEVO
notebooks/06_optimizacion.ipynb   # orquesta: reserva → búsqueda → evolución → importancias → comprobación → guardar
reports/06_optimizacion.md · reports/06_best_params.json · reports/06_comprobacion.csv
.gitignore                        # + optuna_06.db
```

## Qué cambia frente al `tuning.py` del ejemplo

| Ejemplo del curso (CreditSight) | Nuestro proyecto | Por qué |
|---|---|---|
| 3 clases, `decide_min_cost` | Binario, `decide(proba)` con umbral 1/6 | Nuestra decisión es llamar / no llamar |
| Remuestrea **clientes con 8 meses** cada uno | Remuestrea **filas** (1 fila = 1 cliente) | No hay entidades repetidas |
| LightGBM y random forest | Solo LightGBM | Decisión del torneo |
| `build_pipeline(model, scale=...)` | `build_pipeline(model, use_engineered=True)` | Nuestro pipeline del torneo |
| Métricas `auc_ovr`, `macro_f1`… | Las de nuestro `metrics_from_proba` (`cost`, `pr_auc`, `roc_auc`, `capture_30`…) | Mismas métricas del torneo |

## Funciones de `tuning.py`

| Función | Qué hace |
|---|---|
| `lgbm_space(trial)` | Devuelve los hiperparámetros de un ensayo (tabla de abajo) |
| `make_lgbm(params)` | `LGBMClassifier` con esos parámetros, `subsample_freq=1`, semilla 42 |
| `OBJECTIVES` | Métricas que se pueden optimizar y su dirección (`cost` → minimizar, `pr_auc` → maximizar…) |
| `tune(X, y, folds, n_trials, metric="cost", storage=None, log=True)` | Estudio de Optuna; cada ensayo = ejecución anidada en MLflow con todas las métricas; se reanuda desde `storage` |
| `bootstrap_cost_difference(y, proba_a, proba_b)` | Diferencia de costo (A − B) con intervalo del 95 %, remuestreando clientes |
| `bootstrap_metric_difference(y, proba_a, proba_b, metric_fn)` | Lo mismo para cualquier métrica (PR-AUC) |

## Espacio de búsqueda de LightGBM

| Parámetro | Rango | Motivo |
|---|---|---|
| `n_estimators` | 150 – 800 | Partida 300; con tasa baja hacen falta más árboles |
| `learning_rate` | 0,01 – 0,2 (log) | Partida 0,05; escala logarítmica porque importa el orden de magnitud |
| `num_leaves` | 15 – 127 | Partida 31; más hojas = más interacciones (edad × daño × región) |
| `min_child_samples` | 20 – 500 | Con 230.000 filas, hojas grandes evitan sobreajustar a pocos clientes |
| `subsample` | 0,6 – 1,0 | Submuestreo de filas: reduce varianza |
| `colsample_bytree` | 0,5 – 1,0 | Submuestreo de variables: hay pocas (≈ 14), no bajar más de la mitad |
| `reg_lambda` | 0,001 – 10 (log) | Regularización L2 de las hojas |

## Revisión contra la constitución

- **II:** reserva y pliegues estratificados por fila; cada cliente aparece una vez. Prueba: la reserva y la búsqueda no comparten `id`.
- **III:** la prueba no se carga. El umbral 1/6 no se toca. La búsqueda nunca ve el 25 % reservado.
- **IV / VII:** cifras reales en `reports/06_*`; la regla de decisión se escribe antes de ejecutar.
- **Regla 7 de `CLAUDE.md`:** MLflow en Databricks vía `configure_mlflow()`; si no hay conexión, local, y se dice.

## Riesgos

- **Optimismo:** el mejor de 40 ensayos está sesgado a la baja en costo → por eso la comprobación en el 25 % reservado.
- **Tiempo:** ≈ 230.000 filas × 3 pliegues × 40 ensayos; estimado 5–15 min. Si Databricks es lento, registrar 40 ejecuciones
  anidadas puede añadir minutos.
- **Mejora pequeña:** el torneo mostró que los tres modelos de árboles empatan; es posible que la optimización **no** supere al ruido.
  Eso sería un resultado válido y se reporta tal cual.

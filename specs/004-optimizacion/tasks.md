# Tareas: Optimización de hiperparámetros (`004-optimizacion`)

**Entrada:** `specs/004-optimizacion/plan.md` · **Estado:** aprobado por el grupo (2026-11-05)
Una tarea se marca `[x]` solo cuando su prueba pasa (`pytest tests`).

- [x] T001 Agregar `TUNE_HOLDOUT`, `TUNE_SEED`, `TUNE_FOLDS` y `TUNE_TRIALS` a `src/proyecto/config.py`; `optuna_06.db` a `.gitignore`.
- [x] T002 [P] Escribir `tests/test_tuning.py`. Debe cubrir:
  - `lgbm_space` devuelve los 7 parámetros dentro de sus rangos (`optuna.trial.FixedTrial`);
  - `OBJECTIVES`: `cost` minimiza, `pr_auc` maximiza; `tune` rechaza una métrica desconocida;
  - `bootstrap_cost_difference`: 0 con modelos idénticos; intervalo completo bajo cero con un modelo claramente mejor; reproducible;
  - `bootstrap_metric_difference` detecta un modelo que ordena mejor (PR-AUC);
  - `tune` corre 2 ensayos sobre datos pequeños sin MLflow y devuelve un estudio con 2 ensayos.
- [x] T003 Crear `src/proyecto/models/tuning.py` con las funciones del plan.
- [x] T004 Llenar `notebooks/06_optimizacion.ipynb`: conexión MLflow → reserva del 25 % → búsqueda (40 ensayos) → evolución del costo →
  importancia de parámetros → comprobación honesta con intervalo → registros en MLflow → guardar `06_best_params.json` y `06_comprobacion.csv`.
- [x] T005 Ejecutar el notebook completo y `pytest tests` en verde.
- [x] T006 Escribir `reports/06_optimizacion.md` con las cifras reales y la decisión según la regla.
- [x] T007 Anotar la decisión en la sección 7 de `especificacion-proyecto.md`.

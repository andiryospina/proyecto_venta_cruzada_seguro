# Plan: Torneo de modelos (`003-torneo`)

**Fecha:** 2026-10-31 · **Spec:** `specs/003-torneo/spec.md` · **Estado:** aprobado por el grupo (2026-10-31)

## Diseño

```text
src/proyecto/config.py          # + COST_MATRIX = [[0, 1], [5, 0]], CV_FOLDS = 5
src/proyecto/models/train.py    # NUEVO
tests/test_models.py            # NUEVO
notebooks/05_torneo.ipynb       # orquesta: carga → pliegues → torneo → tablas → comparación pareada → finalistas
reports/05_torneo.md · reports/05_torneo_folds.csv
```

## Funciones de `train.py`

| Función | Qué hace |
|---|---|
| `cost_threshold(cost)` | Umbral óptimo para llamar: costo_FP / (costo_FP + costo_FN) = 1/6 |
| `expected_cost(y, decision)` | Costo promedio por cliente con la matriz |
| `decide(proba)` | 1 (llamar) si P(interesado) > umbral |
| `capture_at(y, proba, share)` | % de interesados que hay entre el `share` de clientes con mayor probabilidad |
| `metrics_from_proba(y, proba)` | Todas las métricas de negocio y técnicas de un pliegue |
| `BusinessRuleClassifier` | La regla "sin seguro y con daño" convertida en modelo de sklearn (probabilidad 1/0), para evaluarla igual que los modelos |
| `candidates()` | Las 2 líneas base y los 5 modelos, con parámetros de partida fijos y `random_state=42` |
| `build_pipeline(model, use_engineered, use_gender)` | (`add_features`) → `build_preprocessor` → modelo |
| `make_folds(X, y)` | Los 5 pliegues estratificados, calculados una vez |
| `evaluate_folds(pipeline, X, y, folds)` | Una fila por pliegue: métricas y segundos de ajuste |
| `run_tournament(models, X, y, folds)` | Recorre los candidatos y devuelve la tabla larga (modelo × pliegue) |
| `summarize(per_fold)` | Media ± desviación por modelo, ordenada por costo |
| `compare_paired(a, b)` | Diferencia media, pliegues que gana y diferencia / ruido |

## Parámetros de partida (sin optimizar: eso es la etapa 06)

- **Regresión logística:** `max_iter=1000`.
- **Árbol:** `max_depth=6`, `min_samples_leaf=200`.
- **Random forest:** `n_estimators=200`, `min_samples_leaf=50`, `max_features="sqrt"`.
- **LightGBM:** `n_estimators=300`, `learning_rate=0.05`, `num_leaves=31`.
- **XGBoost:** `n_estimators=300`, `learning_rate=0.05`, `max_depth=6`, `tree_method="hist"`.

Todos con `n_jobs=-1` donde aplica.

## Revisión contra la constitución

- **II:** pliegues estratificados por fila; cada cliente aparece una sola vez.
- **III:** la prueba no se carga. El umbral 1/6 sale de la matriz de costos, no se elige con datos.
- **IV:** los resultados por pliegue y las decisiones quedan en `reports/`.
- **VII:** las cifras salen de la ejecución.

## Riesgo

El tiempo de cómputo: 5 modelos × 5 pliegues × unas 243.000 filas. Random forest es el más lento. Se reporta el tiempo de ajuste de cada modelo.

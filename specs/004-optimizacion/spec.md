# Especificación: Optimización de hiperparámetros (`004-optimizacion`)

**Fecha:** 2026-11-05 · **Estado:** aprobado por el grupo (2026-11-05)
**Entrada:** `reports/05_torneo.md` (finalista: LightGBM) · Guía: `material-del-curso/kit/guia-modelado-y-optimizacion.md`, secciones 3 y 4 ·
Ejemplo: `material-del-curso/ejemplo-creditsight/src/creditsight/models/tuning.py`

## Qué se quiere

Construir `src/proyecto/models/tuning.py` y llenar `notebooks/06_optimizacion.ipynb` para buscar los hiperparámetros de
**LightGBM** que **bajan el costo de negocio** (costo esperado por cliente, matriz 5 a 1, llamar si P > 1/6).
Cada ensayo queda registrado en **MLflow** (Databricks; local si no hay conexión). **La prueba no se abre.**

## Qué se optimiza

- **Modelo:** solo LightGBM (decisión del 2026-10-31). XGBoost no se optimiza: queda como referencia del torneo.
- **Métrica que se optimiza:** `cost` (minimizar). En MLflow se registran **todas** las métricas de `metrics_from_proba`
  (PR-AUC, ROC-AUC, captura, recall, precisión, log loss…) con su desviación entre pliegues, para ver lo que el costo esconde.
- **El umbral NO se optimiza:** sigue en 1/6, que sale de la matriz de costos. Optimizarlo a la vez mezclaría dos decisiones.
- **Sin balanceo de clases** (`scale_pos_weight`, `class_weight`): cambiaría las probabilidades y dejaría de valer el umbral 1/6.
- **Mismas variables del torneo:** base + las 5 nuevas (`use_engineered=True`), con `Gender`.

## Datos y validación

- Del entrenamiento (`data/processed/train.parquet`) se **reserva el 25 %** de los clientes, estratificado por `Response`,
  semilla 7. Por fila es válido: cada cliente aparece una sola vez.
- La búsqueda trabaja solo con el 75 % restante, con **3 pliegues estratificados** (semilla 42) para que cada ensayo tarde poco.
- **Comprobación honesta:** LightGBM con parámetros de **partida** (los del torneo) frente al **optimizado**, ambos entrenados con
  el 75 % y evaluados en el 25 % reservado. Intervalo del 95 % de la diferencia de costo con *bootstrap* de clientes (1.000 remuestreos).

## Regla de decisión (escrita antes de mirar)

Se usan los parámetros optimizados **solo si todo el intervalo del 95 % de (costo optimizado − costo de partida) está por debajo de
cero**. Si cruza el cero, la mejora no se distingue del ruido y se conservan los de partida. Como control se reporta también la
diferencia de PR-AUC con su intervalo; no decide.

## Presupuesto

**40 ensayos** de Optuna (muestreador TPE, semilla 42), fijado antes de empezar. El estudio se guarda en disco
(`optuna_06.db`, ignorado por Git) para reanudarlo si se corta.

## Criterios de aceptación

1. Cada ensayo es una ejecución anidada en MLflow con parámetros, todas las métricas y etiquetas (`etapa=06_optimizacion`).
2. Hay 40 ensayos terminados y la gráfica de evolución del costo.
3. La tabla de la comprobación honesta (partida vs. optimizado, diferencia, intervalo) sale del notebook con cifras reales.
4. `reports/06_best_params.json`, `reports/06_comprobacion.csv` y `reports/06_optimizacion.md` quedan completos.
5. `pytest tests` en verde.

"""Optimización de hiperparámetros de LightGBM con Optuna, registrando cada ensayo en MLflow (specs/004-optimizacion).

Adaptado de `material-del-curso/ejemplo-creditsight/src/creditsight/models/tuning.py` a nuestro problema BINARIO:
- se optimiza el costo de negocio (matriz 5 a 1) con el umbral FIJO de 1/6: el umbral no se busca aquí;
- cada cliente aparece una sola vez, así que el bootstrap remuestrea filas (= clientes);
- solo se optimiza LightGBM, el finalista del torneo (reports/05_torneo.md).
La prueba (data/processed/test.parquet) NO se usa aquí.
"""
from pathlib import Path

import mlflow
import numpy as np
import optuna
import pandas as pd
from lightgbm import LGBMClassifier

from proyecto.config import COST_MATRIX, SEED
from proyecto.models.train import build_pipeline, decide, evaluate_folds

MODEL_NAME = "lightgbm"
STAGE_TAG = "06_optimizacion"

# Métricas de `metrics_from_proba` que se pueden optimizar y en qué dirección.
OBJECTIVES = {
    "cost": "minimize",          # negocio: costo esperado por cliente (decide)
    "pr_auc": "maximize",        # técnica principal: ¿quedan los interesados al principio de la lista?
    "roc_auc": "maximize",
    "capture_30": "maximize",    # % de interesados al llamar al 30 % de la base
    "log_loss": "minimize",      # calidad de las probabilidades (importa: el umbral se aplica a la probabilidad)
    "brier": "minimize",
}


def lgbm_space(trial: optuna.Trial) -> dict:
    """Hiperparámetros de un ensayo. Los rangos rodean los valores de partida del torneo (ver specs/004-optimizacion/plan.md)."""
    return {
        "n_estimators": trial.suggest_int("n_estimators", 150, 800),
        "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.2, log=True),
        "num_leaves": trial.suggest_int("num_leaves", 15, 127),
        "min_child_samples": trial.suggest_int("min_child_samples", 20, 500),
        "subsample": trial.suggest_float("subsample", 0.6, 1.0),
        "colsample_bytree": trial.suggest_float("colsample_bytree", 0.5, 1.0),
        "reg_lambda": trial.suggest_float("reg_lambda", 1e-3, 10.0, log=True),
    }


def make_lgbm(params: dict, random_state: int = SEED) -> LGBMClassifier:
    """LightGBM sin balanceo de clases: balancear movería las probabilidades y el umbral 1/6 dejaría de valer.

    `subsample_freq=1` hace que `subsample` tenga efecto (LightGBM lo ignora si la frecuencia es 0).
    """
    return LGBMClassifier(subsample_freq=1, random_state=random_state, verbose=-1, n_jobs=-1, **params)


def tune(X: pd.DataFrame, y, folds, n_trials: int, metric: str = "cost", seed: int = SEED, log: bool = True,
         storage: str | Path | None = None, use_engineered: bool = True) -> optuna.Study:
    """Estudio de Optuna que optimiza `metric` (ver OBJECTIVES) con validación cruzada en `folds`.

    - Cada ensayo guarda TODAS las métricas (media entre pliegues) en `trial.user_attrs`; con `log=True` además queda como
      ejecución anidada en MLflow con sus desviaciones, para poder ordenar la lista por cualquier métrica.
    - Con `storage` (ruta de un archivo .db) el estudio se guarda en disco y se reanuda: solo se corren los ensayos que
      faltan hasta completar `n_trials`.
    """
    if metric not in OBJECTIVES:
        raise ValueError(f"Métrica no soportada: {metric}. Opciones: {sorted(OBJECTIVES)}")

    def objective(trial: optuna.Trial) -> float:
        params = lgbm_space(trial)
        table = evaluate_folds(build_pipeline(make_lgbm(params, seed), use_engineered=use_engineered), X, y, folds)
        means = {col: float(table[col].mean()) for col in table.columns if col != "fold"}
        stds = {f"{col}_std": float(table[col].std()) for col in table.columns if col not in ("fold", "fit_seconds")}
        for name, value in {**means, **stds}.items():
            trial.set_user_attr(name, value)
        if log:
            with mlflow.start_run(run_name=f"{MODEL_NAME}-trial-{trial.number}", nested=True):
                mlflow.log_params(params)
                mlflow.log_metrics({**means, **stds})
                mlflow.set_tags({"etapa": STAGE_TAG, "modelo": MODEL_NAME, "metrica_optimizada": metric,
                                 "ensayo": str(trial.number)})
        return means[metric]

    optuna.logging.set_verbosity(optuna.logging.WARNING)
    study = optuna.create_study(
        direction=OBJECTIVES[metric],
        sampler=optuna.samplers.TPESampler(seed=seed),
        study_name=f"venta-cruzada-{MODEL_NAME}-{metric}",
        storage=f"sqlite:///{Path(storage).as_posix()}" if storage else None,
        load_if_exists=True,
    )
    done = len([t for t in study.trials if t.state == optuna.trial.TrialState.COMPLETE])
    remaining = max(n_trials - done, 0)
    if done:
        print(f"Se reanuda el estudio: {done} ensayos ya hechos, faltan {remaining}.")
    study.set_user_attr("metric", metric)
    if log:
        with mlflow.start_run(run_name=f"optuna-{MODEL_NAME}-{metric}") as parent:
            mlflow.set_tags({"etapa": STAGE_TAG, "modelo": MODEL_NAME, "metrica_optimizada": metric})
            mlflow.log_params({"n_trials": n_trials, "n_folds": len(folds), "n_rows": len(y)})
            study.optimize(objective, n_trials=remaining)
            mlflow.log_metric(f"best_{metric}", study.best_value)
            mlflow.log_params({f"best_{k}": v for k, v in study.best_params.items()})
            study.set_user_attr("mlflow_parent_run_id", parent.info.run_id)
    else:
        study.optimize(objective, n_trials=remaining)
    return study


def _row_costs(y_true, proba, cost=COST_MATRIX) -> np.ndarray:
    """Costo de cada cliente con la decisión de negocio (umbral 1/6)."""
    return np.asarray(cost, dtype=float)[np.asarray(y_true, dtype=int), decide(proba)]


def bootstrap_cost_difference(y_true, proba_a, proba_b, n_boot: int = 1000, seed: int = SEED) -> tuple[float, float, float]:
    """Diferencia de costo por cliente (A menos B) con intervalo del 95 %, remuestreando clientes.

    Cada fila es un cliente distinto, así que remuestrear filas es remuestrear clientes. Negativo: A cuesta menos que B.
    Devuelve (diferencia observada, límite inferior, límite superior).
    """
    diff = _row_costs(y_true, proba_a) - _row_costs(y_true, proba_b)
    rng = np.random.default_rng(seed)
    boot = np.array([diff[rng.integers(0, len(diff), len(diff))].mean() for _ in range(n_boot)])
    return float(diff.mean()), float(np.percentile(boot, 2.5)), float(np.percentile(boot, 97.5))


def bootstrap_metric_difference(y_true, proba_a, proba_b, metric_fn, n_boot: int = 300,
                                seed: int = SEED) -> tuple[float, float, float]:
    """Diferencia de una métrica cualquiera (A menos B) con intervalo del 95 %, remuestreando clientes.

    `metric_fn(y_true, proba)` devuelve un número, p. ej. `average_precision_score` (PR-AUC).
    Positivo: A obtiene una métrica mayor que B.
    """
    y_true, proba_a, proba_b = np.asarray(y_true), np.asarray(proba_a), np.asarray(proba_b)
    rng = np.random.default_rng(seed)
    diffs = []
    for _ in range(n_boot):
        rows = rng.integers(0, len(y_true), len(y_true))
        diffs.append(metric_fn(y_true[rows], proba_a[rows]) - metric_fn(y_true[rows], proba_b[rows]))
    full = metric_fn(y_true, proba_a) - metric_fn(y_true, proba_b)
    return float(full), float(np.percentile(diffs, 2.5)), float(np.percentile(diffs, 97.5))

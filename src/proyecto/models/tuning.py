"""Optimización de los finalistas: espacios de búsqueda, pipeline con parámetros y comprobación honesta.

La búsqueda solo ve una parte del entrenamiento (`busqueda`); la otra parte (`reservado`) sirve para **comprobar** si lo
encontrado es real, porque la mejor puntuación de una búsqueda es **optimista**: es el máximo de muchas estimaciones con ruido.
"""
import numpy as np
import optuna
import pandas as pd
from lightgbm import LGBMClassifier
from sklearn.base import clone
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

from proyecto.models.metrics import COST_FALSE_NEGATIVE, COST_FALSE_POSITIVE, decision_threshold, technical_metrics
from proyecto.models.train import RANDOM_STATE, TOURNAMENT_FEATURES, TOURNAMENT_FEATURES_LINEAR, build_pipeline

FINALISTS = ("lightgbm", "regresion_logistica")

# Parámetros de PARTIDA: exactamente los del torneo (etapa 5). Son la referencia que la optimización debe vencer.
START_PARAMS = {
    "lightgbm": {"n_estimators": 200, "learning_rate": 0.08, "num_leaves": 31, "min_child_samples": 100,
                 "subsample": 0.8, "colsample_bytree": 0.8, "reg_lambda": 0.0},
    "regresion_logistica": {"C": 1.0, "age_spline_knots": 6, "profile_12": False},
}


def lightgbm_space(trial) -> dict:
    """Espacio de búsqueda de LightGBM: cada rango lleva conocimiento del algoritmo, y todos incluyen el valor de partida."""
    return {
        "n_estimators": trial.suggest_int("n_estimators", 100, 500, step=50),                # cuántos árboles
        "learning_rate": trial.suggest_float("learning_rate", 0.02, 0.2, log=True),          # cuánto corrige cada árbol (escala log)
        "num_leaves": trial.suggest_int("num_leaves", 8, 64),                                  # complejidad de cada árbol
        "min_child_samples": trial.suggest_int("min_child_samples", 20, 400, log=True),      # mínimo de clientes por hoja
        "subsample": trial.suggest_float("subsample", 0.6, 1.0),                              # fracción de clientes por árbol
        "colsample_bytree": trial.suggest_float("colsample_bytree", 0.5, 1.0),                # fracción de columnas por árbol
        "reg_lambda": trial.suggest_float("reg_lambda", 0.0, 10.0),                           # penalización de pesos grandes
    }


def logistic_space(trial) -> dict:
    """Espacio de la regresión logística: fuerza de la regularización y flexibilidad de la edad y de los perfiles."""
    return {
        "C": trial.suggest_float("C", 1e-3, 10.0, log=True),                                  # más pequeño = más regularización
        "age_spline_knots": trial.suggest_int("age_spline_knots", 4, 12),                      # flexibilidad de la curva de la edad
        "profile_12": trial.suggest_categorical("profile_12", [False, True]),                  # añade los 12 perfiles (quedó "en observación")
    }


SPACES = {"lightgbm": lightgbm_space, "regresion_logistica": logistic_space}


def build_tuned_pipeline(finalist: str, params: dict, random_state: int = RANDOM_STATE) -> Pipeline:
    """Pipeline completo del finalista con unos parámetros dados (los de partida o los de un ensayo)."""
    if finalist == "lightgbm":
        model = LGBMClassifier(**params, subsample_freq=1, random_state=random_state, n_jobs=4, verbose=-1)
        return build_pipeline(model, TOURNAMENT_FEATURES)
    if finalist == "regresion_logistica":
        options = TOURNAMENT_FEATURES_LINEAR.with_changes(age_spline_knots=int(params["age_spline_knots"]), profile_12=bool(params["profile_12"]))
        return build_pipeline(LogisticRegression(C=float(params["C"]), max_iter=500, random_state=random_state), options)
    raise ValueError(f"finalista desconocido: {finalist!r}; opciones: {FINALISTS}")


def evaluate_pipeline(pipeline: Pipeline, X: pd.DataFrame, y, folds) -> pd.DataFrame:
    """Valida un pipeline con `folds`: una fila por pliegue con todas las métricas de `technical_metrics`."""
    y = np.asarray(y)
    rows = []
    for train_idx, valid_idx in folds:
        model = clone(pipeline).fit(X.iloc[train_idx], y[train_idx])
        proba = model.predict_proba(X.iloc[valid_idx])[:, 1]
        rows.append(technical_metrics(y[valid_idx], proba))
    return pd.DataFrame(rows)


def per_client_cost(y_true, proba, fn_cost: float = COST_FALSE_NEGATIVE, fp_cost: float = COST_FALSE_POSITIVE) -> np.ndarray:
    """Costo de la decisión de cada cliente (0, `fp_cost` o `fn_cost`), llamando si la probabilidad supera el umbral."""
    y_true = np.asarray(y_true)
    call = np.asarray(proba) >= decision_threshold(fn_cost, fp_cost)
    cost = np.zeros(len(y_true))
    cost[call & (y_true == 0)] = fp_cost          # falsa alarma
    cost[~call & (y_true == 1)] = fn_cost         # venta perdida
    return cost


def bootstrap_interval(difference_per_client, clients, n: int = 1000, seed: int = 42, level: float = 95.0) -> tuple:
    """Intervalo del `level` % de la diferencia media, remuestreando **clientes completos** (no filas sueltas).

    `difference_per_client` = costo(optimizado) - costo(partida), fila a fila. Negativo = el optimizado mejora.
    Si un mismo cliente aparece en varias filas, pasarlo en `clients` las mantiene juntas al remuestrear.
    """
    table = pd.DataFrame({"g": np.asarray(clients), "d": np.asarray(difference_per_client, dtype=float)}).groupby("g")["d"].agg(["sum", "count"])
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(table), size=(n, len(table)))
    means = table["sum"].to_numpy()[idx].sum(axis=1) / table["count"].to_numpy()[idx].sum(axis=1)
    low, high = np.percentile(means, [(100 - level) / 2, 100 - (100 - level) / 2])
    return float(low), float(high)


def run_search(finalist: str, X: pd.DataFrame, y, folds, n_trials: int = 20, seed: int = 42, on_trial=None):
    """Búsqueda de hiperparámetros de un finalista con Optuna (TPE) y un presupuesto fijo de ensayos.

    - El **ensayo 0 es siempre la configuración de partida**, medida con los mismos pliegues: la comparación es limpia.
    - Cada ensayo guarda en `trial.user_attrs` el ruido entre pliegues, la PR-AUC y el log loss.
    - `on_trial(study, trial)` se llama al terminar cada ensayo: sirve para registrarlo en MLflow.
    Devuelve el `study` de Optuna (minimiza el costo por cliente).
    """
    if finalist not in SPACES:
        raise ValueError(f"finalista desconocido: {finalist!r}; opciones: {FINALISTS}")
    y = np.asarray(y)
    study = optuna.create_study(direction="minimize", sampler=optuna.samplers.TPESampler(seed=seed), study_name=finalist)
    study.enqueue_trial(START_PARAMS[finalist])

    def objective(trial):
        params = SPACES[finalist](trial)
        table = evaluate_pipeline(build_tuned_pipeline(finalist, params), X, y, folds)
        trial.set_user_attr("cost_sd", float(table["cost"].std(ddof=1)))
        trial.set_user_attr("pr_auc", float(table["pr_auc"].mean()))
        trial.set_user_attr("log_loss", float(table["log_loss"].mean()))
        return float(table["cost"].mean())

    study.optimize(objective, n_trials=n_trials, callbacks=[on_trial] if on_trial else None)
    return study

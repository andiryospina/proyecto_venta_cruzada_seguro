"""Candidatos, métrica de costo de negocio y evaluación con validación cruzada (specs/003-torneo).

Sigue el patrón del ejemplo del curso (`material-del-curso/ejemplo-creditsight/src/creditsight/models/train.py`),
adaptado a un problema BINARIO: ¿llamamos o no a este cliente para ofrecerle el seguro de vehículo?

- La decisión de negocio es llamar si P(interesado) > umbral de costo (1/6 con la matriz 5 a 1).
- Todo el preprocesamiento va dentro del Pipeline: en cada pliegue se ajusta solo con su parte de entrenamiento.
- La prueba (data/processed/test.parquet) NO se usa aquí.
"""
import time

import numpy as np
import pandas as pd
from lightgbm import LGBMClassifier
from sklearn.base import BaseEstimator, ClassifierMixin, clone
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    average_precision_score,
    balanced_accuracy_score,
    brier_score_loss,
    f1_score,
    log_loss,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import StratifiedKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer
from sklearn.tree import DecisionTreeClassifier
from xgboost import XGBClassifier

from proyecto.config import COST_MATRIX, CV_FOLDS, SEED, TARGET
from proyecto.features.engineering import add_features
from proyecto.features.preprocessing import build_preprocessor

BASELINE_PRIOR = "línea base: clase más frecuente"
BASELINE_RULE = "línea base: regla de negocio"


# --- Costo y decisión --------------------------------------------------------------------------------

def cost_threshold(cost=COST_MATRIX) -> float:
    """Probabilidad a partir de la cual conviene llamar: costo_FP / (costo_FP + costo_FN).

    Con la matriz 5 a 1: 1 / (1 + 5) = 1/6 ≈ 0,167. Llamar cuesta menos que no llamar cuando P(interesado) > 1/6.
    """
    cost = np.asarray(cost, dtype=float)
    false_positive, false_negative = cost[0, 1], cost[1, 0]
    return float(false_positive / (false_positive + false_negative))


def expected_cost(y_true, decision, cost=COST_MATRIX) -> float:
    """Costo promedio por cliente según la matriz (menor es mejor)."""
    cost = np.asarray(cost, dtype=float)
    return float(cost[np.asarray(y_true, dtype=int), np.asarray(decision, dtype=int)].mean())


def decide(proba, threshold: float | None = None) -> np.ndarray:
    """1 = llamar, 0 = no llamar. Por defecto usa el umbral de costo (1/6)."""
    threshold = cost_threshold() if threshold is None else threshold
    return (np.asarray(proba) > threshold).astype(int)


def capture_at(y_true, proba, share: float) -> float:
    """% de los interesados que quedan dentro del `share` de clientes con mayor probabilidad.

    Responde: "si el equipo solo puede llamar al 20 % de la base, ¿a qué % de los interesados alcanza?"
    """
    y_true = np.asarray(y_true)
    n_top = int(np.ceil(share * len(y_true)))
    top = np.argsort(-np.asarray(proba), kind="stable")[:n_top]
    return float(y_true[top].sum() / y_true.sum())


def metrics_from_proba(y_true, proba) -> dict:
    """Métricas de un pliegue: las de negocio (deciden) y las técnicas (muestran lo que el costo puede esconder).

    - Negocio: costo con el umbral 1/6, costo con el umbral 0,5 (para ver cuánto aporta el umbral) y % de clientes a llamar.
    - Técnicas de clasificación (con la decisión de negocio): recall, precisión, F1 y exactitud balanceada.
    - Técnicas de ordenamiento (con las probabilidades): PR-AUC (principal técnica), ROC-AUC y captura al 20/30/50 %.
    - Calibración: log loss y Brier.
    """
    y_true = np.asarray(y_true, dtype=int)
    proba = np.clip(np.asarray(proba, dtype=float), 1e-6, 1 - 1e-6)
    decision = decide(proba)
    return {
        # negocio
        "cost": expected_cost(y_true, decision),
        "cost_at_05": expected_cost(y_true, decide(proba, 0.5)),
        "contact_rate": float(decision.mean()),
        # técnicas de ordenamiento
        "pr_auc": float(average_precision_score(y_true, proba)),
        "roc_auc": float(roc_auc_score(y_true, proba)),
        "capture_20": capture_at(y_true, proba, 0.2),
        "capture_30": capture_at(y_true, proba, 0.3),
        "capture_50": capture_at(y_true, proba, 0.5),
        # técnicas de clasificación (con la decisión de negocio)
        "recall": float(recall_score(y_true, decision, zero_division=0)),
        "precision": float(precision_score(y_true, decision, zero_division=0)),
        "f1": float(f1_score(y_true, decision, zero_division=0)),
        "balanced_accuracy": float(balanced_accuracy_score(y_true, decision)),
        # calibración
        "log_loss": float(log_loss(y_true, proba, labels=[0, 1])),
        "brier": float(brier_score_loss(y_true, proba)),
    }


# --- Candidatos ----------------------------------------------------------------------------------------

class BusinessRuleClassifier(ClassifierMixin, BaseEstimator):
    """La regla de negocio como modelo: "llamar a quien no tiene seguro de vehículo y ya tuvo daño".

    En `fit` aprende, solo con el entrenamiento del pliegue, la tasa de interés de cada grupo (cumple / no cumple la
    regla); esa tasa es su probabilidad. Así se evalúa con las mismas métricas y pliegues que los modelos.
    """

    def fit(self, X, y):
        rule = self._rule(X)
        y = np.asarray(y, dtype=int)
        self.classes_ = np.array([0, 1])
        self.rate_rule_ = float(y[rule].mean()) if rule.any() else 0.0
        self.rate_other_ = float(y[~rule].mean()) if (~rule).any() else 0.0
        return self

    def predict_proba(self, X):
        p = np.where(self._rule(X), self.rate_rule_, self.rate_other_)
        return np.column_stack([1 - p, p])

    def predict(self, X):
        return decide(self.predict_proba(X)[:, 1])

    @staticmethod
    def _rule(X) -> np.ndarray:
        uninsured = pd.Series(X["Previously_Insured"]).astype(float).eq(0).to_numpy()
        damaged = pd.Series(X["Vehicle_Damage"]).astype(float).eq(1).to_numpy()
        return uninsured & damaged


def candidates(random_state: int = SEED) -> dict:
    """Las 2 líneas base y los 5 modelos del torneo, con parámetros de partida fijos (sin optimizar)."""
    return {
        BASELINE_PRIOR: DummyClassifier(strategy="prior"),
        BASELINE_RULE: BusinessRuleClassifier(),
        "regresión logística": LogisticRegression(max_iter=1000, random_state=random_state),
        "árbol de decisión": DecisionTreeClassifier(max_depth=6, min_samples_leaf=200, random_state=random_state),
        "random forest": RandomForestClassifier(
            n_estimators=200, min_samples_leaf=50, max_features="sqrt", n_jobs=-1, random_state=random_state
        ),
        "lightgbm": LGBMClassifier(
            n_estimators=300, learning_rate=0.05, num_leaves=31, n_jobs=-1, random_state=random_state, verbose=-1
        ),
        "xgboost": XGBClassifier(
            n_estimators=300, learning_rate=0.05, max_depth=6, tree_method="hist", n_jobs=-1,
            random_state=random_state, eval_metric="logloss",
        ),
    }


def build_pipeline(model, use_engineered: bool | list[str] = False, use_gender: bool = True) -> Pipeline:
    """Pipeline completo: (variables nuevas) → preprocesamiento → modelo. Se ajusta y se guarda entero.

    La regla de negocio no necesita preprocesamiento: lee las columnas limpias directamente.
    """
    if isinstance(model, BusinessRuleClassifier):
        return Pipeline([("model", model)])
    steps = []
    if use_engineered:
        steps.append(("features", FunctionTransformer(add_features)))
    steps.append(("prep", build_preprocessor(use_engineered=use_engineered, use_gender=use_gender)))
    steps.append(("model", model))
    return Pipeline(steps)


# --- Validación cruzada --------------------------------------------------------------------------------

def split_xy(df: pd.DataFrame) -> tuple[pd.DataFrame, np.ndarray]:
    """Separa el objetivo. X conserva todas las columnas limpias: el Pipeline elige las que usa (id queda fuera)."""
    return df.drop(columns=[TARGET]), df[TARGET].astype(int).to_numpy()


def make_folds(X: pd.DataFrame, y, n_splits: int = CV_FOLDS, seed: int = SEED) -> list:
    """Los pliegues estratificados, calculados UNA vez y reutilizados para todos los modelos y variantes."""
    return list(StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=seed).split(X, y))


def evaluate_folds(pipeline, X: pd.DataFrame, y, folds) -> pd.DataFrame:
    """Una fila por pliegue con todas las métricas y los segundos de ajuste."""
    y = np.asarray(y)
    rows = []
    for fold, (train_idx, valid_idx) in enumerate(folds):
        model = clone(pipeline)
        start = time.time()
        model.fit(X.iloc[train_idx], y[train_idx])
        seconds = time.time() - start
        proba = model.predict_proba(X.iloc[valid_idx])[:, 1]
        rows.append({"fold": fold, **metrics_from_proba(y[valid_idx], proba), "fit_seconds": seconds})
    return pd.DataFrame(rows)


def run_tournament(pipelines: dict, X: pd.DataFrame, y, folds, verbose: bool = True) -> pd.DataFrame:
    """Evalúa cada pipeline en los mismos pliegues. Devuelve una tabla larga: una fila por modelo y pliegue."""
    tables = []
    for name, pipeline in pipelines.items():
        table = evaluate_folds(pipeline, X, y, folds)
        table.insert(0, "model", name)
        tables.append(table)
        if verbose:
            print(f"{name:34s} costo {table['cost'].mean():.4f} ± {table['cost'].std():.4f} "
                  f"| PR-AUC {table['pr_auc'].mean():.4f} | {table['fit_seconds'].mean():.1f} s por pliegue")
    return pd.concat(tables, ignore_index=True)


def summarize(per_fold: pd.DataFrame, metric: str = "cost") -> pd.DataFrame:
    """Media y desviación entre pliegues de cada métrica, por modelo, ordenada por `metric` (menor es mejor)."""
    numeric = per_fold.drop(columns="fold")
    means = numeric.groupby("model").mean().add_suffix("_mean")
    stds = numeric.groupby("model").std().add_suffix("_std")
    return means.join(stds).sort_values(f"{metric}_mean")


# --- Comparaciones -----------------------------------------------------------------------------------

def improvement_over_noise(reference, variant) -> dict:
    """Etapa 04 (fórmula de la guía): mejora = media(referencia) − media(variante), en una métrica donde MENOR es mejor;
    ruido = desviación de la variante entre pliegues. Una idea se conserva si mejora / ruido > 1."""
    reference, variant = np.asarray(reference, float), np.asarray(variant, float)
    improvement = reference.mean() - variant.mean()
    noise = variant.std(ddof=1)
    return {
        "improvement": float(improvement),
        "noise": float(noise),
        "improvement_over_noise": float(improvement / noise) if noise > 0 else float("inf"),
        "folds_won": int((variant < reference).sum()),
    }


def compare_paired(best, other) -> dict:
    """Torneo: compara pliegue a pliegue dos modelos (valores donde MENOR es mejor). Diferencia positiva: `best` gana."""
    diff = np.asarray(other, float) - np.asarray(best, float)
    noise = diff.std(ddof=1)
    return {
        "mean_difference": float(diff.mean()),
        "folds_won": f"{int((diff > 0).sum())} de {len(diff)}",
        "difference_over_noise": float(diff.mean() / noise) if noise > 0 else float("inf"),
    }

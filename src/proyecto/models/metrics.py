"""Métricas de negocio y técnicas para comparar variables y modelos.

La métrica de negocio es el **costo promedio por cliente** en "unidades de llamada" (ver `notebooks/01_caso_negocio.ipynb`):
una falsa alarma cuesta 1 y una venta perdida cuesta R. **R = 5 es una hipótesis de trabajo** que el negocio debe confirmar;
cambiarla aquí cambia el costo y el umbral, no el ranking de modelos medido con PR-AUC.
"""
import numpy as np
from sklearn.metrics import (
    average_precision_score,
    balanced_accuracy_score,
    brier_score_loss,
    f1_score,
    log_loss,
    make_scorer,
    precision_score,
    recall_score,
    roc_auc_score,
)

COST_FALSE_POSITIVE = 1.0   # llamar a quien no compra
COST_FALSE_NEGATIVE = 5.0   # no llamar a quien habría comprado (R = 5, por confirmar con el negocio)


def decision_threshold(fn_cost: float = COST_FALSE_NEGATIVE, fp_cost: float = COST_FALSE_POSITIVE) -> float:
    """Probabilidad desde la cual conviene llamar: 1 / (R + 1) cuando la falsa alarma cuesta 1."""
    return fp_cost / (fp_cost + fn_cost)


def cost_per_client(y_true, y_pred, fn_cost: float = COST_FALSE_NEGATIVE, fp_cost: float = COST_FALSE_POSITIVE) -> float:
    """Costo promedio por cliente de las decisiones `y_pred` (0/1)."""
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)
    false_alarms = ((y_pred == 1) & (y_true == 0)).sum()
    lost_sales = ((y_pred == 0) & (y_true == 1)).sum()
    return float((false_alarms * fp_cost + lost_sales * fn_cost) / len(y_true))


def cost_at_threshold(y_true, proba, fn_cost: float = COST_FALSE_NEGATIVE, fp_cost: float = COST_FALSE_POSITIVE) -> float:
    """Costo promedio por cliente si se llama a todo cliente cuya probabilidad supera el umbral óptimo."""
    return cost_per_client(y_true, np.asarray(proba) >= decision_threshold(fn_cost, fp_cost), fn_cost, fp_cost)


def make_scoring(fn_cost: float = COST_FALSE_NEGATIVE, fp_cost: float = COST_FALSE_POSITIVE) -> dict:
    """Métricas para `cross_validate`: PR-AUC (principal), costo (negocio), log loss y ROC-AUC (control)."""
    return {
        "pr_auc": "average_precision",
        "cost": make_scorer(cost_at_threshold, response_method="predict_proba", greater_is_better=False,
                            fn_cost=fn_cost, fp_cost=fp_cost),
        "log_loss": "neg_log_loss",
        "roc_auc": "roc_auc",
    }


TOP_SHARE = 0.20   # capacidad de contacto de referencia: el equipo puede llamar al 20 % mejor puntuado [por confirmar con el negocio]


def technical_metrics(y_true, proba, fn_cost: float = COST_FALSE_NEGATIVE, fp_cost: float = COST_FALSE_POSITIVE,
                      top_share: float = TOP_SHARE) -> dict:
    """Métricas de un modelo en un pliegue: de **ranking**, de **decisión** y de **negocio**.

    - Ranking (usan solo las probabilidades): `roc_auc`, `pr_auc`, `recall_top`, `lift_top`.
    - Decisión (llama si la probabilidad supera 1 / (R + 1)): exactitud balanceada, precisión y recall por clase, F1 macro,
      porcentaje de clientes contactados.
    - Calidad de las probabilidades: `log_loss` y `brier`.
    - Negocio: `cost` (con el umbral de arriba) y `cost_top` (si solo se llama al `top_share` mejor puntuado: no depende de
      que las probabilidades estén calibradas).
    """
    y_true = np.asarray(y_true)
    proba = np.asarray(proba, dtype=float)
    decision = (proba >= decision_threshold(fn_cost, fp_cost)).astype(int)

    order = np.argsort(-proba, kind="stable")
    n_top = int(np.ceil(top_share * len(y_true)))
    in_top = np.zeros(len(y_true), dtype=bool)
    in_top[order[:n_top]] = True
    recall_top = float(y_true[in_top].sum() / y_true.sum())

    return {
        "roc_auc": roc_auc_score(y_true, proba),
        "pr_auc": average_precision_score(y_true, proba),
        "recall_top": recall_top,
        "lift_top": recall_top / top_share,
        "balanced_accuracy": balanced_accuracy_score(y_true, decision),
        "precision_1": precision_score(y_true, decision, zero_division=0),
        "recall_0": recall_score(y_true, decision, pos_label=0, zero_division=0),
        "recall_1": recall_score(y_true, decision, pos_label=1, zero_division=0),
        "f1_macro": f1_score(y_true, decision, average="macro", zero_division=0),
        "contact_rate": float(decision.mean()),
        "log_loss": log_loss(y_true, np.clip(proba, 1e-6, 1 - 1e-6), labels=[0, 1]),
        "brier": brier_score_loss(y_true, proba),
        "cost": cost_per_client(y_true, decision, fn_cost, fp_cost),
        "cost_top": cost_per_client(y_true, in_top.astype(int), fn_cost, fp_cost),
    }

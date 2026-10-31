"""Métricas de negocio y técnicas para comparar variables y modelos.

La métrica de negocio es el **costo promedio por cliente** en "unidades de llamada" (ver `notebooks/01_caso_negocio.ipynb`):
una falsa alarma cuesta 1 y una venta perdida cuesta R. **R = 5 es una hipótesis de trabajo** que el negocio debe confirmar;
cambiarla aquí cambia el costo y el umbral, no el ranking de modelos medido con PR-AUC.
"""
import numpy as np
from sklearn.metrics import make_scorer

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

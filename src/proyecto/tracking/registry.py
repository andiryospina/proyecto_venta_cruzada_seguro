"""Funciones del registro del modelo (etapa 08): qué parámetros y métricas acompañan al modelo, y la ida y vuelta.

Todo sale de `reports/07_metricas_test.json`: aquí no se calcula ni se inventa ninguna métrica, solo se copia.
"""
import numpy as np

from proyecto.models.train import cost_threshold

# Métricas del modelo en la prueba que se registran (nombre en el JSON de la etapa 07)
_MODEL_METRICS = ("pr_auc", "roc_auc", "recall", "precision", "contact_rate",
                  "capture_20", "capture_30", "capture_50", "log_loss", "brier")


def registry_params(decisions: dict) -> dict:
    """Parámetros a registrar: tipo de modelo, hiperparámetros, umbral de decisión y si se calibró.

    `decisions` es el bloque `decisiones` de `07_metricas_test.json`. Devuelve un diccionario plano.
    """
    params = {"model_type": decisions["modelo_final"]}
    params.update(decisions["parametros"])
    params["threshold"] = cost_threshold()   # 1/6 con la matriz 5 a 1
    params["calibrated"] = decisions["calibrar"]
    return params


def registry_metrics(test_block: dict) -> dict:
    """Métricas de la prueba a registrar, solo números y con nombres planos.

    `test_block` es el bloque `prueba` de `07_metricas_test.json`. Si falta una clave lanza `KeyError`
    (mejor un error que registrar un cero inventado).
    """
    model = test_block["modelo"]
    low, high = model["cost_ic95"]
    metrics = {"test_cost": model["cost"], "test_cost_ic95_low": low, "test_cost_ic95_high": high}
    for name in _MODEL_METRICS:
        metrics[f"test_{name}"] = model[name]
    diff = test_block["diferencia_costo"]
    diff_low, diff_high = diff["ic95"]
    metrics.update({"baseline_cost": test_block["linea_base"]["cost"], "cost_diff": diff["valor"],
                    "cost_diff_ic95_low": diff_low, "cost_diff_ic95_high": diff_high})
    return {name: float(value) for name, value in metrics.items()}


def max_proba_difference(model_a, model_b, X) -> float:
    """Mayor diferencia absoluta entre las probabilidades de "interesado" de dos modelos en las mismas filas."""
    proba_a = model_a.predict_proba(X)[:, 1]
    proba_b = model_b.predict_proba(X)[:, 1]
    return float(np.max(np.abs(proba_a - proba_b)))

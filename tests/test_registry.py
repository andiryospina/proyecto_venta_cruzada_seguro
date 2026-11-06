"""Pruebas de las funciones de registro del modelo (etapa 08). No tocan MLflow, Databricks ni el modelo real."""
import numpy as np
import pandas as pd
import pytest
from sklearn.linear_model import LogisticRegression

from proyecto.tracking.registry import max_proba_difference, registry_metrics, registry_params


def _decisions():
    return {
        "modelo_final": "lightgbm",
        "parametros": {"n_estimators": 186, "learning_rate": 0.0315, "num_leaves": 31},
        "calibrar": False,
        "variables": "texto que no se registra",
    }


def _test_block():
    model = {"cost": 0.33, "cost_ic95": [0.32, 0.34], "pr_auc": 0.35, "roc_auc": 0.85, "recall": 0.88,
             "precision": 0.30, "contact_rate": 0.36, "capture_20": 0.56, "capture_30": 0.78, "capture_50": 0.99,
             "log_loss": 0.27, "brier": 0.09}
    return {"clientes": 100, "modelo": model, "linea_base": {"cost": 0.37},
            "diferencia_costo": {"valor": -0.04, "ic95": [-0.045, -0.036]}}


def test_registry_params_is_flat_and_has_threshold():
    params = registry_params(_decisions())
    assert params["model_type"] == "lightgbm"
    assert params["n_estimators"] == 186 and params["learning_rate"] == 0.0315
    assert params["threshold"] == pytest.approx(1 / 6)
    assert params["calibrated"] is False
    assert all(not isinstance(v, (dict, list)) for v in params.values())


def test_registry_metrics_copies_exact_numbers():
    metrics = registry_metrics(_test_block())
    assert metrics == {
        "test_cost": 0.33, "test_cost_ic95_low": 0.32, "test_cost_ic95_high": 0.34,
        "test_pr_auc": 0.35, "test_roc_auc": 0.85, "test_recall": 0.88, "test_precision": 0.30,
        "test_contact_rate": 0.36, "test_capture_20": 0.56, "test_capture_30": 0.78, "test_capture_50": 0.99,
        "test_log_loss": 0.27, "test_brier": 0.09,
        "baseline_cost": 0.37, "cost_diff": -0.04, "cost_diff_ic95_low": -0.045, "cost_diff_ic95_high": -0.036,
    }
    assert all(isinstance(v, float) for v in metrics.values())


def test_registry_metrics_fails_if_a_metric_is_missing():
    block = _test_block()
    del block["modelo"]["pr_auc"]
    with pytest.raises(KeyError):
        registry_metrics(block)


def test_max_proba_difference():
    rng = np.random.default_rng(0)
    X = pd.DataFrame(rng.normal(size=(60, 2)), columns=["a", "b"])
    y = (X["a"] > 0).astype(int)
    model_a = LogisticRegression().fit(X, y)
    model_b = LogisticRegression(C=0.01).fit(X, y)
    assert max_proba_difference(model_a, model_a, X) == 0.0
    assert max_proba_difference(model_a, model_b, X) > 0

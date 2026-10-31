"""Pruebas del torneo: líneas base, métricas técnicas por pliegue y candidatos."""
import numpy as np
import pandas as pd
import pytest

from proyecto.models.baselines import DamageRuleClassifier
from proyecto.models.metrics import TOP_SHARE, decision_threshold, technical_metrics
from proyecto.models.train import tournament_candidates

from test_features import make_clean_frame


# --- línea base de negocio: llamar si hubo daño
def test_damage_rule_learns_the_rate_of_each_group_from_training_only():
    X = pd.DataFrame({"Vehicle_Damage": [1, 1, 1, 1, 0, 0, 0, 0]})
    y = np.array([1, 1, 0, 0, 0, 0, 0, 1])
    rule = DamageRuleClassifier().fit(X, y)
    proba = rule.predict_proba(pd.DataFrame({"Vehicle_Damage": [1, 0]}))
    assert proba[:, 1].tolist() == pytest.approx([0.5, 0.25])
    assert np.allclose(proba.sum(axis=1), 1.0)
    assert rule.predict(pd.DataFrame({"Vehicle_Damage": [1, 0, 1]})).tolist() == [1, 0, 1]


def test_damage_rule_uses_the_global_rate_for_a_value_it_never_saw():
    X = pd.DataFrame({"Vehicle_Damage": [1, 1, 1, 1]})        # en el entrenamiento nadie tiene 0
    y = np.array([1, 0, 0, 0])
    proba = DamageRuleClassifier().fit(X, y).predict_proba(pd.DataFrame({"Vehicle_Damage": [0]}))
    assert proba[0, 1] == pytest.approx(0.25)


# --- métricas técnicas
def test_perfect_ranking_has_perfect_auc_and_lift():
    y = np.array([1] * 20 + [0] * 80)
    proba = np.array([0.9] * 20 + [0.01] * 80)
    m = technical_metrics(y, proba)
    assert m["roc_auc"] == pytest.approx(1.0) and m["pr_auc"] == pytest.approx(1.0)
    assert m["recall_top"] == pytest.approx(1.0)
    assert m["lift_top"] == pytest.approx(1.0 / TOP_SHARE)
    assert m["cost"] == 0.0 and m["cost_top"] == 0.0


def test_constant_probability_is_no_better_than_chance():
    y = np.array([1] * 12 + [0] * 88)
    m = technical_metrics(y, np.full(100, y.mean()))
    assert m["roc_auc"] == pytest.approx(0.5)
    assert m["pr_auc"] == pytest.approx(y.mean())
    assert m["contact_rate"] == 0.0                             # 0,12 < 1/6: nunca llama
    assert m["recall_1"] == 0.0 and m["recall_0"] == 1.0
    assert m["cost"] == pytest.approx(0.12 * 5)                 # todas las ventas se pierden a costo R = 5


def test_decision_metrics_follow_the_cost_threshold():
    y = np.array([1, 1, 0, 0])
    proba = np.array([0.20, 0.10, 0.20, 0.05])                 # umbral 1/6 = 0,167: llama a los clientes 0 y 2
    m = technical_metrics(y, proba)
    assert decision_threshold() == pytest.approx(1 / 6)
    assert m["contact_rate"] == 0.5
    assert m["precision_1"] == pytest.approx(0.5) and m["recall_1"] == pytest.approx(0.5)
    assert m["cost"] == pytest.approx((1 * 1 + 1 * 5) / 4)      # 1 falsa alarma y 1 venta perdida


def test_cost_top_depends_only_on_the_ranking_not_on_calibration():
    y = np.array([1, 0, 0, 0, 0, 1, 0, 0, 0, 0])
    a = np.array([0.9, 0.8, 0.1, 0.1, 0.1, 0.7, 0.1, 0.1, 0.1, 0.1])
    b = a / 100.0                                                  # mismo orden, probabilidades descalibradas
    assert technical_metrics(y, a)["cost_top"] == pytest.approx(technical_metrics(y, b)["cost_top"])
    assert technical_metrics(y, a)["recall_top"] == pytest.approx(technical_metrics(y, b)["recall_top"])


# --- candidatos
def test_candidates_include_baselines_and_at_least_three_models():
    candidates = tournament_candidates()
    baselines = [n for n in candidates if n.startswith("línea base")]
    assert len(baselines) >= 1 and len(candidates) - len(baselines) >= 3


def test_every_candidate_fits_and_returns_probabilities_for_the_same_data():
    frame = make_clean_frame(500, seed=2)
    X, y = frame.drop(columns="Response"), frame["Response"]
    for name, estimator in tournament_candidates().items():
        proba = estimator.fit(X, y).predict_proba(X.head(20))
        assert proba.shape == (20, 2), name
        assert np.isfinite(proba).all() and np.allclose(proba.sum(axis=1), 1.0), name


def test_tournament_features_drop_the_variables_retired_in_stage_4():
    from proyecto.features.engineering import build_preprocessor
    from proyecto.models.train import TOURNAMENT_FEATURES, TOURNAMENT_FEATURES_LINEAR

    frame = make_clean_frame(400)
    X, y = frame.drop(columns="Response"), frame["Response"]
    for options in (TOURNAMENT_FEATURES, TOURNAMENT_FEATURES_LINEAR):
        names = list(build_preprocessor(options).fit(X, y).get_feature_names_out())
        assert "Vintage" not in names and "Driving_License" not in names and not any(n.startswith("Gender") for n in names)
        assert "Annual_Premium" in names and "Previously_Insured" in names     # la prima se conserva (decisión de la etapa 4)

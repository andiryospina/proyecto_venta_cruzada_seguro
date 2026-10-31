"""Pruebas de train.py (specs/003-torneo). Casos hechos a mano."""
import numpy as np
import pandas as pd
import pytest

from proyecto.config import ENGINEERED_FEATURES
from proyecto.data.cleaning import clean
from proyecto.features.engineering import feature_columns
from proyecto.models.train import (
    BusinessRuleClassifier,
    build_pipeline,
    candidates,
    capture_at,
    compare_paired,
    cost_threshold,
    decide,
    evaluate_folds,
    expected_cost,
    improvement_over_noise,
    make_folds,
    metrics_from_proba,
    split_xy,
)


# --- costo y decisión ------------------------------------------------------------------------------

def test_cost_threshold_is_one_sixth():
    assert cost_threshold() == pytest.approx(1 / 6)


def test_expected_cost_zero_when_perfect():
    y = np.array([0, 1, 1, 0])
    assert expected_cost(y, y) == 0.0


def test_expected_cost_uses_matrix():
    # no llamar a un interesado cuesta 5; llamar a un no interesado cuesta 1
    assert expected_cost([1], [0]) == 5.0
    assert expected_cost([0], [1]) == 1.0
    assert expected_cost([1, 0], [0, 1]) == 3.0


def test_decide_uses_cost_threshold():
    """0,2 es poco para 0,5 pero suficiente para llamar con el umbral de costo (1/6)."""
    assert decide([0.10, 0.20, 0.60]).tolist() == [0, 1, 1]
    assert decide([0.10, 0.20, 0.60], threshold=0.5).tolist() == [0, 0, 1]


def test_capture_at():
    y = np.array([1, 0, 1, 0, 0, 0, 0, 0, 0, 1])
    proba = np.array([0.9, 0.1, 0.8, 0.2, 0.1, 0.1, 0.1, 0.1, 0.1, 0.05])
    assert capture_at(y, proba, 0.2) == pytest.approx(2 / 3)   # los 2 de mayor probabilidad son interesados
    assert capture_at(y, proba, 1.0) == 1.0


# --- métricas -----------------------------------------------------------------------------------------

def test_perfect_probabilities():
    y = np.array([0, 1, 0, 1, 0, 0, 1, 0])
    m = metrics_from_proba(y, y.astype(float))
    assert m["cost"] == 0.0 and m["pr_auc"] == pytest.approx(1.0) and m["roc_auc"] == 1.0
    assert m["recall"] == 1.0 and m["precision"] == 1.0


def test_uninformative_probabilities():
    rng = np.random.default_rng(0)
    y = rng.binomial(1, 0.12, 5000)
    m = metrics_from_proba(y, rng.uniform(size=5000))
    assert abs(m["roc_auc"] - 0.5) < 0.05
    assert abs(m["pr_auc"] - y.mean()) < 0.03          # PR-AUC al azar ≈ proporción de interesados


def test_threshold_beats_05_when_positives_are_rare():
    """Con interesados poco probables, el umbral 1/6 encuentra más interesados que 0,5 y cuesta menos."""
    y = np.array([1, 0, 0, 0, 0, 1, 0, 0, 0, 0])
    proba = np.array([0.3, 0.1, 0.1, 0.1, 0.1, 0.25, 0.1, 0.1, 0.1, 0.1])
    m = metrics_from_proba(y, proba)
    assert m["cost"] < m["cost_at_05"]


# --- candidatos y pipeline -------------------------------------------------------------------------

def _clean_sample(n: int = 600, seed: int = 0) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    insured = rng.integers(0, 2, n)
    damage = rng.integers(0, 2, n)
    p = np.where((insured == 0) & (damage == 1), 0.4, 0.02)
    raw = pd.DataFrame({
        "id": np.arange(n), "Gender": rng.choice(["Male", "Female"], n), "Age": rng.integers(20, 85, n),
        "Driving_License": np.ones(n, int), "Region_Code": rng.choice([28.0, 8.0, 3.0], n),
        "Previously_Insured": insured, "Vehicle_Age": rng.choice(["< 1 Year", "1-2 Year", "> 2 Years"], n),
        "Vehicle_Damage": np.where(damage == 1, "Yes", "No"), "Annual_Premium": rng.uniform(2630, 60000, n),
        "Policy_Sales_Channel": rng.choice([26.0, 152.0], n), "Vintage": rng.integers(10, 300, n),
        "Response": rng.binomial(1, p),
    })
    return clean(raw)


def test_business_rule_classifier_learns_group_rates():
    data = _clean_sample()
    X, y = split_xy(data)
    rule = BusinessRuleClassifier().fit(X, y)
    in_rule = (X["Previously_Insured"] == 0) & (X["Vehicle_Damage"] == 1)
    assert rule.rate_rule_ == pytest.approx(y[in_rule.to_numpy()].mean())
    assert rule.predict(X).tolist() == in_rule.astype(int).tolist()   # 0,4 > 1/6 > 0,02: llama exactamente a la regla


def test_make_folds_stratified_and_reproducible():
    data = _clean_sample()
    X, y = split_xy(data)
    folds_a, folds_b = make_folds(X, y), make_folds(X, y)
    assert len(folds_a) == 5
    assert all((a[1] == b[1]).all() for a, b in zip(folds_a, folds_b))
    rates = [y[valid].mean() for _, valid in folds_a]
    assert max(rates) - min(rates) < 0.02
    assert sorted(np.concatenate([v for _, v in folds_a]).tolist()) == list(range(len(y)))


def test_every_candidate_trains_on_clean_output():
    """Integración: los 7 candidatos entrenan con la salida de clean() y dan probabilidades válidas."""
    data = _clean_sample()
    X, y = split_xy(data)
    for name, model in candidates().items():
        pipe = build_pipeline(model, use_engineered=True).fit(X, y)
        proba = pipe.predict_proba(X)[:, 1]
        assert proba.shape == (len(y),) and ((proba >= 0) & (proba <= 1)).all(), name


def test_pipeline_ignores_id_and_target():
    data = _clean_sample()
    X, y = split_xy(data)
    pipe = build_pipeline(candidates()["regresión logística"]).fit(X, y)
    names = pipe.named_steps["prep"].get_feature_names_out()
    assert not any(n.endswith("__id") or "Response" in n for n in names)


def test_evaluate_folds_one_row_per_fold():
    data = _clean_sample()
    X, y = split_xy(data)
    table = evaluate_folds(build_pipeline(candidates()["árbol de decisión"]), X, y, make_folds(X, y))
    assert len(table) == 5 and {"cost", "pr_auc", "fit_seconds"} <= set(table.columns)


def test_feature_columns_accepts_list():
    cols = feature_columns(use_engineered=["premium_per_age"])
    flat = sum(cols.values(), [])
    assert "premium_per_age" in flat and "uninsured_with_damage" not in flat
    with pytest.raises(ValueError):
        feature_columns(use_engineered=["no_existe"])
    assert set(ENGINEERED_FEATURES) <= set(sum(feature_columns(use_engineered=True).values(), []))


# --- comparaciones -------------------------------------------------------------------------------

def test_improvement_over_noise():
    r = improvement_over_noise(reference=[0.40, 0.41, 0.39], variant=[0.30, 0.31, 0.29])
    assert r["improvement"] == pytest.approx(0.10) and r["improvement_over_noise"] > 1 and r["folds_won"] == 3


def test_compare_paired():
    r = compare_paired(best=[0.30, 0.31, 0.29], other=[0.32, 0.32, 0.31])
    assert r["folds_won"] == "3 de 3" and r["mean_difference"] > 0

"""Pruebas de la validación final (specs/005-validacion).

Ninguna prueba toca la prueba real (`data/processed/test.parquet`): todo usa datos pequeños inventados para la prueba
o archivos temporales de pytest (`tmp_path`).
"""
import numpy as np
import pandas as pd
import pytest
from sklearn.calibration import CalibratedClassifierCV
from sklearn.pipeline import Pipeline

from proyecto.models.train import BusinessRuleClassifier, decide, expected_cost, split_xy
from proyecto.models.validation import (
    age_band,
    bootstrap_log_loss_difference,
    bootstrap_mean,
    cost_sensitivity,
    fit_final_model,
    open_test_once,
    segment_table,
    should_calibrate,
)
from test_models import _clean_sample

DECISIONS = {"modelo_final": "lightgbm", "parametros": {"n_estimators": 10}, "calibrar": False}
SMALL_PARAMS = {"n_estimators": 20, "learning_rate": 0.1, "num_leaves": 7, "min_child_samples": 10}


# --- should_calibrate ---------------------------------------------------------------------------------

CLEAR_DROP = (-0.010, -0.015, -0.005)    # (diferencia, límite inferior, límite superior): todo bajo cero
CROSSES_ZERO = (-0.002, -0.006, 0.001)   # baja en promedio, pero no se distingue del ruido


def test_should_calibrate_when_log_loss_drop_is_clear_and_cost_does_not_rise():
    assert should_calibrate({"cost": 0.33}, {"cost": 0.33}, CLEAR_DROP)


def test_should_not_calibrate_when_log_loss_interval_crosses_zero():
    assert not should_calibrate({"cost": 0.33}, {"cost": 0.32}, CROSSES_ZERO)


def test_should_not_calibrate_when_cost_rises_even_if_log_loss_drop_is_clear():
    assert not should_calibrate({"cost": 0.33}, {"cost": 0.34}, CLEAR_DROP)


def test_bootstrap_log_loss_difference_is_zero_for_identical_probabilities():
    y = np.random.default_rng(0).integers(0, 2, 500)
    proba = np.random.default_rng(1).uniform(0.05, 0.95, 500)
    assert bootstrap_log_loss_difference(y, proba, proba, n_boot=100) == (0.0, 0.0, 0.0)


def test_bootstrap_log_loss_difference_is_below_zero_for_clearly_better_probabilities():
    rng = np.random.default_rng(0)
    y = rng.integers(0, 2, 2000)
    good = np.where(y == 1, 0.8, 0.2)        # cerca de la verdad
    bad = np.full(2000, 0.5)                 # no sabe nada
    diff, low, high = bootstrap_log_loss_difference(y, good, bad, n_boot=200)
    assert diff < 0 and high < 0


# --- open_test_once -----------------------------------------------------------------------------------

def _fake_test_file(tmp_path):
    path = tmp_path / "test.parquet"
    pd.DataFrame({"id": [1, 2], "Response": [0, 1]}).to_parquet(path)
    return path


def test_open_test_once_reads_data_and_writes_marker(tmp_path):
    marker = tmp_path / "prueba_abierta.txt"
    data = open_test_once(marker, _fake_test_file(tmp_path), DECISIONS, commit="abc1234")
    assert len(data) == 2
    text = marker.read_text(encoding="utf-8")
    assert "abc1234" in text and "fecha" in text


def test_open_test_once_refuses_second_opening_without_reading(tmp_path):
    marker = tmp_path / "prueba_abierta.txt"
    marker.write_text("ya abierta", encoding="utf-8")
    missing_file = tmp_path / "no_existe.parquet"   # si intentara leerlo, el error sería otro
    with pytest.raises(FileExistsError):
        open_test_once(marker, missing_file, DECISIONS, commit="abc1234")


def test_open_test_once_refuses_empty_decision(tmp_path):
    marker = tmp_path / "prueba_abierta.txt"
    incomplete = {**DECISIONS, "calibrar": None}
    with pytest.raises(ValueError, match="calibrar"):
        open_test_once(marker, _fake_test_file(tmp_path), incomplete, commit="abc1234")
    assert not marker.exists()


# --- bootstrap_mean -----------------------------------------------------------------------------------

def test_bootstrap_mean_interval_contains_mean_and_is_reproducible():
    values = np.random.default_rng(0).integers(0, 6, 2000).astype(float)
    mean, low, high = bootstrap_mean(values, n_boot=200, seed=1)
    assert low <= mean <= high
    assert mean == pytest.approx(values.mean())
    assert (mean, low, high) == bootstrap_mean(values, n_boot=200, seed=1)


def test_bootstrap_mean_has_zero_width_with_constant_values():
    mean, low, high = bootstrap_mean(np.full(100, 0.5), n_boot=50)
    assert mean == low == high == 0.5


# --- age_band -----------------------------------------------------------------------------------------

def test_age_band_limits_fall_in_the_right_band():
    bands = age_band(pd.Series([18, 29, 30, 44, 45, 59, 60, 85]))
    assert list(bands) == ["18-29", "18-29", "30-44", "30-44", "45-59", "45-59", "60+", "60+"]


# --- segment_table ------------------------------------------------------------------------------------

def test_segment_table_counts_rates_and_recall():
    segments = pd.Series(["a", "a", "a", "a", "b", "b"])
    y = np.array([1, 1, 0, 0, 1, 0])
    decision = np.array([1, 0, 1, 0, 0, 0])
    table = segment_table(segments, y, decision).set_index("segment")
    assert table.loc["a", "clients"] == 4
    assert table.loc["a", "contact_rate"] == pytest.approx(0.5)
    assert table.loc["a", "positive_rate"] == pytest.approx(0.5)
    assert table.loc["a", "recall"] == pytest.approx(0.5)
    assert table.loc["a", "cost"] == pytest.approx((0 + 5 + 1 + 0) / 4)
    assert table.loc["b", "recall"] == pytest.approx(0.0)


def test_segment_table_groups_small_segments_as_others():
    segments = pd.Series(["big"] * 5 + ["s1", "s2"])
    y = np.zeros(7, int)
    decision = np.zeros(7, int)
    table = segment_table(segments, y, decision, min_size=3).set_index("segment")
    assert set(table.index) == {"big", "otras"}
    assert table.loc["otras", "clients"] == 2


# --- cost_sensitivity ---------------------------------------------------------------------------------

def test_cost_sensitivity_matches_expected_cost_and_scales_false_negatives():
    y = np.array([1, 1, 0, 0])
    decision = np.array([0, 1, 1, 0])           # 1 falso negativo, 1 falso positivo
    costs = cost_sensitivity(y, decision, ratios=(5, 10))
    assert costs[5] == pytest.approx(expected_cost(y, decision))
    assert costs[10] == pytest.approx((10 + 1) / 4)


# --- línea base ---------------------------------------------------------------------------------------

def test_business_rule_baseline_calls_exactly_the_rule_customers():
    X, y = split_xy(_clean_sample(n=2000))
    proba = BusinessRuleClassifier().fit(X, y).predict_proba(X)[:, 1]
    rule = (X["Previously_Insured"] == 0) & (X["Vehicle_Damage"] == 1)
    assert np.array_equal(decide(proba), rule.astype(int).to_numpy())


# --- fit_final_model ----------------------------------------------------------------------------------

def test_fit_final_model_returns_fitted_pipeline_without_calibration():
    train = _clean_sample(n=600)
    model = fit_final_model(train, SMALL_PARAMS, calibrate=False)
    assert isinstance(model, Pipeline)
    proba = model.predict_proba(split_xy(train)[0])[:, 1]
    assert proba.shape == (600,) and ((proba >= 0) & (proba <= 1)).all()


def test_fit_final_model_wraps_in_calibration_when_asked():
    train = _clean_sample(n=600)
    model = fit_final_model(train, SMALL_PARAMS, calibrate=True)
    assert isinstance(model, CalibratedClassifierCV)
    assert model.predict_proba(split_xy(train)[0]).shape == (600, 2)

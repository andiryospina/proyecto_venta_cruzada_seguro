"""Pruebas del costo de negocio, del pipeline completo y de la carga del entrenamiento."""
import numpy as np
import pandas as pd
import pytest
from sklearn.model_selection import StratifiedKFold, cross_validate

from proyecto.data.loading import load_train
from proyecto.features.engineering import FeatureOptions
from proyecto.models.metrics import cost_at_threshold, cost_per_client, decision_threshold, make_scoring
from proyecto.models.train import build_pipeline, reference_models

from test_features import make_clean_frame


# --- costo de negocio
def test_decision_threshold_is_one_over_r_plus_one():
    assert decision_threshold(fn_cost=5, fp_cost=1) == pytest.approx(1 / 6)
    assert decision_threshold(fn_cost=1, fp_cost=1) == pytest.approx(0.5)


def test_cost_per_client_counts_false_alarms_and_lost_sales():
    y_true = [1, 1, 0, 0, 0]
    y_pred = [1, 0, 1, 0, 0]          # 1 venta perdida (cuesta 5) y 1 falsa alarma (cuesta 1)
    assert cost_per_client(y_true, y_pred, fn_cost=5, fp_cost=1) == pytest.approx((5 + 1) / 5)


def test_cost_at_threshold_calls_only_above_the_threshold():
    y_true = [1, 0, 1, 0]
    proba = [0.9, 0.5, 0.10, 0.01]    # umbral 1/6 = 0,167: llama a los dos primeros
    assert cost_at_threshold(y_true, proba) == pytest.approx((1 * 1 + 1 * 5) / 4)   # falsa alarma en el 2.º, venta perdida en el 3.º


def test_perfect_decisions_cost_nothing():
    assert cost_per_client([1, 0, 1], [1, 0, 1]) == 0.0


# --- pipeline completo
@pytest.mark.parametrize("name", ["lightgbm", "regresion_logistica"])
def test_pipeline_fits_and_returns_probabilities(name):
    frame = make_clean_frame(400)
    X, y = frame.drop(columns="Response"), frame["Response"]
    options = FeatureOptions(scale=(name == "regresion_logistica"))
    pipe = build_pipeline(reference_models()[name], options).fit(X, y)
    proba = pipe.predict_proba(X.head(10))
    assert proba.shape == (10, 2)
    assert np.allclose(proba.sum(axis=1), 1.0)


def test_scoring_works_inside_cross_validation_with_every_idea():
    frame = make_clean_frame(500)
    X, y = frame.drop(columns="Response"), frame["Response"]
    folds = list(StratifiedKFold(3, shuffle=True, random_state=0).split(X, y))
    for changes in ({}, {"target_encode_codes": True}, {"segment_flag": True, "clip_premium": True}):
        pipe = build_pipeline(reference_models()["lightgbm"], FeatureOptions(**changes))
        res = cross_validate(pipe, X, y, cv=folds, scoring=make_scoring(), n_jobs=1)
        for metric in ("pr_auc", "cost", "log_loss", "roc_auc"):
            assert np.isfinite(res[f"test_{metric}"]).all()


def test_target_encoding_does_not_leak_the_labels():
    """Si se barajan las etiquetas no hay nada que aprender: la PR-AUC debe quedar cerca de la proporción de compradores."""
    frame = make_clean_frame(3000, seed=1)
    X = frame.drop(columns="Response")
    y = frame["Response"].sample(frac=1.0, random_state=0).to_numpy()      # etiquetas sin relación con las variables
    folds = list(StratifiedKFold(5, shuffle=True, random_state=0).split(X, y))
    pipe = build_pipeline(reference_models()["lightgbm"], FeatureOptions(target_encode_codes=True))
    res = cross_validate(pipe, X, y, cv=folds, scoring={"pr_auc": "average_precision"}, n_jobs=1)
    assert np.mean(res["test_pr_auc"]) < y.mean() + 0.06


# --- carga del entrenamiento
def test_load_train_prefers_the_processed_file(tmp_path):
    (tmp_path / "data" / "processed").mkdir(parents=True)
    saved = make_clean_frame(50)
    saved.to_parquet(tmp_path / "data" / "processed" / "train.parquet", index=False)
    pd.testing.assert_frame_equal(load_train(tmp_path), saved)


def test_load_train_rebuilds_from_the_csv_without_returning_the_closed_test(tmp_path):
    rng = np.random.default_rng(0)
    n = 400
    raw = pd.DataFrame({
        "id": np.arange(1, n + 1), "Gender": rng.choice(["Male", "Female"], n), "Age": rng.integers(20, 80, n),
        "Driving_License": 1, "Region_Code": rng.choice([3.0, 28.0], n), "Previously_Insured": rng.integers(0, 2, n),
        "Vehicle_Age": rng.choice(["< 1 Year", "1-2 Year", "> 2 Years"], n), "Vehicle_Damage": rng.choice(["Yes", "No"], n),
        "Annual_Premium": rng.uniform(3000, 60000, n).round(0), "Policy_Sales_Channel": rng.choice([26.0, 152.0], n),
        "Vintage": rng.integers(10, 300, n), "Response": (rng.random(n) < 0.15).astype(int),
    })
    raw.to_csv(tmp_path / "dataset.csv", index=False)
    train = load_train(tmp_path)
    assert len(train) == 320                              # 80 % de 400; el 20 % cerrado no se devuelve
    assert train["id"].is_unique and set(train["id"]) <= set(raw["id"])
    assert "Premium_is_minimum" in train.columns          # ya viene limpio

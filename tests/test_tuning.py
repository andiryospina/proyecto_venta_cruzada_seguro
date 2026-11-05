"""Pruebas de la optimización (specs/004-optimizacion): espacio de búsqueda, objetivos, búsqueda e intervalos."""
import numpy as np
import optuna
import pytest
from sklearn.metrics import average_precision_score

from proyecto.models.train import make_folds, split_xy
from proyecto.models.tuning import (
    OBJECTIVES,
    bootstrap_cost_difference,
    bootstrap_metric_difference,
    lgbm_space,
    make_lgbm,
    tune,
)
from test_models import _clean_sample

EXPECTED_RANGES = {
    "n_estimators": (150, 800),
    "learning_rate": (0.01, 0.2),
    "num_leaves": (15, 127),
    "min_child_samples": (20, 500),
    "subsample": (0.6, 1.0),
    "colsample_bytree": (0.5, 1.0),
    "reg_lambda": (1e-3, 10.0),
}


def test_lgbm_space_returns_seven_params_inside_their_ranges():
    study = optuna.create_study(sampler=optuna.samplers.RandomSampler(seed=0))
    for _ in range(20):
        params = lgbm_space(study.ask())
        assert set(params) == set(EXPECTED_RANGES)
        for name, (low, high) in EXPECTED_RANGES.items():
            assert low <= params[name] <= high, name


def test_make_lgbm_never_balances_classes():
    """Balancear movería las probabilidades y dejaría de valer el umbral 1/6."""
    model = make_lgbm({"n_estimators": 10})
    assert model.get_params()["class_weight"] is None
    assert model.get_params().get("scale_pos_weight", 1.0) == 1.0
    assert not model.get_params().get("is_unbalance", False)
    assert model.get_params()["subsample_freq"] == 1


def test_objectives_have_a_direction_and_cost_minimizes():
    assert OBJECTIVES["cost"] == "minimize" and OBJECTIVES["pr_auc"] == "maximize"
    assert set(OBJECTIVES.values()) <= {"minimize", "maximize"}


def test_tune_rejects_unknown_metric():
    with pytest.raises(ValueError, match="no soportada"):
        tune(None, None, None, n_trials=1, metric="inventada")


def test_tune_runs_small_study_without_mlflow():
    X, y = split_xy(_clean_sample(n=600))
    folds = make_folds(X, y, n_splits=3)
    study = tune(X, y, folds, n_trials=2, log=False)
    assert len(study.trials) == 2
    assert study.direction == optuna.study.StudyDirection.MINIMIZE
    assert 0 <= study.best_value <= 5   # el costo por cliente está entre 0 y el costo máximo de la matriz
    assert "pr_auc" in study.best_trial.user_attrs   # las demás métricas quedan guardadas en el ensayo


def test_tune_resumes_from_storage(tmp_path):
    X, y = split_xy(_clean_sample(n=400))
    folds = make_folds(X, y, n_splits=3)
    db = tmp_path / "study.db"
    tune(X, y, folds, n_trials=1, log=False, storage=db)
    study = tune(X, y, folds, n_trials=2, log=False, storage=db)   # solo hace el ensayo que falta
    assert len(study.trials) == 2


def test_bootstrap_cost_difference_is_zero_for_identical_models():
    rng = np.random.default_rng(0)
    y = rng.integers(0, 2, 500)
    proba = rng.uniform(0, 1, 500)
    assert bootstrap_cost_difference(y, proba, proba, n_boot=200) == (0.0, 0.0, 0.0)


def test_bootstrap_cost_difference_detects_a_clearly_better_model():
    rng = np.random.default_rng(1)
    y = rng.binomial(1, 0.15, 2000)
    good = np.where(y == 1, 0.9, 0.05)    # casi siempre acierta
    bad = np.where(y == 1, 0.05, 0.9)     # casi siempre se equivoca
    diff, low, high = bootstrap_cost_difference(y, good, bad, n_boot=300)
    assert diff < 0 and low <= diff <= high and high < 0   # todo el intervalo bajo cero: A cuesta menos


def test_bootstrap_cost_difference_is_reproducible():
    rng = np.random.default_rng(2)
    y = rng.binomial(1, 0.2, 800)
    a, b = rng.uniform(0, 1, 800), rng.uniform(0, 1, 800)
    assert bootstrap_cost_difference(y, a, b, n_boot=100) == bootstrap_cost_difference(y, a, b, n_boot=100)


def test_bootstrap_metric_difference_detects_a_better_ranker():
    rng = np.random.default_rng(3)
    y = rng.binomial(1, 0.15, 1500)
    good = np.clip(y * 0.6 + rng.uniform(0, 0.4, 1500), 0, 1)
    bad = rng.uniform(0, 1, 1500)
    diff, low, high = bootstrap_metric_difference(y, good, bad, average_precision_score, n_boot=100)
    assert diff > 0.3 and low > 0   # todo el intervalo sobre cero: A ordena mejor

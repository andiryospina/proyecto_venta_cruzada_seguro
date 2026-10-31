"""Pruebas de la optimización: espacios de búsqueda, equivalencia con el torneo, costo por cliente e intervalo."""
import numpy as np
import optuna
import pytest

from proyecto.models.metrics import cost_per_client
from proyecto.models.train import tournament_candidates
from proyecto.models.tuning import (
    FINALISTS,
    SPACES,
    START_PARAMS,
    bootstrap_interval,
    build_tuned_pipeline,
    evaluate_pipeline,
    per_client_cost,
)
from proyecto.data import split as sp

from test_features import make_clean_frame

optuna.logging.set_verbosity(optuna.logging.WARNING)


@pytest.mark.parametrize("finalist", FINALISTS)
def test_start_parameters_lie_inside_the_search_space(finalist):
    """Los parámetros de partida deben ser un punto válido de la búsqueda; si no, la búsqueda no los puede comparar."""
    study = optuna.create_study(direction="minimize")
    study.enqueue_trial(START_PARAMS[finalist])
    trial = study.ask()
    assert SPACES[finalist](trial) == START_PARAMS[finalist]


@pytest.mark.parametrize("finalist", FINALISTS)
def test_random_trials_stay_inside_the_declared_ranges_and_build_a_pipeline(finalist):
    frame = make_clean_frame(400, seed=4)
    X, y = frame.drop(columns="Response"), frame["Response"]
    study = optuna.create_study(direction="minimize", sampler=optuna.samplers.RandomSampler(seed=0))
    for _ in range(4):
        params = SPACES[finalist](study.ask())
        pipe = build_tuned_pipeline(finalist, params).fit(X, y)
        assert pipe.predict_proba(X.head(10)).shape == (10, 2)


def test_start_pipelines_reproduce_the_tournament_candidates_exactly():
    """Lo que la optimización llama 'partida' debe ser lo mismo que se midió en el torneo."""
    frame = make_clean_frame(500, seed=5)
    X, y = frame.drop(columns="Response"), frame["Response"]
    candidates = tournament_candidates()
    for finalist, name in (("lightgbm", "LightGBM"), ("regresion_logistica", "regresión logística")):
        mine = build_tuned_pipeline(finalist, START_PARAMS[finalist]).fit(X, y).predict_proba(X)[:, 1]
        theirs = candidates[name].fit(X, y).predict_proba(X)[:, 1]
        assert np.allclose(mine, theirs), finalist


def test_unknown_finalist_is_rejected():
    with pytest.raises(ValueError, match="finalista desconocido"):
        build_tuned_pipeline("bosque", {})


def test_evaluate_pipeline_returns_one_row_per_fold():
    frame = make_clean_frame(600, seed=6)
    X, y = frame.drop(columns="Response"), frame["Response"]
    folds = sp.stratified_folds(frame, n_splits=3)
    table = evaluate_pipeline(build_tuned_pipeline("regresion_logistica", START_PARAMS["regresion_logistica"]), X, y, folds)
    assert len(table) == 3 and {"cost", "pr_auc", "log_loss"} <= set(table.columns)


# --- costo por cliente
def test_per_client_cost_averages_to_the_cost_per_client_metric():
    y = np.array([1, 1, 0, 0, 0, 1])
    proba = np.array([0.9, 0.05, 0.4, 0.01, 0.2, 0.5])
    cost = per_client_cost(y, proba)
    assert cost.mean() == pytest.approx(cost_per_client(y, (proba >= 1 / 6).astype(int)))
    assert cost.tolist() == [0.0, 5.0, 1.0, 0.0, 1.0, 0.0]


# --- intervalo por cliente
def test_interval_of_a_constant_improvement_is_narrow_and_below_zero():
    low, high = bootstrap_interval(np.full(500, -0.01), np.arange(500))
    assert low == pytest.approx(-0.01) and high == pytest.approx(-0.01)


def test_interval_of_pure_noise_contains_zero():
    rng = np.random.default_rng(0)
    low, high = bootstrap_interval(rng.normal(0, 1, 2000), np.arange(2000))
    assert low < 0 < high


def test_interval_resamples_whole_clients_not_rows():
    """Con 2 clientes de 50 filas cada uno y efectos opuestos, remuestrear clientes da un intervalo ancho; remuestrear filas, no."""
    diff = np.concatenate([np.full(50, -1.0), np.full(50, 1.0)])
    clients = np.concatenate([np.zeros(50), np.ones(50)])
    by_client = bootstrap_interval(diff, clients, n=500)
    by_row = bootstrap_interval(diff, np.arange(100), n=500)
    assert (by_client[1] - by_client[0]) > 3 * (by_row[1] - by_row[0])


def test_interval_is_reproducible_with_the_same_seed():
    diff = np.random.default_rng(1).normal(-0.01, 0.5, 300)
    assert bootstrap_interval(diff, np.arange(300), seed=3) == bootstrap_interval(diff, np.arange(300), seed=3)


def test_run_search_always_measures_the_starting_configuration_first_and_respects_the_budget():
    from proyecto.models.tuning import run_search

    frame = make_clean_frame(700, seed=10)
    X, y = frame.drop(columns="Response"), frame["Response"]
    folds = sp.stratified_folds(frame, n_splits=3)
    seen = []
    study = run_search("regresion_logistica", X, y, folds, n_trials=4, on_trial=lambda study, trial: seen.append(trial.number))
    assert len(study.trials) == 4 and seen == [0, 1, 2, 3]                    # presupuesto exacto y un aviso por ensayo
    assert study.trials[0].params == START_PARAMS["regresion_logistica"]      # el ensayo 0 es la partida
    assert {"cost_sd", "pr_auc", "log_loss"} <= set(study.trials[0].user_attrs)
    assert study.best_value <= study.trials[0].value                           # el mejor nunca es peor que la partida


def test_run_search_rejects_an_unknown_finalist():
    from proyecto.models.tuning import run_search

    with pytest.raises(ValueError, match="finalista desconocido"):
        run_search("bosque", None, None, None)

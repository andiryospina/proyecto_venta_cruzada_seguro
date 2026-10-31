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


# ======================================================================================================================
# Lógica que se movió del notebook 05 a los módulos: debe dar lo mismo que antes
# ======================================================================================================================
def test_run_tournament_stores_every_fold_and_out_of_sample_probabilities():
    from proyecto.data import split as sp
    from proyecto.models.train import run_tournament

    frame = make_clean_frame(600, seed=8)
    X, y = frame.drop(columns="Response"), frame["Response"]
    folds = sp.stratified_folds(frame, n_splits=3)
    candidates = {k: v for k, v in tournament_candidates().items() if k in ("línea base: llamar si hubo daño", "regresión logística")}
    per_fold, oof = run_tournament(candidates, X, y, folds)

    assert set(per_fold) == set(candidates) == set(oof)
    for name in candidates:
        assert len(per_fold[name]) == 3                                   # una fila por pliegue
        assert {"cost", "pr_auc", "recall_top", "fit_seconds", "predict_seconds"} <= set(per_fold[name].columns)
        assert oof[name].shape == (len(frame),) and np.isfinite(oof[name]).all()
        assert (oof[name] > 0).any()                                       # cada cliente recibió una probabilidad


def test_run_tournament_oof_is_made_by_models_that_did_not_see_the_client():
    """Si se barajan las respuestas, las probabilidades fuera de muestra no pueden predecir: la PR-AUC queda cerca del azar."""
    from sklearn.metrics import average_precision_score

    from proyecto.data import split as sp
    from proyecto.models.train import run_tournament

    frame = make_clean_frame(3000, seed=9)
    X = frame.drop(columns="Response")
    y = frame["Response"].sample(frac=1.0, random_state=1).reset_index(drop=True)
    data = frame.assign(Response=y)
    folds = sp.stratified_folds(data, n_splits=5)
    _, oof = run_tournament({"regresión logística": tournament_candidates()["regresión logística"]}, X, y, folds)
    assert average_precision_score(y, oof["regresión logística"]) < y.mean() + 0.06


def test_calibration_table_of_a_perfectly_calibrated_model_has_no_gap():
    from proyecto.models.metrics import calibration_table

    rng = np.random.default_rng(0)
    proba = rng.uniform(0.02, 0.5, 50_000)
    y = (rng.random(50_000) < proba).astype(int)
    table = calibration_table(y, proba)
    assert len(table) == 10
    assert (table["predicted"] - table["real"]).abs().max() < 0.02
    assert table["predicted"].is_monotonic_increasing


def test_paired_comparison_counts_folds_and_noise_like_the_notebook_did():
    from proyecto.models.metrics import paired_comparison

    per_fold = {"A": pd.DataFrame({"cost": [0.30, 0.31, 0.32, 0.33, 0.34], "pr_auc": [0.4, 0.4, 0.4, 0.4, 0.4]}),
                "B": pd.DataFrame({"cost": [0.31, 0.32, 0.33, 0.34, 0.345], "pr_auc": [0.3, 0.3, 0.3, 0.3, 0.3]})}
    cost = paired_comparison(per_fold, "A", "B", "cost")
    assert cost["folds_won"] == 5 and cost["n_folds"] == 5 and cost["mean_difference"] == pytest.approx(0.0090)
    assert cost["difference_over_noise"] > 1
    pr = paired_comparison(per_fold, "A", "B", "pr_auc", lower_is_better=False)
    assert pr["mean_difference"] == pytest.approx(0.1) and pr["folds_won"] == 5 and pr["difference_over_noise"] > 1000   # diferencia constante: ruido casi cero
    reverse = paired_comparison(per_fold, "B", "A", "cost")
    assert reverse["folds_won"] == 0 and reverse["mean_difference"] == pytest.approx(-0.0090)


def test_cost_sensitivity_matches_the_cost_per_client_for_each_r():
    from proyecto.models.metrics import cost_per_client, cost_sensitivity

    y = np.array([1, 1, 0, 0, 0, 1, 0, 0])
    probabilities = {"a": np.array([0.9, 0.2, 0.3, 0.05, 0.1, 0.12, 0.4, 0.01]), "b": np.full(8, 0.5)}
    table = cost_sensitivity(y, probabilities, [2, 5])
    assert list(table.columns) == ["R = 2", "R = 5"] and list(table.index) == ["a", "b"]
    for r in (2, 5):
        for name, p in probabilities.items():
            assert table.loc[name, f"R = {r}"] == pytest.approx(cost_per_client(y, (p >= 1 / (r + 1)).astype(int), fn_cost=r))


def test_audit_by_group_reports_who_is_called_and_who_is_missed():
    from proyecto.models.metrics import audit_by_group

    y = np.array([1, 1, 0, 0, 1, 0, 0, 0])
    proba = np.array([0.9, 0.05, 0.4, 0.01, 0.9, 0.01, 0.01, 0.01])
    groups = pd.Series(["a", "a", "a", "a", "b", "b", "b", "b"], name="grupo")
    table = audit_by_group(y, proba, groups)
    assert table.index.name == "grupo" and list(table.index) == ["a", "b"]
    assert table.loc["a", "clients"] == 4 and table.loc["a", "real_rate"] == pytest.approx(0.5)
    assert table.loc["a", "called_rate"] == pytest.approx(0.5)                # llama a los clientes con 0,9 y 0,4
    assert table.loc["a", "recall"] == pytest.approx(0.5) and table.loc["a", "precision"] == pytest.approx(0.5)
    assert table.loc["a", "buyers_missed"] == 1
    assert table.loc["b", "recall"] == pytest.approx(1.0) and table.loc["b", "buyers_missed"] == 0

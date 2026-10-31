"""Pruebas de las variables de la etapa 4: lo que aprende se aprende solo del entrenamiento y nada rompe con datos nuevos."""
import numpy as np
import pandas as pd
import pytest

from proyecto.features.engineering import (
    NEW_FEATURES,
    RARE_LABEL,
    CodeVolume,
    FeatureOptions,
    PremiumClipper,
    PremiumVsAgeBand,
    PremiumVsRegion,
    RareCategoryGrouper,
    build_preprocessor,
    commercial_segment,
    need_score,
    profile_12_code,
    vintage_share,
    young_new_vehicle,
)


def make_clean_frame(n: int = 600, seed: int = 0) -> pd.DataFrame:
    """Datos con la misma forma que la salida de `clean()` (etapa 3), con una señal simple en el objetivo."""
    rng = np.random.default_rng(seed)
    insured = rng.integers(0, 2, n)
    damage = rng.integers(0, 2, n)
    premium = np.round(rng.lognormal(10.3, 0.5, n), 0)
    premium[:30] = 2630.0
    y = ((insured == 0) & (damage == 1) & (rng.random(n) < 0.5)).astype(int)
    return pd.DataFrame({
        "id": np.arange(1, n + 1),
        "Gender": rng.choice(["Male", "Female"], n),
        "Age": rng.integers(20, 80, n),
        "Driving_License": np.ones(n, dtype=int),
        "Region_Code": rng.choice([3, 8, 28, 41], n, p=[0.1, 0.2, 0.6, 0.1]),
        "Previously_Insured": insured,
        "Vehicle_Age": rng.integers(0, 3, n),
        "Vehicle_Damage": damage,
        "Annual_Premium": premium,
        "Policy_Sales_Channel": rng.choice([26, 124, 152, 999], n, p=[0.4, 0.3, 0.29, 0.01]),
        "Vintage": rng.integers(10, 300, n),
        "Premium_is_minimum": (premium == 2630.0).astype(int),
        "Response": y,
    })


# --- recorte de la prima: el corte sale del entrenamiento, no de los datos nuevos
def test_premium_clipper_learns_the_cutoff_only_from_fit_data():
    train = pd.DataFrame({"p": np.arange(1.0, 101.0)})
    clipper = PremiumClipper(quantile=0.99).fit(train)
    new = pd.DataFrame({"p": [50.0, 5000.0]})
    out = clipper.transform(new)
    assert clipper.upper_ == pytest.approx(np.quantile(np.arange(1.0, 101.0), 0.99))
    assert out[0, 0] == 50.0 and out[1, 0] == pytest.approx(clipper.upper_)
    assert new["p"].tolist() == [50.0, 5000.0]            # no modifica el original


# --- canales raros
def test_rare_category_grouper_groups_rare_and_unseen_codes():
    train = np.array([[1]] * 150 + [[2]] * 120 + [[3]] * 5)
    grouper = RareCategoryGrouper(min_count=100).fit(train)
    out = grouper.transform(np.array([[1], [2], [3], [77]]))
    assert out.ravel().tolist() == [1, 2, RARE_LABEL, RARE_LABEL]   # 3 es raro y 77 nunca se vio


def test_rare_category_grouper_does_not_modify_input():
    data = np.array([[1], [3]] * 100)
    before = data.copy()
    RareCategoryGrouper(min_count=100).fit(data).transform(data)
    assert (data == before).all()


# --- prima relativa a la región
def test_premium_vs_region_uses_train_medians_and_global_fallback():
    train = np.array([[100.0, 1], [200.0, 1], [300.0, 1], [10.0, 2], [30.0, 2]])
    transformer = PremiumVsRegion().fit(train)
    out = transformer.transform(np.array([[400.0, 1], [20.0, 2], [100.0, 99]]))
    assert out[0, 0] == pytest.approx(400 / 200)           # mediana de la región 1 = 200
    assert out[1, 0] == pytest.approx(20 / 20)             # mediana de la región 2 = 20
    assert out[2, 0] == pytest.approx(100 / 100)           # región desconocida: mediana global = 100


# --- segmento comercial
def test_commercial_segment_truth_table():
    data = np.array([[0, 1], [0, 0], [1, 1], [1, 0]])
    assert commercial_segment(data).ravel().tolist() == [1, 0, 0, 0]


# --- el preprocesador completo
def test_preprocessor_output_is_numeric_without_missing_values_and_ignores_id_and_target():
    frame = make_clean_frame()
    out = build_preprocessor().fit_transform(frame.drop(columns="Response"), frame["Response"])
    dense = out.toarray() if hasattr(out, "toarray") else np.asarray(out)
    assert dense.shape[0] == len(frame)
    assert np.isfinite(dense).all()
    names = list(build_preprocessor().fit(frame.drop(columns="Response"), frame["Response"]).get_feature_names_out())
    assert "id" not in names and "Response" not in names


@pytest.mark.parametrize("changes", [
    {}, {"clip_premium": True}, {"segment_flag": True}, {"age_splines": True, "scale": True},
    {"target_encode_codes": True}, {"premium_vs_region": True}, {"group_rare": False}, {"scale": True},
])
def test_every_idea_runs_and_gives_finite_numbers(changes):
    frame = make_clean_frame()
    pre = build_preprocessor(FeatureOptions(**changes))
    out = pre.fit_transform(frame.drop(columns="Response"), frame["Response"])
    dense = out.toarray() if hasattr(out, "toarray") else np.asarray(out)
    assert np.isfinite(dense).all() and dense.shape[0] == len(frame)


def test_drop_removes_the_columns_of_that_variable():
    frame = make_clean_frame()
    X, y = frame.drop(columns="Response"), frame["Response"]
    names = list(build_preprocessor(FeatureOptions()).fit(X, y).get_feature_names_out())
    names_dropped = list(build_preprocessor(FeatureOptions(drop=("Gender", "Vintage"))).fit(X, y).get_feature_names_out())
    assert any(n.startswith("Gender") for n in names) and "Vintage" in names
    assert not any(n.startswith("Gender") for n in names_dropped) and "Vintage" not in names_dropped


def test_new_idea_adds_exactly_its_columns():
    frame = make_clean_frame()
    X, y = frame.drop(columns="Response"), frame["Response"]
    base = list(build_preprocessor(FeatureOptions()).fit(X, y).get_feature_names_out())
    seg = list(build_preprocessor(FeatureOptions(segment_flag=True)).fit(X, y).get_feature_names_out())
    assert len(seg) == len(base) + 1


def test_preprocessor_handles_unseen_categories_at_predict_time():
    frame = make_clean_frame()
    X, y = frame.drop(columns="Response"), frame["Response"]
    for changes in ({}, {"target_encode_codes": True}):
        pre = build_preprocessor(FeatureOptions(**changes)).fit(X, y)
        new = X.head(5).copy()
        new["Policy_Sales_Channel"] = 31337      # canal que nunca se vio
        new["Region_Code"] = 7777                # región que nunca se vio
        out = pre.transform(new)
        dense = out.toarray() if hasattr(out, "toarray") else np.asarray(out)
        assert np.isfinite(dense).all()


def test_feature_options_with_changes_returns_a_new_object():
    base = FeatureOptions()
    other = base.with_changes(clip_premium=True)
    assert base.clip_premium is False and other.clip_premium is True


# ======================================================================================================================
# Segunda ronda: variables nuevas
# ======================================================================================================================
def test_code_volume_counts_clients_from_fit_data_only_and_unseen_is_zero():
    train = np.array([[26, 28]] * 100 + [[152, 28]] * 10 + [[152, 3]] * 5)
    transformer = CodeVolume().fit(train)
    out = transformer.transform(np.array([[26, 28], [152, 3], [999, 7777]]))
    assert out[0, 0] == pytest.approx(np.log1p(100)) and out[0, 1] == pytest.approx(np.log1p(110))
    assert out[1, 0] == pytest.approx(np.log1p(15)) and out[1, 1] == pytest.approx(np.log1p(5))
    assert out[2].tolist() == [0.0, 0.0]                  # canal y región que nunca se vieron


def test_need_score_truth_table():
    # columnas: Previously_Insured, Vehicle_Damage, Vehicle_Age
    data = np.array([[0, 1, 2], [0, 1, 0], [1, 0, 0], [1, 1, 1], [0, 0, 0]])
    assert need_score(data).ravel().tolist() == [4.0, 2.0, 0.0, 2.0, 1.0]


def test_profile_12_code_covers_the_twelve_combinations_without_repeats():
    combos = np.array([[p, d, v] for p in (0, 1) for d in (0, 1) for v in (0, 1, 2)])
    codes = profile_12_code(combos).ravel()
    assert sorted(codes.tolist()) == list(range(12))


def test_young_new_vehicle_truth_table():
    # columnas: Age, Vehicle_Age
    data = np.array([[22, 0], [25, 0], [26, 0], [22, 1], [60, 0]])
    assert young_new_vehicle(data).ravel().tolist() == [1, 1, 0, 0, 0]


def test_vintage_share_is_the_fraction_of_life_as_a_client():
    out = vintage_share(np.array([[365.25, 1.0], [365.25 * 10, 40.0]]))
    assert out.ravel().tolist() == pytest.approx([1.0, 0.25])


def test_premium_vs_age_band_uses_train_medians_per_band_and_global_fallback():
    # columnas: Annual_Premium, Age. Tramo 20-25: mediana 100; tramo 36-45: mediana 400
    train = np.array([[100.0, 22], [100.0, 24], [100.0, 25], [400.0, 40], [400.0, 41], [400.0, 42]])
    transformer = PremiumVsAgeBand().fit(train)
    out = transformer.transform(np.array([[200.0, 23], [200.0, 44], [250.0, 70]]))
    assert out[0, 0] == pytest.approx(2.0)                  # 200 / 100
    assert out[1, 0] == pytest.approx(0.5)                  # 200 / 400
    assert out[2, 0] == pytest.approx(250.0 / np.median(train[:, 0]))   # tramo sin datos de entrenamiento -> mediana global


@pytest.mark.parametrize("option,extra_columns", [
    ("channel_region_volume", 2), ("need_score", 1), ("profile_12", 12), ("young_new_vehicle", 1),
    ("premium_vs_age_band", 1), ("vintage_share", 1),
])
def test_each_new_feature_adds_exactly_its_columns_and_keeps_the_existing_ones(option, extra_columns):
    frame = make_clean_frame()
    X, y = frame.drop(columns="Response"), frame["Response"]
    base = list(build_preprocessor(FeatureOptions()).fit(X, y).get_feature_names_out())
    more = list(build_preprocessor(FeatureOptions(**{option: True})).fit(X, y).get_feature_names_out())
    assert len(more) == len(base) + extra_columns
    assert set(base) <= set(more)                           # conserva todas las variables que ya había


def test_all_new_features_together_run_with_and_without_scaling_and_are_finite():
    frame = make_clean_frame()
    X, y = frame.drop(columns="Response"), frame["Response"]
    for scale in (False, True):
        options = FeatureOptions(scale=scale).with_all_new()
        assert all(getattr(options, name) for name in NEW_FEATURES)
        out = build_preprocessor(options).fit_transform(X, y)
        dense = out.toarray() if hasattr(out, "toarray") else np.asarray(out)
        assert np.isfinite(dense).all() and dense.shape[0] == len(frame)


def test_new_features_are_skipped_when_their_columns_are_dropped():
    frame = make_clean_frame()
    X, y = frame.drop(columns="Response"), frame["Response"]
    options = FeatureOptions(drop=("Vintage",), vintage_share=True)
    names = list(build_preprocessor(options).fit(X, y).get_feature_names_out())
    assert "vintage_share" not in names and "Vintage" not in names


def test_new_features_do_not_use_the_target():
    """Con la respuesta barajada, las variables nuevas deben quedar idénticas: no dependen de `Response`."""
    frame = make_clean_frame()
    X = frame.drop(columns="Response")
    y1 = frame["Response"]
    y2 = frame["Response"].sample(frac=1.0, random_state=3)
    options = FeatureOptions().with_all_new()
    a = build_preprocessor(options).fit_transform(X, y1)
    b = build_preprocessor(options).fit_transform(X, y2)
    a = a.toarray() if hasattr(a, "toarray") else np.asarray(a)
    b = b.toarray() if hasattr(b, "toarray") else np.asarray(b)
    assert np.allclose(a, b)

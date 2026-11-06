"""Pruebas de la capa de servicio (specs/007-integracion-main/contracts/serving.md).

Usan un Pipeline de juguete con las mismas columnas limpias que `data/processed/train.parquet`; no tocan el modelo real ni la prueba.
"""
import numpy as np
import pandas as pd
import pytest
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

from proyecto.config import MIN_PREMIUM
from proyecto.inference.predict import InputValidationError
from proyecto.inference.serving import CLEAN_COLUMNS, RAW_COLUMNS, ServingModel, build_defaults, to_raw


def make_clean(n=40, seed=0):
    """Clientes ya limpios (códigos numéricos), con los mismos tipos que train.parquet."""
    rng = np.random.default_rng(seed)
    clean = pd.DataFrame({
        "Gender": pd.array(rng.integers(0, 2, n), dtype="Int64"),
        "Age": rng.integers(20, 80, n).astype(float),
        "Driving_License": pd.array(rng.integers(0, 2, n), dtype="Int64"),
        "Region_Code": pd.array(rng.choice([3, 8, 28], n), dtype="Int64"),
        "Previously_Insured": pd.array(rng.integers(0, 2, n), dtype="Int64"),
        "Vehicle_Age": pd.array(rng.integers(0, 3, n), dtype="Int64"),
        "Vehicle_Damage": pd.array(rng.integers(0, 2, n), dtype="Int64"),
        "Annual_Premium": rng.choice([float(MIN_PREMIUM), 30000.0, 45000.0], n),
        "Vintage": rng.integers(10, 300, n).astype(float),
    })
    clean["is_min_premium"] = clean["Annual_Premium"].eq(MIN_PREMIUM).astype(int)
    return clean


def make_pipeline(clean):
    """Pipeline real pero pequeño: pasa las 10 columnas limpias a una regresión logística."""
    y = (clean["Age"] > 45).astype(int) ^ clean["Vehicle_Damage"].astype(int)
    pipeline = Pipeline([
        ("prep", ColumnTransformer([("keep", "passthrough", CLEAN_COLUMNS)])),
        ("model", LogisticRegression(max_iter=1000)),
    ])
    return pipeline.fit(clean[CLEAN_COLUMNS].astype(float), y)


class Recorder:
    """Pipeline falso que guarda lo que recibe, para ver la traducción a columnas limpias."""
    classes_ = np.array([0, 1])

    def predict_proba(self, X):
        self.seen = X.copy()
        return np.column_stack([np.full(len(X), 0.8), np.full(len(X), 0.2)])


def test_round_trip_gives_the_same_probabilities_as_the_pipeline():
    clean = make_clean()
    pipeline = make_pipeline(clean)
    raw = to_raw(clean)
    assert list(raw.columns) == RAW_COLUMNS
    served = ServingModel(pipeline, build_defaults(raw)).predict_proba(raw)
    direct = pipeline.predict_proba(clean[CLEAN_COLUMNS].astype(float))
    assert np.abs(served - direct).max() <= 1e-9


def test_translation_rebuilds_every_clean_column():
    clean = make_clean()
    recorder = Recorder()
    ServingModel(recorder, build_defaults(to_raw(clean))).predict_proba(to_raw(clean))
    assert list(recorder.seen.columns) == CLEAN_COLUMNS
    for col in CLEAN_COLUMNS:
        assert (recorder.seen[col].to_numpy(dtype=float) == clean[col].to_numpy(dtype=float)).all(), col


def test_is_min_premium_is_computed_from_the_premium():
    raw = to_raw(make_clean()).head(2).copy()
    raw["Annual_Premium"] = [float(MIN_PREMIUM), 31000.0]
    recorder = Recorder()
    ServingModel(recorder, build_defaults(to_raw(make_clean()))).predict_proba(raw)
    assert recorder.seen["is_min_premium"].tolist() == [1, 0]


def test_unknown_value_uses_the_default_like_writing_it():
    clean = make_clean()
    pipeline = make_pipeline(clean)
    defaults = build_defaults(to_raw(clean))
    model = ServingModel(pipeline, defaults)
    row = to_raw(clean).head(1).copy()
    with_gaps = row.assign(Age=np.nan, Vehicle_Damage=np.nan)
    written = row.assign(Age=defaults["Age"], Vehicle_Damage=defaults["Vehicle_Damage"])
    assert np.abs(model.predict_proba(with_gaps) - model.predict_proba(written)).max() <= 1e-12


def test_unknown_category_raises_a_clear_error():
    clean = make_clean()
    raw = to_raw(clean).head(1).assign(Vehicle_Age="3 años")
    with pytest.raises(InputValidationError, match="Vehicle_Age"):
        ServingModel(Recorder(), build_defaults(to_raw(clean))).predict_proba(raw)


def test_non_integer_region_is_rejected_not_rounded():
    """Una región es una etiqueta: 28,7 no es "casi la 29", es un dato mal escrito."""
    clean = make_clean()
    raw = to_raw(clean).head(1).assign(Region_Code=28.7)
    with pytest.raises(InputValidationError, match="Region_Code"):
        ServingModel(Recorder(), build_defaults(to_raw(clean))).predict_proba(raw)


def test_integer_region_written_as_float_is_accepted():
    """28.0 (como llega a veces desde un formulario) sí es la región 28."""
    clean = make_clean()
    recorder = Recorder()
    raw = to_raw(clean).head(1).assign(Region_Code=28.0)
    ServingModel(recorder, build_defaults(to_raw(clean))).predict_proba(raw)
    assert recorder.seen["Region_Code"].iloc[0] == 28


def test_build_defaults_uses_median_for_numbers_and_mode_for_categories():
    raw = pd.DataFrame({
        "Age": [20.0, 30.0, 70.0], "Annual_Premium": [2630.0, 30000.0, 40000.0], "Region_Code": [3, 28, 28],
        "Vintage": [10.0, 100.0, 200.0], "Gender": ["Male", "Male", "Female"], "Driving_License": ["Yes", "Yes", "No"],
        "Previously_Insured": ["No", "No", "Yes"], "Vehicle_Age": ["< 1 Year", "1-2 Year", "1-2 Year"],
        "Vehicle_Damage": ["Yes", "No", "Yes"],
    })
    defaults = build_defaults(raw)
    assert defaults["Age"] == 30.0 and defaults["Annual_Premium"] == 30000.0
    assert defaults["Region_Code"] == 28 and defaults["Vintage"] == 100.0
    assert defaults["Gender"] == "Male" and defaults["Vehicle_Age"] == "1-2 Year" and defaults["Previously_Insured"] == "No"

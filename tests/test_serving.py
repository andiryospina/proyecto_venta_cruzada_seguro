import numpy as np
import pandas as pd
import pytest
from sklearn.dummy import DummyClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer

from proyecto.inference.predict import InputValidationError
from proyecto.inference.serving import RAW_COLUMNS, ServingModel, build_defaults, to_raw


def make_clean(n=20):
    rng = np.random.default_rng(0)
    return pd.DataFrame({
        "Age": rng.integers(20, 80, n), "Gender": rng.choice(["Male", "Female"], n), "Region_Code": rng.choice([3, 28], n),
        "Previously_Insured": rng.integers(0, 2, n), "Vehicle_Age": rng.integers(0, 3, n), "Vehicle_Damage": rng.integers(0, 2, n),
        "Annual_Premium": rng.choice([2630.0, 30000.0, 45000.0], n),
    })


class Recorder:
    """Pipeline falso que guarda lo que recibe, para comprobar la traducción a columnas limpias."""
    classes_ = np.array([0, 1])

    def predict_proba(self, X):
        self.seen = X.copy()
        return np.column_stack([np.full(len(X), 0.8), np.full(len(X), 0.2)])


def test_to_raw_and_back_gives_the_clean_columns():
    clean = make_clean()
    raw = to_raw(clean)
    assert list(raw.columns) == RAW_COLUMNS
    recorder = Recorder()
    ServingModel(recorder, build_defaults(raw)).predict_proba(raw)
    seen = recorder.seen
    for col in ["Age", "Region_Code", "Previously_Insured", "Vehicle_Age", "Vehicle_Damage"]:
        assert (seen[col].to_numpy() == clean[col].to_numpy()).all(), col
    assert (seen["Premium_is_minimum"].to_numpy() == (clean["Annual_Premium"] == 2630.0).astype(int).to_numpy()).all()


def test_unknown_values_are_filled_with_the_defaults_not_rejected():
    raw = to_raw(make_clean())
    defaults = build_defaults(raw)
    row = raw.head(1).copy()
    row["Age"] = np.nan
    row["Vehicle_Damage"] = np.nan
    recorder = Recorder()
    ServingModel(recorder, defaults).predict_proba(row)
    assert recorder.seen["Age"].iloc[0] == defaults["Age"]
    assert recorder.seen["Vehicle_Damage"].iloc[0] == {"No": 0, "Yes": 1}[defaults["Vehicle_Damage"]]


def test_unknown_category_raises_a_clear_error():
    raw = to_raw(make_clean()).head(1).assign(Vehicle_Age="3 años")
    with pytest.raises(InputValidationError, match="Vehicle_Age"):
        ServingModel(Recorder(), build_defaults(to_raw(make_clean()))).predict_proba(raw)

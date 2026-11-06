"""Pruebas de las variables nuevas (specs/002-variables). Filas hechas a mano."""
import numpy as np
import pandas as pd

from proyecto.config import ENGINEERED_FEATURES, FEATURE_COLUMNS, TARGET
from proyecto.data.cleaning import clean
from proyecto.features.engineering import add_features, feature_columns
from proyecto.features.preprocessing import build_preprocessor


def _rows(**kw) -> pd.DataFrame:
    """Cuatro clientes ya limpios (como los deja clean())."""
    base = {
        "id": [1, 2, 3, 4],
        "Gender": [1, 0, 1, 0],
        "Age": [25.0, 42.0, 60.0, 35.0],
        "Driving_License": [1, 1, 1, 1],
        "Region_Code": [28, 8, 28, 3],
        "Previously_Insured": [0, 0, 1, 1],
        "Vehicle_Age": [0, 2, 1, 1],
        "Vehicle_Damage": [1, 1, 1, 0],
        "Annual_Premium": [30000.0, 42000.0, 2630.0, 35000.0],
        "Vintage": [100.0, 200.0, 50.0, 10.0],
        "Response": [0, 1, 0, 0],
        "is_min_premium": [0, 0, 1, 0],
    }
    base.update(kw)
    return pd.DataFrame(base)


# --- add_features ---------------------------------------------------------------------------------

def test_uninsured_with_damage():
    """Sin seguro previo y con daño: solo los dos primeros clientes."""
    assert add_features(_rows())["uninsured_with_damage"].tolist() == [1, 1, 0, 0]


def test_damage_x_vehicle_age():
    assert add_features(_rows())["damage_x_vehicle_age"].tolist() == [0, 2, 1, 0]


def test_is_young_customer():
    out = add_features(_rows(Age=[29.0, 30.0, 60.0, 20.0]))
    assert out["is_young_customer"].tolist() == [1, 0, 0, 1]      # 30 ya no es "joven"


def test_age_peak_distance():
    assert add_features(_rows())["age_peak_distance"].tolist() == [17.0, 0.0, 18.0, 7.0]


def test_premium_per_age():
    out = add_features(_rows())
    assert out["premium_per_age"].iloc[1] == 42000.0 / 42.0


def test_missing_or_zero_gives_nan_not_inf():
    """Edad vacía o cero: las variables que dependen de ella quedan vacías, nunca infinitas."""
    out = add_features(_rows(Age=[np.nan, 0.0, 60.0, 35.0]))
    assert np.isnan(out["premium_per_age"].iloc[0]) and np.isnan(out["premium_per_age"].iloc[1])
    assert pd.isna(out["is_young_customer"].iloc[0]) and pd.isna(out["age_peak_distance"].iloc[0])
    numeric = out[ENGINEERED_FEATURES].astype(float).to_numpy()
    assert not np.isinf(numeric).any()


def test_add_features_does_not_mutate_input():
    frame = _rows()
    before = frame.copy()
    out = add_features(frame)
    pd.testing.assert_frame_equal(frame, before)
    assert len(out) == len(frame)
    assert set(ENGINEERED_FEATURES) <= set(out.columns)


# --- feature_columns ------------------------------------------------------------------------------

def test_feature_columns_default_matches_config():
    """Sin argumentos: las mismas columnas de siempre (sin variables nuevas, con Gender)."""
    cols = feature_columns()
    flat = cols["numeric"] + cols["premium"] + cols["flags"] + cols["categorical"]
    assert sorted(flat) == sorted(FEATURE_COLUMNS)


def test_feature_columns_toggles():
    on = feature_columns(use_engineered=True, use_gender=True)
    off = feature_columns(use_engineered=False, use_gender=False)
    flat_on = sum(on.values(), [])
    flat_off = sum(off.values(), [])
    assert set(ENGINEERED_FEATURES) <= set(flat_on) and not set(ENGINEERED_FEATURES) & set(flat_off)
    assert "Gender" in flat_on and "Gender" not in flat_off
    assert "Policy_Sales_Channel" not in flat_on                 # sigue fuera (posible fuga)


# --- build_preprocessor con variables nuevas --------------------------------------------------------

def test_preprocessor_with_engineered_has_no_nans():
    data = add_features(_rows(Age=[np.nan, 42.0, 60.0, 35.0]))
    pre = build_preprocessor(use_engineered=True).fit(data)
    names = list(pre.get_feature_names_out())
    assert "num__age_peak_distance" in names and "flags__uninsured_with_damage" in names
    assert not np.isnan(pre.transform(data)).any()


def test_preprocessor_without_gender():
    pre = build_preprocessor(use_gender=False).fit(add_features(_rows()))
    assert not any("Gender" in n for n in pre.get_feature_names_out())


def test_add_features_on_clean_output():
    """Integración: la salida de clean() (Int64 con vacíos) pasa por add_features y el preprocesador."""
    raw = pd.DataFrame({
        "id": [1, 2, 3], "Gender": ["Male", "Female", "Male"], "Age": [44, 5, 30],   # 5 años: imposible -> vacío
        "Driving_License": [1, 1, 1], "Region_Code": [28.0, 3.0, 28.0], "Previously_Insured": [0, 1, 0],
        "Vehicle_Age": ["> 2 Years", "< 1 Year", "1-2 Year"], "Vehicle_Damage": ["Yes", "No", "Yes"],
        "Annual_Premium": [40454.0, 2630.0, 30000.0], "Policy_Sales_Channel": [26.0, 152.0, 26.0],
        "Vintage": [217, 27, 100], "Response": [1, 0, 1],
    })
    data = add_features(clean(raw))
    assert data["uninsured_with_damage"].tolist() == [1, 0, 1]
    assert pd.isna(data.loc[1, "age_peak_distance"])
    out = build_preprocessor(use_engineered=True).fit_transform(data.drop(columns=TARGET))
    assert not np.isnan(out).any()

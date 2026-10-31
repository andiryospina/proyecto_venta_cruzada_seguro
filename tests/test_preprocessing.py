"""Pruebas del preprocesador que aprende de entrenamiento (especificaciones/03-preprocesamiento.md, sección 3)."""
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

from proyecto.config import FEATURE_COLUMNS, ID_COL, TARGET
from proyecto.data.cleaning import clean
from proyecto.features.preprocessing import build_preprocessor
from proyecto.features.transformers import PremiumTransformer


def clean_rows(n: int = 2000, seed: int = 0) -> pd.DataFrame:
    """Filas ya limpias (como las deja clean(), sin Policy_Sales_Channel). La región 99 es rara (3 de 2.000 = 0,15 %)."""
    rng = np.random.default_rng(seed)
    rare = np.arange(n) >= n - 3
    return pd.DataFrame({
        "id": np.arange(n),
        "Age": rng.integers(20, 85, n),
        "Vintage": rng.integers(10, 300, n),
        "Annual_Premium": np.r_[rng.uniform(3000, 60000, n - 2), [500000.0, 2630.0]],
        "Gender": rng.integers(0, 2, n),
        "Driving_License": np.ones(n, int),
        "Previously_Insured": rng.integers(0, 2, n),
        "Vehicle_Damage": rng.integers(0, 2, n),
        "Vehicle_Age": rng.integers(0, 3, n),
        "is_min_premium": np.r_[np.zeros(n - 1, int), [1]],
        "Region_Code": np.where(rare, 99, np.where(np.arange(n) % 2 == 0, 28, 8)),
        "Response": rng.integers(0, 2, n),
    })


# --- PremiumTransformer ---------------------------------------------------------------------------

def test_premium_transformer_caps_at_train_quantile():
    x = np.r_[np.arange(1, 1000, dtype=float), [1_000_000.0]].reshape(-1, 1)
    t = PremiumTransformer(quantile=0.999).fit(x)
    assert t.cap_ == np.quantile(x, 0.999)
    out = t.transform(np.array([[1_000_000.0], [10.0]]))
    assert out[0, 0] == np.log1p(t.cap_)       # el extremo queda en el tope
    assert out[1, 0] == np.log1p(10.0)         # un valor normal solo pasa por log1p


def test_premium_transformer_uses_train_only():
    """El tope sale SOLO de los datos de ajuste: una prima enorme en prueba no lo mueve y queda recortada."""
    train = np.arange(1, 1001, dtype=float).reshape(-1, 1)
    test = np.array([[5_000_000.0]])
    fitted_on_train = PremiumTransformer(quantile=0.99).fit(train)
    fitted_on_all = PremiumTransformer(quantile=0.99).fit(np.vstack([train, np.full((50, 1), 5_000_000.0)]))
    assert fitted_on_train.cap_ == np.quantile(train, 0.99)
    assert fitted_on_train.cap_ != fitted_on_all.cap_                  # si se ajustara con prueba, el tope cambiaría
    assert fitted_on_train.transform(test)[0, 0] == np.log1p(np.quantile(train, 0.99))


# --- build_preprocessor ---------------------------------------------------------------------------

def test_feature_columns_exclude_id():
    assert ID_COL not in FEATURE_COLUMNS
    assert TARGET not in FEATURE_COLUMNS


def test_preprocessor_excludes_id_and_target():
    pre = build_preprocessor().fit(clean_rows())
    sources = {n.split("__", 1)[1] for n in pre.get_feature_names_out()}
    assert "id" not in sources and "Response" not in sources


def test_preprocessor_groups_rare_categories():
    """Con el umbral real (0,33 %), la región 99 (0,15 %) no tiene columna propia y cae en 'otros'."""
    pre = build_preprocessor().fit(clean_rows())
    names = list(pre.get_feature_names_out())
    assert "cat__Region_Code_28" in names
    assert "cat__Region_Code_99" not in names
    assert "cat__Region_Code_infrequent_sklearn" in names


def test_preprocessor_handles_unknown_category():
    """Una región nunca vista en entrenamiento va a la columna 'otros' (infrequent), no rompe ni se pierde."""
    df = clean_rows()
    pre = build_preprocessor().fit(df)
    new = df.head(1).copy()
    new["Region_Code"] = 777
    out = pd.DataFrame(pre.transform(new), columns=pre.get_feature_names_out())
    assert out.loc[0, "cat__Region_Code_infrequent_sklearn"] == 1
    assert out.filter(like="cat__Region_Code_").sum(axis=1).iloc[0] == 1


def test_preprocessor_does_not_use_channel():
    """Policy_Sales_Channel quedó fuera del modelo (posible fuga): ni en FEATURE_COLUMNS ni en la salida."""
    assert "Policy_Sales_Channel" not in FEATURE_COLUMNS
    pre = build_preprocessor().fit(clean_rows().assign(Policy_Sales_Channel=26))
    assert not any("Policy_Sales_Channel" in n for n in pre.get_feature_names_out())


def test_preprocessor_output_has_no_nans():
    """Vacíos en cada tipo de columna (los que deja flag_impossible_values) se imputan dentro del Pipeline."""
    df = clean_rows().astype({"Age": float, "Vintage": float})
    df.loc[0, "Age"] = np.nan
    df.loc[1, "Annual_Premium"] = np.nan
    df.loc[2, "Vintage"] = np.nan
    df["Driving_License"] = df["Driving_License"].astype("Int64")
    df.loc[3, "Driving_License"] = pd.NA
    out = build_preprocessor().fit_transform(df)
    assert not np.isnan(out).any()


def test_pipeline_trains_on_clean_output():
    """Integración: lo que deja clean() (Int64 con pd.NA) entra al Pipeline del modelo sin errores."""
    rng = np.random.default_rng(1)
    n = 400
    raw = pd.DataFrame({
        "id": np.arange(n),
        "Gender": rng.choice(["Male", "Female"], n),
        "Age": rng.integers(20, 85, n),
        "Driving_License": np.ones(n, int),
        "Region_Code": rng.choice([28.0, 8.0], n),
        "Previously_Insured": rng.integers(0, 2, n),
        "Vehicle_Age": rng.choice(["< 1 Year", "1-2 Year", "> 2 Years"], n),
        "Vehicle_Damage": rng.choice(["Yes", "No"], n),
        "Annual_Premium": rng.uniform(2630, 60000, n),
        "Policy_Sales_Channel": rng.choice([26.0, 152.0], n),
        "Vintage": rng.integers(10, 300, n),
        "Response": rng.integers(0, 2, n),
    })
    raw.loc[0, "Age"] = 5                         # imposible: clean() lo deja vacío
    data = clean(raw)
    model = Pipeline([("pre", build_preprocessor()), ("clf", LogisticRegression(max_iter=500))])
    model.fit(data[FEATURE_COLUMNS], data[TARGET].astype(int))
    proba = model.predict_proba(data[FEATURE_COLUMNS])[:, 1]
    assert proba.shape == (n,) and np.isfinite(proba).all()

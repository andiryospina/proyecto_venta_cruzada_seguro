"""Capa de servicio: traduce lo que escribe una persona a las columnas limpias que espera el modelo final.

El modelo final (`models/final_pipeline.joblib`) recibe los datos tal como salen de la limpieza de la etapa 3: categorías ya
codificadas como números (`config.CATEGORY_MAPS`) y la marca `is_min_premium`. Una persona, en cambio, escribe "Male", "Yes" o
"< 1 Year". `ServingModel` hace esa traducción y expone `predict_proba`, así que se guarda como un solo archivo
(`models/model.joblib`) que usan la app y `predict_with_scores`.

Los datos que la persona marca como "no sé" llegan vacíos (NaN) y se rellenan con valores neutros calculados SOLO con el
entrenamiento: la mediana en los numéricos y el valor más frecuente en los categóricos.

Contrato: `specs/007-integracion-main/contracts/serving.md`.
"""
import numpy as np
import pandas as pd

from proyecto.config import CATEGORY_MAPS, MIN_PREMIUM
from proyecto.inference.predict import InputValidationError

# Respuesta "sí / no" para las dos columnas que en el archivo original ya vienen como 0/1
YES_NO_MAP = {"No": 0, "Yes": 1}

# Cómo se escribe cada columna categórica (texto de la persona -> código del modelo)
CATEGORY_TRANSLATION = {
    "Gender": CATEGORY_MAPS["Gender"],
    "Driving_License": YES_NO_MAP,
    "Previously_Insured": YES_NO_MAP,
    "Vehicle_Age": CATEGORY_MAPS["Vehicle_Age"],
    "Vehicle_Damage": CATEGORY_MAPS["Vehicle_Damage"],
}
NUMERIC_RAW = ["Age", "Annual_Premium", "Region_Code", "Vintage"]
RAW_COLUMNS = NUMERIC_RAW + list(CATEGORY_TRANSLATION)

# Columnas limpias que recibe el modelo, en el orden de train.parquet (sin `id`, que el modelo descarta, ni `Response`)
CLEAN_COLUMNS = ["Gender", "Age", "Driving_License", "Region_Code", "Previously_Insured", "Vehicle_Age", "Vehicle_Damage",
                 "Annual_Premium", "Vintage", "is_min_premium"]
_INTEGER_CODES = ["Gender", "Driving_License", "Region_Code", "Previously_Insured", "Vehicle_Age", "Vehicle_Damage"]


def to_raw(clean: pd.DataFrame) -> pd.DataFrame:
    """De columnas limpias (como train.parquet) a lo que escribiría una persona. Sirve para probar y para el esquema."""
    raw = pd.DataFrame(index=clean.index)
    raw["Age"] = clean["Age"].astype(float)
    raw["Annual_Premium"] = clean["Annual_Premium"].astype(float)
    raw["Region_Code"] = clean["Region_Code"].astype("int64")
    raw["Vintage"] = clean["Vintage"].astype(float)
    for col, mapping in CATEGORY_TRANSLATION.items():
        inverse = {code: text for text, code in mapping.items()}
        raw[col] = clean[col].astype("int64").map(inverse)
    return raw[RAW_COLUMNS]


def build_defaults(raw_train: pd.DataFrame) -> dict:
    """Valores para los "no sé": mediana en los numéricos y valor más frecuente en los categóricos (solo entrenamiento)."""
    defaults = {}
    for col in RAW_COLUMNS:
        if col in NUMERIC_RAW:
            defaults[col] = float(raw_train[col].median())
        else:
            defaults[col] = raw_train[col].mode().iloc[0]
    defaults["Region_Code"] = int(round(defaults["Region_Code"]))   # un código de región es una etiqueta entera
    return defaults


class ServingModel:
    """Envuelve el modelo final: recibe columnas "de persona" y devuelve probabilidades."""

    def __init__(self, pipeline, defaults: dict):
        self.pipeline = pipeline
        self.defaults = defaults                   # valor neutro por columna, para los "no sé"
        self.classes_ = getattr(pipeline, "classes_", np.array([0, 1]))

    def _to_clean(self, df: pd.DataFrame) -> pd.DataFrame:
        filled = pd.DataFrame(index=df.index)
        for col in RAW_COLUMNS:
            filled[col] = df[col].where(df[col].notna(), self.defaults[col])

        for col, mapping in CATEGORY_TRANSLATION.items():
            unknown = sorted(set(filled[col].astype(str)) - set(mapping))
            if unknown:
                raise InputValidationError(f"{col}: valor desconocido {unknown}; se esperaba uno de {sorted(mapping)}")

        clean = pd.DataFrame(index=df.index)
        clean["Age"] = pd.to_numeric(filled["Age"]).astype(float)
        clean["Region_Code"] = pd.to_numeric(filled["Region_Code"]).round()
        clean["Annual_Premium"] = pd.to_numeric(filled["Annual_Premium"]).astype(float)
        clean["Vintage"] = pd.to_numeric(filled["Vintage"]).astype(float)
        for col, mapping in CATEGORY_TRANSLATION.items():
            clean[col] = filled[col].astype(str).map(mapping)
        for col in _INTEGER_CODES:                 # mismos tipos que train.parquet
            clean[col] = clean[col].astype("int64").astype("Int64")
        clean["is_min_premium"] = clean["Annual_Premium"].eq(MIN_PREMIUM).astype("int64")
        return clean[CLEAN_COLUMNS]

    def predict_proba(self, df: pd.DataFrame) -> np.ndarray:
        return self.pipeline.predict_proba(self._to_clean(df))

    def predict(self, df: pd.DataFrame) -> np.ndarray:
        return self.predict_proba(df).argmax(axis=1)

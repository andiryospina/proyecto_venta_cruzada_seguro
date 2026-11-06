"""Capa de servicio: traduce lo que escribe una persona a las columnas limpias que espera el modelo.

El pipeline registrado (`final_pipeline.joblib`) recibe el dato ya limpio por la etapa 3 (códigos 0/1/2, `Premium_is_minimum`).
La app y `predict_with_scores` reciben, en cambio, lo que una persona conoce al llamar: "Yes"/"No", "< 1 Year", etc.
`ServingModel` hace esa traducción y expone `predict_proba`, así que se puede guardar como un solo archivo (`models/model.joblib`).

Los datos que la persona marca como "no sé" llegan como vacíos (NaN): se imputan con valores neutros conocidos del entrenamiento
(la mediana en los numéricos y el valor más frecuente en los categóricos), igual que haría el equipo comercial al no tener el dato.
"""
import numpy as np
import pandas as pd

from proyecto.data.cleaning import MIN_PREMIUM, VEHICLE_AGE_MAP, YES_NO_MAP
from proyecto.inference.predict import InputValidationError

RAW_COLUMNS = ["Age", "Annual_Premium", "Region_Code", "Gender", "Vehicle_Age", "Vehicle_Damage", "Previously_Insured"]
INVERSE_VEHICLE_AGE = {v: k for k, v in VEHICLE_AGE_MAP.items()}
INVERSE_YES_NO = {v: k for k, v in YES_NO_MAP.items()}


def to_raw(clean: pd.DataFrame) -> pd.DataFrame:
    """De las columnas limpias (etapa 3) a las que escribe una persona. Sirve para probar y para construir el esquema."""
    raw = clean[RAW_COLUMNS[:3] + ["Gender"]].copy()
    raw["Vehicle_Age"] = clean["Vehicle_Age"].map(INVERSE_VEHICLE_AGE)
    raw["Vehicle_Damage"] = clean["Vehicle_Damage"].map(INVERSE_YES_NO)
    raw["Previously_Insured"] = clean["Previously_Insured"].map(INVERSE_YES_NO)
    return raw[RAW_COLUMNS]


class ServingModel:
    """Envuelve el pipeline final: recibe columnas "de persona" y devuelve probabilidades."""

    def __init__(self, pipeline, defaults: dict):
        self.pipeline = pipeline
        self.defaults = defaults                   # valor neutro por columna, para los "no sé"
        self.classes_ = getattr(pipeline, "classes_", np.array([0, 1]))

    def _to_clean(self, df: pd.DataFrame) -> pd.DataFrame:
        out = pd.DataFrame(index=df.index)
        for col in RAW_COLUMNS:
            values = df[col]
            out[col] = values.where(values.notna(), self.defaults[col])
        for col, allowed in ("Vehicle_Age", VEHICLE_AGE_MAP), ("Vehicle_Damage", YES_NO_MAP), ("Previously_Insured", YES_NO_MAP):
            unknown = sorted(set(out[col].astype(str)) - set(allowed))
            if unknown:
                raise InputValidationError(f"{col}: valor desconocido {unknown}; se esperaba uno de {sorted(allowed)}")
        out["Age"] = pd.to_numeric(out["Age"]).astype(float)
        out["Annual_Premium"] = pd.to_numeric(out["Annual_Premium"]).astype(float)
        out["Region_Code"] = pd.to_numeric(out["Region_Code"]).round().astype("int64")
        out["Vehicle_Age"] = out["Vehicle_Age"].map(VEHICLE_AGE_MAP).astype("int64")
        out["Vehicle_Damage"] = out["Vehicle_Damage"].map(YES_NO_MAP).astype("int64")
        out["Previously_Insured"] = out["Previously_Insured"].map(YES_NO_MAP).astype("int64")
        out["Premium_is_minimum"] = (out["Annual_Premium"] == MIN_PREMIUM).astype("int8")
        return out

    def predict_proba(self, df: pd.DataFrame) -> np.ndarray:
        return self.pipeline.predict_proba(self._to_clean(df))

    def predict(self, df: pd.DataFrame) -> np.ndarray:
        return self.predict_proba(df).argmax(axis=1)


def build_defaults(raw_train: pd.DataFrame) -> dict:
    """Valores neutros para los "no sé": mediana en numéricos y valor más frecuente en categóricos (solo del entrenamiento)."""
    defaults = {}
    for col in RAW_COLUMNS:
        if col in ("Age", "Annual_Premium", "Region_Code"):
            defaults[col] = float(raw_train[col].median())
        else:
            defaults[col] = raw_train[col].mode().iloc[0]
    return defaults

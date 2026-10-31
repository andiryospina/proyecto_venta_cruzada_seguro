"""Variables nuevas y selección de columnas del modelo (specs/002-variables).

Sigue el patrón del ejemplo del curso (`material-del-curso/ejemplo-creditsight/src/creditsight/features/engineering.py`):
  - `add_features` calcula las variables nuevas fila por fila, con datos que se conocen ANTES de llamar al cliente.
    No aprende nada de los datos, así que puede aplicarse a entrenamiento y prueba sin fuga de información.
  - `feature_columns` decide qué columnas usa el modelo, con interruptores para medir cada idea con y sin ella
    en la etapa 04 (mismo modelo, mismos pliegues, misma métrica).

Las variables nuevas empiezan APAGADAS (`use_engineered=False`), como en el ejemplo: solo entran al modelo final
si el notebook 04 demuestra que mejoran más que el ruido entre pliegues.
"""
import numpy as np
import pandas as pd

from proyecto.config import (
    CATEGORICAL_FEATURES,
    ENGINEERED_FLAGS,
    ENGINEERED_NUMERIC,
    FLAG_FEATURES,
    NUMERIC_FEATURES,
    PEAK_AGE,
    PREMIUM_FEATURE,
    YOUNG_AGE,
)


def _ratio(num: pd.Series, den: pd.Series) -> pd.Series:
    """División segura: si el denominador es cero, negativo o vacío, el resultado es vacío (nunca infinito)."""
    num = num.astype(float)
    den = den.astype(float)
    return num / den.where(den > 0)


def add_features(df: pd.DataFrame) -> pd.DataFrame:
    """Añade las 5 variables nuevas a datos ya limpios (salida de `clean()`). No modifica el original ni borra filas.

    - `uninsured_with_damage`: 1 si el cliente NO tiene seguro de vehículo y SÍ tuvo daño previo
      (25,0 % de interés frente a 0,5 % del resto; es la regla de la línea base).
    - `damage_x_vehicle_age`: daño previo (0/1) × antigüedad del vehículo (0/1/2): vehículo viejo y con daño.
    - `is_young_customer`: 1 si la edad es menor de 30 (4,1 % de interés frente a 17,9 %).
    - `age_peak_distance`: años de distancia a 42, la edad de mayor interés (la relación tiene forma de campana).
    - `premium_per_age`: prima anual dividida por la edad (prima relativa a la etapa de vida).
    Si un dato de entrada está vacío, la variable que depende de él también queda vacía (se imputa en el Pipeline).
    """
    out = df.copy()
    age = out["Age"].astype(float)

    uninsured = out["Previously_Insured"].astype("Int64").eq(0)
    damaged = out["Vehicle_Damage"].astype("Int64").eq(1)
    out["uninsured_with_damage"] = (uninsured & damaged).astype("Int64")
    out["damage_x_vehicle_age"] = (out["Vehicle_Damage"].astype("Int64") * out["Vehicle_Age"].astype("Int64")).astype("Int64")
    out["is_young_customer"] = age.lt(YOUNG_AGE).astype("Int64").mask(age.isna())
    out["age_peak_distance"] = (age - PEAK_AGE).abs()
    out["premium_per_age"] = _ratio(out["Annual_Premium"], age)
    return out


def _selected_engineered(use_engineered: bool | list[str]) -> list[str]:
    """True → las 5 variables nuevas; False → ninguna; lista → solo esas (para medirlas una por una)."""
    if use_engineered is True:
        return list(ENGINEERED_FLAGS + ENGINEERED_NUMERIC)
    if not use_engineered:
        return []
    unknown = sorted(set(use_engineered) - set(ENGINEERED_FLAGS + ENGINEERED_NUMERIC))
    if unknown:
        raise ValueError(f"Variables nuevas desconocidas: {unknown}")
    return list(use_engineered)


def feature_columns(use_engineered: bool | list[str] = False, use_gender: bool = True) -> dict[str, list[str]]:
    """Devuelve las columnas que usa el modelo, por tipo: `numeric`, `premium`, `flags` y `categorical`.

    - `use_engineered`: True suma las 5 variables nuevas de `add_features`; una lista suma solo esas
      (así se mide cada una en la etapa 04); False (por defecto) no suma ninguna.
    - `use_gender`: permite medir el modelo sin `Gender` (decisión 10 del EDA, equidad).
    Sin argumentos devuelve exactamente `FEATURE_COLUMNS` de `config.py`.
    `id`, `Response` y `Policy_Sales_Channel` (eliminada por posible fuga) nunca aparecen.
    """
    flags = [c for c in FLAG_FEATURES if use_gender or c != "Gender"]
    numeric = list(NUMERIC_FEATURES)
    selected = _selected_engineered(use_engineered)
    flags += [c for c in ENGINEERED_FLAGS if c in selected]
    numeric += [c for c in ENGINEERED_NUMERIC if c in selected]
    return {
        "numeric": numeric,
        "premium": [PREMIUM_FEATURE],
        "flags": flags,
        "categorical": list(CATEGORICAL_FEATURES),
    }


def all_feature_columns(use_engineered: bool | list[str] = False, use_gender: bool = True) -> list[str]:
    """Las mismas columnas de `feature_columns`, en una sola lista (útil para `train[columnas]`)."""
    return [c for group in feature_columns(use_engineered, use_gender).values() for c in group]

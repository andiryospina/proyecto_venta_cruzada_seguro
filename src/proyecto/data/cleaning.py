"""Limpieza del dataset crudo de venta cruzada (reglas SIN aprendizaje: se aplican antes de partir).

Cada regla sale de `especificaciones/03-preprocesamiento.md`, sección 3:
  - `Policy_Sales_Channel` se elimina: es el canal de contacto y puede no conocerse antes de decidir (posible fuga).
  - El código de región llega como decimal (28.0): se convierte a entero (decisión 6 del EDA).
  - Género, daño previo y antigüedad del vehículo llegan como texto: se codifican con mapas fijos (decisión 7).
  - La prima 2.630 es la prima mínima del producto (decisión de negocio): se conserva y se marca (decisión 4).
  - Los valores imposibles (edad < 18, prima <= 0, ...) se marcan como vacío; no se borran filas.

Nada de esto aprende de los datos, así que puede hacerse antes de partir sin fuga de información.
El recorte de atípicos de la prima SÍ aprende (percentil 99,9) y por eso vive en `proyecto.features`.
"""
from pathlib import Path

import numpy as np
import pandas as pd

from proyecto.config import (
    BINARY_COLUMNS,
    CATEGORY_MAPS,
    CODE_COLUMNS,
    DROPPED_COLUMNS,
    MIN_PREMIUM,
    POSITIVE_COLUMNS,
    RAW_COLUMNS,
    RAW_DIR,
    RAW_FILENAME,
    ROOT,
    VALID_RANGE,
)


def find_raw_file() -> Path:
    """Ruta del dataset crudo: `data/raw/dataset.csv` si existe; si no, `dataset.csv` en la raíz del repo."""
    for candidate in (RAW_DIR / RAW_FILENAME, ROOT / RAW_FILENAME):
        if candidate.exists():
            return candidate
    raise FileNotFoundError(f"No se encontró {RAW_FILENAME} en data/raw/ ni en la raíz del repositorio.")


def load_raw(path: str | Path | None = None) -> pd.DataFrame:
    """Lee el CSV crudo (sin modificarlo) y verifica que trae exactamente las columnas esperadas."""
    df = pd.read_csv(path or find_raw_file())
    unexpected = sorted(set(df.columns) - set(RAW_COLUMNS))
    missing = sorted(set(RAW_COLUMNS) - set(df.columns))
    if unexpected:
        raise ValueError(f"Columnas inesperadas en el archivo crudo: {unexpected}")
    if missing:
        raise ValueError(f"Faltan columnas en el archivo crudo: {missing}")
    return df[RAW_COLUMNS]


def drop_excluded_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Elimina las columnas que no deben llegar al modelo (hoy: `Policy_Sales_Channel`, posible fuga)."""
    return df.drop(columns=[c for c in DROPPED_COLUMNS if c in df.columns])


def cast_codes_to_int(df: pd.DataFrame) -> pd.DataFrame:
    """Convierte `Region_Code` de decimal a entero (es una etiqueta, no una cantidad)."""
    out = df.copy()
    for col in CODE_COLUMNS:
        values = out[col].dropna()
        if not (values == np.round(values)).all():
            raise ValueError(f"{col} tiene valores con decimales; no es un código entero")
        out[col] = out[col].astype("Int64")
    return out


def encode_categoricals(df: pd.DataFrame) -> pd.DataFrame:
    """Codifica las columnas de texto con mapas fijos: Male=1, Yes=1 y la antigüedad del vehículo 0/1/2."""
    out = df.copy()
    for col, mapping in CATEGORY_MAPS.items():
        unknown = sorted(set(out[col].dropna()) - set(mapping))
        if unknown:
            raise ValueError(f"{col} tiene valores desconocidos: {unknown}")
        out[col] = out[col].map(mapping).astype("Int64")
    return out


def add_min_premium_flag(df: pd.DataFrame) -> pd.DataFrame:
    """Agrega `is_min_premium` (1 si la prima es la mínima del producto, 2.630). El valor de la prima se conserva."""
    out = df.copy()
    out["is_min_premium"] = out["Annual_Premium"].eq(MIN_PREMIUM).astype(int)
    return out


def flag_impossible_values(df: pd.DataFrame) -> pd.DataFrame:
    """Marca como vacío lo imposible en el mundo real. No borra filas; la imputación va en el Pipeline."""
    out = df.copy()
    for col, (low, high) in VALID_RANGE.items():
        values = out[col].astype(float)
        bad = pd.Series(False, index=out.index)
        if low is not None:
            bad |= values < low
        if high is not None:
            bad |= values > high
        out[col] = values.mask(bad)
    for col in POSITIVE_COLUMNS:
        values = out[col].astype(float)
        out[col] = values.mask(values <= 0)
    for col in BINARY_COLUMNS:
        out[col] = out[col].where(out[col].isin([0, 1])).astype("Int64")
    return out


def clean(df: pd.DataFrame) -> pd.DataFrame:
    """Aplica todas las reglas sin aprendizaje, en orden. Devuelve las mismas filas, sin columnas de texto."""
    out = drop_excluded_columns(df)
    out = cast_codes_to_int(out)
    out = encode_categoricals(out)
    out = add_min_premium_flag(out)
    out = flag_impossible_values(out)
    return out

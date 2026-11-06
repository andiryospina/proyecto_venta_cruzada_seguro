"""Partición entrenamiento / prueba (especificaciones/03-preprocesamiento.md, sección 1).

Cada cliente aparece en una sola fila (381.109 `id` distintos), así que partir por fila equivale a partir por cliente.
Se estratifica por `Response` para conservar el 12,26 % de interesados en las dos partes.
"""
import pandas as pd
from sklearn.model_selection import train_test_split

from proyecto.config import ID_COL, SEED, TARGET, TEST_SIZE


def split_train_test(df: pd.DataFrame, test_size: float = TEST_SIZE, seed: int = SEED) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Parte en entrenamiento y prueba, estratificado por `Response`. No quita ni modifica filas."""
    if df[ID_COL].duplicated().any():
        raise ValueError(f"Hay {ID_COL} repetidos: la partición por fila ya no sería válida; partir por grupo")
    if df[TARGET].isna().any():
        raise ValueError(f"{TARGET} tiene {int(df[TARGET].isna().sum())} vacíos (valores fuera de 0/1): revisar antes de partir")
    train, test = train_test_split(df, test_size=test_size, stratify=df[TARGET], random_state=seed)
    return train.sort_index(), test.sort_index()


def drop_duplicate_rows(df: pd.DataFrame) -> pd.DataFrame:
    """Quita filas repetidas sin contar el `id` (mismo perfil y misma respuesta), conservando la primera.

    Se aplica SOLO al entrenamiento: la prueba se deja tal cual llega, como llegarían los datos reales.
    """
    columns = [c for c in df.columns if c != ID_COL]
    return df.drop_duplicates(subset=columns, keep="first")

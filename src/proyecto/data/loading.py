"""Carga de los datos de entrenamiento de la etapa 3.

Nunca devuelve la prueba cerrada: quien necesite la prueba (etapa 7) debe pedirla de forma explícita y a propósito.
"""
from pathlib import Path

import pandas as pd

from proyecto.data.cleaning import clean, find_train_csv, load_raw
from proyecto.data.split import split_train_holdout


def load_train(root) -> pd.DataFrame:
    """Entrenamiento limpio. Usa `data/processed/train.parquet` si existe; si no, lo reconstruye igual que el notebook 03.

    La reconstrucción es determinista (misma limpieza, misma semilla 42), así que da exactamente las mismas filas.
    La prueba cerrada se descarta sin mirarla.
    """
    processed = Path(root) / "data" / "processed" / "train.parquet"
    if processed.exists():
        return pd.read_parquet(processed)
    cleaned = clean(load_raw(find_train_csv(root)))
    train, _closed_test = split_train_holdout(cleaned)
    return train

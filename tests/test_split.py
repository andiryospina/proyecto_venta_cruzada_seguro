"""Pruebas de la partición (especificaciones/03-preprocesamiento.md, secciones 1 y 6)."""
import numpy as np
import pandas as pd
import pytest

from proyecto.config import ID_COL, TARGET
from proyecto.data.split import drop_duplicate_rows, split_train_test


def customers(n: int = 1000, positive_rate: float = 0.12, seed: int = 0) -> pd.DataFrame:
    """n clientes distintos con una tasa fija de interesados."""
    rng = np.random.default_rng(seed)
    n_pos = int(n * positive_rate)
    return pd.DataFrame({
        ID_COL: np.arange(1, n + 1),
        "Age": rng.integers(20, 85, n),
        TARGET: np.r_[np.ones(n_pos, int), np.zeros(n - n_pos, int)],
    })


def test_split_ids_are_disjoint():
    train, test = split_train_test(customers())
    assert set(train[ID_COL]).isdisjoint(test[ID_COL])


def test_split_loses_no_rows():
    df = customers()
    train, test = split_train_test(df)
    assert len(train) + len(test) == len(df)
    assert set(train[ID_COL]) | set(test[ID_COL]) == set(df[ID_COL])


def test_split_test_size():
    train, test = split_train_test(customers(), test_size=0.2)
    assert len(test) == 200


def test_split_is_stratified():
    """Con estratificación, la prueba lleva exactamente el 20 % de los interesados: 24 de 120 (falla si se quita stratify)."""
    df = customers(n=1000, positive_rate=0.12)
    train, test = split_train_test(df)
    assert int(test[TARGET].sum()) == 24
    assert int(train[TARGET].sum()) == 96


def test_split_is_reproducible():
    df = customers()
    _, test_a = split_train_test(df, seed=42)
    _, test_b = split_train_test(df, seed=42)
    assert test_a[ID_COL].tolist() == test_b[ID_COL].tolist()


def test_split_rejects_repeated_ids():
    """Si un cliente apareciera en varias filas, partir por fila dejaría de ser válido: debe fallar."""
    df = customers()
    df.loc[1, ID_COL] = df.loc[0, ID_COL]
    with pytest.raises(ValueError, match="repetidos"):
        split_train_test(df)


def test_drop_duplicate_rows():
    """Dos clientes con las mismas variables (distinto id): se conserva el primero."""
    df = pd.DataFrame({ID_COL: [1, 2, 3], "Age": [30, 30, 40], TARGET: [0, 0, 1]})
    out = drop_duplicate_rows(df)
    assert out[ID_COL].tolist() == [1, 3]


def test_drop_duplicate_rows_keeps_different_rows():
    df = pd.DataFrame({ID_COL: [1, 2], "Age": [30, 31], TARGET: [0, 0]})
    assert len(drop_duplicate_rows(df)) == 2


def test_test_set_not_deduplicated():
    """El flujo de la etapa 03 (partir y luego deduplicar SOLO entrenamiento) deja la prueba con sus repetidos."""
    df = customers()
    df["Age"] = 50                                   # todos los perfiles quedan repetidos (difieren solo en id)
    train, test = split_train_test(df)
    test_before = test.copy()
    train = drop_duplicate_rows(train)
    pd.testing.assert_frame_equal(test, test_before)
    assert test.drop(columns=ID_COL).duplicated().sum() > 0   # la prueba conserva los repetidos
    assert train.drop(columns=ID_COL).duplicated().sum() == 0


def test_split_rejects_missing_target():
    df = customers().astype({TARGET: "Int64"})
    df.loc[0, TARGET] = pd.NA
    with pytest.raises(ValueError, match="vacíos"):
        split_train_test(df)

"""Pruebas de la partición: la más importante del preprocesamiento (ver sección 4.3 de la guía)."""
import numpy as np
import pandas as pd
import pytest

from proyecto.data.split import (
    assert_disjoint_ids,
    assert_unique_ids,
    split_train_holdout,
    stratified_folds,
)


def make_frame(n: int = 1000, positive_rate: float = 0.12, seed: int = 0) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    y = np.zeros(n, dtype=int)
    y[: int(n * positive_rate)] = 1
    rng.shuffle(y)
    return pd.DataFrame({"id": np.arange(1, n + 1), "x": rng.normal(size=n), "Response": y})


def test_no_id_in_both_partitions_and_no_row_lost():
    df = make_frame()
    train, test = split_train_holdout(df)
    assert set(train["id"]).isdisjoint(set(test["id"]))
    assert len(train) + len(test) == len(df)
    assert sorted(pd.concat([train["id"], test["id"]])) == sorted(df["id"])


def test_test_size_is_respected():
    train, test = split_train_holdout(make_frame(1000), test_size=0.2)
    assert len(test) == 200 and len(train) == 800


def test_split_keeps_the_positive_rate_in_both_partitions():
    df = make_frame(10_000, positive_rate=0.1226)
    train, test = split_train_holdout(df)
    base = df["Response"].mean()
    assert abs(train["Response"].mean() - base) < 0.001
    assert abs(test["Response"].mean() - base) < 0.001


def test_split_is_reproducible_with_the_same_seed_and_changes_with_another():
    df = make_frame()
    a, _ = split_train_holdout(df, seed=42)
    b, _ = split_train_holdout(df, seed=42)
    c, _ = split_train_holdout(df, seed=7)
    assert a["id"].tolist() == b["id"].tolist()
    assert a["id"].tolist() != c["id"].tolist()


def test_guard_fails_when_an_id_is_in_both_partitions():
    df = make_frame(10)
    with pytest.raises(AssertionError, match="más de una partición"):
        assert_disjoint_ids(df.iloc[:6], df.iloc[4:])     # los ids 5 y 6 quedan en las dos


def test_split_refuses_data_where_an_entity_repeats():
    df = make_frame(10)
    df.loc[3, "id"] = df.loc[2, "id"]                      # un mismo cliente en dos filas
    with pytest.raises(AssertionError, match="por grupo"):
        assert_unique_ids(df)
    with pytest.raises(AssertionError, match="por grupo"):
        split_train_holdout(df)


def test_folds_cover_all_rows_once_and_keep_the_positive_rate():
    df = make_frame(5000, positive_rate=0.12)
    folds = stratified_folds(df, n_splits=5)
    assert len(folds) == 5
    validation_ids = np.concatenate([val for _, val in folds])
    assert sorted(validation_ids) == list(range(len(df)))   # cada fila se valida exactamente una vez
    for train_idx, val_idx in folds:
        assert set(train_idx).isdisjoint(set(val_idx))
        assert abs(df.iloc[val_idx]["Response"].mean() - 0.12) < 0.01

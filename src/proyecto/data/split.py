"""Partición de los datos: entrenamiento, prueba cerrada y pliegues de validación.

**Unidad de análisis:** un cliente por fila (`id` único, verificado en el EDA), así que partir por fila es válido:
ningún cliente puede quedar a los dos lados. Aun así se **verifica** en cada partición, por si algún día los datos cambian.

Se **estratifica** por `Response`, porque solo el 12,26 % de los clientes acepta: sin estratificar, la proporción de
compradores de cada partición variaría por azar y las métricas no serían comparables.
"""
import pandas as pd
from sklearn.model_selection import StratifiedKFold, train_test_split

ID_COL = "id"
TARGET = "Response"
RANDOM_STATE = 42
TEST_SIZE = 0.2


def assert_unique_ids(df: pd.DataFrame, id_col: str = ID_COL) -> None:
    """Falla si un mismo `id` aparece en más de una fila (en ese caso hay que partir por grupo, no por fila)."""
    repeated = int(df[id_col].duplicated().sum())
    if repeated:
        raise AssertionError(f"{repeated} filas repiten un {id_col}: la partición debe ser por grupo, no por fila")


def assert_disjoint_ids(*frames: pd.DataFrame, id_col: str = ID_COL) -> None:
    """Falla si algún `id` aparece en más de una partición."""
    seen: set = set()
    for i, frame in enumerate(frames):
        ids = set(frame[id_col])
        overlap = seen & ids
        if overlap:
            raise AssertionError(f"{len(overlap)} {id_col} aparecen en más de una partición (partición {i})")
        seen |= ids


def split_train_holdout(df: pd.DataFrame, target: str = TARGET, test_size: float = TEST_SIZE,
                        seed: int = RANDOM_STATE, id_col: str = ID_COL):
    """Separa entrenamiento y prueba cerrada, estratificando por `target`.

    La prueba **no se mira** hasta la etapa de validación final. Devuelve `(train, test)` con índices reiniciados.
    """
    assert_unique_ids(df, id_col)
    train, test = train_test_split(df, test_size=test_size, random_state=seed, stratify=df[target])
    train = train.reset_index(drop=True)
    test = test.reset_index(drop=True)
    assert_disjoint_ids(train, test, id_col=id_col)
    if len(train) + len(test) != len(df):
        raise AssertionError("la partición perdió o duplicó filas")
    return train, test


def stratified_folds(df: pd.DataFrame, target: str = TARGET, n_splits: int = 5, seed: int = RANDOM_STATE):
    """Pliegues de validación cruzada estratificados, solo sobre el conjunto de entrenamiento.

    Devuelve una lista de `(índices_entrenamiento, índices_validación)`.
    """
    cv = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=seed)
    return list(cv.split(df, df[target]))

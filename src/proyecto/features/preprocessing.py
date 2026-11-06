"""Preprocesador del modelo: todo lo que aprende de los datos, para ajustarlo SOLO con entrenamiento.

Se usa como primer paso del Pipeline del modelo en la etapa 04:

    from sklearn.pipeline import Pipeline
    model = Pipeline([("pre", build_preprocessor()), ("clf", LogisticRegression())])
    model.fit(train[FEATURE_COLUMNS], train[TARGET])
"""
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer, OneHotEncoder, StandardScaler

from proyecto.config import PREMIUM_CAP_QUANTILE, RARE_CATEGORY_MIN_FREQUENCY
from proyecto.features.engineering import feature_columns
from proyecto.features.transformers import PremiumTransformer


def _to_float(X):
    """Convierte enteros con vacíos (Int64 / pd.NA) a float con NaN, que es lo que entiende SimpleImputer."""
    return X.astype(float)


def _to_int(X):
    """Devuelve los códigos imputados a entero, para que las columnas one-hot se llamen `Region_Code_28` y no `_28.0`."""
    return X.astype(int)


def build_preprocessor(
    premium_quantile: float = PREMIUM_CAP_QUANTILE,
    rare_min_frequency: float = RARE_CATEGORY_MIN_FREQUENCY,
    use_engineered: bool | list[str] = False,
    use_gender: bool = True,
) -> ColumnTransformer:
    """Arma el ColumnTransformer de las decisiones del EDA y de atípicos (sin ajustar).

    Las columnas salen de `feature_columns(use_engineered, use_gender)`. Con `use_engineered=True` los datos
    deben haber pasado antes por `add_features` (variables nuevas: las numéricas se imputan y escalan, las
    marcas pasan como números).

    - Prima: imputación por mediana → recorte al percentil 99,9 de entrenamiento + log1p → escalado.
    - Edad y antigüedad como cliente: sin atípicos; imputación por mediana → escalado.
    - Indicadores 0/1 (y antigüedad del vehículo 0/1/2): imputación por el valor más frecuente.
    - Región y canal: one-hot; las categorías con menos de `rare_min_frequency` de las filas de entrenamiento,
      y las que aparezcan nuevas después, van a una sola columna "infrequent".
    `id` y `Response` no se usan (remainder="drop").
    """
    cols = feature_columns(use_engineered=use_engineered, use_gender=use_gender)
    to_float = FunctionTransformer(_to_float, feature_names_out="one-to-one")
    premium = Pipeline([
        ("to_float", to_float),
        ("impute", SimpleImputer(strategy="median")),
        ("cap_log", PremiumTransformer(quantile=premium_quantile)),
        ("scale", StandardScaler()),
    ])
    numeric = Pipeline([
        ("to_float", to_float),
        ("impute", SimpleImputer(strategy="median")),
        ("scale", StandardScaler()),
    ])
    flags = Pipeline([
        ("to_float", to_float),
        ("impute", SimpleImputer(strategy="most_frequent")),
    ])
    categorical = Pipeline([
        ("to_float", to_float),
        ("impute", SimpleImputer(strategy="most_frequent")),
        ("to_int", FunctionTransformer(_to_int, feature_names_out="one-to-one")),
        ("onehot", OneHotEncoder(min_frequency=rare_min_frequency, handle_unknown="infrequent_if_exist",
                                 sparse_output=False)),
    ])
    return ColumnTransformer(
        [
            ("premium", premium, cols["premium"]),
            ("num", numeric, cols["numeric"]),
            ("flags", flags, cols["flags"]),
            ("cat", categorical, cols["categorical"]),
        ],
        remainder="drop",
        verbose_feature_names_out=True,
    )

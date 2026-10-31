"""Variables nuevas y preprocesamiento que APRENDE de los datos (etapa 4).

Todo lo que está aquí se ejecuta **dentro de un `Pipeline`**: `fit` mira solo el entrenamiento de cada pliegue y
`transform` aplica lo aprendido a datos que el modelo no ha visto. Así el recorte de la prima, los canales raros o la
tasa histórica de un canal no filtran información de validación ni de la prueba cerrada.

Cada idea del notebook 04 es una opción de `FeatureOptions`: la referencia es `FeatureOptions()` y cada idea cambia
**una cosa** respecto de ella, para poder medirla sola.
"""
from dataclasses import dataclass, field
from functools import partial

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.compose import ColumnTransformer
from sklearn.model_selection import StratifiedKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer, OneHotEncoder, SplineTransformer, StandardScaler, TargetEncoder

# Grupos de columnas del dataset limpio (etapa 3). `id` y `Response` nunca son variables.
BINARY_COLS = ["Driving_License", "Previously_Insured", "Vehicle_Damage", "Premium_is_minimum"]
ORDINAL_COLS = ["Vehicle_Age"]
NUMERIC_COLS = ["Age", "Vintage"]
PREMIUM_COL = "Annual_Premium"
CATEGORICAL_COL = "Gender"
CODE_COLS = ["Region_Code", "Policy_Sales_Channel"]
RARE_LABEL = -1   # código que reemplaza a los canales o regiones poco frecuentes y a los que no se vieron al entrenar


class PremiumClipper(BaseEstimator, TransformerMixin):
    """Limita la prima por arriba al percentil `quantile` **del entrenamiento** (por defecto el 99)."""

    def __init__(self, quantile: float = 0.99):
        self.quantile = quantile

    def fit(self, X, y=None):
        self.upper_ = float(np.quantile(np.asarray(X, dtype=float), self.quantile))
        return self

    def transform(self, X):
        return np.minimum(np.asarray(X, dtype=float), self.upper_)

    def get_feature_names_out(self, input_features=None):
        return np.asarray(input_features if input_features is not None else ["Annual_Premium"], dtype=object)


class RareCategoryGrouper(BaseEstimator, TransformerMixin):
    """Agrupa en `RARE_LABEL` los códigos con menos de `min_count` clientes **en el entrenamiento**.

    Un código que no aparecía al entrenar (un canal nuevo) también pasa a `RARE_LABEL`, así que el modelo
    nunca se encuentra con una categoría desconocida.
    """

    def __init__(self, min_count: int = 100):
        self.min_count = min_count

    def fit(self, X, y=None):
        data = np.asarray(X)
        self.kept_ = []
        for j in range(data.shape[1]):
            values, counts = np.unique(data[:, j], return_counts=True)
            self.kept_.append(values[counts >= self.min_count])
        return self

    def transform(self, X):
        data = np.asarray(X).copy()
        for j, kept in enumerate(self.kept_):
            data[:, j] = np.where(np.isin(data[:, j], kept), data[:, j], RARE_LABEL)
        return data

    def get_feature_names_out(self, input_features=None):
        return np.asarray(input_features if input_features is not None else CODE_COLS, dtype=object)


class PremiumVsRegion(BaseEstimator, TransformerMixin):
    """Prima del cliente dividida entre la prima mediana de su región (mediana calculada con el entrenamiento).

    Responde a: "¿este cliente paga más o menos que sus vecinos?". Una región desconocida usa la mediana global.
    Recibe dos columnas, en este orden: `Annual_Premium` y `Region_Code`.
    """

    def fit(self, X, y=None):
        frame = pd.DataFrame(np.asarray(X), columns=["premium", "region"])
        self.global_median_ = float(frame["premium"].median())
        self.medians_ = frame.groupby("region")["premium"].median().to_dict()
        return self

    def transform(self, X):
        data = np.asarray(X)
        premium = data[:, 0].astype(float)
        medians = np.array([self.medians_.get(r, self.global_median_) for r in data[:, 1]], dtype=float)
        medians = np.where(medians > 0, medians, self.global_median_)
        return (premium / medians).reshape(-1, 1)

    def get_feature_names_out(self, input_features=None):
        return np.asarray(["premium_vs_region"], dtype=object)


def commercial_segment(X) -> np.ndarray:
    """1 si el cliente NO tiene seguro de vehículo y SÍ tuvo daño (el segmento que concentra el 97,7 % de los compradores).

    Recibe dos columnas, en este orden: `Previously_Insured` y `Vehicle_Damage`. No aprende nada: es una regla de negocio.
    """
    data = np.asarray(X)
    return ((data[:, 0] == 0) & (data[:, 1] == 1)).astype(int).reshape(-1, 1)


def _segment_names(transformer, input_features):
    """Nombre de la columna que produce `commercial_segment` (función normal y no lambda, para poder guardar el pipeline)."""
    return np.asarray(["commercial_segment"], dtype=object)


# ----------------------------------------------------------------------------------------------------------------------
# Segunda ronda: variables NUEVAS. Se agregan a las que ya existen; no reemplazan ni quitan ninguna.
# Todas se calculan solo con datos que se conocen al llamar y NO usan la respuesta (`Response`).
# ----------------------------------------------------------------------------------------------------------------------
YOUNG_MAX_AGE = 25                       # primer tramo de edad del EDA (20-25 años): el de menor aceptación (3,5 %)
AGE_BANDS = [19, 25, 35, 45, 55, 65, 200]   # los mismos tramos del EDA
NEW_FEATURES = ("channel_region_volume", "need_score", "profile_12", "young_new_vehicle", "premium_vs_age_band", "vintage_share")


def _fixed_names(names, transformer, input_features):
    """Nombres de columnas para un `FunctionTransformer` (función normal con `partial`, no lambda, para poder guardar el pipeline)."""
    return np.asarray(names, dtype=object)


class CodeVolume(BaseEstimator, TransformerMixin):
    """Tamaño de cada canal y de cada región: el logaritmo de cuántos clientes tiene en el entrenamiento.

    Responde a: "¿es un canal masivo o de nicho?". No usa la respuesta, solo cuenta clientes. Un código que no se vio
    al entrenar vale 0. Recibe dos columnas, en este orden: `Policy_Sales_Channel` y `Region_Code`.
    """

    def fit(self, X, y=None):
        data = np.asarray(X)
        self.counts_ = [pd.Series(data[:, j]).value_counts().to_dict() for j in range(data.shape[1])]
        return self

    def transform(self, X):
        data = np.asarray(X)
        columns = [np.log1p(pd.Series(data[:, j]).map(self.counts_[j]).fillna(0).to_numpy(dtype=float)) for j in range(data.shape[1])]
        return np.column_stack(columns)

    def get_feature_names_out(self, input_features=None):
        return np.asarray(["channel_volume", "region_volume"], dtype=object)


class PremiumVsAgeBand(BaseEstimator, TransformerMixin):
    """Prima del cliente dividida entre la prima mediana de las personas de su tramo de edad (mediana del entrenamiento).

    Responde a: "¿este cliente paga más o menos que sus pares de edad?". Recibe dos columnas, en este orden:
    `Annual_Premium` y `Age`.
    """

    def _band(self, age):
        return np.digitize(np.asarray(age, dtype=float), AGE_BANDS[1:-1], right=True)

    def fit(self, X, y=None):
        data = np.asarray(X, dtype=float)
        self.global_median_ = float(np.median(data[:, 0]))
        bands = self._band(data[:, 1])
        self.medians_ = {int(b): float(np.median(data[bands == b, 0])) for b in np.unique(bands)}
        return self

    def transform(self, X):
        data = np.asarray(X, dtype=float)
        medians = np.array([self.medians_.get(int(b), self.global_median_) for b in self._band(data[:, 1])])
        medians = np.where(medians > 0, medians, self.global_median_)
        return (data[:, 0] / medians).reshape(-1, 1)

    def get_feature_names_out(self, input_features=None):
        return np.asarray(["premium_vs_age_band"], dtype=object)


def need_score(X) -> np.ndarray:
    """Puntaje de "necesidad de cobertura" de 0 a 4: no tiene seguro (+1), tuvo daño (+1) y antigüedad del vehículo (0, 1 o 2).

    Resume en un número lo que el EDA mostró por separado. Recibe tres columnas, en este orden: `Previously_Insured`,
    `Vehicle_Damage` y `Vehicle_Age`. No aprende nada: es una regla de negocio.
    """
    data = np.asarray(X)
    return ((1 - data[:, 0]) + data[:, 1] + data[:, 2]).astype(float).reshape(-1, 1)


def profile_12_code(X) -> np.ndarray:
    """Código del perfil completo (seguro previo × daño × antigüedad del vehículo): un número de 0 a 11.

    Le da a un modelo lineal las 12 combinaciones como categorías, para que aprenda cada una sin necesitar interacciones.
    """
    data = np.asarray(X)
    return (data[:, 0] * 6 + data[:, 1] * 3 + data[:, 2]).astype(int).reshape(-1, 1)


def young_new_vehicle(X) -> np.ndarray:
    """1 si el cliente tiene 25 años o menos y un vehículo de menos de 1 año (el cruce de dos de los grupos que menos aceptan).

    Recibe dos columnas, en este orden: `Age` y `Vehicle_Age`.
    """
    data = np.asarray(X)
    return ((data[:, 0] <= YOUNG_MAX_AGE) & (data[:, 1] == 0)).astype(int).reshape(-1, 1)


def vintage_share(X) -> np.ndarray:
    """Qué fracción de su vida lleva el cliente con la aseguradora: `Vintage` (días) entre la edad en días.

    Recibe dos columnas, en este orden: `Vintage` y `Age`.
    """
    data = np.asarray(X, dtype=float)
    return (data[:, 0] / (data[:, 1] * 365.25)).reshape(-1, 1)


@dataclass(frozen=True)
class FeatureOptions:
    """Una opción por idea. Todo apagado = la referencia (las variables limpias de la etapa 3, más los canales raros agrupados)."""

    group_rare: bool = True                 # agrupar canales/regiones raros en "otros" (decisión 5 del EDA)
    min_count: int = 100                    # umbral de "raro"
    clip_premium: bool = False              # recortar la prima en el percentil 99 (decisión 4 del EDA)
    segment_flag: bool = False              # marca "sin seguro y con daño"
    age_splines: bool = False               # edad como curva suave en vez de una recta
    target_encode_codes: bool = False       # tasa histórica de región y canal en vez de variables 0/1 por categoría
    premium_vs_region: bool = False         # prima relativa a su región
    scale: bool = False                     # escalar numéricas (necesario para la regresión logística)
    drop: tuple = field(default_factory=tuple)   # columnas que se quitan (prueba de "¿esta variable sirve?")
    # --- segunda ronda: variables NUEVAS (se suman a las existentes) ---
    channel_region_volume: bool = False     # tamaño del canal y de la región (¿masivo o de nicho?)
    need_score: bool = False                # puntaje de necesidad de cobertura, de 0 a 4
    profile_12: bool = False                # las 12 combinaciones de seguro previo × daño × antigüedad del vehículo
    young_new_vehicle: bool = False         # 25 años o menos con vehículo de menos de 1 año
    premium_vs_age_band: bool = False       # prima relativa a la de su tramo de edad
    vintage_share: bool = False             # fracción de su vida como cliente

    def with_changes(self, **changes) -> "FeatureOptions":
        values = {**self.__dict__, **changes}
        return FeatureOptions(**values)

    def with_all_new(self) -> "FeatureOptions":
        """Activa las seis variables nuevas a la vez."""
        return self.with_changes(**{name: True for name in NEW_FEATURES})


def build_preprocessor(options: FeatureOptions = FeatureOptions()) -> ColumnTransformer:
    """Arma el `ColumnTransformer` según `options`. No se ajusta aquí: se ajusta dentro del `Pipeline`."""
    dropped = set(options.drop)

    def keep(columns):
        return [c for c in columns if c not in dropped]

    scaler = StandardScaler() if options.scale else "passthrough"
    parts = []

    numeric = keep(NUMERIC_COLS + ORDINAL_COLS)
    if options.age_splines and "Age" in numeric:
        numeric.remove("Age")
        parts.append(("age_curve", Pipeline([("spline", SplineTransformer(n_knots=6, degree=3, include_bias=False)),
                                             ("scale", scaler)]), ["Age"]))
    if numeric:
        parts.append(("numeric", scaler, numeric))

    binary = keep(BINARY_COLS)
    if binary:
        parts.append(("binary", "passthrough", binary))

    if PREMIUM_COL not in dropped:
        steps = ([("clip", PremiumClipper())] if options.clip_premium else []) + [("scale", scaler)]
        parts.append(("premium", Pipeline(steps), [PREMIUM_COL]))

    if CATEGORICAL_COL not in dropped:
        parts.append(("gender", OneHotEncoder(handle_unknown="ignore"), [CATEGORICAL_COL]))

    codes = keep(CODE_COLS)
    if codes:
        if options.target_encode_codes:
            parts.append(("codes_rate", TargetEncoder(target_type="binary", cv=StratifiedKFold(5, shuffle=True, random_state=42)), codes))
        else:
            steps = ([("group", RareCategoryGrouper(min_count=options.min_count))] if options.group_rare else []) + [
                ("onehot", OneHotEncoder(handle_unknown="ignore"))]
            parts.append(("codes", Pipeline(steps), codes))

    if options.segment_flag and not ({"Previously_Insured", "Vehicle_Damage"} & dropped):
        parts.append(("segment", FunctionTransformer(commercial_segment, validate=False, feature_names_out=_segment_names),
                      ["Previously_Insured", "Vehicle_Damage"]))

    if options.premium_vs_region and not ({PREMIUM_COL, "Region_Code"} & dropped):
        parts.append(("premium_vs_region", Pipeline([("ratio", PremiumVsRegion()), ("scale", scaler)]),
                      [PREMIUM_COL, "Region_Code"]))

    # --- segunda ronda: variables nuevas (solo se agregan si las columnas de las que dependen no se quitaron) ---
    def available(*columns):
        return not (set(columns) & dropped)

    if options.channel_region_volume and available("Policy_Sales_Channel", "Region_Code"):
        parts.append(("volume", Pipeline([("volume", CodeVolume()), ("scale", scaler)]), ["Policy_Sales_Channel", "Region_Code"]))

    if options.need_score and available("Previously_Insured", "Vehicle_Damage", "Vehicle_Age"):
        names = partial(_fixed_names, ["need_score"])
        parts.append(("need_score", Pipeline([("score", FunctionTransformer(need_score, validate=False, feature_names_out=names)),
                                              ("scale", scaler)]), ["Previously_Insured", "Vehicle_Damage", "Vehicle_Age"]))

    if options.profile_12 and available("Previously_Insured", "Vehicle_Damage", "Vehicle_Age"):
        names = partial(_fixed_names, ["profile"])
        parts.append(("profile_12", Pipeline([("code", FunctionTransformer(profile_12_code, validate=False, feature_names_out=names)),
                                              ("onehot", OneHotEncoder(categories=[list(range(12))], handle_unknown="ignore"))]),
                      ["Previously_Insured", "Vehicle_Damage", "Vehicle_Age"]))

    if options.young_new_vehicle and available("Age", "Vehicle_Age"):
        names = partial(_fixed_names, ["young_new_vehicle"])
        parts.append(("young_new_vehicle", FunctionTransformer(young_new_vehicle, validate=False, feature_names_out=names),
                      ["Age", "Vehicle_Age"]))

    if options.premium_vs_age_band and available(PREMIUM_COL, "Age"):
        parts.append(("premium_vs_age_band", Pipeline([("ratio", PremiumVsAgeBand()), ("scale", scaler)]), [PREMIUM_COL, "Age"]))

    if options.vintage_share and available("Vintage", "Age"):
        names = partial(_fixed_names, ["vintage_share"])
        parts.append(("vintage_share", Pipeline([("share", FunctionTransformer(vintage_share, validate=False, feature_names_out=names)),
                                                 ("scale", scaler)]), ["Vintage", "Age"]))

    return ColumnTransformer(parts, remainder="drop", verbose_feature_names_out=False)

"""Limpieza determinista de los datos de venta cruzada de seguros.

Cada función aplica **una** decisión del EDA (`reports/01_eda.md`) y devuelve una copia: nunca modifica el
DataFrame que recibe ni `data/raw/`.

Aquí solo va lo que **no depende de los datos de entrenamiento** (convertir textos fijos a números, avisar de un
valor repetido, validar rangos). Lo que sí depende de ellos (agrupar canales raros, recortar la prima, escalar,
imputar) va dentro del `Pipeline` de la etapa 4, ajustado solo con entrenamiento, para evitar fuga de información.
"""
from pathlib import Path

import pandas as pd

ID_COL = "id"
TARGET = "Response"

# Decisión 3 del EDA: textos con un significado fijo y conocido
YES_NO_MAP = {"No": 0, "Yes": 1}
VEHICLE_AGE_MAP = {"< 1 Year": 0, "1-2 Year": 1, "> 2 Years": 2}  # tiene orden natural

# Decisión 4 del EDA: la prima mínima aparece repetida en el 17 % de las filas (parece un piso impuesto)
MIN_PREMIUM = 2630.0

# Decisión 5 del EDA: son códigos, no cantidades (la región 28 no es "mayor" que la 3)
CODE_COLUMNS = ["Region_Code", "Policy_Sales_Channel"]

# El dataset no trae nombres, documentos ni teléfonos. Si algún día aparecieran, se listan aquí y se eliminan al cargar.
PERSONAL_COLUMNS: tuple = ()

EXPECTED_COLUMNS = [
    "id", "Gender", "Age", "Driving_License", "Region_Code", "Previously_Insured", "Vehicle_Age",
    "Vehicle_Damage", "Annual_Premium", "Policy_Sales_Channel", "Vintage",
]

# Rangos que solo un error de captura podría romper (en train no hay ninguno)
AGE_RANGE = (18, 100)


def drop_personal_columns(df: pd.DataFrame, columns=PERSONAL_COLUMNS) -> pd.DataFrame:
    """Elimina las columnas con datos personales que existan en `df`."""
    present = [c for c in columns if c in df.columns]
    return df.drop(columns=present)


def load_raw(path) -> pd.DataFrame:
    """Lee un CSV crudo y elimina los datos personales en el primer paso, antes de mostrar nada."""
    return drop_personal_columns(pd.read_csv(Path(path)))


def _map_strict(series: pd.Series, mapping: dict, name: str) -> pd.Series:
    """Convierte con `mapping` y falla (en vez de dejar vacíos en silencio) si aparece un valor desconocido."""
    unknown = sorted(set(series.dropna().unique()) - set(mapping))
    if unknown:
        raise ValueError(f"{name}: valores desconocidos {unknown}; se esperaban {sorted(mapping)}")
    if series.isna().any():
        raise ValueError(f"{name}: hay {int(series.isna().sum())} vacíos y no se esperaba ninguno")
    return series.map(mapping).astype("int8")


def encode_vehicle_damage(df: pd.DataFrame) -> pd.DataFrame:
    """`Vehicle_Damage`: Yes/No -> 1/0."""
    out = df.copy()
    out["Vehicle_Damage"] = _map_strict(out["Vehicle_Damage"], YES_NO_MAP, "Vehicle_Damage")
    return out


def encode_vehicle_age(df: pd.DataFrame) -> pd.DataFrame:
    """`Vehicle_Age`: '< 1 Year' -> 0, '1-2 Year' -> 1, '> 2 Years' -> 2 (conserva el orden)."""
    out = df.copy()
    out["Vehicle_Age"] = _map_strict(out["Vehicle_Age"], VEHICLE_AGE_MAP, "Vehicle_Age")
    return out


def cast_code_columns(df: pd.DataFrame, columns=CODE_COLUMNS) -> pd.DataFrame:
    """Los códigos de región y de canal llegan como decimales (28.0); se pasan a enteros (28).

    Falla si hay vacíos o decimales reales, porque un código no puede ser 28.5.
    """
    out = df.copy()
    for col in columns:
        values = out[col]
        if values.isna().any():
            raise ValueError(f"{col}: hay vacíos y un código no puede estar vacío")
        if not (values % 1 == 0).all():
            raise ValueError(f"{col}: hay valores no enteros y un código debe ser entero")
        out[col] = values.astype("int64")
    return out


def flag_minimum_premium(df: pd.DataFrame, minimum: float = MIN_PREMIUM) -> pd.DataFrame:
    """Agrega `Premium_is_minimum` = 1 si la prima vale exactamente el mínimo repetido (2.630).

    No se cambia la prima: se **marca**, y la etapa 4 decide qué hacer con los extremos.
    """
    out = df.copy()
    out["Premium_is_minimum"] = (out["Annual_Premium"] == minimum).astype("int8")
    return out


def find_impossible_values(df: pd.DataFrame) -> dict:
    """Cuenta valores imposibles por columna (no modifica nada). Un diccionario vacío significa 'ninguno'."""
    problems = {}
    age_bad = int((~df["Age"].between(*AGE_RANGE)).sum())
    if age_bad:
        problems["Age fuera de rango"] = age_bad
    for col in ["Driving_License", "Previously_Insured"]:
        bad = int((~df[col].isin([0, 1])).sum())
        if bad:
            problems[f"{col} distinto de 0/1"] = bad
    if (df["Annual_Premium"] <= 0).any():
        problems["Annual_Premium <= 0"] = int((df["Annual_Premium"] <= 0).sum())
    if (df["Vintage"] < 0).any():
        problems["Vintage negativo"] = int((df["Vintage"] < 0).sum())
    return problems


def clean(df: pd.DataFrame) -> pd.DataFrame:
    """Aplica todas las decisiones de limpieza, en orden, y devuelve una copia limpia.

    Sirve tanto para `train.csv` (con `Response`) como para `test.csv` (sin `Response`).
    """
    missing = [c for c in EXPECTED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"Faltan columnas esperadas: {missing}")
    out = drop_personal_columns(df)
    problems = find_impossible_values(out)
    if problems:
        raise ValueError(f"Valores imposibles encontrados: {problems}")
    out = encode_vehicle_damage(out)
    out = encode_vehicle_age(out)
    out = cast_code_columns(out)
    out = flag_minimum_premium(out)
    return out.reset_index(drop=True)

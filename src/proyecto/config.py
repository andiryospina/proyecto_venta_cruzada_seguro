"""Constantes del proyecto de venta cruzada de seguro de vehículo.

Cada valor sale de una decisión escrita en `especificaciones/03-preprocesamiento.md` o en `reports/01_eda.md`.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "data" / "raw"
RAW_FILENAME = "dataset.csv"
PROCESSED_DIR = ROOT / "data" / "processed"

ID_COL = "id"            # identifica al cliente; se conserva en los datos pero NO entra al modelo
TARGET = "Response"      # 1 = interesado en el seguro de vehículo

# Columnas que debe traer el archivo crudo (si falta o sobra alguna, la carga falla)
RAW_COLUMNS = [
    "id", "Gender", "Age", "Driving_License", "Region_Code", "Previously_Insured", "Vehicle_Age",
    "Vehicle_Damage", "Annual_Premium", "Policy_Sales_Channel", "Vintage", "Response",
]

# Decisión de negocio (2026-10-31): 2.630 es la prima mínima del producto (17 % de los clientes)
MIN_PREMIUM = 2630

# Columnas que se eliminan al limpiar (decisión del grupo, 2026-10-31):
#   Policy_Sales_Channel es el canal por el que se contactó al cliente; puede no conocerse antes de decidir
#   a quién llamar (sospecha de fuga, decisión 8 del EDA). Se elimina del todo en vez de medirla con y sin.
DROPPED_COLUMNS = ["Policy_Sales_Channel"]

# Códigos guardados como decimal en el CSV (28.0) que en realidad son etiquetas
CODE_COLUMNS = ["Region_Code"]

# Codificación fija de las categorías de texto (decisión 7 del EDA)
CATEGORY_MAPS = {
    "Gender": {"Female": 0, "Male": 1},
    "Vehicle_Damage": {"No": 0, "Yes": 1},
    "Vehicle_Age": {"< 1 Year": 0, "1-2 Year": 1, "> 2 Years": 2},
}

# Rango de lo POSIBLE en el mundo real (límites incluidos); fuera de él el valor se marca como vacío (hoy: 0 casos)
VALID_RANGE = {
    "Age": (18, 100),
    "Vintage": (0, None),
}
# Columnas que deben ser estrictamente positivas: una prima <= 0 es imposible; sin tope (la cola alta es real)
POSITIVE_COLUMNS = ["Annual_Premium"]
BINARY_COLUMNS = ["Driving_License", "Previously_Insured", "Response"]

# Partición (decisión 1 del EDA)
TEST_SIZE = 0.2
SEED = 42

# Atípicos y categorías raras (se aprenden SOLO de entrenamiento, dentro del Pipeline)
PREMIUM_CAP_QUANTILE = 0.999          # decisión de negocio: recortar al p99,9, no borrar filas
RARE_CATEGORY_MIN_FREQUENCY = 0.0033  # ≈ 1.000 de 304.710 filas de entrenamiento

# Variables que entran al modelo, por tipo (id y Response quedan fuera)
NUMERIC_FEATURES = ["Age", "Vintage"]
PREMIUM_FEATURE = "Annual_Premium"
FLAG_FEATURES = ["Gender", "Driving_License", "Previously_Insured", "Vehicle_Damage", "Vehicle_Age", "is_min_premium"]
CATEGORICAL_FEATURES = ["Region_Code"]
FEATURE_COLUMNS = NUMERIC_FEATURES + [PREMIUM_FEATURE] + FLAG_FEATURES + CATEGORICAL_FEATURES

# Variables nuevas (specs/002-variables; umbrales medidos en el EDA sobre la porción de exploración = entrenamiento)
YOUNG_AGE = 30          # de 20 a 30 años solo se interesa el 4,1 % (frente a 17,9 % del resto)
PEAK_AGE = 42           # la tasa de interés por edad tiene forma de campana con máximo entre 35 y 50 años
ENGINEERED_FLAGS = ["uninsured_with_damage", "damage_x_vehicle_age", "is_young_customer"]
ENGINEERED_NUMERIC = ["age_peak_distance", "premium_per_age"]
ENGINEERED_FEATURES = ENGINEERED_FLAGS + ENGINEERED_NUMERIC

# Costo de equivocarse (reports/00_caso.md). Filas = real (0 no interesado, 1 interesado);
# columnas = decisión (0 no llamar, 1 llamar). Perder un interesado cuesta 5 veces una llamada sin éxito (supuesto del grupo).
COST_MATRIX = [[0, 1],
               [5, 0]]

# Validación cruzada: 5 pliegues estratificados (cada cliente aparece una sola vez: no hace falta agrupar)
CV_FOLDS = 5

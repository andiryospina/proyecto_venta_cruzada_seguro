"""Regenera reports/07_shap.png con nombres de variable legibles, SIN abrir la prueba cerrada.

El cuaderno 07 dibujó la imagen con nombres genéricos (x7, x11...). Aquí se vuelve a calcular SHAP con el modelo final guardado
(models/final_pipeline.joblib) y una muestra de 5.000 clientes del ENTRENAMIENTO (semilla 42), y se nombran las columnas.
La prueba no se vuelve a leer. Uso, desde la raíz del repositorio:  python scripts/regenerar_shap.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import joblib
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import shap

TARGET, ID_COL = "Response", "id"
NOMBRES = {
    "Previously_Insured": "Ya tiene seguro de vehículo", "Vehicle_Damage": "Vehículo con daños",
    "uninsured_with_damage": "Sin seguro y con daño", "age_peak_distance": "Distancia a la edad de mayor interés",
    "damage_x_vehicle_age": "Daño × antigüedad del vehículo", "Age": "Edad", "Vehicle_Age": "Antigüedad del vehículo",
    "Annual_Premium": "Prima anual", "premium_per_age": "Prima por edad", "is_young_customer": "Cliente joven",
    "Vintage": "Días como cliente", "Gender": "Género", "Driving_License": "Licencia de conducir", "is_min_premium": "Prima mínima",
}


def legible(columna: str) -> str:
    """'flags__Previously_Insured' -> 'Ya tiene seguro de vehículo'; 'cat__Region_Code_28' -> 'Región 28'."""
    nombre = columna.split("__", 1)[-1]
    if nombre.startswith("Region_Code_"):
        return "Región " + nombre.removeprefix("Region_Code_")
    if nombre.startswith("Gender_"):
        return "Género: " + {"Male": "hombre", "Female": "mujer", "0": "mujer", "1": "hombre"}.get(nombre.removeprefix("Gender_"), nombre.removeprefix("Gender_"))
    return NOMBRES.get(nombre, nombre)


def main() -> None:
    modelo = joblib.load(ROOT / "models" / "final_pipeline.joblib")
    train = pd.read_parquet(ROOT / "data" / "processed" / "train.parquet")
    X = train.drop(columns=[c for c in (TARGET, ID_COL) if c in train.columns])
    muestra = X.sample(n=min(5000, len(X)), random_state=42)

    lgbm, transformador = modelo.named_steps["model"], modelo[:-1]
    Z = transformador.transform(muestra)
    columnas = [legible(c) for c in modelo.named_steps["prep"].get_feature_names_out()]   # los nombres viven en el ColumnTransformer 'prep'
    Z = pd.DataFrame(np.asarray(Z, dtype=float), columns=columnas)

    valores = shap.TreeExplainer(lgbm).shap_values(Z)
    valores = valores[1] if isinstance(valores, list) else valores
    importancia = pd.Series(np.abs(valores).mean(axis=0), index=columnas).sort_values(ascending=False)

    shap.summary_plot(valores, Z, show=False, max_display=15)
    plt.title("SHAP · muestra de 5.000 clientes de entrenamiento", fontsize=10, loc="left")
    plt.tight_layout()
    plt.savefig(ROOT / "reports" / "07_shap.png", dpi=120, bbox_inches="tight")
    print("guardado reports/07_shap.png")
    print(importancia.head(10).round(3).to_string())


if __name__ == "__main__":
    main()

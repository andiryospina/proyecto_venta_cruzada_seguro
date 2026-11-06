# Contrato: `src/proyecto/inference/serving.py`

Traduce lo que escribe una persona a las columnas limpias del modelo final. Mismo nombre y forma que el de `main` (la app y el
notebook 09 no cambian su manera de usarlo); cambian las columnas.

| Elemento | Contrato |
|---|---|
| `RAW_COLUMNS` | `["Age", "Annual_Premium", "Region_Code", "Vintage", "Gender", "Driving_License", "Previously_Insured", "Vehicle_Age", "Vehicle_Damage"]` |
| `to_raw(clean) -> DataFrame` | De columnas limpias (como `train.parquet`) a las de persona (`"Male"`, `"Yes"`, `"< 1 Year"`…). Solo `RAW_COLUMNS`, en ese orden |
| `build_defaults(raw_train) -> dict` | Valor para cada "no sé": mediana en `Age`, `Annual_Premium`, `Region_Code`, `Vintage`; valor más frecuente en el resto. Solo con **entrenamiento** |
| `ServingModel(pipeline, defaults)` | `predict_proba(raw_df)`: rellena vacíos con `defaults`, valida categorías, codifica con `CATEGORY_MAPS`, calcula `is_min_premium`, llama a `pipeline.predict_proba`. `predict(raw_df)`: clase más probable. `classes_`: las del `Pipeline` |
| Error | Categoría desconocida (p. ej. `Vehicle_Damage="Maybe"`) → `InputValidationError` con la columna y los valores permitidos |

## Pruebas (`tests/test_serving.py`, con un `Pipeline` de juguete, sin el modelo real)

1. **Ida y vuelta:** `ServingModel(p, d).predict_proba(to_raw(X)) == p.predict_proba(X)` (diferencia ≤ 1e-9).
2. **`is_min_premium`:** prima 2.630 → 1; otra → 0.
3. **"No sé":** un vacío se rellena con el valor de `defaults` (misma predicción que escribir ese valor).
4. **Categoría desconocida:** lanza `InputValidationError`.
5. **`build_defaults`:** mediana y moda correctas en una tabla pequeña conocida.

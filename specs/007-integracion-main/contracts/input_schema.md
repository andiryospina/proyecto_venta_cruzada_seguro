# Contrato: `models/input_schema.json` y `models/model.joblib`

Los genera el notebook 09 con `build_schema` (sin cambios, de `main`) a partir de `to_raw(train)`. **Nunca** con la prueba.

| Clave | Valor |
|---|---|
| `numeric` | `Age`, `Annual_Premium`, `Region_Code`, `Vintage` |
| `categorical` | `Gender`, `Driving_License`, `Previously_Insured`, `Vehicle_Age`, `Vehicle_Damage` |
| `class_names` | `["no interesado", "interesado"]`, en el orden de `predict_proba` (0, 1) *(implementado así en T022, como en `main`: más legible en la app)* |
| `cost_matrix` | `COST_MATRIX` de `config.py` (`[[0, 1], [5, 0]]`) → decisión de menor costo = umbral 1/6 |
| `valid_range` | `Age` 18–100 (`VALID_RANGE`), `Annual_Premium` 1–10.000.000, `Vintage` 0–36.500 (100 años en días, límite práctico), `Region_Code` 0–52 (códigos vistos) |
| `decision_labels` | `{"interesado": "LLAMAR", "no interesado": "NO LLAMAR"}` |
| `review_threshold` | `0.0`, como en `main`: se marca "revisar" solo cuando la decisión de costo no coincide con la clase más probable |
| `labels` | Etiquetas en español para el formulario (tabla 3 de `data-model.md`) |
| `app_title`, `responsible_use` | Título de la app y aviso de uso responsable (incluye: apoya, no decide; no usar `Gender` para discriminar; ver `models/ficha_modelo.md`) |

`models/model.joblib` = `ServingModel(final_pipeline, build_defaults(to_raw(train)))`. Debe dar las mismas probabilidades que
`final_pipeline.joblib` sobre 200 clientes de entrenamiento (diferencia máxima ≤ 1e-9).

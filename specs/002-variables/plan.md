# Plan: Variables nuevas (`002-variables`)

**Fecha:** 2026-10-31 · **Spec:** `specs/002-variables/spec.md` · **Estado:** aprobado por el grupo (2026-10-31)

## Diseño

```text
src/proyecto/config.py                 # + YOUNG_AGE=30, PEAK_AGE=42, ENGINEERED_FLAGS, ENGINEERED_NUMERIC
src/proyecto/features/engineering.py   # NUEVO: add_features, feature_columns, _ratio (como el ejemplo)
src/proyecto/features/preprocessing.py # build_preprocessor(use_engineered=False, use_gender=True) usa feature_columns
tests/test_features.py                 # NUEVO
```

| Pieza | Qué hace |
|---|---|
| `_ratio(num, den)` | División segura: si el denominador es ≤ 0 o vacío, devuelve vacío (copiado del ejemplo) |
| `add_features(df)` | Agrega las 5 variables. Funciona con la salida de `clean()` (`Int64` con `pd.NA`) |
| `feature_columns(use_engineered, use_gender)` | Devuelve un diccionario por tipo: `numeric`, `premium`, `flags` y `categorical` |
| `build_preprocessor(...)` | Las variables nuevas numéricas (`age_peak_distance`, `premium_per_age`) se imputan con la mediana y se escalan. Las marcas (`uninsured_with_damage`, `is_young_customer`, `damage_x_vehicle_age`) pasan como números, igual que las otras marcas |

`FEATURE_COLUMNS` de `config.py` se mantiene como el conjunto por defecto (sin variables nuevas, con `Gender`), así que el notebook 03 y las pruebas actuales no cambian.

## Revisión contra la constitución

- **III (la prueba se abre una vez):** las variables se calculan fila por fila. Los umbrales salen del EDA hecho sobre entrenamiento.
- **IV (decisión con motivo):** cada variable lleva su cifra en la spec y en `reports/04_features.md` (etapa 04).
- **VI (código entendible):** funciones cortas, explicadas en español.

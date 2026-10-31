# Plan: Preprocesamiento (`001-preprocesamiento`)

**Fecha:** 2026-10-31 · **Spec:** `specs/001-preprocesamiento/spec.md` · **Contrato:** `especificaciones/03-preprocesamiento.md`
**Estado:** aprobado por el grupo (2026-10-31)

## Resumen

Dos capas, para respetar la regla "nada aprende antes de partir":

1. **Antes de partir (sin aprendizaje)**: `clean(df)` en `src/proyecto/data/cleaning.py`. Reglas fijas, iguales para cualquier fila.
2. **Después de partir (aprende de entrenamiento)**: `build_preprocessor()` en `src/proyecto/features/`, un `ColumnTransformer` que se
   ajusta dentro del `Pipeline` del modelo en la etapa 04. Aquí viven el recorte de atípicos, `log1p`, la agrupación de categorías raras,
   la imputación de seguridad y el escalado.

## Contexto técnico

Python 3.12 · pandas 3.0.6 · scikit-learn 1.9.1 · pyarrow 25.0.1 (parquet) · pytest 9.1.1. Entorno `.venv`.

## Revisión contra la constitución

| Principio | Cómo se cumple |
|---|---|
| I. Datos originales intactos | `load_raw` solo lee; las salidas van a `data/processed/` |
| II. Partir por la unidad de análisis | 1 fila = 1 cliente (`id` único); partición por fila estratificada; prueba de `id` disjuntos |
| III. La prueba se abre una vez | El tope p99,9, las categorías frecuentes y el escalado se ajustan solo con entrenamiento (`Pipeline`); los repetidos se quitan solo en entrenamiento |
| IV. Decisión con motivo | Cada regla enlaza a su fila del EDA en `especificaciones/03-preprocesamiento.md` |
| V. Nada sensible | No hay datos personales; `id` fuera de `FEATURE_COLUMNS` |
| VI. Código entendible | Funciones cortas con docstring en español; nombres en inglés |
| VII. No inventar | Las cifras de aceptación salen del EDA ejecutado |

## Diseño de archivos

```text
src/proyecto/config.py                 # constantes: rutas, TARGET, ID_COL, MIN_PREMIUM=2630, TEST_SIZE=0.2, SEED=42, FEATURE_COLUMNS
src/proyecto/data/cleaning.py          # load_raw, cast_codes_to_int, encode_categoricals, add_min_premium_flag, flag_impossible_values, clean
src/proyecto/data/split.py             # split_train_test, drop_duplicate_rows
src/proyecto/features/transformers.py  # PremiumTransformer (recorte al cuantil 0,999 aprendido + log1p)
src/proyecto/features/preprocessing.py # build_preprocessor (ColumnTransformer)
tests/test_cleaning.py · tests/test_split.py · tests/test_preprocessing.py
notebooks/03_preprocesamiento.ipynb    # orquesta: carga → clean → comprobaciones → partición → guarda parquet
```

## Detalle de `build_preprocessor()`

| Columnas | Pasos |
|---|---|
| `Annual_Premium` | `SimpleImputer(median)` → `PremiumTransformer(quantile=0.999)` → `StandardScaler` |
| `Age`, `Vintage` | `SimpleImputer(median)` → `StandardScaler` |
| `Gender`, `Driving_License`, `Previously_Insured`, `Vehicle_Damage`, `is_min_premium`, `Vehicle_Age` | `SimpleImputer(most_frequent)` (pasan como números 0/1/2) |
| `Region_Code` | `SimpleImputer(most_frequent)` → `OneHotEncoder(min_frequency=0.0033, handle_unknown="infrequent_if_exist")` |
| `Policy_Sales_Channel` | **Eliminada** en `clean()` (posible fuga; cambio aprobado por el grupo el 2026-10-31) |

Se excluyen: `id` y `Response`.

## Riesgos

- `dataset.csv` sigue en la raíz: `load_raw` busca primero en `data/raw/` y luego en la raíz. Recomendado moverlo.
- Los árboles no necesitan `log1p` ni escalado; no les hace daño y mantiene un solo preprocesador para el torneo.
- `pd.NA` en enteros `Int64`: se convierte a `float` antes del `Pipeline` para que `SimpleImputer` lo reconozca.

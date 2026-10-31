# Especificación · Etapa 3 · Preprocesamiento (limpieza y partición)

> Se llena **antes** de pedirle código a Claude, a partir de la tabla de decisiones de
> `especificaciones/02-eda.md`. Claude la lee y la implementa; ustedes revisan que el código haga
> **exactamente** esto (`material-del-curso/kit/checklist-revision-ia.md`).
> Guía: `material-del-curso/kit/guia-eda-y-preprocesamiento.md`, sección 4 · Ejemplo: `material-del-curso/ejemplo-creditsight/src/creditsight/data/`.

**Grupo:** _______________   **Fecha:** 2026-10-31   **Estado:** ☒ borrador  ☐ cerrada

> Redactada por Claude a partir de `reports/01_eda.md`, del análisis de atípicos (sección 3b) y de las respuestas de negocio del grupo
> del 2026-10-31 (prima alta, prima mínima, clientes sin licencia). El grupo la revisa y la marca como cerrada.

## 1. Unidad de análisis y partición

- **Una fila es:** un cliente actual del seguro de salud, con su vehículo y su respuesta a la oferta de seguro de vehículo.
- **Entidad que se repite (columna):** `id`  ☒ no se repite → partir por fila es válido porque: los 381.109 `id` son distintos (1 fila por cliente).
- **Se parte por:** ☐ grupo ☒ fila, **estratificada por `Response`** (12,26 % positivos en cada parte)
- **Proporción de prueba:** 20 %   **Semilla:** 42
- **¿Hay orden temporal que respetar?** ☒ no ☐ sí (no hay columnas de fecha)
- **Dónde se guarda la prueba:** `data/processed/test.parquet` (cerrada: **no se mira** hasta la etapa 7)

## 2. Datos personales

| Columna | Qué es | Se elimina en | Prueba que lo verifica |
|---|---|---|---|
| — | No hay nombres, documentos, teléfonos ni correos | — | `test_no_personal_columns` (verifica que el resultado tenga solo las 12 columnas esperadas + `is_min_premium`) |
| `id` | Consecutivo del cliente | **No** se elimina de los datos: se conserva como identificador para verificar la partición y rastrear predicciones. **Se excluye de las variables del modelo** (`FEATURE_COLUMNS`) | `test_feature_columns_exclude_id` |
| `Gender`, `Age` | Atributos sensibles | Se conservan; en la etapa 4 se mide el modelo con y sin `Gender` (decisión 10 del EDA) | — |

## 3. Reglas de limpieza

Reglas **sin aprendizaje** (no dependen de los datos): se aplican antes de partir, en `clean()`.

| # (de la tabla del EDA) | Columna(s) | Problema | Regla exacta (con el umbral o valor) | Función en `src/proyecto/data/cleaning.py` | Prueba en `tests/test_cleaning.py` |
|---|---|---|---|---|---|
| 8 | `Policy_Sales_Channel` | Canal de contacto: puede no conocerse antes de decidir (posible fuga) | **Eliminar la columna** al limpiar (decisión del grupo, 2026-10-31) | `drop_excluded_columns` | `test_drop_excluded_columns`, `test_clean_removes_channel`, `test_preprocessor_does_not_use_channel` |
| 6 | `Region_Code` | Código guardado como decimal (`28.0`) | Convertir a entero (`Int64`); si un valor no es entero, error | `cast_codes_to_int` | `test_cast_codes_to_int`, `test_cast_codes_rejects_fraction` |
| 7 | `Gender`, `Vehicle_Damage`, `Vehicle_Age` | Categorías en texto | `Gender`: Male=1, Female=0. `Vehicle_Damage`: Yes=1, No=0. `Vehicle_Age`: `< 1 Year`=0, `1-2 Year`=1, `> 2 Years`=2. Valor desconocido → error | `encode_categoricals` | `test_encode_categoricals`, `test_encode_rejects_unknown` |
| 4 | `Annual_Premium` | 2.630 en 17,02 % = **prima mínima del producto** (decisión de negocio) | Conservar el valor y crear `is_min_premium` = 1 si `Annual_Premium == 2630`, si no 0 | `add_min_premium_flag` | `test_add_min_premium_flag` |
| — (rangos) | `Age`, `Annual_Premium`, `Vintage`, `Driving_License`, `Previously_Insured`, `Response` | Valores imposibles (hoy 0 casos; protege la app y datos nuevos) | Marcar como vacío: `Age` fuera de [18, 100]; `Annual_Premium` ≤ 0; `Vintage` < 0; binarias fuera de {0, 1} | `flag_impossible_values` | `test_flag_impossible_values` |
| 3 | Todas menos `id` | 269 filas repetidas sin contar `id` (0,07 %) | Quitar repetidas **solo en entrenamiento, después de partir**, conservando la primera | `drop_duplicate_rows` (en `split.py`) | `test_drop_duplicate_rows`, `test_test_set_not_deduplicated` |
| — | — | Orquestación | `clean(df)` aplica, en orden: `drop_excluded_columns` → `cast_codes_to_int` → `encode_categoricals` → `add_min_premium_flag` → `flag_impossible_values`. No borra filas | `clean` | `test_clean_keeps_rows` |

Reglas **que aprenden de entrenamiento** (van dentro del `Pipeline` en `src/proyecto/features/`; se ajustan solo con entrenamiento):

| # | Columna(s) | Problema | Regla exacta | Clase / función | Prueba |
|---|---|---|---|---|---|
| 5 | `Annual_Premium` | Cola alta real: 2,72 % sobre IQR, máx. 540.165; la tasa de interés sube con la prima → **no son errores** (decisión de negocio: no borrar) | Recortar por arriba al **percentil 99,9 aprendido en entrenamiento** (≈ 115.269 en exploración) y luego `log1p`. No se borran filas | `PremiumTransformer` (`features/transformers.py`) | `test_premium_transformer_caps_at_train_quantile`, `test_premium_transformer_uses_train_only` |
| 6 | `Region_Code` | 5 regiones con < 1.000 filas (0,75 %) | One-hot con `min_frequency=0.0033` (≈ 1.000 de 304.238 filas) y `handle_unknown="infrequent_if_exist"`: las categorías raras o nuevas van a una sola columna "otros" | `build_preprocessor` (`features/preprocessing.py`) | `test_preprocessor_groups_rare_categories`, `test_preprocessor_handles_unknown_category` |
| — | `Age`, `Vintage` | **Sin atípicos** (0 filas fuera de IQR × 1,5 y de \|z\| > 3) | Se usan tal cual (escalado estándar dentro del `Pipeline`) | `build_preprocessor` | `test_preprocessor_output_has_no_nans` |
| — | `Driving_License` | 654 sin licencia (0,21 %), mediana 67 años | **Se conservan** (decisión de negocio: pueden asegurar un vehículo que conduce otra persona) | — | — |

### 3b. Revisión de atípicos (porción de exploración, 304.887 filas)

| Variable | p1 – p99 | Máximo | Fuera de IQR × 1,5 | \|z\| > 3 | Lectura | Decisión |
|---|---|---|---|---|---|---|
| `Age` | 20 – 77 | 85 | 0 | 0 | Rango adulto normal | Ninguna |
| `Vintage` | 12 – 297 | 299 | 0 | 0 | Rango acotado (10–299 días) | Ninguna |
| `Annual_Premium` | 2.630 – 73.132 | 540.165 | 8.280 (2,72 %), todos por arriba | 1.683 (0,55 %) | 250 valores distintos sobre el p99,9; tasa de interés 15,0 % (62–100 mil), 15,3 % (100–200 mil), 16,9 % (> 200 mil) frente a 12,3 % global: **clientes reales** | Recortar al p99,9 de entrenamiento + `log1p` |
| `Annual_Premium` = 2.630 | — | — | — | — | 17 % de clientes; siguiente valor 6.098; edad mediana 40 vs 35 | Prima mínima: conservar + `is_min_premium` |

## 4. Vacíos

| Columna | Qué significa el vacío | Tratamiento hoy | Tratamiento en la etapa 4 (dentro del `Pipeline`) |
|---|---|---|---|
| Todas | ☒ no aplica: el dataset no tiene vacíos | — | — |
| `Age`, `Annual_Premium`, `Vintage`, binarias | ☒ imposible (solo si llega un valor fuera de rango; hoy 0 casos) | ☒ dejar vacío | Imputar con la mediana de entrenamiento (`SimpleImputer`), para que el modelo no falle con datos nuevos |

## 5. Entradas y salidas

| | Ruta |
|---|---|
| Entrada | `data/raw/dataset.csv` si existe; si no, `dataset.csv` en la raíz (temporal, hasta moverlo). Nunca se modifica |
| Salida: entrenamiento | `data/processed/train.parquet` |
| Salida: prueba (cerrada) | `data/processed/test.parquet` |
| Código de limpieza | `src/proyecto/data/cleaning.py` |
| Código de partición | `src/proyecto/data/split.py` |
| Código del `Pipeline` | `src/proyecto/features/transformers.py`, `src/proyecto/features/preprocessing.py` |
| Notebook que orquesta | `notebooks/03_preprocesamiento.ipynb` (solo llama a las funciones) |

## 6. Pruebas que deben existir

- ☒ **Partición:** ningún `id` aparece en las dos particiones, no se pierde ninguna fila y la prueba lleva exactamente el 20 % de los interesados (`tests/test_split.py`).
- ☒ **La prueba de partición falla si se parte por fila:** no aplica — cada cliente tiene una sola fila, así que por fila y por grupo dan lo mismo. En su lugar, `test_split_is_stratified` falla si se quita la estratificación.
- ☒ **Una prueba por regla de limpieza** de la sección 3, con un caso normal y un caso sucio hechos a mano.
- ☒ **Datos personales:** el resultado de cargar no contiene columnas fuera de las esperadas.
- ☒ `pytest tests` en verde desde la raíz del repo (51 pruebas).

## 7. Criterios de cierre (H1)

- ☒ La limpieza corre **de principio a fin desde cero** (`data/processed/` borrada y regenerada con el notebook 03), sin pasos manuales.
- ☒ Unidad de análisis y forma de partir **escritas** (sección 1) y documentadas en `reports/01_eda.md`.
- ☒ `pytest tests` en verde.
- ☒ Conjunto de prueba guardado y sin mirar.
- ☐ `data/raw/` intacta y `.env` fuera de Git (`git status`).
- ☐ Todo subido a GitHub.
- ☐ Revisaron el código de Claude con `checklist-revision-ia.md` y cada integrante puede explicar una función.
- ☐ **Hallazgo que no esperaban** (para la puesta en común): la prima alta no es ruido: los clientes con primas más altas se interesan más.

# Especificación · Etapa 3 · Preprocesamiento (limpieza y partición)

> **BORRADOR por aprobar.** Salió de las decisiones del EDA (`reports/01_eda.md`), que el grupo aún debe aprobar. El código ya está escrito sobre este borrador
> (`src/proyecto/data/cleaning.py`, `split.py` y sus pruebas en `tests/`) **sin pasar por el plan y las tareas de Spec Kit**, por pedido expreso del grupo.
> Si algo de esta especificación cambia, hay que cambiar también el código y las pruebas.
> Guía: `material-del-curso/kit/guia-eda-y-preprocesamiento.md`, sección 4 · Ejemplo: `material-del-curso/ejemplo-creditsight/src/creditsight/data/`.

**Grupo:** _______________   **Fecha:** _______________   **Estado:** ☒ borrador  ☐ cerrada

## 1. Unidad de análisis y partición

- **Una fila es:** un cliente con seguro de salud y su respuesta a la oferta de seguro de vehículo.
- **Entidad que se repite (columna):** `id`  ☒ no se repite → partir por fila es válido porque: `id` es único en las 381.109 filas (verificado en el EDA y en cada partición con `assert_unique_ids`).
- **Se parte por:** ☐ grupo (`GroupShuffleSplit` / `StratifiedGroupKFold`) ☒ fila, **estratificada por `Response`**
- **Proporción de prueba:** 20 %   **Semilla:** 42
- **¿Hay orden temporal que respetar?** ☒ no → no hay columnas de fecha.
- **Dónde se guarda la prueba:** `data/processed/` (cerrada: **no se mira** hasta la etapa 7)
- **Validación:** pliegues estratificados (`StratifiedKFold`, 5, semilla 42) **solo sobre el entrenamiento**.
- **`test.csv` original:** no tiene `Response`; solo sirve para predecir. No es la prueba cerrada.

## 2. Datos personales

| Columna | Qué es | Se elimina en | Prueba que lo verifica |
|---|---|---|---|
| _(ninguna)_ | El dataset no trae nombres, documentos ni teléfonos; `id` es un identificador anónimo | `load_raw()` (lista `PERSONAL_COLUMNS`, hoy vacía) | `test_no_personal_columns` |

## 3. Reglas de limpieza

Se marca lo imposible; no se borran filas sin criterio. Hoy no se elimina ninguna fila.

| # (de la tabla del EDA) | Columna(s) | Problema | Regla exacta | Función en `cleaning.py` | Prueba en `test_cleaning.py` |
|---|---|---|---|---|---|
| 3 | `Vehicle_Damage` | Texto Yes/No | `Yes`→1, `No`→0; falla si aparece otro valor o un vacío | `encode_vehicle_damage` | `test_vehicle_damage_*` (3) |
| 3 | `Vehicle_Age` | Texto con orden | `< 1 Year`→0, `1-2 Year`→1, `> 2 Years`→2; falla con otro valor | `encode_vehicle_age` | `test_vehicle_age_*` (2) |
| 4 | `Annual_Premium` | 17 % vale exactamente 2.630 (el mínimo) | Agregar `Premium_is_minimum` = 1 si vale 2.630. **No se cambia la prima**; los extremos se tratan en la etapa 4 | `flag_minimum_premium` | `test_minimum_premium_is_flagged_not_changed` |
| 5 | `Region_Code`, `Policy_Sales_Channel` | Códigos guardados como decimales (28.0) | Pasar a entero; falla si hay vacíos o decimales reales. Se tratan como **categorías** en la etapa 4 | `cast_code_columns` | `test_code_columns_*` (2) |
| — | `Age`, `Driving_License`, `Previously_Insured`, `Annual_Premium`, `Vintage` | Valores imposibles | Edad entre 18 y 100; licencia y seguro previo solo 0/1; prima > 0; `Vintage` ≥ 0. Si hay alguno, **falla** (hoy hay 0) | `find_impossible_values` | `test_impossible_values_are_counted` |

Las decisiones 1, 2, 6 y 7 del EDA no son limpieza: 1 es la partición (sección 1), 2 es solo una comprobación, 6 y 7 son de modelado (etapa 4).

## 4. Vacíos

| Columna | Qué significa el vacío | Tratamiento hoy | Tratamiento en la etapa 4 (dentro del `Pipeline`) |
|---|---|---|---|
| _(todas)_ | ☒ no aplica: **0 vacíos** en `train.csv` | Si aparece alguno, la limpieza **falla** a propósito para enterarnos | Imputador de respaldo dentro del `Pipeline`, por si `test.csv` o datos nuevos traen vacíos |

> Imputar con medias o medianas **no se hace aquí**: depende del entrenamiento y va dentro del `Pipeline`.

## 4.1 Lo que NO se hace en esta etapa (y por qué)

Estas decisiones del EDA **dependen de los datos de entrenamiento**; si se calcularan con todo el dataset, la prueba "se colaría" en el ajuste (fuga de información). Van dentro del `Pipeline` de la etapa 4, ajustadas solo con entrenamiento:

| Decisión | Por qué espera a la etapa 4 |
|---|---|
| Agrupar canales de venta raros en "otros" (umbral de 100 filas) | Qué canales son raros se decide **con el entrenamiento**; `test` también trae canales que no existen en train (141, 142) |
| Recortar o transformar los extremos de `Annual_Premium` | El corte (por ejemplo el percentil 99) se calcula con el entrenamiento |
| Codificar `Gender`, región y canal (one-hot u otra) | El encoder aprende las categorías del entrenamiento |
| Escalar variables numéricas | Depende de la media y la desviación del entrenamiento |
| Tramos o no linealidad de `Age` | Es una decisión de modelo |
| Con o sin `Vintage` | Se mide con validación (etapa 4) |

## 5. Entradas y salidas

| | Ruta |
|---|---|
| Entrada | `data/raw/train.csv` (nunca se modifica; el notebook comprueba su huella SHA-256 antes y después) |
| Salida: entrenamiento | `data/processed/train.parquet` |
| Salida: prueba (cerrada) | `data/processed/holdout.parquet` |
| Código de limpieza | `src/proyecto/data/cleaning.py` |
| Código de partición | `src/proyecto/data/split.py` |
| Notebook que orquesta | `notebooks/03_preprocesamiento.ipynb` (solo llama a las funciones) |

## 6. Pruebas que deben existir

- ☒ **Partición:** ninguna entidad aparece en dos particiones y no se pierde ninguna fila (`tests/test_split.py`).
- ☒ **La prueba de partición falla** si una entidad se repite o si un `id` queda en dos lados (`test_guard_fails_when_an_id_is_in_both_partitions`, `test_split_refuses_data_where_an_entity_repeats`). _Verificado con casos hechos a mano; el "cambio temporal a partición por fila" no aplica porque aquí la partición ya es por fila._
- ☒ **Una prueba por regla de limpieza** de la sección 3, con un caso normal y un caso sucio hechos a mano.
- ☒ **Datos personales:** `test_no_personal_columns`.
- ☒ `pytest` en verde desde la raíz del repo (se añadió `pytest.ini` para que solo recoja `tests/`).

## 7. Criterios de cierre (H1)

- ☐ La limpieza corre **de principio a fin desde cero** (`data/processed/` borrada y regenerada con el notebook 03), sin pasos manuales.
- ☐ Unidad de análisis y forma de partir **revisadas por el grupo** y documentadas en `reports/01_eda.md`.
- ☐ `pytest` en verde.
- ☐ Conjunto de prueba guardado y sin mirar.
- ☐ `data/raw/` intacta y `.env` fuera de Git (`git status`).
- ☐ Todo subido a GitHub.
- ☐ Revisaron el código de Claude con `checklist-revision-ia.md` y cada integrante puede explicar una función.
- ☐ **Hallazgo que no esperaban** (para la puesta en común): _______________

# Tareas: Preprocesamiento (`001-preprocesamiento`)

**Entrada:** `specs/001-preprocesamiento/plan.md` · **Estado:** aprobado por el grupo (2026-10-31)
Una tarea se marca `[x]` solo cuando su prueba pasa (`pytest tests`).

## Fase 1 · Base

- [x] T001 Crear `src/proyecto/config.py` con rutas, `TARGET`, `ID_COL`, `MIN_PREMIUM`, `TEST_SIZE`, `SEED`, `FEATURE_COLUMNS`

## Fase 2 · US1 Limpieza reproducible (P1)

- [x] T002 [P] [US1] Pruebas en `tests/test_cleaning.py` con datos hechos a mano (caso normal y sucio por regla) — deben fallar primero
- [x] T003 [US1] `load_raw` en `src/proyecto/data/cleaning.py` (busca en `data/raw/`, si no en la raíz; valida columnas esperadas)
- [x] T004 [US1] `cast_codes_to_int` (error si hay decimales reales)
- [x] T005 [US1] `encode_categoricals` (mapas fijos; error con valores desconocidos)
- [x] T006 [US1] `add_min_premium_flag` (`is_min_premium` = prima == 2.630)
- [x] T007 [US1] `flag_impossible_values` (fuera de rango → vacío)
- [x] T008 [US1] `clean` (orquesta T004–T007 sin borrar filas)

## Fase 3 · US2 Partición honesta (P1)

- [x] T009 [P] [US2] Pruebas en `tests/test_split.py`: `id` disjuntos, sin pérdida de filas, estratificación (± 0,1 pp), reproducible con semilla, prueba sin deduplicar
- [x] T010 [US2] `split_train_test` en `src/proyecto/data/split.py` (80/20, estratificado, semilla 42)
- [x] T011 [US2] `drop_duplicate_rows` (sin contar `id`, conserva la primera; solo se aplica a entrenamiento)

## Fase 4 · US3 Atípicos y categorías raras en el `Pipeline` (P2)

- [x] T012 [P] [US3] Pruebas en `tests/test_preprocessing.py`: tope aprendido solo de entrenamiento, `log1p`, categoría nueva no rompe, salida sin vacíos, `id` y `Response` excluidos
- [x] T013 [US3] `PremiumTransformer` en `src/proyecto/features/transformers.py`
- [x] T014 [US3] `build_preprocessor` en `src/proyecto/features/preprocessing.py`

## Fase 5 · Orquestación y cierre

- [x] T015 Llenar `notebooks/03_preprocesamiento.ipynb`: carga → `clean` → comprobaciones (afirmaciones) → partición → deduplicar entrenamiento → guardar `data/processed/*.parquet` → ajustar el preprocesador **solo con entrenamiento** y mostrar el tope aprendido
- [x] T016 Ejecutar el notebook desde cero (borrar `data/processed/*.parquet`) y `pytest tests` en verde
- [x] T017 Revisar con los subagentes `auditor-de-fuga` y `revisor-de-codigo-ia`; corregir lo que encuentren
- [x] T018 Actualizar `reports/01_eda.md` (sección de atípicos) y la sección 7 de `especificacion-proyecto.md`

## Dependencias

T001 → (T002–T008) y (T009–T011) → (T012–T014) → T015 → T016 → T017 → T018. Las pruebas [P] se escriben antes que su código.

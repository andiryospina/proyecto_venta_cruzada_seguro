# Tareas: Registro del modelo final (`006-registro-modelo`)

**Entrada:** `specs/006-registro-modelo/plan.md` · **Estado:** aprobado por el grupo (2026-11-05)
Una tarea se marca `[x]` solo cuando su prueba pasa (`pytest tests`). **No se lee `test.parquet` en ninguna tarea.**

## Fase 1 · Funciones de `src/` (primero la prueba)

- [x] T001 Escribir `tests/test_registry.py` (primero, debe fallar porque `registry.py` no existe). Debe cubrir:
  - `registry_params`: con un bloque `decisiones` de juguete devuelve tipo de modelo, los hiperparámetros, el umbral 1/6 y `calibrar`,
    en un diccionario plano (sin listas ni diccionarios anidados);
  - `registry_metrics`: con un bloque `prueba` de juguete devuelve solo números con los nombres del plan (`test_cost`,
    `test_cost_ic95_low`, `test_cost_ic95_high`, …, `cost_diff_ic95_high`) y los valores exactos del JSON; **lanza `KeyError`** si falta
    una clave (no rellena con ceros);
  - `max_proba_difference`: 0,0 con el mismo modelo dos veces; > 0 con dos modelos distintos (dos `LogisticRegression` pequeñas).
- [x] T002 Crear `src/proyecto/tracking/registry.py` con las 3 funciones del plan (docstrings en español, nombres en inglés);
  `pytest tests/test_registry.py -q` en verde.

## Fase 2 · Notebook 08 (solo orquesta)

- [x] T003 `notebooks/08_registro_modelo.ipynb`, sección 0: `configure_mlflow()` y `set_experiment("venta-cruzada-registro")`; imprime
  `databricks (token)` o `local` y el aviso si cae a local. No imprime el token ni la dirección del workspace.
- [x] T004 Sección 1: cargar `models/final_pipeline.joblib` y `reports/07_metricas_test.json`; si falta alguno, `FileNotFoundError` con
  "ejecuta primero el notebook 07". Leer la fecha de `reports/prueba_abierta.txt` y el commit (`git rev-parse --short HEAD`).
- [x] T005 Sección 2: `COLUMNAS_ENTRADA` = las 10 columnas sin `id` ni `Response`; ejemplo = 5 filas de `data/processed/train.parquet`
  (no `train.joblib`); firma con `infer_signature`; una ejecución `modelo-final` con `registry_params`, `registry_metrics`, las etiquetas
  de la spec y `mlflow.sklearn.log_model(..., name="model", registered_model_name=registered_model_name("venta_cruzada_lgbm"),
  serialization_format="cloudpickle", code_paths=["../src/proyecto"])`. La versión sale de `registered_model_version`.
- [x] T006 Sección 3: alias `champion` a esa versión con `MlflowClient().set_registered_model_alias`.
- [x] T007 Sección 4: cargar `models:/<nombre>@champion` y `max_proba_difference` contra el modelo local en 200 clientes de
  `train.parquet`; `assert diferencia <= 1e-9` (si falla, no se escribe la constancia).
- [x] T008 Sección 5: escribir `reports/08_registro.json` (tracking, experimento, nombre completo, versión, alias, `run_id`, diferencia
  de la ida y vuelta, fecha y hora).
- [x] T009 *(hecha el 2026-11-06 desde el computador de Ricardo con token, no dentro de Databricks: `workspace.default.venta_cruzada_seguros` versión 2, alias `champion`, ida y vuelta con diferencia 0,0; se arregló antes la línea `fecha:` de `reports/prueba_abierta.txt`, que el cuaderno lee)* Ejecutar el notebook completo **una vez, dentro de Databricks** (Git folder actualizado desde GitHub; si la sección 1 pide
  versiones, `%pip install -r ../requirements.txt`) y `pytest tests -q` en verde. Si Databricks rechaza el registro (permisos de Unity
  Catalog), detenerse y avisar al grupo antes de pasar a local. Desde Databricks, commit y push de `reports/08_registro.json` y del
  notebook con sus salidas; después, `git pull` en el equipo local. *(Enmienda 2026-11-05, ver plan. T003–T008 verificadas con un
  ensayo local: diferencia de la ida y vuelta 0,0.)*

## Fase 3 · Cierre

- [ ] T010 Completar `reports/08_registro.md` con lo que imprimió el notebook (dónde, versión, alias, ida y vuelta, tracking frente a
  registro, reproducibilidad), sin espacios en blanco.
- [ ] T011 [P] Revisar `src/proyecto/tracking/registry.py` y el notebook 08 con el subagente `revisor-de-codigo-ia`; anotar lo que diga
  en el reporte.
- [ ] T012 [P] Comprobar que ningún archivo versionado contiene el token ni la dirección del workspace
  (`git grep -n -i "dapi\|cloud.databricks.com\|azuredatabricks"` sin resultados fuera de `.env.example`).
- [ ] T013 Anotar en la sección 7 de `especificacion-proyecto.md` el registro del modelo (nombre, versión `champion`, dónde) y la
  decisión de quitar `id` de la firma.

## Dependencias

T001 → T002 → T003 … T009 (en orden: cada sección usa lo de la anterior) → T010 → T013. T011 y T012 se pueden hacer en paralelo
después de T009.

## Cómo verificar

```bash
pytest tests/test_registry.py -q
pytest tests -q
```
El notebook imprime la versión con alias `champion` y `diferencia máxima = 0.0`; existe `reports/08_registro.json`.

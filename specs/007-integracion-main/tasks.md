# Tareas: Integrar `main` sobre el modelo final de la rama (`007-integracion-main`)

**Entrada:** `specs/007-integracion-main/plan.md`, `data-model.md`, `research.md`, `contracts/`, `quickstart.md`
**Estado:** borrador, pendiente de aprobación del grupo
Una tarea se marca `[x]` solo cuando su comprobación pasa. **Ninguna tarea lee `data/processed/test.parquet` ni recalcula métricas de
prueba.** Toda cifra de prueba se copia de `reports/07_metricas_test.json` (versión de la rama).

## Fase 1 · Preparación

- [x] T001 Confirmar que `006-registro-modelo` está limpia y al día (`git status -sb` sin cambios salvo `specs/007-integracion-main/`),
  hacer commit de `specs/007-integracion-main/` en `006-registro-modelo` y crear la rama `git switch -c 007-integracion-main`.
- [x] T002 `git fetch origin` y `git merge --no-commit --no-ff origin/main`. Guardar la lista de conflictos (`git diff --name-only
  --diff-filter=U`) y comprobar que son los 8 de la spec; si aparece otro, detenerse y avisar.

## Fase 2 · Base: resolver la fusión (bloquea todo lo demás)

- [x] T003 Volver a la versión de la rama (**R**) con `git checkout HEAD -- <archivo>` en: `src/proyecto/config.py`,
  `src/proyecto/data/cleaning.py`, `src/proyecto/data/split.py`, `src/proyecto/features/__init__.py`,
  `src/proyecto/features/engineering.py`, `src/proyecto/features/preprocessing.py`, `src/proyecto/features/transformers.py`,
  `src/proyecto/models/train.py`, `src/proyecto/models/tuning.py`.
- [x] T004 R en pruebas: `tests/test_cleaning.py`, `tests/test_features.py`, `tests/test_models.py`, `tests/test_split.py`,
  `tests/test_tuning.py`, `tests/test_preprocessing.py`.
- [x] T005 R en datos y notebooks: `data/processed/train.parquet` (debe tener 304.238 filas), `notebooks/01_caso_negocio.ipynb` a
  `notebooks/08_registro_modelo.ipynb`.
- [x] T006 R en informes y especificaciones: `especificaciones/03-preprocesamiento.md`, `specs/002-variables/spec.md`,
  `reports/04_features.md`, `reports/04_features_tabla.csv`, `reports/05_torneo.md`, `reports/06_optimizacion.md`,
  `reports/06_best_params.json`, `reports/07_decisiones_congeladas.json`, `reports/07_metricas_test.json`, `reports/07_validacion.md`,
  `reports/08_registro.md`. Para `especificacion-proyecto.md` y `reports/prueba_abierta.txt` tomar la versión de la rama como base
  (se completan en T016 y T018).
- [x] T007 Quitar (**Q**) con `git rm`: `src/proyecto/data/loading.py`, `src/proyecto/models/metrics.py`,
  `src/proyecto/models/baselines.py`, `tests/test_tournament.py`, `reports/04_features_tabla_nuevas.csv`, `reports/05_torneo_tabla.csv`,
  `reports/08_registro.json`, `models/model.joblib`, `models/input_schema.json` (estos dos se regeneran en T023).
  `tests/test_serving.py` y `src/proyecto/inference/serving.py` se quedan temporalmente (se reescriben en T020–T021); si rompen la
  colección de pruebas, quitarlos de la ejecución con `--ignore` solo hasta T021.
- [x] T008 Confirmar que quedan de `main` (**M**) sin cambios: `pytest.ini`, `requirements.txt` (con `pyarrow==25.0.1`), `.gitignore`,
  `specs/README.md`, `src/proyecto/inference/predict.py`, `src/proyecto/inference/schema.py`, `tests/test_inference.py`,
  `app/streamlit_app.py`, `reports/06_mlflow_runs.csv`. `git diff --name-only --diff-filter=U` debe salir vacío.
- [x] T009 `PYTHONUTF8=1 python -m pytest -q --ignore=tests/test_serving.py`: las 113 pruebas de la rama en verde. Si falla, detenerse
  (no seguir con archivos A).

## Fase 3 · Historia 1 (P1): un solo modelo final coherente 🎯 MVP

**Objetivo:** el repositorio tiene un solo modelo final (rama), que carga y predice, con el código de `src/` que lo construyó.
**Prueba independiente:** pasos 1, 3 y 4 de `quickstart.md`.

- [x] T010 [US1] Comprobar que `models/final_pipeline.joblib` carga con el `src/` resultante y que `feature_names_in_` incluye
  `Gender`, `Vintage`, `Driving_License` y no `Policy_Sales_Channel` (paso 3 de `quickstart.md`); comprobar 304.238 filas en
  `data/processed/train.parquet` (paso 4).
- [x] T011 [US1] En `notebooks/08_registro_modelo.ipynb`, cambiar el nombre del modelo registrado de `venta_cruzada_lgbm` a
  `venta_cruzada_seguros` (solo esa constante); actualizar el mismo nombre en `specs/006-registro-modelo/spec.md` con una nota
  "(cambiado en 007, 2026-11-06)".
- [x] T012 [US1] Commit intermedio de la fusión resuelta: "Integra main: conserva el modelo final de la rama (código, datos y etapas
  1–8)". Es el punto seguro al que volver.

## Fase 4 · Historia 2 (P1): las cifras y decisiones escritas dicen la verdad

**Objetivo:** informes y registro de decisiones describen el modelo final, sin cifras del modelo de `main` como vigentes.
**Prueba independiente:** paso 5 de `quickstart.md` y lectura de `reports/decisiones_del_grupo.md`.

- [ ] T013 [US2] `reports/decisiones_del_grupo.md`: agregar el estado **[REEMPLAZADO]** a "Cómo leer los estados"; marcar D12, D14 y la
  decisión de la etapa 4 como `[REEMPLAZADO 2026-11-06] por D15` sin borrar su texto; agregar **D15** y cerrar **P12** exactamente como
  la sección 2 de `data-model.md`. Actualizar la tabla "Resumen".
- [ ] T014 [P] [US2] `reports/07_validacion.md`: agregar una sección "La prueba en el grupo" que diga que se abrió dos veces el
  2026-11-05 (19:09 con el modelo de `main`, 20:43 con el modelo final), que el modelo final se eligió por un criterio fijado sin
  comparar cifras de prueba (incluir las 5 variables nuevas) y que las cifras del modelo de `main` no se usan para decidir nada.
- [ ] T015 [P] [US2] Revisar `reports/00_caso.md`, `reports/01_eda.md` y `especificaciones/02-eda.md` (versión de `main`): quitar o
  ajustar lo que cite secciones o cifras que solo existen en los notebooks 01–02 de `main` (por ejemplo, la sección 4.2 de señal de
  variables nuevas de `main` y el conteo de 304.887); conservar el resto.
- [ ] T016 [US2] `especificacion-proyecto.md`: unir la sección 7 de ambas versiones (fusión de la rama + lo que agregó `main` que siga
  siendo cierto) y agregar la entrada "2026-11-06 · integración de `main`: modelo final = rama (D15)".
- [ ] T017 [P] [US2] `models/ficha_modelo.md`: estructura de `main`; variables (base + 5 nuevas, con `Gender`, `Vintage`,
  `Driving_License`, sin canal), parámetros del ensayo #13, 304.238 clientes de entrenamiento y cifras de prueba copiadas de
  `reports/07_metricas_test.json`; mantener los límites y la auditoría por género y edad (`reports/07_segmentos.csv`).
- [ ] T018 [P] [US2] `reports/prueba_abierta.txt`: dejar las dos aperturas (19:09 modelo de `main`; 20:43, usuario, commit `e94c0cb`,
  76.222 filas, modelo final), cada una en su línea.
- [ ] T019 [US2] `reports/informe_tecnico.md` y `presentacion/ejecutiva.md` (máximo 5 diapositivas): estructura de `main`, modelo, variables,
  decisiones y cifras del modelo final (de `07_metricas_test.json`); mencionar la doble apertura de la prueba y que `champion` en
  Databricks sigue en el modelo de `main` hasta T009 de `006-registro-modelo`. Ejecutar el paso 5 de `quickstart.md`.

## Fase 5 · Historia 3 (P2): la app y la inferencia usan el modelo final

**Objetivo:** `models/model.joblib` = modelo final con la traducción persona → modelo; la app lo usa.
**Prueba independiente:** pasos 1, 2 y 9 de `quickstart.md`.

- [ ] T020 [US3] Reescribir `tests/test_serving.py` (primero; debe fallar con el `serving.py` de `main`) con las 5 pruebas de
  `contracts/serving.md`, usando un `Pipeline` de juguete entrenado con columnas como las de `train.parquet` (no el modelo real).
- [ ] T021 [US3] Reescribir `src/proyecto/inference/serving.py` según `contracts/serving.md`: `RAW_COLUMNS` = `["Age",
  "Annual_Premium", "Region_Code", "Vintage", "Gender", "Driving_License", "Previously_Insured", "Vehicle_Age", "Vehicle_Damage"]`;
  codificación con `CATEGORY_MAPS` y `MIN_PREMIUM` de `config.py` (`Driving_License` y `Previously_Insured`: `Yes`=1, `No`=0); sin `id`
  (plan B de `research.md` R5 si el modelo la exige). `pytest tests/test_serving.py -q` en verde.
- [ ] T022 [US3] `notebooks/09_inferencia.ipynb` (solo orquesta): cargar `models/final_pipeline.joblib` y
  `data/processed/train.parquet`; `build_defaults(to_raw(train))`; `build_schema` con las claves de `contracts/input_schema.md`
  (`valid_range`: `Age` 18–100, `Annual_Premium` > 0, `Vintage` ≥ 0, `Region_Code` 0–52; `cost_matrix` = `COST_MATRIX`;
  `decision_labels` {"0": "No llamar", "1": "Llamar"}; etiquetas, título y aviso de uso responsable). No importa nada de
  `proyecto.models.metrics` ni lee `test.parquet`.
- [ ] T023 [US3] Ejecutar el notebook 09: guarda `models/model.joblib` (`ServingModel`) y `models/input_schema.json`; celda de ida y
  vuelta: diferencia máxima entre `model.joblib` (con `to_raw`) y `final_pipeline.joblib` en 200 clientes de entrenamiento `<= 1e-9`
  (paso 2 de `quickstart.md`); ejemplo con 3 clientes de entrenamiento y un caso inválido (edad 150) que lanza `InputValidationError`.
- [ ] T024 [US3] Abrir la app (`streamlit run app/streamlit_app.py`) y comprobar el paso 9 de `quickstart.md`: 9 datos, sin canal,
  "Llamar/No llamar", aviso de uso responsable, error con edad 150. Si hace falta tocar `app/streamlit_app.py`, solo cambios pequeños
  (la app es de `main`).
- [ ] T025 [US3] `reports/09_despliegue.md`: estructura de `main`, con las 9 entradas del formulario, cómo se generan `model.joblib` e
  `input_schema.json` (notebook 09) y el resultado de la ida y vuelta de T023.

## Fase 6 · Historia 4 (P2): nada personal en el repositorio

**Objetivo y prueba independiente:** paso 6 de `quickstart.md` sin resultados.

- [ ] T026 [US4] Ejecutar `git grep -nE '@(unaula|gmail|hotmail|outlook)' -- . ':!material-del-curso'` y
  `git grep -n -i "dapi\|cloud.databricks.com\|azuredatabricks" -- . ':!.env.example'`; ambos vacíos. Si aparece algo, quitarlo del
  archivo (no del historial: anotarlo en `reports/integracion_main.md`).

## Fase 7 · Cierre

- [ ] T027 Escribir `reports/integracion_main.md` con la tabla de la sección 1 de `data-model.md` (archivo, cambio de `main`, decisión,
  motivo) y las cifras de comprobación (pruebas, ida y vuelta, filas); comprobar el paso 8 de `quickstart.md` (todo archivo borrado
  aparece en la tabla).
- [ ] T028 [P] Actualizar `README.md` (modelo final, cómo abrir la app) y `specs/README.md` (agregar `007-integracion-main`).
- [ ] T029 [P] Revisar con el subagente `auditor-de-fuga` (notebook 09, `serving.py`, defaults solo de entrenamiento) y con
  `revisor-de-codigo-ia` (`serving.py`, `test_serving.py`, notebook 09); anotar lo que digan en `reports/integracion_main.md`.
- [ ] T030 Ejecutar todo `quickstart.md` (pasos 1 a 9) y `PYTHONUTF8=1 python -m pytest -q` completo en verde; commit
  "Integra main: inferencia, app e informes sobre el modelo final".
- [ ] T031 Con autorización del usuario: `git push -u origin 007-integracion-main` y *pull request* a `main` con el resumen de
  `reports/integracion_main.md`, para que el grupo lo revise.

## Dependencias

- T001 → T002 → **Fase 2 (T003–T009)** → todo lo demás. T003–T008 tocan archivos distintos, pero se hacen en orden dentro de la misma
  fusión; T009 es la compuerta.
- Historia 1 (T010–T012) va primero: T012 es el punto seguro.
- Historia 2 (T013–T019) e Historia 3 (T020–T025) son independientes entre sí después de T012. T019 conviene después de T023 si se quiere
  citar la ida y vuelta en el informe.
- Historia 4 (T026) después de las historias 2 y 3 (revisa los archivos finales).
- Cierre (T027–T031) al final; T031 solo con permiso del usuario.

## Trabajo en paralelo

- Historia 2: T014, T015, T017 y T018 (archivos distintos) a la vez; luego T013 → T016 → T019.
- Historia 3: T020 → T021 → T022 → T023 → T024/T025 (en orden: cada uno usa lo anterior).
- Cierre: T028 y T029 a la vez.

## Estrategia

1. **MVP = Fases 1–3** (hasta T012): fusión resuelta, modelo final único, 113 pruebas en verde, commit de seguridad.
2. Luego Historia 3 (app funcionando) e Historia 2 (textos), en el orden que prefiera el grupo.
3. Historia 4 y cierre antes del *pull request*.

## Cómo verificar

```bash
PYTHONUTF8=1 python -m pytest -q
PYTHONUTF8=1 python -m pytest tests/test_serving.py -q
```

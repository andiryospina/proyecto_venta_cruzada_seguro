# Investigación: integración de `main` (`007-integracion-main`)

Todo lo de este archivo se comprobó en el repositorio el 2026-11-06 (base común de las ramas: `e94c0cb`).

## R1. ¿Por qué no basta con fusionar y resolver los 8 conflictos?

- **Decisión:** fusionar sin guardar y decidir **todos** los archivos que cambió `main` (63 fuera de `material-del-curso/`) con la
  tabla del plan.
- **Motivo:** la base común `e94c0cb` es un commit de la rama (etapa 06). Después, `main` reemplazó `src/`, `tests/`, notebooks 01–06,
  `train.parquet` e informes 04–06 por la versión de la compañera. La rama no tocó esos archivos, así que Git **toma los de `main` sin
  avisar**. En la fusión de prueba: 8 de las 9 funciones que importan los notebooks 07 y 08 desaparecían y el código de las 5
  variables nuevas también.
- **Alternativas descartadas:** `git merge -X ours` (solo decide trozos en conflicto: no recupera lo que Git fusiona solo);
  `git merge -s ours` (descarta **todo** `main`, también la inferencia, el registro de decisiones y el informe técnico).

## R2. ¿Qué hacer con `data/processed/train.parquet`?

- **Decisión:** versión de la rama (304.238 filas).
- **Motivo:** el modelo final se entrenó con ese archivo; `main` lo cambió a 304.887. Las 649 filas de diferencia (P12) son clientes que
  quedan **repetidos** al quitar `Policy_Sales_Channel`; `split.drop_duplicate_rows` los quita. `test.parquet` es el mismo en las dos
  ramas (`main` no lo modificó).
- **Alternativa descartada:** quedarse con el de `main`: obligaría a reentrenar, y la prueba ya se abrió con el modelo actual.

## R3. ¿Sirven los notebooks 01–06 de `main`?

- **Decisión:** no; se usan los de la rama.
- **Motivo:** importan funciones que solo existen en el código de `main` (`find_train_csv`, `load_train`, `FeatureOptions`,
  `run_tournament`, `per_client_cost`, `CodeVolume`, `vintage_share`…). Con el código de la rama fallarían en la primera celda.
- **Alternativa descartada:** conservar ambos códigos en `src/` (dos limpiezas y dos juegos de variables): dos verdades en el mismo
  repositorio, justo lo que esta integración quiere evitar.

## R4. ¿La inferencia de `main` sirve para el modelo de la rama?

- **Decisión:** `predict.py`, `schema.py` y la app se conservan tal cual; `serving.py` se reescribe.
- **Motivo:** `predict.py` y `schema.py` son genéricos (cualquier `Pipeline` con `predict_proba`) y `main` no los cambió desde la base.
  La app arma su formulario desde `input_schema.json`. En cambio, `serving.py` importa `VEHICLE_AGE_MAP` y `YES_NO_MAP` de la limpieza
  de `main` y fabrica `Premium_is_minimum`, `Vintage` y `Driving_License` no existen en su lista: con el modelo de la rama falla.
- **Decisión de la regla de decisión:** `predict_with_scores` elige la decisión de **menor costo esperado** con la matriz
  `[[0, 1], [5, 0]]`. Es lo mismo que el umbral 1/6: llamar cuesta `1 − p`, no llamar cuesta `5p`; se llama si `p > 1/6`. En el empate
  exacto `p = 1/6` gana "no llamar" (primera columna), igual que la regla de la etapa 07 (`>`).

## R5. ¿El modelo predice sin la columna `id`?

- **Decisión:** `ServingModel` no envía `id`.
- **Motivo:** se comprobó en la etapa 08 (2026-11-05): mismas probabilidades sin `id` (diferencia 0,0 en 200 clientes, sin avisos).
  Se vuelve a comprobar en la prueba de ida y vuelta del notebook 09. **Plan B** si una versión nueva de scikit-learn lo rechaza:
  `ServingModel` agrega `id = 0` (el `Pipeline` la descarta).

## R6. ¿Dónde estaba el dato personal?

- **Hallazgo:** un correo de un compañero en `reports/08_registro.json`, `reports/08_registro.md` y `notebooks/08_registro_modelo.ipynb`
  de `main` (ruta del experimento de MLflow). Los tres quedan con la versión de la rama (R) o se quitan (Q).
- **Comprobación:** `git grep -E '@(unaula|gmail|hotmail|outlook)'` fuera de `material-del-curso/` debe salir vacío.

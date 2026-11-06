# Plan: Registro del modelo final (`006-registro-modelo`)

**Fecha:** 2026-11-05 · **Spec:** `specs/006-registro-modelo/spec.md` · **Estado:** aprobado por el grupo (2026-11-05)

## Diseño

```text
src/proyecto/tracking/registry.py         # NUEVO: 3 funciones pequeñas y puras (tabla de abajo)
tests/test_registry.py                    # NUEVO: una prueba por función
notebooks/08_registro_modelo.ipynb        # se llena el esqueleto existente; solo orquesta
reports/08_registro.json                  # lo escribe el notebook (constancia)
reports/08_registro.md                    # se llena la plantilla existente con las cifras reales
```

Se reutiliza lo que ya existe y está probado: `configure_mlflow`, `set_experiment` y `registered_model_name`
(`tracking/mlflow_utils.py`). El modelo **no** se reentrena: se carga `models/final_pipeline.joblib` tal cual.

## Funciones nuevas de `registry.py`

| Función | Qué hace |
|---|---|
| `registry_params(decisions)` | Del bloque `decisiones` de `07_metricas_test.json` saca los parámetros a registrar: tipo de modelo, los 7 hiperparámetros, umbral (1/6), `calibrar`. Devuelve un diccionario plano de textos y números |
| `registry_metrics(test_block)` | Del bloque `prueba` saca **solo números**, con nombres planos: `test_cost`, `test_cost_ic95_low/high`, `test_pr_auc`, `test_roc_auc`, `test_recall`, `test_precision`, `test_contact_rate`, `test_capture_20/30/50`, `test_log_loss`, `test_brier`, `baseline_cost`, `cost_diff`, `cost_diff_ic95_low/high`. Lanza un error si falta alguna clave (no inventa ceros) |
| `max_proba_difference(model_a, model_b, X)` | Diferencia absoluta máxima entre las probabilidades de "interesado" de dos modelos en las mismas filas (para la ida y vuelta) |

Las pruebas usan un JSON de juguete y dos modelos pequeños de `sklearn`: no tocan MLflow, ni Databricks, ni el modelo real.

## Orden del notebook 08

0. **Conexión:** `configure_mlflow()` → imprime `databricks (token)` o `local` (y el aviso, si cae a local). `set_experiment("venta-cruzada-registro")`.
1. **Cargar:** `final_pipeline.joblib` y `07_metricas_test.json`; si falta alguno, se detiene con `FileNotFoundError` y el mensaje
   "ejecuta primero el notebook 07". Se lee también la fecha de `reports/prueba_abierta.txt` y el commit actual (`git rev-parse --short HEAD`).
2. **Registrar** (una ejecución `modelo-final`):
   - `log_params(registry_params(...))`, `log_metrics(registry_metrics(...))`, etiquetas de la spec;
   - `COLUMNAS_ENTRADA` = las 10 columnas del entrenamiento **sin `id` ni `Response`** (`Gender`, `Age`, `Driving_License`,
     `Region_Code`, `Previously_Insured`, `Vehicle_Age`, `Vehicle_Damage`, `Annual_Premium`, `Vintage`, `is_min_premium`);
   - firma con `infer_signature(ejemplo, probabilidades del ejemplo)`; ejemplo = 5 filas de `train.parquet`;
   - `mlflow.sklearn.log_model(..., name="model", registered_model_name=registered_model_name("venta_cruzada_lgbm"),
     serialization_format="cloudpickle", code_paths=["../src/proyecto"])`.
   - La versión sale de lo que devuelve `log_model` (`registered_model_version`), no de buscar "la mayor".
3. **Alias:** `MlflowClient().set_registered_model_alias(nombre, "champion", version)`.
4. **Ida y vuelta:** `mlflow.sklearn.load_model("models:/<nombre>@champion")` y `max_proba_difference` contra el modelo local en
   200 clientes de `train.parquet`. `assert diferencia <= 1e-9`; si falla, se detiene antes de la constancia.
5. **Constancia:** `reports/08_registro.json` con `tracking` (`databricks (token)` o `local`), experimento, nombre completo, versión,
   alias, `run_id`, diferencia de la ida y vuelta, fecha y hora. **Sin** la dirección del workspace ni el token.

Después, a mano: completar `reports/08_registro.md` con lo que imprimió el notebook.

## Decisiones técnicas (comprobadas, sin investigación pendiente)

- **Sin `id` en la firma:** se comprobó el 2026-11-05 que el `Pipeline` da **exactamente** las mismas probabilidades sin `id`
  (diferencia máxima 0,0 en 200 clientes, sin avisos): el `ColumnTransformer` la descarta. Así no sube un identificador al registro.
- **`code_paths=["../src/proyecto"]`:** el primer paso del `Pipeline` es `proyecto.features.engineering.add_features`; sin el paquete,
  cargar el modelo da `ModuleNotFoundError: No module named 'proyecto'` (comprobado). MLflow copia la carpeta junto al modelo y la
  agrega al `sys.path` al cargarlo.
- **`cloudpickle`:** el formato por defecto (skops) rechaza transformadores propios; es la nota técnica del esqueleto.
- **Ejemplo y ida y vuelta con `train.parquet`**, no con la prueba (no se vuelve a leer `test.parquet`). El esqueleto apuntaba a
  `train.joblib`, que no existe en este proyecto: se corrige.
- **Columnas con tipo `Int64` de pandas:** si `infer_signature` no las acepta, se convierten a `int64` solo en el ejemplo (no hay
  vacíos en esas columnas tras la limpieza). Se anota en el reporte si pasa.
- No se generan `research.md`, `data-model.md`, `contracts/` ni `quickstart.md`, igual que en las specs 001 a 005: la etapa no expone
  interfaces nuevas (la interfaz para la app se define en la etapa 09) y no hay dudas técnicas abiertas.

## Revisión contra la constitución

- **III:** no se abre la prueba; las métricas de la prueba se **copian** del JSON de la etapa 07, no se recalculan.
- **IV / VII:** las métricas se leen del JSON con `registry_metrics`, que falla si falta una clave; nada se escribe a mano.
- **V:** el token se lee de `.env` y no se imprime; la constancia guarda solo `databricks (token)` o `local`; el ejemplo no lleva `id`.
- **VI:** la lógica reutilizable (3 funciones) va en `src/`; el notebook solo orquesta.
- **Regla 7 de `CLAUDE.md`:** MLflow en Databricks vía `configure_mlflow()`, con `PYTHONUTF8=1`; si cae a local, se dice.
- **Regla 9:** cada función de `registry.py` tiene prueba.

## Cómo verificar

```bash
pytest tests/test_registry.py -q     # funciones nuevas
pytest tests -q                      # todo el proyecto en verde
```
Después de ejecutar el notebook: imprime la versión con alias `champion` y `diferencia máxima = 0.0`; existe `reports/08_registro.json`;
en Databricks (Catalog → `workspace.default.venta_cruzada_lgbm`) se ve la versión con el alias.

## Enmienda (2026-11-05): el notebook 08 se ejecuta dentro de Databricks

El grupo trabaja así: **GitHub → Databricks** (Git folder) → los resultados vuelven a GitHub. El equipo local no tiene conexión con
Databricks (el `.env` local no tiene la dirección del workspace; el notebook 06 se ejecutó en Databricks). Cambios:

- `models/final_pipeline.joblib` **se sube a GitHub** (se quita del `.gitignore`): pesa 681 KB y no tiene datos de clientes. Así
  Databricks lo recibe sin pasos manuales. Cambia lo dicho en la spec 005 ("no se sube a GitHub").
- Sección 1 del notebook: comprueba que scikit-learn y LightGBM tengan las versiones de `requirements.txt` antes de cargar el modelo
  (si no, pide `%pip install -r ../requirements.txt`); si `git` no está disponible, la etiqueta del commit dice "no disponible".
- En Databricks `configure_mlflow()` devuelve `databricks (dentro del workspace)` y el registro va a Unity Catalog.
- Ensayo local previo (MLflow local, salida fuera del repo): todas las celdas corren, ida y vuelta con diferencia 0,0. La constancia del
  ensayo se borró; la oficial sale de Databricks.

## Riesgos

- **Sin permisos en Unity Catalog** para crear modelos en `workspace.default`: el registro falla aunque el tracking funcione.
  Mitigación: definir `UC_CATALOG` / `UC_SCHEMA` en `.env`, o registrar en local (`MLFLOW_FORCE_LOCAL=1`) y decirlo en el reporte.
- **Unity Catalog exige firma** con entradas y salidas: por eso la firma es obligatoria aquí, no opcional.
- **Cada ejecución crea una versión nueva:** es lo esperado; el alias siempre apunta a la última y el reporte dice cuál.
- **El modelo pesa** (`final_pipeline.joblib` no está en GitHub): quien clone el repo necesita ejecutar el notebook 07 o pedir el
  modelo **desde el registro** con el alias, que es justamente lo que esta etapa resuelve.
- **Tiempo:** subir el modelo a Databricks y cargarlo de vuelta: 1–3 minutos.

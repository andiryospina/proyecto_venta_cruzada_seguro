# Registro del modelo

> Resultado de `notebooks/08_registro_modelo.ipynb`, ejecutado el 2026-11-06 contra **Databricks** sobre el modelo final (D15). Constancia en `reports/08_registro.json`.

## 1. Dónde quedó registrado

| Dato | Valor |
|---|---|
| Plataforma | ☒ Databricks (Unity Catalog; conexión por token personal desde el computador de Ricardo) ☐ MLflow local |
| Experimento | `venta-cruzada-registro` (queda bajo la carpeta del usuario en el workspace; la ruta completa no se guarda porque lleva un correo) |
| Nombre del modelo registrado | `workspace.default.venta_cruzada_seguros` |
| Versión | **2** (la versión 1 es el modelo anterior de `main`, que ya no es el final) |
| Alias | `champion` → versión 2 |
| Quién lo registró y cuándo | Ricardo, desde su computador, 2026-11-06 17:47:18; ejecución `62407bc214714c8fb8ac118b99005076` |

## 2. Qué se registró junto al modelo

- **Parámetros:** tipo de modelo (LightGBM), hiperparámetros del ensayo #13 de Optuna (186 árboles, tasa 0,0315, 31 hojas, `min_child_samples` 137, `subsample` 0,943, `colsample_bytree` 0,601, `reg_lambda` 0,478), umbral de decisión 1/6 y si se calibró (no).
- **Métricas de la prueba** (copiadas de `reports/07_metricas_test.json`, no recalculadas): costo por cliente 0,3312 con su intervalo, PR-AUC, ROC-AUC, recall, precisión, % contactado, captura al 20/30/50 %, log loss y Brier; más el costo de la línea base (0,3720) y la diferencia con su intervalo.
- **Firma y ejemplo de entrada:** 10 columnas limpias (`Gender`, `Age`, `Driving_License`, `Region_Code`, `Previously_Insured`, `Vehicle_Age`, `Vehicle_Damage`, `Annual_Premium`, `Vintage`, `is_min_premium`), sin `id`; ejemplo: las 5 primeras filas del entrenamiento.
- **Etiquetas:** `etapa` = 08_registro, `proyecto`, `commit`, `prueba_abierta_el`, `nota` y `mejor_que_linea_base`.

## 3. Comprobación de ida y vuelta

- ¿El modelo recuperado del registro predice igual que el local? ☒ sí
- Cómo se comprobó: se cargó `models:/workspace.default.venta_cruzada_seguros@champion` con `mlflow.sklearn.load_model` y se comparó `predict_proba` contra `models/final_pipeline.joblib` en 200 clientes del entrenamiento. **Diferencia máxima: 0,0** (el cuaderno falla con un `assert` si supera 1e-9 y no escribe la constancia).

## 4. Tracking frente a registro (en nuestras palabras)

- **Tracking:** guardó las ejecuciones de la etapa 6 (los ensayos de la búsqueda de Optuna, con sus parámetros y métricas) y la de la validación. Sirve para auditar qué se probó y demostrar que la mejora de los parámetros se comprobó en clientes que la búsqueda no vio.
- **Registro:** guarda **una** versión del modelo que usamos, con su firma y las métricas de la prueba. El alias `champion` permite que cualquiera pida "el champion" sin saber el número de versión: cuando hubo un modelo final distinto (D15) bastó con registrar la versión 2 y mover el alias, sin tocar ningún código.

## 5. Reproducibilidad

- ¿Alguien de otro grupo podría recuperar el modelo con lo que dejamos escrito? ☐ sí  ☒ no → **qué falta:** el modelo registrado vive en el workspace de Databricks de Ricardo y solo lo ve quien tenga permisos en Unity Catalog. Cualquiera puede, en cambio, **recuperar el mismo modelo del repositorio**: `models/final_pipeline.joblib` (etapa 7) y `models/model.joblib` (para la app); o regenerarlo ejecutando los cuadernos 03 a 08. El seguimiento de las etapas 6 y 7 en `mlflow_local.db` no se versiona.

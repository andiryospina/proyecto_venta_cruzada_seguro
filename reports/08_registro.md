# Registro del modelo

> Resultado de `notebooks/08_registro_modelo.ipynb`, ejecutado el 2026-11-05 contra **Databricks** (se había ejecutado antes en MLflow local como respaldo). Constancia en `reports/08_registro.json`.

## 1. Dónde quedó registrado

| Dato | Valor |
|---|---|
| Plataforma | ☒ Databricks (workspace `dbc-42fa3d87-63b6`, conexión por token personal) ☐ MLflow local |
| Experimento | `/Users/ricardo.gonzalez1544@unaula.edu.co/venta-cruzada-seguros-modelo-final` |
| Nombre del modelo registrado | `workspace.default.venta_cruzada_seguros` (Unity Catalog) |
| Versión | 1 |
| Alias | `champion` |
| Quién lo registró y cuándo | `ricardo.gonzalez1544@unaula.edu.co`, 2026-11-05 19:36; ejecución `978b062c00f54eb785f11f28b62928a5` |

## 2. Qué se registró junto al modelo

- **Parámetros:** modelo (LightGBM), parámetros de partida (`n_estimators` 200, `learning_rate` 0,08, `num_leaves` 31, `min_child_samples` 100, `subsample` 0,8, `colsample_bytree` 0,8, `reg_lambda` 0), variables usadas, calibración (no), umbral 0,1667 y R = 5.
- **Métricas de la prueba:** costo por cliente 0,3317 (intervalo 95 % [0,3264; 0,3369]), costo del baseline 0,3967, PR-AUC 0,3533, ROC-AUC 0,8519, recall 0,875, precisión 0,296, % contactado 0,362 y log loss 0,2672.
- **Firma y ejemplo de entrada:** 8 columnas limpias: `Age`, `Gender`, `Previously_Insured`, `Vehicle_Age`, `Vehicle_Damage`, `Region_Code`, `Annual_Premium`, `Premium_is_minimum`. Ejemplo: las 5 primeras filas del entrenamiento.
- **Etiquetas:** `etapa` = 08_registro, `nota` (prueba abierta una sola vez en la etapa 7), `decididas_el` (2026-11-05 19:09), `sin_canal_de_venta` = true, `con_gender` = true.

## 3. Comprobación de ida y vuelta

- ¿El modelo recuperado del registro predice igual que el local? ☒ sí
- Cómo se comprobó: se cargó `models:/venta_cruzada_seguros@champion` con `mlflow.sklearn.load_model` y se comparó `predict_proba` contra el modelo local en 2.000 clientes del entrenamiento (`np.allclose`; el notebook falla con un `assert` si no coinciden).

## 4. Tracking frente a registro (en nuestras palabras)

- **Tracking:** en este proyecto guardó las 40 ejecuciones de la búsqueda de la etapa 6 (20 por finalista), cada una con sus parámetros, su costo, su PR-AUC y etiquetas. Sirvió para demostrar que la optimización no encontró nada mejor de forma demostrable y para poder auditarla.
- **Registro:** guarda **una** versión del modelo que usamos (`venta_cruzada_seguros` v1) con su firma y sus métricas de la prueba. El alias `champion` permite que la app y el notebook 09 pidan "el champion" sin saber el número de versión: si mañana hay un modelo mejor, se mueve el alias.

## 5. Reproducibilidad

- ¿Alguien de otro grupo podría recuperar el modelo con lo que dejamos escrito? ☐ sí  ☒ no → **qué falta:** quien no tenga acceso al workspace del registro no puede cargarlo por nombre. Puede **regenerarlo** ejecutando los notebooks 03 a 08 en orden, o usar `models/model.joblib` (archivo exportado del `champion`, que viaja en el repositorio). Para compartir el registro hay que dar permisos en Unity Catalog.

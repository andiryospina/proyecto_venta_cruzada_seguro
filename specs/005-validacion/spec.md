# Especificación: Validación final con el conjunto de prueba (`005-validacion`)

**Fecha:** 2026-11-05 · **Estado:** aprobado por el grupo (2026-11-05)
**Entrada:** `reports/06_best_params.json` (LightGBM con parámetros optimizados) · `reports/05_torneo.md` · Guía:
`material-del-curso/kit/guia-validacion-registro-y-app.md`, secciones 1 a 4 · Notebook: `notebooks/07_validacion_interpretacion.ipynb`

## Qué se quiere

Medir **una sola vez**, en clientes que ningún paso anterior vio (`data/processed/test.parquet`), cuánto cuesta usar el modelo
para decidir a quién llamar, y si ese costo es **menor que el de la regla de negocio** con confianza del 95 %. Todas las
decisiones se congelan y se escriben **antes** de abrir la prueba. Lo que se vea en la prueba **no cambia el modelo**: si algo
sale mal, se anota como límite.

Fuera de esta etapa: el registro del modelo en MLflow con alias `champion`, la exportación a `models/model.joblib`, el esquema
de entrada y la app (etapas 08 y 09, con su propia especificación).

## Decisiones congeladas (se escriben en `reports/07_validacion.md` con fecha y hora antes de abrir la prueba)

| Decisión | Valor | De dónde sale |
|---|---|---|
| Modelo final | LightGBM | Torneo, decisión del 2026-10-31 |
| Parámetros | Los optimizados de `reports/06_best_params.json` | El IC 95 % de la mejora en los clientes reservados quedó todo bajo cero (decisión del 2026-11-05) |
| Variables | Las mismas del torneo y la optimización: base + las 5 nuevas, con `Gender`; sin `Policy_Sales_Channel` | Specs 002 a 004 |
| Entrenamiento final | Con **todo** `train.parquet` (100 %), con el mismo `Pipeline` | Guía, sección 3 |
| Métrica principal | Costo esperado por cliente, matriz `[[0, 1], [5, 0]]` (menor es mejor) | `especificacion-proyecto.md`, sección 4 |
| Regla de decisión | Llamar si la probabilidad de interés > **1/6** (umbral fijo, sale de la matriz) | Spec 004 |
| Calibración | Se decide en el paso 1, **solo con los clientes reservados** | Ver abajo |
| Línea base | Regla "sin seguro de vehículo previo **y** con daño previo" (`Previously_Insured = 0` y `Vehicle_Damage = Yes`) | Mejor estrategia sin modelo (costo 0,373 en todo el dataset) |

## Paso 1 — ¿Se calibran las probabilidades? (sin abrir la prueba)

- Como el modelo decide con un umbral sobre la probabilidad, esa probabilidad tiene que ser creíble.
- Se usa **la misma reserva de la etapa 06**: 25 % del entrenamiento, estratificado por `Response`, semilla 7. Cada cliente
  aparece una sola vez, así que partir por fila es válido.
- Se comparan, entrenados con el 75 % y medidos en el 25 %: modelo **sin calibrar** y modelo **calibrado** (isotónica, 3 pliegues
  estratificados dentro del 75 %).
- **Regla escrita antes de mirar:** se calibra **solo si** se cumplen las dos condiciones; si una falla, no se calibra.
  1. **Mejora mínima del log loss:** todo el intervalo del 95 % de (log loss calibrado − sin calibrar), con *bootstrap* de clientes
     (1.000 remuestreos), está **por debajo de cero**. Una baja que no se distingue del ruido no basta (mismo criterio que la etapa 06).
  2. El costo de negocio en la reserva **no sube**.
  *(Enmienda del grupo, 2026-11-05, antes de ejecutar: la primera versión aceptaba cualquier baja del log loss.)*
- Se reportan la curva de calibración (10 grupos por cuantil), el log loss y el costo de ambos.

## Paso 2 — Abrir la prueba (una sola vez)

1. Se entrena el modelo final con todo el entrenamiento (calibrado solo si el paso 1 lo decidió) y se guarda entero en
   `models/final_pipeline.joblib` (no se sube a GitHub).
2. Se abre `test.parquet` y se deja constancia en `reports/prueba_abierta.txt` (fecha, hora, quién lo ejecutó y el código del commit).
   Si el archivo ya existe, el notebook **se detiene** en vez de abrir la prueba otra vez.
3. En la prueba se calculan, para el modelo **y** para la línea base:
   - **costo esperado por cliente** (métrica principal);
   - controles: PR-AUC, ROC-AUC (solo el modelo: la regla no da probabilidades), recall y precisión de "interesado",
     **% de la base contactada** (carga de trabajo) y **% de interesados capturados al contactar al 20 %, 30 % y 50 %** de la base.
4. **Intervalos del 95 %** con *bootstrap* de clientes (1.000 remuestreos, semilla 42) para el costo del modelo, el de la línea base
   y su **diferencia** (modelo − línea base).
5. **Regla de lectura, escrita antes de mirar:** el modelo es mejor que la regla de negocio **solo si todo el intervalo de la
   diferencia está por debajo de cero**. Si cruza el cero, se reporta que no hay evidencia de mejora.

## Paso 3 — Errores por segmento, sensibilidad e interpretación (con la prueba ya abierta, solo para reportar)

- **Por segmento:** `Gender`, tramos de `Age` (18–29, 30–44, 45–59, 60 o más) y `Region_Code` (cada región con al menos 1.000
  clientes en la prueba; las demás se agrupan como "otras"). Por segmento: número de clientes, costo, **% contactado frente a %
  real de interesados** y recall. Señal de alarma: un segmento donde el % contactado y el % real se separan mucho, o donde el recall
  cae muy por debajo del general.
- **Sensibilidad del costo:** costo del modelo y de la línea base con matrices **3 a 1** y **10 a 1**, con el mismo umbral 1/6. Es
  solo un reporte: **no** se cambia el umbral con la prueba.
- **Interpretación:** valores SHAP del modelo final en una muestra de la prueba (o importancia por permutación si SHAP falla), con las
  tres advertencias: explican al modelo y no al mundo, las variables correlacionadas se reparten el crédito y una importancia alta no
  es causa. Se declara que `Gender`, `Age` y `Region_Code` son **atributos sensibles** y qué haría falta antes de usarlos en producción.

## Seguimiento

La ejecución de la prueba se registra como **una** ejecución de MLflow en Databricks (local si no hay conexión), experimento
`venta-cruzada-validacion`, etiqueta `etapa=07_validacion`, con todas las métricas y sus intervalos.

## Supuestos

- `test.parquet` no se ha usado para ninguna decisión hasta hoy (las etapas 04 a 06 trabajaron solo con `train.parquet`). Si alguien
  del grupo lo abrió, se declara en `reports/07_validacion.md`.
- Los tramos de edad y el mínimo de 1.000 clientes por región son elecciones de este borrador para que cada segmento tenga suficientes
  casos; el grupo puede cambiarlos **antes** de abrir la prueba.
- Con 1 fila = 1 cliente, remuestrear clientes es lo mismo que remuestrear filas.

## Criterios de aceptación

1. `reports/07_validacion.md` tiene la tabla de decisiones congeladas con fecha y hora **anterior** a la de `reports/prueba_abierta.txt`.
2. La decisión de calibración sale de los clientes reservados, con log loss, costo y curva de calibración, y aplica la regla escrita.
3. `reports/prueba_abierta.txt` existe y el notebook se niega a abrir la prueba una segunda vez.
4. `reports/07_metricas_test.json` tiene, para el modelo y la línea base, el costo con su intervalo, la diferencia con su intervalo y
   todas las métricas de control; todas las cifras salen del notebook (ninguna escrita a mano).
5. `reports/07_validacion.md` tiene la tabla por segmento, la sensibilidad 3 a 1 y 10 a 1, la gráfica SHAP, la advertencia de atributos
   sensibles y la conclusión según la regla de lectura.
6. Las funciones nuevas de `src/` (costo por cliente, regla de línea base, *bootstrap*, tabla por segmento) tienen prueba en `tests/`, y
   `pytest tests` queda en verde.
7. El `auditor-de-fuga` revisa el notebook 07 antes de cerrar la etapa.

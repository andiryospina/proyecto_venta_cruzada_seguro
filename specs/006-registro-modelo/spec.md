# Especificación: Registro del modelo final (`006-registro-modelo`)

**Fecha:** 2026-11-05 · **Estado:** aprobado por el grupo (2026-11-05)
**Entrada:** `models/final_pipeline.joblib` y `reports/07_metricas_test.json` (etapa 07) · Guía:
`material-del-curso/kit/guia-validacion-registro-y-app.md`, sección 5 · Notebook: `notebooks/08_registro_modelo.ipynb` (esqueleto)

## Qué se quiere

Dejar el modelo final guardado en **un registro de modelos** (MLflow en Databricks; local si no hay conexión), con todo lo que hace
falta para confiar en él y recuperarlo: qué modelo es, con qué parámetros, qué resultado dio en la prueba, qué columnas espera y de
dónde salió. La versión que se usa lleva el alias **`champion`**: cualquiera del grupo (o de otro grupo) la pide por ese nombre, sin
saber el número de versión.

El **tracking** (etapas 06 y 07) responde "¿qué probamos y qué dio?"; el **registro** responde "¿qué modelo usamos y en qué versión?".

Esta etapa **no entrena, no cambia y no vuelve a evaluar** el modelo: registra exactamente el archivo que salió de la etapa 07. La
prueba **no se abre** (ya se abrió una vez, `reports/prueba_abierta.txt`).

Fuera de esta etapa: la exportación a `models/model.joblib`, el esquema de entrada para la app (`models/input_schema.json`) y la app
(etapa 09, con su propia especificación).

## Qué se registra

| Elemento | Valor | De dónde sale |
|---|---|---|
| Modelo | El `Pipeline` completo de `models/final_pipeline.joblib` (variables nuevas + preprocesamiento + LightGBM), sin reentrenar | Etapa 07 |
| Nombre en el registro | `venta_cruzada_seguros` (en Databricks queda como `workspace.default.venta_cruzada_seguros`) | Nombre que ya usa el grupo (cambiado en 007, 2026-11-06; antes `venta_cruzada_lgbm`) |
| Parámetros | Tipo de modelo y los 7 parámetros optimizados; umbral de decisión 1/6; si se calibró (no) | `reports/07_metricas_test.json` → `decisiones` |
| Métricas de la prueba | Del modelo: costo por cliente y su IC 95 %, PR-AUC, ROC-AUC, recall, precisión, % contactado, captura al 20/30/50 %, log loss, Brier. De la comparación: costo de la línea base y la diferencia con su IC 95 % | `reports/07_metricas_test.json` → `prueba` (solo números; ninguna cifra escrita a mano) |
| Firma y ejemplo de entrada | Las columnas con las que se entrenó el `Pipeline` (las de `train.parquet` sin `Response`) y 5 filas de ejemplo del **entrenamiento** | `data/processed/train.parquet` |
| Etiquetas | `etapa=08_registro`, `proyecto=venta-cruzada`, commit del código, fecha de apertura de la prueba, "prueba abierta una sola vez en la etapa 07", decisión frente a la línea base (`mejor_que_linea_base`) | `reports/prueba_abierta.txt`, `07_metricas_test.json` |
| Código propio | El paquete `src/proyecto` viaja con el modelo, porque el `Pipeline` usa funciones y transformadores propios (sin él, el modelo no se puede cargar en otro equipo) | `src/proyecto/features` |

Experimento de MLflow: `venta-cruzada-registro`, **una** ejecución llamada `modelo-final`.

## Pasos

1. **Conexión:** se conecta a Databricks con lo que hay en `.env`; si no hay conexión, usa MLflow local (`mlflow_local.db`) y lo
   **dice en pantalla y en el reporte**.
2. **Cargar:** el modelo de la etapa 07 y sus métricas. Si falta alguno, el notebook se detiene con un mensaje claro.
3. **Registrar:** una ejecución con parámetros, métricas, etiquetas, firma, ejemplo y código propio; el modelo queda registrado con el
   nombre de arriba. Si el nombre ya existe, se crea una **versión nueva** (no se borra la anterior).
4. **Alias:** la versión recién creada recibe el alias `champion`.
5. **Ida y vuelta:** se carga el modelo **desde el registro** por su alias (`models:/<nombre>@champion`) y se comprueba que da
   **las mismas probabilidades** que el archivo local en 200 clientes del entrenamiento (diferencia máxima ≤ 1e-9). Si no coinciden,
   el notebook se detiene y **no** se escribe la constancia.
6. **Constancia:** `reports/08_registro.json` (dónde, experimento, nombre completo, versión, alias, `run_id`, resultado de la ida y
   vuelta, fecha) y `reports/08_registro.md` completo con las cifras reales.

## Casos límite

- **Sin conexión con Databricks** (sin `.env`, sin red, cuota agotada): se registra en local; el reporte dice "local" y por qué. No es
  un error, es el respaldo previsto.
- **Se ejecuta el notebook dos veces:** queda una versión nueva y el alias `champion` pasa a ella; el reporte anota cuál es la vigente.
- **Falta `final_pipeline.joblib`** (no se sube a GitHub, pesa): el notebook pide ejecutar primero la etapa 07; no reentrena por su cuenta.
- **El modelo recuperado no predice igual:** se detiene; se investiga antes de seguir a la etapa 09.

## Riesgos que se vigilan

- **Datos personales:** el ejemplo de entrada sube 5 filas del entrenamiento a Databricks. La columna `id` es un número interno del
  dataset público (no identifica a una persona real), pero si la firma no la necesita se **excluye** del ejemplo.
- **Secretos:** el token de `.env` nunca se imprime ni se escribe en los reportes ni en las etiquetas.
- **Archivos *pickle*:** el modelo se guarda con *cloudpickle* (el formato por defecto de MLflow rechaza un `Pipeline` con
  transformadores propios). Un *pickle* puede ejecutar código al cargarse: solo se cargan modelos de nuestro propio registro.

## Supuestos

- El nombre `venta_cruzada_seguros` (cambiado en 007, 2026-11-06; antes `venta_cruzada_lgbm`) y el experimento `venta-cruzada-registro` son elecciones de este borrador; el grupo puede cambiarlos.
- Columnas de la firma: las 11 con las que se ajustó el `Pipeline` (`id`, `Gender`, `Age`, `Driving_License`, `Region_Code`,
  `Previously_Insured`, `Vehicle_Age`, `Vehicle_Damage`, `Annual_Premium`, `Vintage`, `is_min_premium`). `id` no la usa el modelo (se
  descarta dentro del `Pipeline`): en el plan se comprueba si el modelo predice sin ella; si es así, se quita de la firma. Que una
  persona en la app no conozca `is_min_premium` ni las categorías ya codificadas es un asunto de la etapa 09 (esquema de entrada).
- La ida y vuelta se hace en el mismo entorno (mismas versiones de `requirements.txt`).

## Criterios de aceptación

1. El registro (Databricks o local) tiene el modelo `venta_cruzada_seguros` (cambiado en 007, 2026-11-06) con una versión que lleva el alias `champion`.
2. La ejecución `modelo-final` tiene los parámetros, **todas** las métricas de la tabla (iguales a las de `07_metricas_test.json`), las
   etiquetas, la firma y el ejemplo de entrada.
3. El modelo recuperado por el alias da las mismas probabilidades que el local en 200 clientes (diferencia máxima ≤ 1e-9).
4. `reports/08_registro.json` existe con dónde, versión, alias, `run_id` y el resultado de la ida y vuelta; `reports/08_registro.md`
   tiene todas las secciones completas, sin espacios en blanco, incluido si alguien de otro grupo podría recuperar el modelo.
5. Las funciones nuevas de `src/` (si las hay) tienen prueba en `tests/`, y `pytest tests` queda en verde.
6. Ningún archivo del repositorio contiene el token ni la dirección completa del workspace.

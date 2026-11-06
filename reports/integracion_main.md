# Integración de `main` sobre el modelo final

> Fecha: 2026-11-06 · Rama: `007-integracion-main` · Especificación, plan y tareas: `specs/007-integracion-main/`.
> Decisión del grupo que la origina: **D15** en `reports/decisiones_del_grupo.md`.

## Por qué hizo falta

El grupo terminó el 2026-11-05 con **dos modelos finales**, uno en cada rama:

| | Rama de Andiry (`006-registro-modelo`) | `main` (PR #1, rama de la compañera) |
|---|---|---|
| Sin `Policy_Sales_Channel` / con `Gender` | sí / sí | sí / sí |
| Variables nuevas | **5 incluidas** | ninguna (su etapa 4 descartó otras 5 ideas) |
| `Vintage`, `Driving_License` | se conservan | se retiran (D12) |
| Hiperparámetros | Optuna, ensayo #13 | de partida (D14) |
| Clientes de entrenamiento | 304.238 (sin perfiles repetidos) | 304.887 |
| Prueba abierta | 2026-11-05 20:43 | 2026-11-05 19:09 |
| Código de `src/` | el de la rama | reescrito (limpieza, variables, entrenamiento y optimización distintos) |

**Decisión (2026-11-06):** el modelo final es el de la rama de Andiry, porque **debe incluir las 5 variables nuevas**. No se eligió
comparando cifras de prueba (ver "La prueba" abajo).

**Por qué no bastó con fusionar y resolver conflictos:** la base común de las dos ramas (`e94c0cb`) es un commit de la rama de Andiry.
Después, `main` reemplazó `src/`, `tests/`, los notebooks 01–06, `train.parquet` y los informes 04–06. Como la rama no había tocado esos
archivos, Git los tomaba de `main` **sin marcar conflicto**: se perdía el código de las 5 variables nuevas y 8 de las 9 funciones que usan
los notebooks 07 y 08, y `models/final_pipeline.joblib` no se podía cargar. Por eso cada archivo se decidió con una tabla.

## Qué se tomó de cada lado

Estados: **R** = versión de la rama · **M** = versión de `main` · **A** = se adaptó o rehízo · **Q** = se quitó.

| Archivo | Decisión | Motivo |
|---|---|---|
| `src/proyecto/config.py`, `data/cleaning.py`, `data/split.py`, `features/__init__.py`, `features/engineering.py`, `models/train.py`, `models/tuning.py` | R | Código con el que se construyó y evaluó el modelo final (5 variables nuevas, validación) |
| `src/proyecto/features/preprocessing.py`, `transformers.py` | R (`main` los había borrado) | El `Pipeline` guardado usa sus clases: sin ellos no carga |
| `src/proyecto/data/loading.py` | **Q** | Llama a funciones de la limpieza de `main` que no existen en la rama |
| `src/proyecto/models/metrics.py`, `baselines.py` | **Q** | Solo los usaban los notebooks 04–06 y 09 de `main`; la rama tiene sus equivalentes en `train.py` |
| `src/proyecto/inference/serving.py` | A | Reescrito para las columnas del modelo final (9 datos de persona → 10 columnas limpias) |
| `src/proyecto/inference/predict.py`, `schema.py` | M | Genéricos; `main` no los cambió |
| `tests/test_cleaning.py`, `test_features.py`, `test_models.py`, `test_split.py`, `test_tuning.py`, `test_preprocessing.py` | R | Prueban el código R |
| `tests/test_tournament.py` | **Q** | Probaba funciones de `main` que se quitaron |
| `tests/test_serving.py` | A | 6 pruebas nuevas (escritas antes que el código) |
| `tests/test_inference.py`, `pytest.ini`, `requirements.txt` (+ `pyarrow`), `.gitignore` | M | Configuración; `.gitignore` conserva la línea de la rama que **sí** versiona `final_pipeline.joblib` |
| `data/processed/train.parquet` | R | El modelo se entrenó con este (304.238 clientes). `test.parquet` es el mismo en las dos ramas |
| `notebooks/01` a `08` | R | Los de `main` importan funciones que ya no existen. En el 08, el nombre del registro pasa a `venta_cruzada_seguros` |
| `notebooks/09_inferencia.ipynb` | A | Rehecho: exporta desde `final_pipeline.joblib` y **ya no lee la prueba** (el de `main` leía `holdout.parquet` para comprobar el costo) |
| `models/model.joblib`, `models/input_schema.json` | A (regenerados) | Del modelo final; 9 datos en el formulario, sin canal |
| `reports/00_caso.md`, `01_eda.md`, `especificaciones/02-eda.md` | R + notas de `main` | La versión de `main` era un borrador de sus notebooks 01–02 (métrica principal PR-AUC, hipótesis del EDA en blanco). Se conservan sus notas sobre el canal (D13, P11) y el enlace al registro de decisiones |
| `especificaciones/03-preprocesamiento.md`, `specs/002-variables/spec.md` | R | Describen la limpieza y las variables de la rama |
| `reports/04_features.md`, `04_features_tabla.csv`, `05_torneo.md`, `06_optimizacion.md`, `06_best_params.json` | R | Resultados del código de la rama |
| `reports/04_features_tabla_nuevas.csv`, `05_torneo_tabla.csv` | **Q** | Resultados del código de `main` |
| `reports/06_mlflow_runs.csv` | M | Exporta las 44 ejecuciones del experimento de Optuna de la rama (ensayos, ejecuciones padre y comprobación en los reservados); sin datos personales |
| `reports/07_*` | R | Validación del modelo final; `07_validacion.md` suma la sección 3.1 (la prueba en el grupo) |
| `reports/prueba_abierta.txt` | A | Registra las dos aperturas |
| `reports/08_registro.json` | **Q** | Describía el modelo de `main` y contenía un correo personal; lo regenera T009 de `specs/006-registro-modelo` |
| `reports/08_registro.md` | R | Plantilla de la rama (se llena con T010 de `006`) |
| `reports/09_despliegue.md`, `informe_tecnico.md`, `models/ficha_modelo.md`, `presentacion/ejecutiva.md`, `README.md` | A | Estructura de `main`; modelo, variables y cifras del modelo final |
| `reports/decisiones_del_grupo.md` | A | Estado [REEMPLAZADO]; D12 y D14 → D15; P12 cerrada |
| `especificacion-proyecto.md` | A | Secciones 1–6 de la rama; la sección 7 une ambas |
| `specs/README.md` | M + 007 | Índice de especificaciones |

Los archivos quitados siguen en la historia de Git de `main` (commit `579bf8c`) por si el grupo los necesita.

## La prueba

La prueba (76.222 clientes) se abrió **dos veces** en el grupo el 2026-11-05: a las 19:09 con el modelo de `main` y a las 20:43 con el
modelo final. Cada modelo se evaluó una sola vez y nada se ajustó después de ver la prueba. El modelo final se eligió por un criterio de
alcance (incluir las variables nuevas), no por su cifra: el de `main` costó 0,3317 y el final 0,3312, una diferencia que **no se usó para
decidir**. Aun así es una desviación del principio III de la constitución y se declara en `reports/07_validacion.md` §3.1.
**Esta integración no abrió la prueba**: ninguna tarea lee `test.parquet`.

## Comprobaciones

| Qué | Resultado |
|---|---|
| Pruebas (`PYTHONUTF8=1 python -m pytest -q`) | 119 en verde (113 de la rama + 6 de `test_serving.py`) |
| Modelo final carga con el código integrado | Sí; entradas con `Gender`, `Vintage`, `Driving_License`, sin `Policy_Sales_Channel`; calcula las 5 variables nuevas |
| `train.parquet` | 304.238 filas |
| `model.joblib` frente a `final_pipeline.joblib` | Diferencia máxima de probabilidades 0 en 200 clientes de entrenamiento |
| App (`AppTest` de Streamlit) | Abre sin errores; 9 datos, sin canal; LLAMAR / NO LLAMAR; aviso de uso responsable; "no sé" funciona. La vista en el navegador la comprueba una persona (T024) |
| Correos, tokens, dirección del workspace en archivos versionados | Ninguno. **El correo sigue en la historia de Git** (commit de `main` que agregó `08_registro.json`); quitarlo de la historia exigiría reescribirla para todo el grupo |
| Cifras del modelo de `main` como vigentes en informes | Ninguna (solo como historia en el registro de decisiones y en este reporte) |

## Pendientes

- **T009 de `specs/006-registro-modelo`:** registrar el modelo final en Databricks y mover `champion` (hoy apunta a la versión 1, el modelo de `main`).
- **T024:** mirar la app en el navegador.
- **Registro de decisiones:** D01–D11 y P01–P04 conservan cifras del código de `main` (marcadas como historia); conviene revisarlas.
- Revisión del grupo en el *pull request* a `main`.

## Revisión con subagentes (T029, 2026-11-06)

**`auditor-de-fuga` — veredicto: sin fuga evidente; 2 hallazgos menores, ninguno crítico.**
- Ni `serving.py`, ni el notebook 09, ni `test_serving.py` leen la prueba. Los valores para "no sé" y el esquema salen solo de `train.parquet`.
- La app no pide ninguna columna que se conozca después de decidir: el canal queda fuera y `Vintage` son días como cliente.
- La regla de la app (menor costo esperado con `[[0, 1], [5, 0]]`) equivale a llamar si P > 1/6, la misma de la etapa 07.
- *Menor 1:* la ida y vuelta solo prueba que la traducción es correcta. No prueba que `final_pipeline.joblib` sea el modelo evaluado en la etapa 07.
  **Verificado:** el archivo entró a Git en un solo commit (`044a0fa`, etapa 08) y no cambió desde entonces (huella `66f7525…`). La
  ejecución de la etapa 07 lo guardó, pero su commit (`cdda173`) no lo incluía. Probarlo con una métrica exigiría volver a abrir la prueba,
  así que **se acepta como límite**.
- *Menor 2:* la muestra de la ida y vuelta no incluye filas con "no sé". Ese caso lo cubre `test_serving.py` con un modelo de juguete.

**`revisor-de-codigo-ia` — veredicto: aceptar con cambios.** Las 6 pruebas pasan, la lógica coincide con el contrato y con `cleaning.py`, y
no hay cifras inventadas ni secretos.

| Hallazgo | Severidad | Qué pasa en la app (comprobado el 2026-11-06) | Estado |
|---|---|---|---|
| `serving.py` no valida números escritos como texto (`ValueError` en vez de `InputValidationError`) | Media | `predict_with_scores` valida antes: «Age: hay valores que no son números» | Cubierto en la app; abierto si se usa `ServingModel` directamente |
| `Region_Code` 28,7 se redondea a 29 sin avisar | Media | **Pasa** por `predict_with_scores` (responde). En el formulario no ocurre: el campo de región solo admite enteros. La región 90 sí se rechaza («debe estar entre 0 y 52») | **Abierto** |
| Si falta una columna, sale un `KeyError` poco claro | Media | `predict_with_scores` responde «Faltan columnas: Vintage» | Cubierto en la app |
| Distingue mayúsculas y espacios («male» se rechaza) | Baja | Rechazo claro; el formulario usa listas cerradas | Aceptado: es mejor fallar que adivinar |
| En un empate, `mode()` elige el primero por orden alfabético | Baja | — | Aceptado |
| `ServingModel.predict` usa umbral 0,5, no 1/6 | Baja | La app usa `predict_with_scores` (umbral de costo) | **Abierto**: aclararlo en el docstring |
| Las pruebas usan un modelo de juguete, no el real | Baja | La equivalencia con el modelo real está en el notebook 09 (diferencia 0) | Aceptado |
| `RANGOS_POSIBLES` (topes de 10.000.000 de prima y 36.500 días) y el aviso de uso responsable viven en el notebook, no en `config.py` ni en `reports/` | Baja | — | **Abierto**: el tope de prima es una elección práctica sin dato que la respalde; el grupo debe confirmarlo |

Casos que las pruebas no cubren (sugeridos por el revisor): región no entera o negativa, textos con espacios, las 9 columnas en "no sé",
varias filas con vacíos distintos, una tabla vacía y una prima de 2.630 escrita como texto. Con muchos "no sé", la app arma un perfil
"típico" que quizá no exista: la probabilidad es menos confiable y la app no lo avisa.

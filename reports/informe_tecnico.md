# Informe técnico — Venta cruzada de seguro de vehículo

> **BORRADOR para revisión del grupo (actualizado el 2026-11-06).** Ensamblado a partir de los informes de `reports/`; las cifras de la
> prueba coinciden con `reports/07_metricas_test.json` y `reports/07_validacion.md`. Se entrega el domingo 15 de noviembre (hito H4).
> **Regla del informe:** cada decisión va con su motivo. Lo que depende de un dato externo está marcado **[PENDIENTE: dato externo]** y no se da por resuelto.
> **Integración (2026-11-06, `specs/007-integracion-main`):** el grupo tenía dos modelos finales; quedó el que incluye las 5 variables nuevas
> (D15 en `reports/decisiones_del_grupo.md`). Este informe describe **ese** modelo. Qué se tomó de cada rama: `reports/integracion_main.md`.

**Grupo:** **[PENDIENTE: P07]** (integrantes y roles) · **Repositorio:** `andiryospina/proyecto_venta_cruzada_seguro` · **App:** **[PENDIENTE]** (enlace público)

## Resumen ejecutivo

Una aseguradora quiere ofrecer un seguro de vehículo a clientes que ya tienen seguro de salud, y el equipo comercial debe decidir a quién llamar primero. Solo el 12,3 % de los clientes se interesa. Construimos un modelo (LightGBM) que ordena a los clientes por probabilidad de interés y recomienda llamar a quien supere el 16,7 %: en la prueba, al 36,5 % de la lista.

En una prueba con 76.222 clientes que el modelo nunca vio, el costo por cliente fue **0,3312** (intervalo del 95 %: 0,3263 a 0,3364) frente a **0,3720** de la mejor regla sin modelo ("llamar a quien no tiene seguro de vehículo y tuvo un daño"). Son **≈ 408 llamadas inútiles ahorradas por cada 10.000 clientes (11 %)**, con el intervalo de la diferencia entero por debajo de cero, y llamando a 11 puntos menos de la base. La cifra supone que perder a un interesado cuesta 5 veces una llamada inútil (R = 5), una hipótesis **[PENDIENTE: P01]**: con R = 10 la regla sería mejor.

Principales límites: el modelo usa la **edad y el género** (Legal debe aprobar el género) y encuentra solo a la mitad de los interesados de 18 a 29 años; se **eliminó el canal de venta** por posible fuga; y la prueba se usó para evaluar **dos** modelos del grupo (se declara en la sección 6). Enlace de la app: **[PENDIENTE]**.

## 1. Caso de negocio

> Fuente: `reports/00_caso.md` (ficha en estado `borrador`; la aprueba el instructor, **P10**).

- **Quién decide y qué decide:** el gerente de la campaña comercial decide a quién contactar y en qué orden; el asesor hace la llamada y cierra la venta (por confirmar con la aseguradora, **P06**).
- **Con qué información:** edad, género, licencia de conducir, región, antigüedad del vehículo, daño previo, si ya tiene seguro de vehículo, prima anual y días como cliente.
- **Qué cuesta equivocarse:** no llamar a un interesado cuesta una venta; llamar a un no interesado cuesta el tiempo de un asesor. Se asume R = 5 (matriz `[[0, 1], [5, 0]]`) **[PENDIENTE: P01]**, con sensibilidad a 3 a 1 y 10 a 1.
- **Cómo se midió el éxito:** costo esperado por cliente (métrica principal, de negocio) y PR-AUC (técnica), frente a la regla "sin seguro de vehículo previo y con daño previo".

## 2. Datos y limpieza

> Fuente: `reports/01_eda.md`, `especificaciones/03-preprocesamiento.md` y `src/proyecto/data/`.

- **Unidad de análisis y partición:** un cliente por fila (`id` único en 381.109 filas), así que se parte por fila, estratificada por `Response` (12,26 % de interesados en ambas partes), semilla 42: 76.222 clientes de prueba. Del entrenamiento (304.887) se quitan **solo allí** 649 perfiles repetidos (misma fila y misma respuesta con distinto `id`, que aparecen al eliminar el canal; P12 cerrada): quedan **304.238**. Los 5 pliegues de validación son los mismos en las etapas 4 y 5.
- **Hallazgos y decisiones:**
  - `Gender`, `Vehicle_Damage` y `Vehicle_Age` son texto con significado fijo → códigos 0/1 y 0/1/2 (la antigüedad conserva su orden).
  - El 17 % de las primas vale exactamente 2.630, la prima mínima del producto (dato de negocio) → se conserva y se **marca** (`is_min_premium`).
  - La cola alta de la prima es real (esos clientes se interesan más) → se recorta al percentil 99,9 del entrenamiento y se aplica `log1p`, sin borrar filas.
  - Los 654 clientes sin licencia se conservan: pueden asegurar un vehículo que conduce otra persona.
  - Región es un código, no una cantidad → categoría; las regiones raras se agrupan.
  - **`Policy_Sales_Channel` se elimina** (decisión 8 del EDA; D13): es el canal de contacto y puede no conocerse antes de decidir a quién llamar (posible fuga). Se pierde una señal media (V de Cramér 0,263) **[P11]**.
  - Todo lo que aprende de los datos (recortes, categorías raras, escalas) va dentro del `Pipeline` y se ajusta solo con entrenamiento.
- **Datos personales o sensibles:** no hay nombres ni documentos. `Gender` y `Age` son sensibles: se conservan en el modelo y se auditan (sección 6).

## 3. Variables

> Fuente: `reports/04_features.md`.

Se crearon 5 variables nuevas a partir del EDA, todas calculadas fila por fila con datos que se conocen antes de llamar: sin seguro y con daño (`uninsured_with_damage`), daño × antigüedad del vehículo (`damage_x_vehicle_age`), cliente menor de 30 años (`is_young_customer`), distancia a la edad de mayor interés, 42 años (`age_peak_distance`), y prima por año de edad (`premium_per_age`).

- **Medición (LightGBM, 5 pliegues):** **ninguna pasa la regla escrita antes de medir** (mejora / ruido > 1). La mayor, `premium_per_age`, mejora 0,0007 el costo, 4 veces menos que el ruido. Tampoco empeoran: todo está dentro del ruido.
- **Decisión del grupo (2026-10-31): el torneo y el modelo final las usan**, en contra de la regla de la etapa. Motivo: los modelos simples (regresión logística, árbol) no descubren solos las interacciones ni la campana de la edad. El torneo lo confirmó: con ellas la regresión baja de 0,3542 a 0,3389 (mejora / ruido 4,9; gana en 5 de 5 pliegues). Para LightGBM el efecto es nulo.
- **2026-11-06 (D15):** el grupo ratificó que el modelo final **debe** incluirlas. Las ideas que `main` descartó en su etapa 4 eran **otras** (recorte de la prima, tasa histórica de región, etc.).
- **`Vintage` y `Driving_License` se conservan** (aportan poco, pero no hay costo en mantenerlas); `Gender` se conserva por decisión del grupo.

## 4. Torneo de modelos

> Fuente: `reports/05_torneo.md`.

Cinco modelos y dos líneas base, con los mismos datos (base + 5 nuevas), los mismos 5 pliegues y parámetros de partida fijos:

| Modelo | Costo por cliente ± pliegues | PR-AUC | Segundos por pliegue |
|---|---|---|---|
| **LightGBM** | **0,3324 ± 0,0030** | 0,3469 | 2,4 |
| XGBoost | 0,3329 ± 0,0028 | 0,3472 | 8,5 |
| Random forest | 0,3336 ± 0,0033 | 0,3477 | 26,9 |
| Árbol de decisión | 0,3357 ± 0,0043 | 0,3246 | 1,9 |
| Regresión logística | 0,3389 ± 0,0031 | 0,3356 | 3,3 |
| Regla de negocio | 0,3729 ± 0,0017 | 0,2474 | — |
| Clase más frecuente (no llamar a nadie) | 0,6133 | 0,1227 | — |

- **Todos los modelos vencen a la regla en los 5 pliegues.** LightGBM cuesta un 11 % menos, llama al 36 % en vez del 48 % y encuentra al 87 % de los interesados.
- **El umbral de negocio (1/6) es imprescindible:** con 0,5 todos cuestan ≈ 0,613, lo mismo que no llamar a nadie.
- **Elegido: LightGBM** (costo más bajo y el más rápido de los de árboles). XGBoost está empatado (diferencia / ruido 0,50) y queda como referencia; random forest se descarta por lento; árbol y regresión, por más caros.

## 5. Optimización y seguimiento

> Fuente: `reports/06_optimizacion.md`, `reports/06_mlflow_runs.csv`.

- **Diseño:** 40 ensayos de Optuna sobre LightGBM (presupuesto fijado antes), optimizando el costo de negocio con el umbral 1/6 fijo y sin balanceo de clases. Se reservó el 25 % del entrenamiento (76.060 clientes) que la búsqueda no vio; la búsqueda usó el 75 % con 3 pliegues. Regla escrita antes: usar los parámetros optimizados solo si todo el IC 95 % de la diferencia en los reservados está bajo cero.
- **Resultado:** mejor ensayo #13 (186 árboles, tasa 0,0315, 31 hojas, `min_child_samples` 137, `subsample` 0,943, `colsample_bytree` 0,601, `reg_lambda` 0,478). En los reservados el costo baja de 0,3327 a 0,3303: **−0,0024, IC 95 % [−0,0042; −0,0006]**, todo bajo cero → **se usan los parámetros optimizados**. La mejora es pequeña (≈ 24 llamadas por 10.000 clientes).
- **Seguimiento:** 40 ensayos como ejecuciones anidadas en MLflow (experimento `venta-cruzada-optimizacion`), con parámetros, métricas y etiquetas; exportados en `reports/06_mlflow_runs.csv`.
- **Nota:** en `main` se decidió no adoptar estos parámetros (D14) porque la prueba ya se había abierto con los de partida; con D15 esa decisión quedó reemplazada.

## 6. Validación e interpretación

> Fuente: `reports/07_validacion.md`, `reports/07_metricas_test.json`, `reports/07_segmentos.csv`.

- **Decisiones congeladas antes de abrir la prueba** (2026-11-05 20:43:52, `reports/07_decisiones_congeladas.json`): LightGBM optimizado, base + 5 nuevas, sin calibrar (en la reserva, calibrar no mejora: log loss −0,00008, IC 95 % [−0,00025; +0,00010]), costo con R = 5, umbral 1/6.
- **Resultado en la prueba (76.222 clientes, 2026-11-05 20:43:56):**

  | Métrica | Modelo | Regla de negocio | IC 95 % |
  |---|---|---|---|
  | **Costo por cliente** | **0,3312** | 0,3720 | modelo [0,3263; 0,3364] |
  | **Diferencia (modelo − regla)** | **−0,0408** | | **[−0,0453; −0,0362]** |
  | % a llamar | 36,5 % | 47,8 % | |
  | Recall / precisión | 87,9 % / 29,5 % | 97,7 % / 25,1 % | |
  | PR-AUC / ROC-AUC | 0,353 / 0,852 | 0,248 / 0,785 (referencia) | |

  Coincide con la reserva de la etapa 06 (0,3303): no hay señales de sobreajuste.
- **La prueba en el grupo:** los mismos 76.222 clientes se usaron **dos veces** el 2026-11-05: a las 19:09 con el modelo de `main` y a las 20:43 con este. El modelo final se eligió por un criterio de alcance fijado sin comparar cifras de prueba (incluir las variables nuevas, D15), y nada se ajustó después de verla. Aun así es una desviación de "abrir la prueba una sola vez" y se declara (`reports/07_validacion.md` §3.1).
- **Sensibilidad al supuesto de costo:** con 3 a 1 el modelo gana (0,302 frente a 0,367); con 10 a 1 **gana la regla** (0,386 frente a 0,405). El umbral correcto cambiaría y habría que decidirlo con validación, no con esta prueba.
- **Por segmento:** recall de 97,8 % (30–44 años) y 98,5 % (45–59), pero **48,3 % en 18–29 y 64,0 % en 60+**. Por género se llama al 42,1 % de los hombres y al 29,9 % de las mujeres, en proporción a su interés real (14,0 % y 10,2 %), con recall parecido (89,8 % y 85,0 %).
- **Interpretación (SHAP, 5.000 clientes):** pesan sobre todo `Previously_Insured`, `uninsured_with_damage` y `Vehicle_Damage`; luego la edad (`age_peak_distance`, `Age`), la antigüedad del vehículo y la región. `Gender` no está entre las 10 con más peso. En esencia, es **la regla de negocio refinada por edad, antigüedad del vehículo y región**. Límite: SHAP explica al modelo, no al mundo; las variables correlacionadas se reparten el crédito **[P09]**.
- **Carga de trabajo:** 3,4 llamadas por interesado encontrado (4,0 con la regla). Si los asesores solo pueden llamar al 20 %, conviene ordenar por probabilidad: captura el 56,4 % de los interesados **[P02]**.
- **Revisión de fuga** (subagente `auditor-de-fuga`): sin fuga evidente; observaciones menores aceptadas como límites (`reports/07_validacion.md` §7).

## 7. Registro del modelo

> Fuente: `reports/08_registro.md`, `models/ficha_modelo.md`, `specs/006-registro-modelo/`.

- **Pendiente (T009 de `specs/006-registro-modelo`):** registrar el modelo final en Databricks (Unity Catalog) como versión nueva de `workspace.default.venta_cruzada_seguros` y moverle el alias `champion`, con la comprobación de ida y vuelta (el modelo recuperado debe predecir igual que el local). **Hoy `champion` (versión 1) es el modelo anterior de `main`**, que ya no es el final.
- **Exportado a `models/model.joblib`** desde `models/final_pipeline.joblib` (etapa 7): capa `ServingModel` que traduce lo que escribe una persona a las columnas limpias, con su esquema en `models/input_schema.json`. Comprobado: **mismas probabilidades** que el modelo de la etapa 7 en 200 clientes de entrenamiento (diferencia máxima 0), sin volver a abrir la prueba.

## 8. Despliegue

> Fuente: `reports/09_despliegue.md`.

**[PENDIENTE]** el enlace público. La app carga `models/model.joblib` desde el repositorio, no consulta Databricks, pide 9 datos (sin canal de venta), valida los datos (el formulario no admite una edad fuera de 18–100 y la función de predicción rechaza una edad de 150 con un mensaje claro) y trata "no sé" con valores del entrenamiento. Probada en local con la prueba automática de Streamlit.

## 9. Riesgos, límites y siguientes pasos

- **Qué no hace el modelo:** no decide si se vende o se niega un seguro, predice **interés declarado** (no compra efectiva), no mide el efecto de llamar (los datos son históricos, no experimentales) y no explica por qué se interesan.
- **Límites de los datos:** un solo conjunto de una aseguradora, de época y país sin confirmar; licencia sin verificar **[P05]**. Hay perfiles idénticos con distinto `id` a ambos lados de la partición (pocos): pueden hacer las métricas apenas optimistas.
- **La prueba se usó para dos modelos** (sección 6): las cifras de este modelo son honestas porque nada se ajustó después de verla, pero la próxima evaluación debe hacerse con datos nuevos.
- **Uso responsable:** usa edad, género y región; **Legal debe aprobar el uso del género** y el grupo definir qué hacer con los interesados de 18–29 y 60+ que no recibirían la llamada **[P04]**. Falta medir el modelo sin `Gender` (con validación, no con la prueba).
- **Supuestos por confirmar:** R = 5 **[P01]** (con 10 a 1 la regla es mejor), la capacidad de llamadas **[P02]**, si hay que explicar cada llamada **[P03]** (si sí, la alternativa explicable es la regresión logística, que en el torneo costó 0,3389 frente a 0,3324; habría que optimizarla y validarla) y si el canal de venta se conoce antes de llamar **[P11]**.
- **Siguiente mejora concreta:** registrar el modelo en Databricks (T009); conseguir datos nuevos (historial de contactos, vencimiento del seguro actual) **[P08]**; vigilar la tasa real de interés frente a la predicha y reentrenar si se aleja más de 10 % relativo durante 2 campañas (D11).

## Anexo: cómo reproducir el proyecto

```bash
uv venv --python 3.12 .venv
uv pip install --python .venv/Scripts/python.exe -r requirements.txt   # en Mac/Linux: .venv/bin/python
# colocar el CSV de entrenamiento en data/raw/ (ver notebooks/03_preprocesamiento.ipynb)
# ejecutar en orden los notebooks 03_preprocesamiento a 09_inferencia (los 01 y 02 son de caso y EDA)
PYTHONUTF8=1 python -m pytest           # 119 pruebas
streamlit run app/streamlit_app.py
```

`data/processed/train.parquet` y `test.parquet` están versionados (dataset público); la prueba solo la abre la etapa 7. El seguimiento de las etapas 6 y 7 está en `mlflow_local.db` (no se versiona; la etapa 6 está exportada en `reports/06_mlflow_runs.csv`). Quien no tenga acceso a Databricks usa `models/final_pipeline.joblib` y `models/model.joblib`. Las credenciales van solo en `.env` (ignorado por Git).

---

### Lista de comprobación antes de entregar

- [x] Las **9 secciones** tienen contenido y cada decisión lleva su motivo (la 7 y la 8 tienen pasos pendientes, declarados).
- [x] Las cifras de la prueba coinciden con `reports/07_metricas_test.json` y `reports/07_validacion.md`.
- [ ] Completar integrantes, roles, nombre de la startup y enlace de la app.
- [ ] Registrar el modelo final en Databricks (T009 de `specs/006-registro-modelo`).
- [x] No hay credenciales, `.env` ni datos personales.
- [ ] El enlace de la app abre en una ventana privada.
- [ ] Un tercero reproduce el proyecto con el anexo.

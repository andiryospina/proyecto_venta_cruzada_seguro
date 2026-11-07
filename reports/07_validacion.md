# Validación e interpretación

> Cifras de `notebooks/07_validacion_interpretacion.ipynb`, ejecutado una sola vez el 2026-11-05 (salidas en
> `reports/07_metricas_test.json`, `07_segmentos.csv`, `07_calibracion.png`, `07_shap.png`, `07_shap_nombres.csv`).
> Especificación: `specs/005-validacion/spec.md`.

## 1. Decisiones congeladas (escritas ANTES de abrir la prueba)

| Decisión | Valor | Cómo se decidió (con qué datos) |
|---|---|---|
| Modelo final | LightGBM | Torneo (`reports/05_torneo.md`): menor costo en validación cruzada (0,3324) y el más rápido de los árboles |
| Parámetros (optimizados o de partida) | Optimizados (`reports/06_best_params.json`): 186 árboles, tasa 0,0315, 31 hojas, `min_child_samples` 137, `subsample` 0,943, `colsample_bytree` 0,601, `reg_lambda` 0,478 | Etapa 06: en 76.060 clientes reservados, IC 95 % de (optimizado − partida) = [−0,0042; −0,0006], todo bajo cero |
| Variables | Base + 5 nuevas, con `Gender`, sin `Policy_Sales_Channel` | Specs 002 a 004 |
| ¿Calibrar las probabilidades? | **No** | Reserva de la etapa 06 con la regla escrita (sección 2) |
| Métrica principal | Costo esperado por cliente, matriz `[[0, 1], [5, 0]]` | `especificacion-proyecto.md`, sección 4 |
| Regla de decisión | Llamar si P(interesado) > 1/6 (umbral fijo, sale de la matriz) | Spec 004 |
| Línea base | Regla de negocio: `Previously_Insured = 0` y `Vehicle_Damage = Yes` | Mejor estrategia sin modelo |
| Regla de lectura | El modelo es mejor solo si todo el IC 95 % de (costo modelo − costo línea base) está bajo cero | Spec 005 |
| **Fecha y hora en que se congelaron** | **2026-11-05 20:43:52** (`reports/07_decisiones_congeladas.json`) | 4 segundos **antes** de abrir la prueba |

## 2. Calibración (con entidades reservadas, no con la prueba)

- ¿Se evaluó? ☒ sí ☐ no. Misma reserva de la etapa 06 (25 % del entrenamiento, estratificado, semilla 7): ambos modelos
  entrenados con 228.178 clientes y medidos en 76.060.
- Regla escrita antes de mirar (con la enmienda del 2026-11-05): calibrar solo si (1) todo el IC 95 % de (log loss calibrado −
  sin calibrar) está bajo cero **y** (2) el costo no sube.
- Resultado: log loss −0,00008, IC 95 % [−0,00025; +0,00010] → **cruza el cero, la condición 1 no se cumple**. Costo +0,0001
  (0,3304 frente a 0,3303) → **la condición 2 tampoco**. **Decisión: no se calibra.** LightGBM sin balanceo de clases ya da
  probabilidades bien calibradas (curva en `reports/07_calibracion.png`), por eso la isotónica no aporta.

## 3. La prueba, abierta **una sola vez**

- Fecha y hora en que se abrió: **2026-11-05 20:43:56** (`reports/prueba_abierta.txt`), 76.222 clientes, 12,26 % interesados.
  Ningún cliente de la prueba está en el entrenamiento (comprobado en el notebook).
- ¿Se cambió algo del modelo después de verla? ☒ no ☐ sí. Lo único hecho después es **de presentación**: los nombres de las
  variables de SHAP salieron como `x0…x62` y se recuperaron del modelo guardado (`07_shap_nombres.csv`), sin volver a usar la prueba.
- La marca registra el commit `e94c0cb`; el código de esta etapa (`src/proyecto/models/validation.py` y el notebook 07) aún no
  estaba en un commit en ese momento.

### 3.1 La prueba en el grupo: se abrió dos veces *(agregado el 2026-11-06, `specs/007-integracion-main`)*

- En el grupo, la prueba (los mismos 76.222 clientes) se abrió **dos veces** el 2026-11-05, con **dos modelos distintos**:
  1. **19:09**, en `main`: LightGBM con parámetros de partida, sin variables nuevas y sin `Vintage` ni `Driving_License`.
  2. **20:43:56**, en esta rama: el modelo de este informe (5 variables nuevas, parámetros optimizados).
- **El modelo final es el segundo, y no se eligió mirando la prueba.** El criterio lo fijó el grupo el 2026-11-06 por alcance: el
  modelo final **debe incluir las 5 variables nuevas** (decisión D15 en `reports/decisiones_del_grupo.md`). Las cifras de prueba del
  modelo de `main` no se usaron para decidir nada.
- **Qué significa para quien lea estas cifras:** cada modelo se evaluó una sola vez y nada se ajustó después de ver la prueba, así que
  las cifras de la sección 3 siguen siendo honestas para este modelo. Pero que existan dos evaluaciones sobre la misma prueba es una
  desviación de la regla "la prueba se abre una sola vez" (principio III de la constitución), y por eso se declara. Si se
  hubiera elegido el de menor costo en la prueba, la cifra ganadora estaría sesgada a favor.
- La constancia de las dos aperturas está en `reports/prueba_abierta.txt`. La prueba no se volverá a abrir.

Intervalos con *bootstrap* de clientes (1.000 remuestreos; 1 fila = 1 cliente).

| Métrica | Modelo final | Línea base (regla) | Intervalo del 95 % |
|---|---|---|---|
| **Costo por cliente** (principal, menor es mejor) | **0,3312** | 0,3720 | modelo [0,3263; 0,3364] · regla [0,3682; 0,3759] |
| **Diferencia de costo (modelo − regla)** | **−0,0408** | | **[−0,0453; −0,0362]** |
| % de la base a llamar | 36,5 % | 47,8 % | |
| Recall (interesados que se llaman) | 87,9 % | 97,7 % | |
| Precisión (de los llamados, cuántos se interesan) | 29,5 % | 25,1 % | |
| PR-AUC (técnica principal) | 0,353 | 0,248* | |
| ROC-AUC | 0,852 | 0,785* | |
| % de interesados al llamar al 20 / 30 / 50 % | 56,4 / 77,9 / 98,9 % | 40,8 / 61,8 / 97,8 %* | |

\* La regla solo da dos probabilidades distintas: sus métricas de ordenamiento son de referencia, no comparables 1 a 1.

**¿Mejora a la línea base con confianza?** **Sí.** Todo el intervalo de la diferencia está bajo cero: el modelo ahorra unas
408 unidades de costo por cada 10.000 clientes (1 unidad = una llamada sin éxito) y llama a 11 puntos menos de la base.
El costo en la prueba (0,3312) es casi igual al de la reserva de la etapa 06 (0,3303): no hay señales de sobreajuste.

## 4. Errores y carga de trabajo

| Segmento | Casos | Costo | % que el modelo llama | % real de interesados | Recall |
|---|---|---|---|---|---|
| **General** | 76.222 | 0,331 | 36,5 % | 12,3 % | 87,9 % |
| Gender: hombre | 41.309 | 0,367 | 42,1 % | 14,0 % | 89,8 % |
| Gender: mujer | 34.913 | 0,289 | 29,9 % | 10,2 % | 85,0 % |
| **Edad 18–29** | 31.037 | 0,168 | 8,1 % | 4,1 % | **48,3 %** |
| Edad 30–44 | 18.848 | 0,425 | 60,3 % | 20,5 % | 97,8 % |
| Edad 45–59 | 17.060 | 0,480 | 65,4 % | 19,2 % | 98,5 % |
| **Edad 60+** | 9.277 | 0,416 | 30,0 % | 10,0 % | **64,0 %** |
| Región 28 (la más grande) | 21.263 | 0,445 | 56,7 % | 18,8 % | 94,2 % |
| Regiones con < 1.000 clientes ("otras") | 16.859 | 0,319 | 28,5 % | 9,4 % | 77,4 % |
| **Región 37** | 1.112 | 0,319 | 17,9 % | 8,6 % | **56,3 %** |
| Región 36 / 15 / 47 | 1.732 / 2.731 / 1.555 | 0,26 / 0,24 / 0,32 | 19,8 / 18,8 / 25,5 % | 8,3 / 6,6 / 10,0 % | 70,1 / 71,0 / 72,3 % |

Las 19 regiones con su detalle están en `reports/07_segmentos.csv`.

- **¿Hay un segmento al que le va peor?** Sí: los **jóvenes de 18 a 29 años** (el modelo encuentra solo a la mitad de los
  interesados) y los **mayores de 60** (64 %). Tienen tasas de interés bajas (4 % y 10 %), así que pocos clientes de esos grupos
  superan el umbral de 1/6 y el modelo casi no los llama. Es coherente con el costo (llamar a todos los jóvenes costaría más de lo
  que se recupera), pero quiere decir que **la mitad de los jóvenes interesados no recibirá la llamada**. Lo mismo, en menor medida,
  en regiones con baja tasa de interés (37, 36, 15, 47 y las pequeñas). La región 37 tiene solo ≈ 96 interesados: su recall es poco preciso.
- **Carga de trabajo:** el modelo pide llamar al **36,5 %** de la base para un 12,3 % de interesados: **3,4 llamadas por interesado
  encontrado**, frente a 4,0 con la regla (que llama al 47,8 %). El costo ya cuenta las llamadas sin éxito, pero la cifra hay que
  contrastarla con la capacidad real de los asesores: si solo pueden llamar al 20 %, conviene ordenar la lista por probabilidad
  (captura del 56 % de los interesados) en vez de usar el umbral.
- **Sensibilidad al supuesto de costo** (misma decisión, umbral 1/6 sin tocar):

  | Perder un interesado cuesta… | Modelo | Regla | Diferencia |
  |---|---|---|---|
  | 3 llamadas | 0,302 | 0,367 | −0,065 (gana el modelo) |
  | **5 llamadas (supuesto)** | **0,331** | **0,372** | **−0,041 (gana el modelo)** |
  | 10 llamadas | 0,405 | 0,386 | **+0,019 (gana la regla)** |

  **La ventaja del modelo depende del supuesto 5 a 1.** Si una venta perdida vale 10 llamadas, la regla (que llama a casi todos los
  que podrían interesarse) cuesta menos. En ese caso el umbral correcto sería 1/11, no 1/6: habría que **volver a decidirlo con
  validación**, nunca con esta prueba.

## 5. Interpretación

- **Variables que más pesan** (|SHAP| promedio en 5.000 clientes de la prueba, `07_shap_nombres.csv`):
  1. `Previously_Insured` (1,32): quien ya tiene seguro de vehículo casi nunca se interesa;
  2. `uninsured_with_damage` (0,84) y `Vehicle_Damage` (0,41): sin seguro y con daño previo, el perfil de la regla de negocio;
  3. `age_peak_distance` (0,18) y `Age` (0,11): el interés tiene forma de campana con máximo entre 35 y 50 años;
  4. `damage_x_vehicle_age` (0,11), `Vehicle_Age` (0,06), región 28 (0,05), `Annual_Premium` (0,04), `premium_per_age` (0,03).

  Para el negocio: el modelo es, en esencia, **la regla de negocio refinada por edad, antigüedad del vehículo y región**. Por eso
  llama a menos gente que la regla sin perder muchos interesados.
- **Límite de la explicación:** SHAP explica **cómo decide el modelo**, no por qué un cliente se interesa ni si el modelo acertó.
  `Previously_Insured`, `Vehicle_Damage` y las variables nuevas que se construyen con ellas están correlacionadas y **se reparten el
  crédito**: el peso de cada una por separado no se debe leer como su efecto. Ninguna importancia es causa.
- **Atributos sensibles:** `Age`, `Gender` y `Region_Code` entran al modelo.
  - `Age` pesa mucho y produce las diferencias de recall de la sección 4 (jóvenes y mayores).
  - `Gender` **no** está entre las 10 variables con más peso. El modelo llama más a hombres (42 % frente a 30 %), pero en
    proporción a su interés real (14 % frente a 10 %); el recall es parecido (90 % frente a 85 %).
  - `Region_Code` puede ser un sustituto de nivel socioeconómico.
  - **Qué haría falta antes de producción:** revisión legal del uso de edad y género para decidir contactos comerciales; medir el
    modelo **sin `Gender`** con validación (no con esta prueba) y quitarlo si el costo no empeora de forma distinguible; y vigilar el
    recall por edad y región en cada campaña.

## 6. Conclusión

- **¿El modelo sirve para la decisión del caso?** **Sí, con condiciones.** Con el supuesto de costo 5 a 1, ordena y filtra la lista
  mejor que la regla de negocio con confianza del 95 %: menos llamadas (36,5 % de la base) y menor costo por cliente (−0,041). Condiciones:
  1. **validar el supuesto 5 a 1** con el margen real de una póliza frente al costo de una llamada: con 10 a 1 ya no supera a la regla;
  2. **revisar el uso de edad y género** (sección 5);
  3. aceptar que **pierde a la mitad de los jóvenes interesados** y a un tercio de los mayores de 60 interesados, o diseñar una
     campaña aparte para ellos.
- **Qué NO debe hacerse con él:**
  - usarlo para fijar precios o negar el seguro: solo ordena una lista de llamadas;
  - leerlo como compra efectiva: predice **interés declarado**;
  - leer SHAP como causa ("los jóvenes no quieren seguro");
  - cambiar el umbral o el modelo mirando estos resultados de prueba: cualquier ajuste se decide con validación y se mide con datos nuevos.
- **Lo que no se evaluó:** el comportamiento en campañas futuras (cambios de producto o de precio), el modelo sin `Gender`, y la
  calibración por segmento.
## 7. Revisión de fuga (subagente `auditor-de-fuga`, 2026-11-05)

**Veredicto: sin fuga evidente; ningún hallazgo crítico ni medio.** Revisó 7 puntos y los 7 salen sin problema, con evidencia:
- las decisiones no usaron la prueba y su hora es anterior a la apertura;
- la calibración usó solo la reserva, que es la misma de la etapa 06: el costo sin calibrar coincide, 0,33029;
- todo lo que aprende de los datos está dentro del `Pipeline`;
- las constantes del EDA salen de la porción de exploración;
- la línea base aprende solo con el entrenamiento;
- nada calculado después de abrir la prueba cambió el modelo ni el umbral;
- `Policy_Sales_Channel` está fuera del modelo y `Vintage` se conoce antes de decidir;
- la partición por fila es válida.

Las métricas de la prueba y de la reserva son casi iguales (ROC-AUC 0,8515 frente a 0,8506).

Observaciones menores, que se aceptan como límites:
1. **La reserva se usó dos veces** (parámetros en la etapa 06 y calibración en la 07). No toca la prueba y, como la decisión fue
   "no calibrar", no tiene efecto práctico.
2. **Las marcas de tiempo las escribe el propio notebook**, y el commit `e94c0cb` de la marca no contiene el código de esta etapa.
   **Corregido:** el código, la marca y `07_decisiones_congeladas.json` quedaron en el commit `cdda173` (rama `005-validacion`).
3. **Los nombres de SHAP salieron genéricos**; ya están traducidos en `07_shap_nombres.csv` (sección 5). **Actualización 2026-11-06:** `reports/07_shap.png` se regeneró con nombres legibles con `scripts/regenerar_shap.py`, usando una muestra de 5.000 clientes del **entrenamiento** (la prueba no se volvió a abrir). El orden y los valores coinciden con los de la prueba de `07_shap_nombres.csv` (por ejemplo, 1,319 frente a 1,318 en «Ya tiene seguro de vehículo»).
4. **Hay perfiles idénticos con distinto `id` a ambos lados de la partición.** Son clientes distintos, no fuga estricta, y son pocos
   (269 filas repetidas en el EDA, 649 sin el canal). Pueden hacer las métricas apenas optimistas.

El auditor no pudo verificar de forma independiente que nadie abrió `test.parquet` antes de esta etapa: se apoya en el código y en la marca.

## 8. Seguimiento

- **MLflow:** la ejecución quedó en **MLflow local** (`mlflow_local.db`, run `231873a7c3ff45d798252037407d9451`), no en
  Databricks, porque el `.env` de quien ejecutó tenía `MLFLOW_FORCE_LOCAL` y la conexión comentada. No se repite (sería abrir la prueba
  otra vez); las cifras están completas en `reports/07_metricas_test.json` y el registro del modelo (etapa 08) se hará en Databricks.

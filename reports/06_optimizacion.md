# Informe de la optimización

> **BORRADOR para revisión del grupo.** Resultado de `notebooks/06_optimizacion.ipynb`. La mejor puntuación de una búsqueda es **optimista**: se comprueba en clientes que la búsqueda no vio.
> La prueba cerrada **no se abrió**. Estados de decisión: **[DECIDIDO]** (resuelto con evidencia del proyecto), **[ADOPTADO]** (propuesta vigente por defecto hasta que el grupo diga lo contrario) o **[PENDIENTE: dato externo]** (no se puede resolver con estos datos); registro en `reports/decisiones_del_grupo.md`. Decisión guardada en `reports/06_best_params.json`.
> Guía: `material-del-curso/kit/guia-modelado-y-optimizacion.md`, secciones 3 y 4.

## Resumen para quien decide

- Se optimizaron los **dos finalistas** (LightGBM y regresión logística) con **20 ensayos cada uno**. **Ninguna optimización resultó mejor de forma demostrable**: se conservan los parámetros de partida del torneo.
- **LightGBM:** la búsqueda vio una mejora de 0,3270 a 0,3259, pero en los clientes reservados la diferencia es **+0,0003**, con intervalo del 95 % **[-0,0017, +0,0023]**: cruza el cero. Era **ruido** (sesgo optimista).
- **Regresión logística:** el mejor ensayo fue la propia configuración de partida.
- **Umbral:** el teórico `1 ÷ (R + 1) = 16,7 %` funciona; el mínimo empírico (16,0 %) no es mejor en los reservados. **Se mantiene el teórico.**
- **Capacidad:** el óptimo está en llamar a ≈ **35 %** de los clientes. Llamar solo al 20 % cuesta ≈ **6.000 unidades por 100.000 clientes** más.
- **LightGBM contra regresión en los reservados:** la regresión cuesta +0,0025 (≈ 250 unidades por 100.000 clientes), con intervalo **[-0,0006, +0,0052]**: **no se distinguen con certeza**.

## Diseño de la búsqueda

- **Finalistas optimizados:** LightGBM y regresión logística (los del torneo, `reports/05_torneo.md`).
- **Métrica de la búsqueda:** la **misma del torneo**: costo por cliente con R = 5 (umbral 16,7 %), promedio de 3 pliegues; control con PR-AUC y log loss.
- **Espacio de búsqueda** (todos los rangos incluyen el valor de partida, comprobado con una prueba automática):

| Finalista | Parámetro | Rango | Partida | Motivo |
|---|---|---|---|---|
| LightGBM | `n_estimators` | 100 a 500 | 200 | Cuántos árboles: pocos subajustan, muchos sobreajustan |
| | `learning_rate` | 0,02 a 0,2 (log) | 0,08 | Cuánto corrige cada árbol; con tasa baja hacen falta más árboles |
| | `num_leaves` | 8 a 64 | 31 | Complejidad de cada árbol |
| | `min_child_samples` | 20 a 400 (log) | 100 | Mínimo de clientes por hoja |
| | `subsample` | 0,6 a 1,0 | 0,8 | Fracción de clientes por árbol |
| | `colsample_bytree` | 0,5 a 1,0 | 0,8 | Fracción de columnas por árbol |
| | `reg_lambda` | 0 a 10 | 0 | Penaliza pesos grandes |
| Regresión | `C` | 0,001 a 10 (log) | 1 | Inverso de la regularización |
| | `age_spline_knots` | 4 a 12 | 6 | Flexibilidad de la curva de la edad |
| | `profile_12` | sí / no | no | Añadir los 12 perfiles (en observación desde la etapa 4) |

- **Presupuesto:** **20 ensayos por finalista**, fijado antes de empezar. Cada ensayo cuesta 3 ajustes; con tan pocos ensayos una búsqueda inteligente (Optuna, TPE) y una aleatoria suelen llegar al mismo lugar. **El ensayo 0 es la configuración de partida**, medida con los mismos pliegues.
- **Clientes reservados:** **25 %** del entrenamiento (76.222 de 304.887), estratificado por `Response`, semilla 7. Hay **un cliente por fila** (`id` único), así que reservar por fila es reservar por cliente. La búsqueda usa el 75 % (228.665) con 3 pliegues.

## Seguimiento (tracking)

- **Dónde quedó registrado:** MLflow **local** (`mlflow_local.db`, ignorado por Git). Experimento: **`venta-cruzada-seguros-optimizacion`**. Databricks entra en la etapa 8.
- **¿Cada ensayo es una ejecución con parámetros, métrica y etiquetas?** ☒ sí. **40 ejecuciones** (20 por finalista), con las etiquetas `etapa`, `finalista`, `ejecucion` y `es_partida`. El notebook lo verifica con una consulta a MLflow.
- **Mejor ejecución:** LightGBM, `lightgbm-ensayo-13` (costo 0,3259); regresión, `regresion_logistica-ensayo-00` (la partida; costo 0,3277).

## Resultados de la búsqueda

| | LightGBM | Regresión logística |
|---|---|---|
| Costo de la partida (ensayo 0) | 0,3270 | 0,3277 |
| Mejor costo encontrado | 0,3259 (ensayo 13) | 0,3277 (ensayo 0) |
| Mejora aparente | +0,0011 | 0,0000 |
| Rango de los 20 ensayos | 0,3259 a 0,3326 | 0,3277 a 0,3344 |
| Puesto de la partida (de 20) | **11** | **1** |

- **Los parámetros que más influyeron** (importancia estimada por Optuna): en LightGBM, `colsample_bytree` (≈ 63 %), `n_estimators` (≈ 17 %) y `reg_lambda` (≈ 16 %); en la regresión, `C` (≈ 55 %) y `age_spline_knots` (≈ 43 %). `profile_12` pesa ≈ 2 %: confirma no incluir los 12 perfiles.
- **El modelo es poco sensible** a casi todos los parámetros (≈ 1 % cada uno): ya estaba en una zona plana.
- **El ruido entre pliegues dentro de la búsqueda es ≈ 0,0006**, y aun así la mejora aparente de 0,0011 **no sobrevivió** a la comprobación: elegir el mejor de 20 intentos subestima el ruido real.

## Comprobación honesta (clientes reservados)

> Parámetros de **partida** frente a parámetros **optimizados**, entrenados con la búsqueda y evaluados en los 76.222 clientes reservados. Intervalo del 95 % remuestreando clientes completos (1.000 repeticiones).

| Modelo | Costo con parámetros de partida | Costo con parámetros optimizados | Diferencia (optimizado − partida) | Intervalo 95 % |
|---|---|---|---|---|
| LightGBM | 0,3241 | 0,3244 | +0,0003 | **[-0,0017; +0,0023]** |
| Regresión logística | 0,3266 | 0,3266 | 0,0000 | [0,0000; 0,0000] (modelos idénticos) |

- Métricas de control sin cambio: PR-AUC 0,3687 → 0,3694 y log loss 0,2648 → 0,2648 en LightGBM.

**Regla de decisión escrita antes de mirar:** "Uso los parámetros optimizados **solo si todo el intervalo del 95 % está por debajo de cero**. Si cruza el cero, la mejora no se distingue del ruido y uso los de partida." (Por una razón de negocio además de la estadística: cambiar un modelo ya validado cuesta reentrenar, revalidar y documentar.) **[ADOPTADO · D06]**

**Resultado de la regla (¿todo el intervalo por debajo de cero?):** **No, en ninguno de los dos.** Se usan los parámetros de partida.

## Umbral y capacidad

- **Umbral:** el teórico (16,7 %) cuesta 0,3270 y el mínimo empírico (16,0 %) 0,3267. Entre **15 % y 17,5 %** el costo varía menos de 0,001. En los reservados, usar 16,0 % en vez de 16,7 % da una diferencia de **+0,0002** con intervalo **[-0,0011; +0,0015]**: no mejora. **Se mantiene `1 ÷ (R + 1)`.**
- **Robustez a R:** si el negocio usara por error el umbral de R = 4 (20 %) o de R = 6 (14,3 %) cuando la realidad fuera R = 5, el costo sería ≈ 0,331 o ≈ 0,328: a menos de 0,005 del mínimo.

| % de clientes a llamar | Costo por cliente | Compradores encontrados | Precisión | Unidades por 100.000 clientes |
|---|---|---|---|---|
| 10 % | 0,4759 | 32,2 % | 39,5 % | 47.588 |
| 20 % | 0,3868 | 57,9 % | 35,5 % | 38.682 |
| 30 % | 0,3341 | 78,7 % | 32,2 % | 33.408 |
| **35 %** | **0,3269** | **86,5 %** | 30,3 % | **32.691** |
| 40 % | 0,3326 | 92,5 % | 28,3 % | 33.262 |
| 50 % | 0,3847 | 99,0 % | 24,3 % | 38.473 |

El umbral de 16,7 % equivale a llamar al **35,0 %** de los clientes. Operar con una capacidad fija del 20 % cuesta ≈ **6.000 unidades por 100.000 clientes** y pierde el 42 % de los compradores.

## Los finalistas frente a frente (clientes reservados)

| | LightGBM | Regresión logística |
|---|---|---|
| Costo por cliente | **0,3241** | 0,3266 |
| PR-AUC | **0,3687** | 0,3538 |
| ROC-AUC | **0,8569** | 0,8538 |
| Mayor diferencia entre probabilidad predicha y real | 0,0194 | **0,0077** |

- **Regresión menos LightGBM: +0,0025** por cliente (≈ 252 unidades por 100.000), intervalo **[-0,0006; +0,0052]**: **no se puede afirmar** que LightGBM sea mejor en costo. En ranking (PR-AUC) la ventaja de LightGBM sí es clara.
- **Ambos están bien calibrados**; LightGBM tiende a ser algo optimista en el grupo de mayor probabilidad (dice 40,7 %, real 38,8 %): a vigilar en la etapa 7.
- **Lo que la regresión le dice al negocio:** quien **ya tiene seguro de vehículo** tiene un **98 % menos de posibilidades** de comprar (razón de odds 0,018); quien **tuvo un daño** tiene **6,8 veces más**; los canales 160, 151 y 152 restan (razones de odds 0,32, 0,43 y 0,51).

## Decisión

- **Parámetros que se usarán a partir de ahora:** **los de partida** para los dos finalistas, porque ninguna optimización pasó la regla. Guardados en `reports/06_best_params.json`.
- **Umbral:** **16,7 % (`1 ÷ (R + 1)`)**, con R = 5 **[PENDIENTE: dato externo · P01]** (no cambia el umbral de forma relevante: la zona plana va de 15 % a 17,5 %).
- **Modelo que pasa a la validación final:** **LightGBM como principal** y **regresión logística como alternativa explicable**. Si el negocio exige explicar cada llamada, el modelo desplegado es la regresión; si no, LightGBM. **La decisión se toma antes de abrir la prueba cerrada, que se usa una sola vez para confirmar la cifra** **[ADOPTADO POR DEFECTO · D10]**.
- **Lo que no pudimos concluir:** (1) si LightGBM es mejor que la regresión en costo (el intervalo cruza el cero); (2) el valor real de R (el umbral es robusto, pero el ahorro absoluto depende de él); (3) cómo se comporta el modelo por edad y género con la prueba cerrada (vista previa en la etapa 5).

## Decisiones de negocio antes de la etapa 7 (estado de cada una: `reports/decisiones_del_grupo.md`)

| # | Decisión | Propuesta |
|---|---|---|
| 1 | ¿Se exige explicar cada llamada? | Confirmarlo con Negocio y Legal: decide el modelo desplegado |
| 2 | Operar por umbral o por capacidad fija | **Umbral (16,7 %)**, dimensionando al equipo para ≈ 35 % de la base |
| 3 | Confirmar R | Margen por venta ÷ costo de llamada; no bloquea la etapa 7 (zona plana de 15 % a 17,5 %) |
| 4 | Piso de contacto para 20-25 y 66+ | Definir antes de la auditoría de equidad |
| 5 | Cuándo volver a optimizar | **No antes de tener datos nuevos** (historial de contactos, vencimiento del seguro actual): optimizar dio cero mejora demostrable |

## Para la clase siguiente

- **Etapa 7 (`07_validacion_interpretacion.ipynb`):** se abre la prueba cerrada **una sola vez** con el modelo elegido; se audita la equidad por género y edad; se interpreta el modelo (importancias y SHAP).
- **Etapa 8:** registro del modelo y seguimiento en Databricks.

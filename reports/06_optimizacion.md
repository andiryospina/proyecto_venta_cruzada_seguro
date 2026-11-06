# Informe de la optimización

> **BORRADOR para revisión del grupo.** Resultado de `notebooks/06_optimizacion.ipynb`, reejecutado el 2026-11-05 **sin `Policy_Sales_Channel` y con `Gender`**. La mejor puntuación de una búsqueda es **optimista**: se comprueba en clientes que la búsqueda no vio.
> La prueba cerrada **no se abrió**. Estados de decisión: **[DECIDIDO]** (resuelto con evidencia del proyecto), **[ADOPTADO]** (propuesta vigente por defecto hasta que el grupo diga lo contrario) o **[PENDIENTE: dato externo]** (no se puede resolver con estos datos); registro en `reports/decisiones_del_grupo.md`. Decisión guardada en `reports/06_best_params.json`.
> Guía: `material-del-curso/kit/guia-modelado-y-optimizacion.md`, secciones 3 y 4.

## Resumen para quien decide

- Se optimizaron los **dos finalistas** (LightGBM y regresión logística) con **20 ensayos cada uno**. **Ninguna optimización resultó mejor de forma demostrable**: se conservan los parámetros de partida del torneo.
- **LightGBM:** la búsqueda vio una mejora de 0,3331 a 0,3318, pero en los clientes reservados la diferencia es **-0,0002**, con intervalo del 95 % **[-0,0021, +0,0018]**: cruza el cero. Era **ruido** (sesgo optimista).
- **Regresión logística:** la búsqueda vio 0,3360 → 0,3341, pero en los reservados la diferencia es **-0,0006**, intervalo **[-0,0020, +0,0009]**: también cruza el cero.
- **Umbral:** el teórico `1 ÷ (R + 1) = 16,7 %` funciona; el mínimo empírico (17,5 %) no es mejor en los reservados. **Se mantiene el teórico.**
- **Capacidad:** el óptimo está en llamar a ≈ **35 %** de los clientes. Llamar solo al 20 % cuesta ≈ **7.000 unidades por 100.000 clientes** más.
- **LightGBM contra regresión en los reservados:** la regresión cuesta +0,0028 (≈ 280 unidades por 100.000 clientes), con intervalo **[+0,0002, +0,0055]**: LightGBM es mejor con confianza del 95 %, **por poco**.

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
| | `profile_12` | sí / no | no | Añadir los 12 perfiles (variable derivada descartada en la etapa 4) |

- **Presupuesto:** **20 ensayos por finalista**, fijado antes de empezar. Cada ensayo cuesta 3 ajustes; con tan pocos ensayos una búsqueda inteligente (Optuna, TPE) y una aleatoria suelen llegar al mismo lugar. **El ensayo 0 es la configuración de partida**, medida con los mismos pliegues.
- **Clientes reservados:** **25 %** del entrenamiento (76.222 de 304.887), estratificado por `Response`, semilla 7. Hay **un cliente por fila** (`id` único), así que reservar por fila es reservar por cliente. La búsqueda usa el 75 % (228.665) con 3 pliegues.

## Seguimiento (tracking)

- **Dónde quedó registrado:** MLflow **local** (`mlflow_local.db`, ignorado por Git). Experimento: **`venta-cruzada-seguros-optimizacion`**. Databricks entra en la etapa 8.
- **¿Cada ensayo es una ejecución con parámetros, métrica y etiquetas?** ☒ sí. **40 ejecuciones** (20 por finalista), con las etiquetas `etapa`, `finalista`, `ejecucion` y `es_partida`. El notebook lo verifica con una consulta a MLflow.
- **Mejor ejecución:** LightGBM, `lightgbm-ensayo-15` (costo 0,3318); regresión, `regresion_logistica-ensayo-13` (costo 0,3341). Ninguna es la de partida, pero la comprobación en reservados mostró que sus mejoras no se sostienen.

## Resultados de la búsqueda

| | LightGBM | Regresión logística |
|---|---|---|
| Costo de la partida (ensayo 0) | 0,3331 | 0,3360 |
| Mejor costo encontrado | 0,3318 (ensayo 15) | 0,3341 (ensayo 13) |
| Mejora aparente | +0,0013 | +0,0020 |
| Peor ensayo | 0,3425 | 0,3379 |
| Puesto de la partida (de 20) | **13** | **15** |

- **Parámetros que más influyeron:** la importancia estimada por Optuna está en la sección 5 del notebook. LightGBM es poco sensible a casi todos los parámetros (ya estaba en una zona plana).
- **El ruido entre pliegues dentro de la búsqueda es del orden de la mejora aparente**, y elegir el mejor de 20 intentos subestima el ruido real: por eso hace falta la comprobación en reservados.

## Comprobación honesta (clientes reservados)

> Parámetros de **partida** frente a parámetros **optimizados**, entrenados con la búsqueda y evaluados en los 76.222 clientes reservados. Intervalo del 95 % remuestreando clientes completos (1.000 repeticiones).

| Modelo | Costo con parámetros de partida | Costo con parámetros optimizados | Diferencia (optimizado − partida) | Intervalo 95 % |
|---|---|---|---|---|
| LightGBM | 0,3318 | 0,3316 | -0,0002 | **[-0,0021; +0,0018]** |
| Regresión logística | 0,3346 | 0,3340 | -0,0006 | **[-0,0020; +0,0009]** |

- Métricas de control: LightGBM, PR-AUC 0,3509 → 0,3498 y log loss 0,2679 → 0,2676; regresión, PR-AUC 0,3396 → 0,3428 y log loss 0,2691 → 0,2688. Mejoras pequeñas que no alcanzan para cambiar la decisión de costo.

**Regla de decisión escrita antes de mirar:** "Uso los parámetros optimizados **solo si todo el intervalo del 95 % está por debajo de cero**. Si cruza el cero, la mejora no se distingue del ruido y uso los de partida." (Por una razón de negocio además de la estadística: cambiar un modelo ya validado cuesta reentrenar, revalidar y documentar.) **[ADOPTADO · D06]**

**Resultado de la regla (¿todo el intervalo por debajo de cero?):** **No, en ninguno de los dos.** Se usan los parámetros de partida.

## Umbral y capacidad

- **Umbral:** el teórico (16,7 %) cuesta 0,3331 y el mínimo empírico (17,5 %) 0,3330. Entre **15 % y 18 %** el costo varía menos de 0,001. En los reservados, usar 17,5 % en vez de 16,7 % da una diferencia de **+0,0011** con intervalo **[-0,0004; +0,0027]**: no mejora. **Se mantiene `1 ÷ (R + 1)`.**
- **Robustez a R:** la curva es muy plana alrededor del óptimo, así que equivocarse un poco en R cuesta poco.

| % de clientes a llamar | Costo por cliente | Compradores encontrados | Precisión | Unidades por 100.000 clientes |
|---|---|---|---|---|
| 10 % | 0,4934 | 29,8 % | 36,6 % | 49.335 |
| 20 % | 0,4033 | 55,7 % | 34,1 % | 40.333 |
| 30 % | 0,3459 | 77,1 % | 31,5 % | 34.592 |
| **35 %** | **0,3331** | **85,6 %** | 30,0 % | **33.307** |
| 40 % | 0,3368 | 91,9 % | 28,2 % | 33.682 |
| 50 % | 0,3858 | 98,9 % | 24,2 % | 38.578 |

El umbral de 16,7 % equivale a llamar al **36,0 %** de los clientes. Operar con una capacidad fija del 20 % cuesta ≈ **7.000 unidades por 100.000 clientes** y pierde el 44 % de los compradores.

## Los finalistas frente a frente (clientes reservados)

| | LightGBM | Regresión logística |
|---|---|---|
| Costo por cliente | **0,3318** | 0,3346 |
| PR-AUC | **0,3509** | 0,3396 |
| ROC-AUC | **0,8503** | 0,8484 |
| Recall de compradores | 0,8771 | 0,8786 |
| Precisión (compradores) | 0,2954 | 0,2927 |
| % contactados | 36,4 % | 36,8 % |
| Mayor diferencia entre probabilidad predicha y real | **0,0074** | 0,0139 |

- **Regresión menos LightGBM: +0,0028** por cliente (≈ 281 unidades por 100.000), intervalo **[+0,0002; +0,0055]**: LightGBM es mejor con confianza del 95 %, aunque el límite inferior roza el cero. En ranking (PR-AUC) la ventaja de LightGBM es clara.
- **Ambos están bien calibrados** en los reservados.
- **Lo que la regresión le dice al negocio:** quien **ya tiene seguro de vehículo** tiene un **98 % menos de posibilidades** de comprar (razón de odds 0,016); quien **tuvo un daño** tiene **7,3 veces más**; las regiones 0, 26, 50 y 48 restan (razones de odds de 0,58 a 0,65) y las regiones 11, 29 y 18 suman (1,50 a 1,60).

## Decisión

- **Parámetros que se usarán a partir de ahora:** **los de partida** para los dos finalistas, porque ninguna optimización pasó la regla. Guardados en `reports/06_best_params.json`.
- **Umbral:** **16,7 % (`1 ÷ (R + 1)`)**, con R = 5 **[PENDIENTE: dato externo · P01]** (la zona plana va de 15 % a 18 %).
- **Modelo que pasa a la validación final:** **LightGBM como principal** y **regresión logística como alternativa explicable**. Si el negocio exige explicar cada llamada, el modelo desplegado es la regresión; si no, LightGBM. **La decisión se toma antes de abrir la prueba cerrada, que se usa una sola vez para confirmar la cifra** **[ADOPTADO POR DEFECTO · D10]**.
- **Lo que no pudimos concluir:** (1) el valor real de R (el umbral es robusto, pero el ahorro absoluto depende de él); (2) cómo se comporta el modelo por edad y género con la prueba cerrada (vista previa en la etapa 5); (3) si el canal de venta se conoce al llamar (eliminarlo costó ≈ 800 unidades por 100.000 clientes).

## Decisiones de negocio antes de la etapa 7 (estado de cada una: `reports/decisiones_del_grupo.md`)

| # | Decisión | Propuesta |
|---|---|---|
| 1 | ¿Se exige explicar cada llamada? | Confirmarlo con Negocio y Legal: decide el modelo desplegado |
| 2 | Operar por umbral o por capacidad fija | **Umbral (16,7 %)**, dimensionando al equipo para ≈ 36 % de la base |
| 3 | Confirmar R | Margen por venta ÷ costo de llamada; no bloquea la etapa 7 (zona plana de 15 % a 18 %) |
| 4 | Piso de contacto para 20-25 y 66+, y uso de `Gender` | Definir antes de la auditoría de equidad; Legal aprueba el uso del género |
| 5 | Cuándo volver a optimizar | **No antes de tener datos nuevos** (historial de contactos, vencimiento del seguro actual): optimizar dio cero mejora demostrable |

## Para la clase siguiente

- **Etapa 7 (`07_validacion_interpretacion.ipynb`):** se abre la prueba cerrada **una sola vez** con el modelo elegido; se audita la equidad por género y edad; se interpreta el modelo (importancias y SHAP).
- **Etapa 8:** registro del modelo y seguimiento en Databricks.

# Informe de la optimización

> Resultado de `notebooks/06_optimizacion.ipynb`, ejecutado el 2026-11-05. Código: `src/proyecto/models/tuning.py`
> (adaptado del `tuning.py` del ejemplo del curso). Spec, plan y tareas: `specs/004-optimizacion/`.
> La mejor puntuación de una búsqueda es **optimista**: se comprueba en clientes que la búsqueda no vio.

## Diseño de la búsqueda

- **Finalista optimizado:** LightGBM (decisión del torneo, `reports/05_torneo.md`). Mismo pipeline y mismas variables
  (base + 5 nuevas).
- **Métrica optimizada:** costo de negocio por cliente (matriz 5 a 1, llamar si P > 1/6; menor es mejor).
  **El umbral 1/6 no se optimizó:** sale de la matriz de costos. **Sin balanceo de clases:** cambiaría las probabilidades.
- **Espacio de búsqueda:**

| Parámetro | Rango | Motivo |
|---|---|---|
| `n_estimators` | 150 – 800 | Partida 300; con tasa baja hacen falta más árboles |
| `learning_rate` | 0,01 – 0,2 (log) | Partida 0,05; importa el orden de magnitud |
| `num_leaves` | 15 – 127 | Partida 31; más hojas = más interacciones |
| `min_child_samples` | 20 – 500 | Hojas grandes evitan sobreajustar a pocos clientes |
| `subsample` | 0,6 – 1,0 | Submuestreo de filas: reduce varianza |
| `colsample_bytree` | 0,5 – 1,0 | Pocas variables: no bajar de la mitad |
| `reg_lambda` | 0,001 – 10 (log) | Regularización L2 |

- **Presupuesto:** 40 ensayos de Optuna (TPE, semilla 42), fijados antes de empezar. LightGBM tarda ≈ 2–3 s por pliegue,
  así que 40 ensayos × 3 pliegues caben en unos minutos.
- **Clientes reservados:** 25 % del entrenamiento (76.060 clientes, 12,27 % interesados), estratificado por `Response`,
  semilla 7. Por fila es válido porque cada cliente aparece una sola vez (se verificó que ningún `id` está en los dos lados).
  La búsqueda usó el 75 % restante (228.178 clientes) con 3 pliegues estratificados. **La prueba no se abrió.**

## Seguimiento (tracking)

- **Dónde quedó registrado:** MLflow **local** (`mlflow_local.db`), experimento `venta-cruzada-optimizacion`.
  El `.env` tiene `MLFLOW_FORCE_LOCAL=1` y no tiene credenciales de Databricks; con la conexión configurada, el mismo
  notebook registra en Databricks.
- **¿Está cada ensayo como una ejecución con parámetros, métrica y etiquetas?** ☒ sí: 40 ejecuciones anidadas
  `lightgbm-trial-N` dentro de `optuna-lightgbm-cost`, con los 7 parámetros, todas las métricas (y su desviación entre
  pliegues) y las etiquetas `etapa=06_optimizacion`, `modelo=lightgbm`, `metrica_optimizada=cost`. La comprobación quedó
  en la ejecución `comprobacion-reservada`.
- **Mejor ejecución:** `lightgbm-trial-13` (run_id `5d20ad8cfdca4d92bdc45c8c3124f5cc`), costo 0,3326 ± 0,0028.

## Resultados de la búsqueda (validación cruzada, optimista)

| | Costo ± pliegues | % a llamar | Recall | PR-AUC | Log loss |
|---|---|---|---|---|---|
| Parámetros de partida | 0,3346 ± 0,0033 | 36,1 % | 0,869 | 0,3438 | 0,2691 |
| Mejor ensayo (#13) | 0,3326 ± 0,0028 | 36,3 % | 0,874 | 0,3457 | 0,2688 |

Parámetros del ensayo 13: `n_estimators=186`, `learning_rate=0,0315`, `num_leaves=31`, `min_child_samples=137`,
`subsample=0,943`, `colsample_bytree=0,601`, `reg_lambda=0,478`.

- **Lo que más influyó** (importancia fANOVA): `learning_rate` 0,45, `min_child_samples` 0,17, `subsample` 0,16;
  `reg_lambda` casi nada (0,007).
- Los 5 mejores ensayos quedan en 0,3326–0,3328: hay una meseta. Prefieren **tasa de aprendizaje más baja** (0,027–0,043),
  **hojas con más clientes** (137–311) y **submuestreo** de filas y variables.
- La mejora en validación cruzada (−0,0020) es menor que la desviación entre pliegues (≈ 0,003): por sí sola no basta,
  de ahí la comprobación.

## Comprobación honesta (clientes reservados)

Dos LightGBM entrenados con el 75 % de búsqueda y evaluados en los 76.060 clientes reservados. Intervalo del 95 % con
*bootstrap* de clientes (1.000 remuestreos para el costo; 300 para PR-AUC).

| Métrica | Partida | Optimizado | Diferencia (optimizado − partida) | Intervalo 95 % |
|---|---|---|---|---|
| **Costo por cliente** | 0,3327 | 0,3303 | **−0,0024** | **[−0,0042 ; −0,0006]** |
| PR-AUC (control) | 0,3486 | 0,3530 | +0,0045 | [+0,0016 ; +0,0076] |
| % a llamar | 36,2 % | 36,4 % | +0,2 pp | — |
| Recall | 0,874 | 0,880 | +0,006 | — |
| Precisión | 0,296 | 0,296 | +0,000 | — |
| Log loss | 0,2682 | 0,2678 | −0,0004 | — |

Detalle en `reports/06_comprobacion.csv`.

**Regla de decisión escrita antes de mirar:** se usan los parámetros optimizados solo si **todo** el intervalo del 95 % de
(costo optimizado − costo de partida) está por debajo de cero; si cruza el cero, se conservan los de partida.

**Resultado de la regla:** ☒ todo el intervalo está bajo cero ([−0,0042 ; −0,0006]). La PR-AUC confirma en la misma
dirección (intervalo sobre cero) y la calibración no empeora.

## Decisión

- **Parámetros que se usarán a partir de ahora:** los **optimizados** (ensayo 13), guardados en `reports/06_best_params.json`.
  Cuestan 24 unidades menos por cada 10.000 clientes (≈ −0,7 %), llamando casi al mismo porcentaje de clientes y
  encontrando un poco más de interesados.
- **Lo que no pudimos concluir:**
  - La mejora es **real pero pequeña** (el límite superior del intervalo, −0,0006, está cerca de cero). La ganancia grande
    ya estaba en pasar de la regla de negocio (0,373) al modelo (≈ 0,333); la optimización afina.
  - No se optimizó XGBoost, que empataba con LightGBM en el torneo; no sabemos si optimizado lo superaría.
  - Con 40 ensayos la importancia de parámetros es una pista, no una conclusión.
  - El valor en dinero depende del supuesto 5 a 1 de la matriz, aún por validar con el negocio.

## Para la clase siguiente

- LightGBM con los parámetros optimizados pasa a la **etapa 07**: se reentrena con todo el entrenamiento y se abre la
  prueba **una sola vez**, con el umbral 1/6.

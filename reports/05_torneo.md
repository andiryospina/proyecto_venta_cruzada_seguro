# Etapa 05 · Torneo de modelos

> Resultado de `notebooks/05_torneo.ipynb`, ejecutado el 2026-10-31. Una fila por modelo y pliegue en `reports/05_torneo_folds.csv`.
> Código: `src/proyecto/models/train.py`.

## Cómo se comparó

- **Datos:** `data/processed/train.parquet`, 304.238 clientes. La prueba no se abrió.
- **Variables:** las base más las 5 nuevas (decisión del grupo, ver `reports/04_features.md`).
- **Validación:** 5 pliegues estratificados, semilla 42. Son los mismos pliegues para todos los modelos y los mismos que en la etapa 04.
- **Métrica de negocio (decide):** costo esperado por cliente. Usa la matriz 5 a 1 y llama si P(interesado) > 1/6. Menor es mejor.
- **Métricas técnicas:** PR-AUC (principal técnica), ROC-AUC, captura al 20/30/50 %, recall, precisión, F1, exactitud balanceada, log loss y Brier.
- **Parámetros:** de partida y fijos. Se optimizan en la etapa 06.

## Resultados (media de 5 pliegues)

| Modelo | Costo ± pliegues | % a llamar | PR-AUC | ROC-AUC | Recall | Precisión | Captura 30 % | Log loss | Seg./pliegue |
|---|---|---|---|---|---|---|---|---|---|
| **LightGBM** | **0,3324 ± 0,0030** | 36,3 % | 0,3469 | 0,8494 | 0,875 | 0,296 | 77,3 % | 0,2685 | 2,4 |
| **XGBoost** | 0,3329 ± 0,0028 | 36,0 % | 0,3472 | 0,8496 | 0,871 | 0,296 | 77,4 % | **0,2685** | 8,5 |
| Random forest | 0,3336 ± 0,0033 | 36,9 % | **0,3477** | 0,8496 | 0,881 | 0,293 | 77,3 % | 0,2692 | 26,9 |
| Árbol de decisión | 0,3357 ± 0,0043 | 36,2 % | 0,3246 | 0,8432 | 0,869 | 0,294 | 76,7 % | 0,2708 | 1,9 |
| Regresión logística | 0,3389 ± 0,0031 | 35,6 % | 0,3356 | 0,8461 | 0,856 | 0,295 | 76,5 % | 0,2705 | 3,3 |
| Línea base: regla de negocio | 0,3729 ± 0,0017 | 47,9 % | 0,2474 | 0,7840 | 0,977 | 0,250 | 61,1 % | 0,2869 | 0,0 |
| Línea base: clase más frecuente | 0,6133 ± 0,0000 | 0,0 % | 0,1227 | 0,5000 | 0,000 | 0,000 | 30,0 % | 0,3722 | 0,3 |

**Costo por cada 10.000 clientes evaluados**, en unidades: 1 = una llamada sin éxito; 5 = un interesado no contactado.

| Modelo | Costo | Diferencia frente a la regla de negocio |
|---|---|---|
| LightGBM | 3.324 | 405 menos (−11 %) |
| XGBoost | 3.329 | 400 menos |
| Random forest | 3.336 | 394 menos |
| Árbol de decisión | 3.357 | 372 menos |
| Regresión logística | 3.389 | 340 menos |
| Regla de negocio | 3.729 | — |

No hay cifra real del volumen mensual. El grupo puede multiplicar por su volumen real.

## Comparación pareada (costo, mismos pliegues)

| Mejor | Contra | Diferencia media | Pliegues que gana | Diferencia / ruido |
|---|---|---|---|---|
| LightGBM | XGBoost | 0,0005 | 3 de 5 | 0,50 (empate) |
| LightGBM | Random forest | 0,0011 | 4 de 5 | 1,25 |
| XGBoost | Random forest | 0,0006 | 4 de 5 | 0,79 |
| LightGBM | Regla de negocio | 0,0405 | 5 de 5 | 17,8 |
| XGBoost | Regla de negocio | 0,0400 | 5 de 5 | 22,8 |
| Random forest | Regla de negocio | 0,0394 | 5 de 5 | 16,4 |

## Hallazgos

1. **Todos los modelos vencen a la regla de negocio en todos los pliegues.**
   - LightGBM cuesta un 11 % menos que la regla.
   - Llama al 36 % de los clientes en vez del 48 %.
   - Encuentra el 87 % de los interesados, contra el 98 % de la regla.
   - Hace menos llamadas sin éxito y pierde algunos interesados. Con la matriz 5 a 1 el balance es favorable.
2. **El umbral de negocio (1/6) es imprescindible.** Con umbral 0,5 todos los modelos cuestan ~0,613, lo mismo que no llamar a nadie, porque casi ningún cliente supera el 50 % de probabilidad de interés.
3. **Los tres modelos de árboles en conjunto (LightGBM, XGBoost y random forest) están empatados en ordenamiento:** PR-AUC 0,347–0,348 y ROC-AUC ≈ 0,85.
   - Las diferencias de costo son del orden del ruido entre pliegues.
   - Los rankings de negocio y técnico no coinciden del todo: random forest es 1.º en PR-AUC y 3.º en costo.
   - La diferencia viene de cómo decide cada uno con el umbral, no de qué tan bien ordena.
4. **Las variables nuevas sí ayudan a la regresión logística.**
   - Su costo baja de 0,3542 a 0,3389 (mejora / ruido 4,9; gana en 5 de 5 pliegues).
   - Al árbol casi no lo ayudan (0,3365 a 0,3357; 0,18).
   - Esto confirma el motivo de la decisión del grupo en la etapa 04.

## Finalistas

| Finalista | Por qué | Qué podría cambiar con la optimización |
|---|---|---|
| **LightGBM** | El costo más bajo, el más rápido de los tres de árboles en conjunto (2,4 s por pliegue) y gana a random forest en 4 de 5 pliegues | Número de árboles, hojas, tasa de aprendizaje y regularización |
| **XGBoost** | Empatado con LightGBM (diferencia / ruido 0,50) y el mejor calibrado (log loss 0,2685), lo que importa porque la decisión aplica un umbral a la probabilidad | Profundidad, tasa de aprendizaje y submuestreo |

**Descartados:**
- **Random forest:** igual de bueno, pero 11 veces más lento que LightGBM.
- **Árbol y regresión logística:** más caros. Quedan como referencias interpretables.

**Por qué el torneo no corona un campeón:** las diferencias entre los finalistas son menores que el ruido, y la optimización (etapa 06) puede cambiar el orden. Solo la prueba final de la etapa 07 dice qué tan bueno es el modelo elegido.

## Decisión del grupo (2026-10-31)

**Modelo elegido: LightGBM.** Pasa solo a la etapa 06 (optimización).

**Motivos:**
- tiene el costo más bajo del torneo (0,3324 por cliente);
- es el más rápido de los tres de árboles en conjunto: 2,4 s por pliegue, frente a 8,5 de XGBoost y 26,9 de random forest.

**Sobre XGBoost:** estaba empatado (diferencia / ruido 0,50) y queda como referencia. Si LightGBM optimizado se calibrara mal, XGBoost es la alternativa natural.
